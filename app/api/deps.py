from functools import lru_cache
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import Role, User
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService
from app.services.ticket_service import TicketService
from app.services.user_service import UserService
from app.triage.base import Classifier
from app.triage.keyword_classifier import KeywordClassifier

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

DbSession = Annotated[Session, Depends(get_db)]


def get_current_user(db: DbSession, token: Annotated[str, Depends(oauth2_scheme)]) -> User:
    user_id = decode_access_token(token)
    user = UserRepository(db).get_by_id(user_id) if user_id is not None else None
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_staff(user: CurrentUser) -> User:
    if not user.is_staff:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Acesso restrito a atendentes")
    return user


def require_admin(user: CurrentUser) -> User:
    if user.role != Role.ADMIN:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Acesso restrito a administradores")
    return user


StaffUser = Annotated[User, Depends(require_staff)]
AdminUser = Annotated[User, Depends(require_admin)]


@lru_cache
def get_classifier() -> Classifier:
    return KeywordClassifier()


def get_auth_service(db: DbSession) -> AuthService:
    return AuthService(db)


def get_user_service(db: DbSession) -> UserService:
    return UserService(db)


def get_ticket_service(
    db: DbSession, classifier: Annotated[Classifier, Depends(get_classifier)]
) -> TicketService:
    return TicketService(db, classifier)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
UserServiceDep = Annotated[UserService, Depends(get_user_service)]
TicketServiceDep = Annotated[TicketService, Depends(get_ticket_service)]
