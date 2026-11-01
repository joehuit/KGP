"""Pytest configuration, shared test fixtures, and isolated test database harness."""

import os
import sys
from pathlib import Path
from typing import Generator
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# Ensure backend root directory is on Python path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# Configure test environment variables prior to importing application settings
os.environ["ENVIRONMENT"] = "testing"
os.environ["DEBUG"] = "False"
os.environ["SECRET_KEY"] = "test_environment_secret_key_minimum_32_characters_for_validation"
os.environ["ADMIN_API_KEY"] = "test_admin_api_key_minimum_32_characters_for_validation"
os.environ["DATABASE_URL"] = "postgresql+psycopg://kgp_user:kgp_test_pass@localhost:5432/kgp_test_db"
os.environ["CORS_ORIGINS"] = '["http://localhost:3000"]'

from app.core.config import settings
from app.core.rate_limit import get_rate_limiter
from app.core.security import AdminRole, create_access_token, get_password_hash
from app.db.base import Base
from app.models.admin_user import AdminUser
from app.models.customer import Customer
from app.api.deps import get_db_session
from app.main import app


# Isolated in-memory engine strictly for fast unit testing of ORM model logic
# NOTE: As per architecture rules, this is NOT a replacement for PostgreSQL integration testing.
TEST_SQLITE_URL = "sqlite:///:memory:"
test_engine = create_engine(
    TEST_SQLITE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Ensure test settings are loaded."""
    assert settings.ENVIRONMENT == "testing"
    yield


@pytest.fixture(scope="session")
def admin_headers() -> dict[str, str]:
    """Administrative authorization headers for privileged API testing."""
    return {"X-Admin-Key": "test_admin_api_key_minimum_32_characters_for_validation"}


@pytest.fixture(autouse=True)
def reset_rate_limiters():
    """Reset rate limiting counters between test cases."""
    get_rate_limiter().reset()
    yield
    get_rate_limiter().reset()


@pytest.fixture
def superadmin_user(db_session: Session) -> AdminUser:
    """Create a Superadmin user in the test database."""
    user = AdminUser(
        email="superadmin@kgp-test.dz",
        hashed_password=get_password_hash("SuperSecurePassword123!"),
        full_name="Super Administrator",
        role=AdminRole.SUPERADMIN.value,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def superadmin_token(superadmin_user: AdminUser) -> str:
    """JWT access token for Superadmin."""
    return create_access_token({
        "sub": str(superadmin_user.id),
        "email": superadmin_user.email,
        "role": AdminRole.SUPERADMIN.value,
        "type": "admin",
    })


@pytest.fixture
def admin_user(db_session: Session) -> AdminUser:
    """Create an Admin role user in the test database."""
    user = AdminUser(
        email="admin@kgp-test.dz",
        hashed_password=get_password_hash("AdminPassword123!"),
        full_name="Standard Administrator",
        role=AdminRole.ADMIN.value,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def admin_token(admin_user: AdminUser) -> str:
    """JWT access token for standard Admin."""
    return create_access_token({
        "sub": str(admin_user.id),
        "email": admin_user.email,
        "role": AdminRole.ADMIN.value,
        "type": "admin",
    })


@pytest.fixture
def operator_user(db_session: Session) -> AdminUser:
    """Create an Operator role user in the test database."""
    user = AdminUser(
        email="operator@kgp-test.dz",
        hashed_password=get_password_hash("OperatorPassword123!"),
        full_name="Warehouse Operator",
        role=AdminRole.OPERATOR.value,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def operator_token(operator_user: AdminUser) -> str:
    """JWT access token for Operator."""
    return create_access_token({
        "sub": str(operator_user.id),
        "email": operator_user.email,
        "role": AdminRole.OPERATOR.value,
        "type": "admin",
    })


@pytest.fixture
def registered_customer(db_session: Session) -> Customer:
    """Create a verified test customer in the database."""
    customer = Customer(
        full_name="Arezki Dahmani",
        phone_number="0550112233",
        business_name="Arezki GSM Repair",
        wilaya="Tizi Ouzou",
        address="Rue Larbi Ben M'hidi",
        is_active=True,
    )
    db_session.add(customer)
    db_session.commit()
    db_session.refresh(customer)
    return customer


@pytest.fixture
def customer_token(registered_customer: Customer) -> str:
    """JWT access token for verified customer."""
    return create_access_token({
        "sub": str(registered_customer.id),
        "phone_number": registered_customer.phone_number,
        "role": "customer",
        "type": "customer",
    })


@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    """Provide an isolated, clean transactional session for testing ORM behavior."""
    Base.metadata.create_all(bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """FastAPI TestClient with overridden database session dependency."""
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db_session] = override_get_db
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
    app.dependency_overrides.clear()


def is_postgres_available() -> bool:
    """Helper to detect if a real PostgreSQL server is reachable for integration tests."""
    import socket
    try:
        sock = socket.create_connection((settings.POSTGRES_SERVER, settings.POSTGRES_PORT), timeout=1.0)
        sock.close()
        return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False
