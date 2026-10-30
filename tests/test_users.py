from tests.utils import auth_headers


def test_admin_lists_users(client, admin, requester):
    response = client.get("/users", headers=auth_headers(admin))

    assert response.status_code == 200
    emails = [user["email"] for user in response.json()]
    assert emails == ["ana@empresa.com", "maria@empresa.com"]


def test_requester_cannot_list_users(client, requester):
    response = client.get("/users", headers=auth_headers(requester))

    assert response.status_code == 403


def test_agent_cannot_list_users(client, agent):
    response = client.get("/users", headers=auth_headers(agent))

    assert response.status_code == 403


def test_admin_promotes_requester_to_agent(client, admin, requester):
    response = client.patch(
        f"/users/{requester.id}/role", json={"role": "agent"}, headers=auth_headers(admin)
    )

    assert response.status_code == 200
    assert response.json()["role"] == "agent"


def test_admin_cannot_change_own_role(client, admin):
    response = client.patch(
        f"/users/{admin.id}/role", json={"role": "requester"}, headers=auth_headers(admin)
    )

    assert response.status_code == 422


def test_change_role_of_unknown_user(client, admin):
    response = client.patch("/users/999/role", json={"role": "agent"}, headers=auth_headers(admin))

    assert response.status_code == 404


def test_change_role_rejects_unknown_role(client, admin, requester):
    response = client.patch(
        f"/users/{requester.id}/role", json={"role": "superuser"}, headers=auth_headers(admin)
    )

    assert response.status_code == 422
