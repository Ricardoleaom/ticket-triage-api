from datetime import UTC, datetime

from sqlalchemy import ColumnElement, func, select
from sqlalchemy.orm import Session, joinedload

from app.models.ticket import ACTIVE_STATUSES, Ticket, TicketPriority, TicketStatus
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

    def count_by_status(self) -> dict[TicketStatus, int]:
        rows = self.db.execute(select(Ticket.status, func.count()).group_by(Ticket.status))
        return {status: total for status, total in rows}

    def count_by_priority(self) -> dict[TicketPriority, int]:
        rows = self.db.execute(select(Ticket.priority, func.count()).group_by(Ticket.priority))
        return {priority: total for priority, total in rows}

    def count_overdue(self, now: datetime) -> int:
        query = select(func.count()).select_from(Ticket).where(*overdue_conditions(now))
        return self.db.scalar(query) or 0

    def count_resolved(self) -> tuple[int, int]:
        resolved = select(func.count()).select_from(Ticket).where(Ticket.resolved_at.is_not(None))
        resolved_within_sla = resolved.where(Ticket.resolved_at <= Ticket.sla_due_at)
        return self.db.scalar(resolved) or 0, self.db.scalar(resolved_within_sla) or 0

    def count_triage_overridden(self) -> int:
        query = select(func.count()).select_from(Ticket).where(Ticket.triage_overridden.is_(True))
        return self.db.scalar(query) or 0

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
            conditions.extend(overdue_conditions(datetime.now(UTC)))
        return conditions


def overdue_conditions(now: datetime) -> list[ColumnElement[bool]]:
    return [Ticket.status.in_(ACTIVE_STATUSES), Ticket.sla_due_at < now]
