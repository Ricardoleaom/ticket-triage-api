from datetime import UTC, datetime

from sqlalchemy import ColumnElement, func, select
from sqlalchemy.orm import Session, joinedload

from app.models.ticket import ACTIVE_STATUSES, Ticket
from app.schemas.ticket import TicketFilters


class TicketRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, ticket_id: int) -> Ticket | None:
        return self.db.get(Ticket, ticket_id)

    def add(self, ticket: Ticket) -> None:
        self.db.add(ticket)

    def search(
        self, filters: TicketFilters, requester_id: int | None = None
    ) -> tuple[list[Ticket], int]:
        conditions = self._build_conditions(filters, requester_id)

        total = self.db.scalar(select(func.count()).select_from(Ticket).where(*conditions))
        query = (
            select(Ticket)
            .where(*conditions)
            .options(joinedload(Ticket.requester), joinedload(Ticket.assignee))
            .order_by(Ticket.id.desc())
            .limit(filters.limit)
            .offset(filters.offset)
        )
        return list(self.db.scalars(query)), total or 0

    @staticmethod
    def _build_conditions(
        filters: TicketFilters, requester_id: int | None
    ) -> list[ColumnElement[bool]]:
        conditions = []
        if requester_id is not None:
            conditions.append(Ticket.requester_id == requester_id)
        if filters.status:
            conditions.append(Ticket.status == filters.status)
        if filters.priority:
            conditions.append(Ticket.priority == filters.priority)
        if filters.category:
            conditions.append(Ticket.category == filters.category)
        if filters.assignee_id is not None:
            conditions.append(Ticket.assignee_id == filters.assignee_id)
        if filters.overdue:
            conditions.append(Ticket.status.in_(ACTIVE_STATUSES))
            conditions.append(Ticket.sla_due_at < datetime.now(UTC))
        return conditions
