from datetime import UTC, datetime, timedelta

import pytest

from app.models import TicketPriority, TicketStatus
from app.services.ticket_rules import calculate_sla_due_at, can_change_status


@pytest.mark.parametrize(
    ("priority", "hours"),
    [
        (TicketPriority.CRITICAL, 4),
        (TicketPriority.HIGH, 8),
        (TicketPriority.MEDIUM, 24),
        (TicketPriority.LOW, 72),
    ],
)
def test_sla_depends_on_priority(priority, hours):
    opened_at = datetime(2026, 1, 5, 9, 0, tzinfo=UTC)

    assert calculate_sla_due_at(priority, opened_at) == opened_at + timedelta(hours=hours)


@pytest.mark.parametrize(
    ("current", "new"),
    [
        (TicketStatus.OPEN, TicketStatus.IN_PROGRESS),
        (TicketStatus.OPEN, TicketStatus.CLOSED),
        (TicketStatus.IN_PROGRESS, TicketStatus.RESOLVED),
        (TicketStatus.IN_PROGRESS, TicketStatus.OPEN),
        (TicketStatus.RESOLVED, TicketStatus.CLOSED),
        (TicketStatus.RESOLVED, TicketStatus.IN_PROGRESS),
    ],
)
def test_allowed_transitions(current, new):
    assert can_change_status(current, new)


@pytest.mark.parametrize(
    ("current", "new"),
    [
        (TicketStatus.OPEN, TicketStatus.RESOLVED),
        (TicketStatus.OPEN, TicketStatus.OPEN),
        (TicketStatus.IN_PROGRESS, TicketStatus.CLOSED),
        (TicketStatus.RESOLVED, TicketStatus.OPEN),
    ],
)
def test_forbidden_transitions(current, new):
    assert not can_change_status(current, new)


@pytest.mark.parametrize("new", list(TicketStatus))
def test_closed_ticket_cannot_change(new):
    assert not can_change_status(TicketStatus.CLOSED, new)
