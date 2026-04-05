"""
Tests for backend models and database operations.
"""

from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from backend.models import Job, User, JobType, JobStatus, ScanHistory
from backend.database import Base


def test_user_model_creation(db_session: Session):
    """Test creating a User model instance"""
    user = User(
        email="model_test@example.com",
        hashed_password="fakehash"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    assert user.id is not None
    assert user.email == "model_test@example.com"
    assert user.is_active is True
    assert user.created_at is not None


def test_user_repr(db_session: Session):
    """Test User string representation"""
    user = User(email="repr@example.com", hashed_password="hash")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    assert "repr@example.com" in repr(user)


def test_user_email_unique(db_session: Session):
    """Test that duplicate emails are rejected"""
    user1 = User(email="unique@example.com", hashed_password="hash1")
    db_session.add(user1)
    db_session.commit()

    user2 = User(email="unique@example.com", hashed_password="hash2")
    db_session.add(user2)
    with pytest.raises(Exception):
        db_session.commit()


def test_job_model_creation(db_session: Session):
    """Test creating a Job model instance"""
    job = Job(
        id="test-job-123",
        project_name="test_project",
        job_type=JobType.ATTACK_SURFACE,
        status=JobStatus.PENDING,
        target_url="https://example.com",
        accept_terms=True,
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)

    assert job.id == "test-job-123"
    assert job.project_name == "test_project"
    assert job.job_type == JobType.ATTACK_SURFACE
    assert job.status == JobStatus.PENDING
    assert job.created_at is not None


def test_job_to_dict(db_session: Session):
    """Test Job.to_dict() method"""
    job = Job(
        id="dict-test-456",
        project_name="dict_project",
        job_type=JobType.SCA,
        status=JobStatus.RUNNING,
        target_url="/path/to/repo",
        accept_terms=True,
    )
    db_session.add(job)
    db_session.commit()

    d = job.to_dict()
    assert d["job_id"] == "dict-test-456"
    assert d["project_name"] == "dict_project"
    assert d["job_type"] == "sca"
    assert d["status"] == "running"


def test_job_repr(db_session: Session):
    """Test Job string representation"""
    job = Job(
        id="repr-789",
        project_name="repr_project",
        job_type=JobType.SMART_CONTRACT,
        status=JobStatus.COMPLETED,
        accept_terms=True,
    )
    db_session.add(job)
    db_session.commit()
    assert "repr-789" in repr(job)


def test_job_type_enum():
    """Test JobType enum values"""
    assert JobType.ATTACK_SURFACE.value == "attack_surface"
    assert JobType.SCA.value == "sca"
    assert JobType.SMART_CONTRACT.value == "smart_contract"


def test_job_status_enum():
    """Test JobStatus enum values"""
    assert JobStatus.PENDING.value == "pending"
    assert JobStatus.RUNNING.value == "running"
    assert JobStatus.COMPLETED.value == "completed"
    assert JobStatus.FAILED.value == "failed"
    assert JobStatus.CANCELLED.value == "cancelled"


def test_scan_history_creation(db_session: Session):
    """Test creating a ScanHistory record"""
    history = ScanHistory(
        job_id="history-test-001",
        action="scan_started",
        details={"target": "https://example.com"}
    )
    db_session.add(history)
    db_session.commit()
    db_session.refresh(history)

    assert history.id is not None
    assert history.job_id == "history-test-001"
    assert history.action == "scan_started"
    assert history.details["target"] == "https://example.com"
    assert history.timestamp is not None


def test_job_with_result_json(db_session: Session):
    """Test storing JSON result in job"""
    result_data = {
        "web_scan": {"vulnerabilities": [{"id": "XSS-001", "severity": "high"}]},
        "nuclei": {"findings": []}
    }
    job = Job(
        id="json-test-001",
        project_name="json_project",
        job_type=JobType.ATTACK_SURFACE,
        status=JobStatus.COMPLETED,
        accept_terms=True,
        result=result_data
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)

    assert job.result is not None
    assert len(job.result["web_scan"]["vulnerabilities"]) == 1
    assert job.result["web_scan"]["vulnerabilities"][0]["id"] == "XSS-001"
