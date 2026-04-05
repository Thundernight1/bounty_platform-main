"""
SQLAlchemy models for the bug bounty platform.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, DateTime, Text, JSON, Integer, Boolean, Enum as SQLEnum
from sqlalchemy.sql import func
import enum

from backend.database import Base


class JobType(str, enum.Enum):
    """Enumeration of job types"""
    ATTACK_SURFACE = "attack_surface"
    SCA = "sca"
    SMART_CONTRACT = "smart_contract"


class JobStatus(str, enum.Enum):
    """Enumeration of job statuses"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class User(Base):
    """
    User model for authentication and job ownership.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email})>"


class Job(Base):
    """
    Job model representing a security scan job.
    Stores job metadata, configuration, and results.
    """
    __tablename__ = "jobs"

    # Primary key
    id = Column(String(36), primary_key=True, index=True)

    # Job metadata
    project_name = Column(String(255), nullable=False, index=True)
    job_type = Column(SQLEnum(JobType), nullable=False, index=True)
    status = Column(SQLEnum(JobStatus), nullable=False, default=JobStatus.PENDING, index=True)

    # Ownership
    user_id = Column(Integer, nullable=True, index=True)  # Linked to User.id

    # Target information
    target_url = Column(String(2048), nullable=True)
    contract_source = Column(Text, nullable=True)
    scope = Column(JSON, nullable=True)  # List of allowed domains/repos

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    finished_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Results
    result = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)

    # Metadata
    accept_terms = Column(Boolean, nullable=False, default=False)
    created_by = Column(String(255), nullable=True)  # For future multi-tenancy

    def __repr__(self) -> str:
        return f"<Job(id={self.id}, type={self.job_type}, status={self.status})>"

    def to_dict(self) -> dict:
        """Convert model to dictionary for API responses"""
        return {
            "job_id": self.id,
            "project_name": self.project_name,
            "job_type": self.job_type.value if isinstance(self.job_type, enum.Enum) else self.job_type,
            "status": self.status.value if isinstance(self.status, enum.Enum) else self.status,
            "target_url": self.target_url,
            "scope": self.scope,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "result": self.result,
            "error_message": self.error_message,
        }


class ScanHistory(Base):
    """
    Audit log for tracking all scans and their outcomes.
    Useful for compliance and reporting.
    """
    __tablename__ = "scan_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(String(36), nullable=False, index=True)
    action = Column(String(100), nullable=False)  # e.g., "scan_started", "scan_completed"
    details = Column(JSON, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<ScanHistory(job_id={self.job_id}, action={self.action})>"
