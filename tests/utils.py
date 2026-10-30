from app.core.security import create_access_token
from app.models import User

PASSWORD = "senha-segura-123"


def auth_headers(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(user.id)}"}


def open_ticket(
    client,
    user: User,
    title: str = "Senha bloqueada",
    description: str = "Minha conta foi bloqueada depois de errar a senha três vezes",
):
    return client.post(
        "/tickets",
        json={"title": title, "description": description},
        headers=auth_headers(user),
    )
