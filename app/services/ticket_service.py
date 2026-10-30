from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.exceptions import BusinessRuleError, NotFoundError
from app.models.comment import Comment
from app.models.ticket import ACTIVE_STATUSES, Ticket, TicketStatus
from app.models.user import User
from app.repositories.comment_repository import CommentRepository
from app.repositories.ticket_repository import TicketRepository
from app.repositories.user_repository import UserRepository
from app.schemas.comment import CommentCreate
from app.schemas.ticket import TicketCreate, TicketFilters, TicketUpdate
from app.services.ticket_rules import calculate_sla_due_at, can_change_status
from app.triage.base import Classifier


class TicketService:
    def __init__(self, db: Session, classifier: Classifier) -> None:
        self.db = db
        self.classifier = classifier
        self.tickets = TicketRepository(db)
        self.users = UserRepository(db)
        self.comments = CommentRepository(db)

    def open_ticket(self, data: TicketCreate, requester: User) -> Ticket:
        triage = self.classifier.classify(data.title, data.description)
        opened_at = datetime.now(UTC)

        ticket = Ticket(
            title=data.title,
            description=data.description,
            category=triage.category,
            priority=triage.priority,
            triage_source=triage.source,
            triage_reason=triage.reason,
            requester_id=requester.id,
            created_at=opened_at,
            updated_at=opened_at,
            sla_due_at=calculate_sla_due_at(triage.priority, opened_at),
        )
        self.tickets.add(ticket)
        self.db.commit()
        self.db.refresh(ticket)
        return ticket

    def get_ticket(self, ticket_id: int, user: User) -> Ticket:
        ticket = self.tickets.get_by_id(ticket_id)
        # solicitante só enxerga os próprios chamados; o 404 não revela que o id existe
        if ticket is None or not (user.is_staff or ticket.requester_id == user.id):
            raise NotFoundError("Chamado não encontrado")
        return ticket

    def search_tickets(self, filters: TicketFilters, user: User) -> tuple[list[Ticket], int]:
        requester_id = None if user.is_staff else user.id
        return self.tickets.search(filters, requester_id)

    def update_ticket(self, ticket_id: int, data: TicketUpdate, agent: User) -> Ticket:
        ticket = self.get_ticket(ticket_id, agent)
        self._ensure_not_closed(ticket)

        if data.category and data.category != ticket.category:
            ticket.category = data.category
            ticket.triage_overridden = True

        if data.priority and data.priority != ticket.priority:
            ticket.priority = data.priority
            ticket.sla_due_at = calculate_sla_due_at(data.priority, ticket.created_at)
            ticket.triage_overridden = True

        if "assignee_id" in data.model_fields_set:
            ticket.assignee_id = self._validate_assignee(data.assignee_id)

        self.db.commit()
        self.db.refresh(ticket)
        return ticket

    def change_status(self, ticket_id: int, new_status: TicketStatus, agent: User) -> Ticket:
        ticket = self.get_ticket(ticket_id, agent)
        if not can_change_status(ticket.status, new_status):
            raise BusinessRuleError(
                f"Não é possível mudar o status de '{ticket.status}' para '{new_status}'"
            )

        if new_status == TicketStatus.IN_PROGRESS and ticket.assignee_id is None:
            ticket.assignee_id = agent.id

        if new_status == TicketStatus.RESOLVED:
            ticket.resolved_at = datetime.now(UTC)
        elif new_status in ACTIVE_STATUSES:
            ticket.resolved_at = None

        ticket.status = new_status
        self.db.commit()
        self.db.refresh(ticket)
        return ticket

    def add_comment(self, ticket_id: int, data: CommentCreate, author: User) -> Comment:
        ticket = self.get_ticket(ticket_id, author)
        self._ensure_not_closed(ticket)

        comment = Comment(ticket_id=ticket.id, author_id=author.id, body=data.body)
        self.comments.add(comment)
        self.db.commit()
        self.db.refresh(comment)
        return comment

    def list_comments(self, ticket_id: int, user: User) -> list[Comment]:
        ticket = self.get_ticket(ticket_id, user)
        return self.comments.list_by_ticket(ticket.id)

    def _validate_assignee(self, assignee_id: int | None) -> int | None:
        if assignee_id is None:
            return None

        assignee = self.users.get_by_id(assignee_id)
        if assignee is None or not assignee.is_staff:
            raise BusinessRuleError("O responsável pelo chamado precisa ser um atendente")
        return assignee.id

    @staticmethod
    def _ensure_not_closed(ticket: Ticket) -> None:
        if ticket.status == TicketStatus.CLOSED:
            raise BusinessRuleError("Chamado fechado não pode ser alterado")
