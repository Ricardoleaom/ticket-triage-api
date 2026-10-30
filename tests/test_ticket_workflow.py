from datetime import datetime, timedelta

import pytest

from tests.utils import auth_headers, open_ticket


@pytest.fixture
def ticket(client, requester):
    return open_ticket(client, requester).json()


def change_status(client, ticket_id, new_status, user):
    return client.patch(
        f"/tickets/{ticket_id}/status", json={"status": new_status}, headers=auth_headers(user)
    )


def update_ticket(client, ticket_id, payload, user):
    return client.patch(f"/tickets/{ticket_id}", json=payload, headers=auth_headers(user))


def test_requester_cannot_change_status(client, requester, ticket):
    response = change_status(client, ticket["id"], "in_progress", requester)

    assert response.status_code == 403


def test_starting_work_assigns_the_agent(client, agent, ticket):
    response = change_status(client, ticket["id"], "in_progress", agent)

    assert response.status_code == 200
    assert response.json()["status"] == "in_progress"
    assert response.json()["assignee"]["id"] == agent.id


def test_cannot_resolve_ticket_that_was_not_started(client, agent, ticket):
    response = change_status(client, ticket["id"], "resolved", agent)

    assert response.status_code == 422
    assert response.json()["detail"] == "Não é possível mudar o status de 'open' para 'resolved'"


def test_resolving_sets_resolved_at(client, agent, ticket):
    change_status(client, ticket["id"], "in_progress", agent)

    response = change_status(client, ticket["id"], "resolved", agent)

    assert response.json()["resolved_at"] is not None


def test_reopening_clears_resolved_at(client, agent, ticket):
    change_status(client, ticket["id"], "in_progress", agent)
    change_status(client, ticket["id"], "resolved", agent)

    response = change_status(client, ticket["id"], "in_progress", agent)

    assert response.json()["status"] == "in_progress"
    assert response.json()["resolved_at"] is None


def test_closed_ticket_cannot_be_reopened(client, agent, ticket):
    change_status(client, ticket["id"], "closed", agent)

    response = change_status(client, ticket["id"], "open", agent)

    assert response.status_code == 422


def test_changing_priority_recalculates_sla(client, agent, ticket):
    response = update_ticket(client, ticket["id"], {"priority": "critical"}, agent)

    body = response.json()
    created_at = datetime.fromisoformat(body["created_at"])
    sla_due_at = datetime.fromisoformat(body["sla_due_at"])
    assert body["priority"] == "critical"
    assert sla_due_at - created_at == timedelta(hours=4)
    assert body["triage_overridden"] is True


def test_changing_category_marks_triage_as_overridden(client, agent, ticket):
    response = update_ticket(client, ticket["id"], {"category": "network"}, agent)

    assert response.json()["category"] == "network"
    assert response.json()["triage_overridden"] is True


def test_sending_same_values_does_not_mark_override(client, agent, ticket):
    same_values = {"category": "access", "priority": "high"}

    response = update_ticket(client, ticket["id"], same_values, agent)

    assert response.json()["triage_overridden"] is False


def test_assign_ticket_to_another_agent(client, agent, admin, ticket):
    response = update_ticket(client, ticket["id"], {"assignee_id": admin.id}, agent)

    assert response.json()["assignee"]["id"] == admin.id


def test_cannot_assign_ticket_to_requester(client, agent, requester, ticket):
    response = update_ticket(client, ticket["id"], {"assignee_id": requester.id}, agent)

    assert response.status_code == 422


def test_unassign_ticket(client, agent, ticket):
    update_ticket(client, ticket["id"], {"assignee_id": agent.id}, agent)

    response = update_ticket(client, ticket["id"], {"assignee_id": None}, agent)

    assert response.json()["assignee"] is None


def test_requester_cannot_update_ticket(client, requester, ticket):
    response = update_ticket(client, ticket["id"], {"priority": "critical"}, requester)

    assert response.status_code == 403


def test_closed_ticket_cannot_be_updated(client, agent, ticket):
    change_status(client, ticket["id"], "closed", agent)

    response = update_ticket(client, ticket["id"], {"priority": "low"}, agent)

    assert response.status_code == 422
