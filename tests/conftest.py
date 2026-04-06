"""
Pytest configuration and fixtures for testing.
"""

from __future__ import annotations

import os
import pytest
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# Set test environment BEFORE importing app modules
os.environ["APP_ENV"] = "test"
os.environ["DATABASE_URL"] = "sqlite:///./test.db"

from backend.database import Base, get_db
from backend.main import app

# Create test database engine
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    """
    Create a fresh database session for each test.
    Automatically rolls back changes after test completes.
    """
    # Create tables
    Base.metadata.create_all(bind=engine)

    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        # Drop tables after test
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """
    Create a test client with database session override.
    """

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers(client: TestClient) -> dict:
    """
    Register a test user and return auth headers with a valid Bearer token.
    """
    # Register
    client.post(
        "/auth/register", json={"email": "test@example.com", "password": "testpass123"}
    )
    # Login
    resp = client.post(
        "/auth/token", data={"username": "test@example.com", "password": "testpass123"}
    )
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(autouse=True)
def no_background_tasks(monkeypatch):
    """
    Prevent background tasks from running during tests.
    """

    async def _noop(job_id, request, db=None):
        return None

    # Patch the background task function
    try:
        monkeypatch.setattr("backend.main._run_scans", _noop)
    except AttributeError:
        pass


@pytest.fixture
def sample_job_payload():
    """Sample job payload for testing"""
    return {
        "project_name": "test_project",
        "job_type": "attack_surface",
        "target_url": "https://example.com",
        "accept_terms": True,
        "scope": ["example.com"],
    }
