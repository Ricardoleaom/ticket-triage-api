from fastapi import APIRouter

from app.api.deps import AdminUser, CurrentUser, UserServiceDep
from app.models.user import User
from app.schemas.user import RoleUpdate, UserResponse

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
def read_me(user: CurrentUser) -> User:
    return user


@router.get("", response_model=list[UserResponse])
def list_users(_: AdminUser, service: UserServiceDep) -> list[User]:
    return service.list_users()


@router.patch("/{user_id}/role", response_model=UserResponse)
def change_role(user_id: int, data: RoleUpdate, admin: AdminUser, service: UserServiceDep) -> User:
    return service.change_role(user_id, data.role, current_user=admin)
