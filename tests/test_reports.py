from datetime import UTC, datetime, timedelta

from app.models import Ticket
from tests.utils import auth_headers, open_ticket


def get_summary(client, user):
    return client.get("/reports/summary", headers=auth_headers(user))


def change_status(client, ticket_id, new_status, user):
    client.patch(
        f"/tickets/{ticket_id}/status", json={"status": new_status}, headers=auth_headers(user)
    )


def move_sla_to_the_past(db, ticket_id):
    ticket = db.get(Ticket, ticket_id)
    ticket.sla_due_at = datetime.now(UTC) - timedelta(hours=1)
    db.commit()


def test_summary_without_tickets(client, agent):
    response = get_summary(client, agent)

    assert response.status_code == 200
    body = response.json()
    assert body["total_tickets"] == 0
    assert body["by_status"] == {"open": 0, "in_progress": 0, "resolved": 0, "closed": 0}
    assert body["sla_compliance_rate"] is None
    assert body["triage_override_rate"] is None


def test_requester_cannot_see_reports(client, requester):
    response = get_summary(client, requester)

    assert response.status_code == 403


def test_summary_counts_sla_and_triage_corrections(client, db, requester, agent):
    on_time = open_ticket(client, requester).json()["id"]
    late = open_ticket(
        client,
        requester,
        title="Dúvida sobre o Excel",
        description="Como faço uma tabela dinâmica no Excel?",
    ).json()["id"]
    overdue = open_ticket(client, requester).json()["id"]

    change_status(client, on_time, "in_progress", agent)
    change_status(client, on_time, "resolved", agent)

    move_sla_to_the_past(db, late)
    change_status(client, late, "in_progress", agent)
    change_status(client, late, "resolved", agent)

    client.patch(f"/tickets/{overdue}", json={"category": "network"}, headers=auth_headers(agent))
    move_sla_to_the_past(db, overdue)

    body = get_summary(client, agent).json()

    assert body["total_tickets"] == 3
    assert body["by_status"]["open"] == 1
    assert body["by_status"]["resolved"] == 2
    assert body["by_priority"]["high"] == 2
    assert body["by_priority"]["low"] == 1
    assert body["overdue"] == 1
    assert body["sla_compliance_rate"] == 50.0
    assert body["triage_override_rate"] == 33.3
