from functools import cache

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import AuthenticationError, ConflictError
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import Role, User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate

EMAIL_ALREADY_USED = "Já existe um usuário com este e-mail"
INVALID_CREDENTIALS = "E-mail ou senha inválidos"


@cache
def _dummy_password_hash() -> str:
    return hash_password("senha-que-nunca-sera-usada")


class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.users = UserRepository(db)

    def register(self, data: UserCreate, role: Role = Role.REQUESTER) -> User:
        email = data.email.lower()
        if self.users.get_by_email(email):
            raise ConflictError(EMAIL_ALREADY_USED)

        user = User(
            name=data.name,
            email=email,
            password_hash=hash_password(data.password),
            role=role,
        )
        self.users.add(user)
        try:
            self.db.commit()
        except IntegrityError:
            # outro cadastro com o mesmo e-mail pode ter sido salvo entre a consulta e o commit
            self.db.rollback()
            raise ConflictError(EMAIL_ALREADY_USED) from None

        self.db.refresh(user)
        return user

    def authenticate(self, email: str, password: str) -> str:
        user = self.users.get_by_email(email.lower())
        if user is None:
            # compara com um hash qualquer para o tempo de resposta não revelar se o e-mail existe
            verify_password(password, _dummy_password_hash())
            raise AuthenticationError(INVALID_CREDENTIALS)

        if not verify_password(password, user.password_hash):
            raise AuthenticationError(INVALID_CREDENTIALS)

        return create_access_token(user.id)
