"""
Shared test fixtures for the Digital CMO AI test suite.
"""

import os
import sys
import tempfile

import pytest

# Set test environment before importing app modules
os.environ["DATABASE_URL"] = "sqlite:///./test_data/test.db"
os.environ["SECRET_KEY"] = "test-secret-key-not-for-production"
os.environ["DEBUG"] = "false"
os.environ["MEMORY_BASE_PATH"] = "./test_memory"


@pytest.fixture()
def temp_memory_dir():
    """Provide a temporary directory for memory tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


# Only import app modules if they are available (some tests are unit-only)
try:
    from fastapi.testclient import TestClient
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from app.db.session import Base, get_db
    from app.main import app

    # Test database setup
    TEST_DB_URL = "sqlite:///./test_data/test.db"
    engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    @pytest.fixture(scope="session", autouse=True)
    def setup_test_db():
        """Create test database tables once for the entire test session."""
        os.makedirs("test_data", exist_ok=True)
        Base.metadata.create_all(bind=engine)
        yield
        Base.metadata.drop_all(bind=engine)

    @pytest.fixture()
    def db_session():
        """Provide a clean database session for each test."""
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.rollback()
            session.close()

    @pytest.fixture()
    def client():
        """Provide a FastAPI test client with overridden database dependency."""
        app.dependency_overrides[get_db] = override_get_db
        with TestClient(app) as c:
            yield c
        app.dependency_overrides.clear()

    @pytest.fixture()
    def auth_headers(client):
        """Register a test user and return authorization headers."""
        signup_data = {"email": "test@example.com", "password": "testpassword123"}
        response = client.post("/auth/signup", json=signup_data)
        if response.status_code == 409:
            response = client.post("/auth/login", json=signup_data)
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

except ImportError:
    # App modules not fully available; skip integration fixtures
    pass
