from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models.ticket import TicketPriority, TicketStatus
from app.repositories.ticket_repository import TicketRepository
from app.schemas.report import SummaryReport


class ReportService:
    def __init__(self, db: Session) -> None:
        self.tickets = TicketRepository(db)

    def summary(self) -> SummaryReport:
        by_status = self.tickets.count_by_status()
        by_priority = self.tickets.count_by_priority()
        total = sum(by_status.values())
        resolved, resolved_within_sla = self.tickets.count_resolved()

        return SummaryReport(
            total_tickets=total,
            by_status={status: by_status.get(status, 0) for status in TicketStatus},
            by_priority={priority: by_priority.get(priority, 0) for priority in TicketPriority},
            overdue=self.tickets.count_overdue(datetime.now(UTC)),
            sla_compliance_rate=percentage(resolved_within_sla, resolved),
            triage_override_rate=percentage(self.tickets.count_triage_overridden(), total),
        )


def percentage(part: int, total: int) -> float | None:
    if total == 0:
        return None
    return round(part / total * 100, 1)
