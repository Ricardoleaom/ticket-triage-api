from sqlalchemy.orm import Session

from app.core.exceptions import BusinessRuleError, NotFoundError
from app.models.user import Role, User
from app.repositories.user_repository import UserRepository


class UserService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.users = UserRepository(db)

    def list_users(self) -> list[User]:
        return self.users.list_all()

    def change_role(self, user_id: int, role: Role, current_user: User) -> User:
        if user_id == current_user.id:
            raise BusinessRuleError("Você não pode alterar o seu próprio perfil")

        user = self.users.get_by_id(user_id)
        if user is None:
            raise NotFoundError("Usuário não encontrado")

        user.role = role
        self.db.commit()
        return user
