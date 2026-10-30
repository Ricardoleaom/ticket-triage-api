from app.core.security import create_access_token
from app.models import User

PASSWORD = "senha-segura-123"


def auth_headers(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(user.id)}"}
