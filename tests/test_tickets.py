from datetime import UTC, datetime, timedelta

from app.models import Ticket
from tests.utils import auth_headers, open_ticket


def test_open_ticket_runs_triage(client, requester):
    response = open_ticket(client, requester)

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "open"
    assert body["category"] == "access"
    assert body["priority"] == "high"
    assert body["triage_source"] == "keywords"
    assert body["triage_overridden"] is False
    assert body["requester"] == {"id": requester.id, "name": requester.name}
    assert body["assignee"] is None


def test_sla_is_calculated_from_priority(client, requester):
    body = open_ticket(client, requester).json()

    created_at = datetime.fromisoformat(body["created_at"])
    sla_due_at = datetime.fromisoformat(body["sla_due_at"])
    assert sla_due_at - created_at == timedelta(hours=8)


def test_open_ticket_validates_input(client, requester):
    response = open_ticket(client, requester, title="Oi", description="curta")

    assert response.status_code == 422


def test_open_ticket_requires_authentication(client):
    response = client.post("/tickets", json={"title": "Sem login", "description": "x" * 20})

    assert response.status_code == 401


def test_requester_lists_only_own_tickets(client, requester, make_user):
    colleague = make_user("pedro@empresa.com")
    open_ticket(client, requester)
    open_ticket(client, colleague)

    response = client.get("/tickets", headers=auth_headers(requester))

    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["requester"]["id"] == requester.id


def test_staff_lists_all_tickets(client, requester, agent, make_user):
    colleague = make_user("pedro@empresa.com")
    open_ticket(client, requester)
    open_ticket(client, colleague)

    response = client.get("/tickets", headers=auth_headers(agent))

    assert response.json()["total"] == 2


def test_requester_cannot_see_ticket_from_another_user(client, requester, make_user):
    colleague = make_user("pedro@empresa.com")
    ticket_id = open_ticket(client, colleague).json()["id"]

    response = client.get(f"/tickets/{ticket_id}", headers=auth_headers(requester))

    assert response.status_code == 404


def test_agent_sees_any_ticket(client, requester, agent):
    ticket_id = open_ticket(client, requester).json()["id"]

    response = client.get(f"/tickets/{ticket_id}", headers=auth_headers(agent))

    assert response.status_code == 200


def test_get_unknown_ticket(client, agent):
    response = client.get("/tickets/999", headers=auth_headers(agent))

    assert response.status_code == 404


def test_filters_by_priority_and_category(client, requester, agent):
    open_ticket(client, requester)
    open_ticket(
        client,
        requester,
        title="Dúvida sobre o Excel",
        description="Como faço uma tabela dinâmica no Excel?",
    )
    headers = auth_headers(agent)

    by_priority = client.get("/tickets", params={"priority": "low"}, headers=headers).json()
    by_category = client.get("/tickets", params={"category": "access"}, headers=headers).json()

    assert by_priority["total"] == 1
    assert by_priority["items"][0]["category"] == "software"
    assert by_category["total"] == 1
    assert by_category["items"][0]["priority"] == "high"


def test_filters_overdue_tickets(client, db, requester, agent):
    late_id = open_ticket(client, requester).json()["id"]
    open_ticket(client, requester)
    late_ticket = db.get(Ticket, late_id)
    late_ticket.sla_due_at = datetime.now(UTC) - timedelta(hours=1)
    db.commit()

    response = client.get("/tickets", params={"overdue": True}, headers=auth_headers(agent))

    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["id"] == late_id


def test_list_is_paginated_newest_first(client, requester):
    ids = [open_ticket(client, requester).json()["id"] for _ in range(3)]
    headers = auth_headers(requester)

    first_page = client.get("/tickets", params={"limit": 2}, headers=headers).json()
    second_page = client.get("/tickets", params={"limit": 2, "offset": 2}, headers=headers).json()

    assert first_page["total"] == 3
    assert [item["id"] for item in first_page["items"]] == [ids[2], ids[1]]
    assert [item["id"] for item in second_page["items"]] == [ids[0]]


def test_list_rejects_limit_above_maximum(client, requester):
    response = client.get("/tickets", params={"limit": 500}, headers=auth_headers(requester))

    assert response.status_code == 422
