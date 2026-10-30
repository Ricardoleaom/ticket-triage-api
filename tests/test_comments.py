import pytest

from tests.utils import auth_headers, open_ticket


@pytest.fixture
def ticket(client, requester):
    return open_ticket(client, requester).json()


def add_comment(client, ticket_id, body, user):
    return client.post(
        f"/tickets/{ticket_id}/comments", json={"body": body}, headers=auth_headers(user)
    )


def test_requester_comments_on_own_ticket(client, requester, ticket):
    response = add_comment(client, ticket["id"], "Consegue ver hoje ainda?", requester)

    assert response.status_code == 201
    assert response.json()["author"]["id"] == requester.id


def test_comments_are_listed_in_order(client, requester, agent, ticket):
    add_comment(client, ticket["id"], "Já reiniciei o computador", requester)
    add_comment(client, ticket["id"], "Vou desbloquear a conta agora", agent)

    response = client.get(f"/tickets/{ticket['id']}/comments", headers=auth_headers(requester))

    bodies = [comment["body"] for comment in response.json()]
    assert bodies == ["Já reiniciei o computador", "Vou desbloquear a conta agora"]


def test_other_requester_cannot_comment(client, make_user, ticket):
    stranger = make_user("pedro@empresa.com")

    response = add_comment(client, ticket["id"], "Olá", stranger)

    assert response.status_code == 404


def test_other_requester_cannot_read_comments(client, make_user, ticket):
    stranger = make_user("pedro@empresa.com")

    response = client.get(f"/tickets/{ticket['id']}/comments", headers=auth_headers(stranger))

    assert response.status_code == 404


def test_cannot_comment_on_closed_ticket(client, agent, ticket):
    client.patch(
        f"/tickets/{ticket['id']}/status", json={"status": "closed"}, headers=auth_headers(agent)
    )

    response = add_comment(client, ticket["id"], "Ainda está com problema", agent)

    assert response.status_code == 422


def test_comment_cannot_be_blank(client, requester, ticket):
    response = add_comment(client, ticket["id"], "   ", requester)

    assert response.status_code == 422
