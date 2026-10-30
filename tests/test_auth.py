import pytest

from app.core.config import settings
from tests.utils import PASSWORD, auth_headers


def register(client, **overrides):
    payload = {"name": "Maria Silva", "email": "maria@empresa.com", "password": PASSWORD}
    payload.update(overrides)
    return client.post("/auth/register", json=payload)


def login(client, email, password):
    return client.post("/auth/login", data={"username": email, "password": password})


def test_register_creates_requester(client):
    response = register(client, email="Maria@Empresa.com")

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "maria@empresa.com"
    assert body["role"] == "requester"
    assert "password" not in body
    assert "password_hash" not in body


def test_register_rejects_duplicate_email(client, requester):
    response = register(client, email="MARIA@empresa.com")

    assert response.status_code == 409
    assert response.json()["detail"] == "Já existe um usuário com este e-mail"


@pytest.mark.parametrize(
    "overrides",
    [
        {"password": "curta"},
        {"password": "ç" * 40},
        {"email": "email-invalido"},
        {"name": "A"},
    ],
)
def test_register_validates_input(client, overrides):
    response = register(client, **overrides)

    assert response.status_code == 422


def test_login_returns_token(client, requester):
    response = login(client, "maria@empresa.com", PASSWORD)

    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    assert response.json()["access_token"]


def test_login_ignores_email_case(client, requester):
    response = login(client, "Maria@Empresa.COM", PASSWORD)

    assert response.status_code == 200


def test_login_with_wrong_password(client, requester):
    response = login(client, "maria@empresa.com", "senha-errada")

    assert response.status_code == 401
    assert response.json()["detail"] == "E-mail ou senha inválidos"


def test_login_with_unknown_email_returns_same_error(client):
    response = login(client, "ninguem@empresa.com", PASSWORD)

    assert response.status_code == 401
    assert response.json()["detail"] == "E-mail ou senha inválidos"


def test_login_with_password_longer_than_bcrypt_limit(client, requester):
    response = login(client, "maria@empresa.com", "a" * 100)

    assert response.status_code == 401


def test_me_returns_logged_user(client, requester):
    response = client.get("/users/me", headers=auth_headers(requester))

    assert response.status_code == 200
    assert response.json()["email"] == "maria@empresa.com"


def test_me_requires_token(client):
    response = client.get("/users/me")

    assert response.status_code == 401


def test_me_rejects_invalid_token(client):
    response = client.get("/users/me", headers={"Authorization": "Bearer token-falso"})

    assert response.status_code == 401


def test_me_rejects_expired_token(client, requester, monkeypatch):
    monkeypatch.setattr(settings, "access_token_expire_minutes", -1)

    response = client.get("/users/me", headers=auth_headers(requester))

    assert response.status_code == 401
