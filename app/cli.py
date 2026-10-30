import argparse
import getpass
import sys

from pydantic import ValidationError

from app.core.database import SessionLocal
from app.core.exceptions import ConflictError
from app.models.user import Role
from app.schemas.user import UserCreate
from app.services.auth_service import AuthService


def main() -> None:
    parser = argparse.ArgumentParser(description="Cria um usuário administrador.")
    parser.add_argument("--name", required=True)
    parser.add_argument("--email", required=True)
    args = parser.parse_args()

    password = getpass.getpass("Senha: ")
    try:
        data = UserCreate(name=args.name, email=args.email, password=password)
    except ValidationError as error:
        sys.exit(f"Dados inválidos:\n{error}")

    with SessionLocal() as db:
        try:
            AuthService(db).register(data, role=Role.ADMIN)
        except ConflictError as error:
            sys.exit(error.message)

    print(f"Administrador {data.email} criado com sucesso.")


if __name__ == "__main__":
    main()
