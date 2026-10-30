import os

os.environ.setdefault("JWT_SECRET_KEY", "chave-usada-somente-nos-testes-automatizados")
os.environ.setdefault("BCRYPT_ROUNDS", "4")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.security import hash_password
from app.main import app
from app.models import Role, User
from tests.utils import PASSWORD

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "sqlite://")

if TEST_DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
else:
    engine = create_engine(TEST_DATABASE_URL)

TestingSession = sessionmaker(bind=engine, autoflush=False)


@pytest.fixture
def db():
    Base.metadata.create_all(engine)
    session = TestingSession()
    yield session
    session.close()
    Base.metadata.drop_all(engine)


@pytest.fixture
def client(db):
    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def make_user(db):
    def _make_user(email: str, role: Role = Role.REQUESTER) -> User:
        user = User(
            name=email.split("@")[0].title(),
            email=email,
            password_hash=hash_password(PASSWORD),
            role=role,
        )
        db.add(user)
        db.commit()
        return user

    return _make_user


@pytest.fixture
def requester(make_user):
    return make_user("maria@empresa.com")


@pytest.fixture
def agent(make_user):
    return make_user("joao@empresa.com", Role.AGENT)


@pytest.fixture
def admin(make_user):
    return make_user("ana@empresa.com", Role.ADMIN)
