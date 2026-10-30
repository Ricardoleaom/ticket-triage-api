from datetime import datetime, timedelta

from app.models.ticket import TicketPriority, TicketStatus

SLA_HOURS = {
    TicketPriority.CRITICAL: 4,
    TicketPriority.HIGH: 8,
    TicketPriority.MEDIUM: 24,
    TicketPriority.LOW: 72,
}

ALLOWED_TRANSITIONS = {
    TicketStatus.OPEN: {TicketStatus.IN_PROGRESS, TicketStatus.CLOSED},
    TicketStatus.IN_PROGRESS: {TicketStatus.OPEN, TicketStatus.RESOLVED},
    TicketStatus.RESOLVED: {TicketStatus.IN_PROGRESS, TicketStatus.CLOSED},
    TicketStatus.CLOSED: set(),
}


def calculate_sla_due_at(priority: TicketPriority, opened_at: datetime) -> datetime:
    return opened_at + timedelta(hours=SLA_HOURS[priority])


def can_change_status(current: TicketStatus, new: TicketStatus) -> bool:
    return new in ALLOWED_TRANSITIONS[current]
