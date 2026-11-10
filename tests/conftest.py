import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.config import settings
from app.core.security import create_access_token, hash_password
from app.db.models import Organization, Plan, User
from app.db.seed import seed_database
from app.db.session import Base, get_db
from app.main import app

# In-memory SQLite for isolated test runs
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    seed_database(db)
    db.close()
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db():
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers(db):
    admin = db.query(User).filter(User.email == "admin@nuviogrowth.com").first()
    token = create_access_token(
        subject=admin.id,
        claims={"org_id": admin.organization_id, "role": admin.role, "email": admin.email},
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def editor_auth_headers(db):
    editor = db.query(User).filter(User.email == "editor@nuviogrowth.com").first()
    token = create_access_token(
        subject=editor.id,
        claims={"org_id": editor.organization_id, "role": editor.role, "email": editor.email},
    )
    return {"Authorization": f"Bearer {token}"}

