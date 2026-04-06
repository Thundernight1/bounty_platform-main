"""
Backend service for the blockchain-based bug bounty platform.

Adds job types (attack_surface, sca, smart_contract), guardrails (accept_terms,
scope checks), and routes scans to the correct agent. Stores results to disk.
"""

from __future__ import annotations

import uuid
import json
import asyncio
from datetime import datetime, timedelta
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Literal
from urllib.parse import urlparse

from fastapi import FastAPI, BackgroundTasks, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, EmailStr
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import JWTError, jwt

from backend.database import get_db, init_db
from backend.models import Job, User, JobType, JobStatus as JobStatusEnum

# Support both package and script execution
try:
    from .utils.scanners import (
        run_zap_scan,
        run_mythril_scan,
        run_nuclei_scan,
        run_sca_scan,
    )
except Exception:
    from utils.scanners import (
        run_zap_scan,
        run_mythril_scan,
        run_nuclei_scan,
        run_sca_scan,
    )

app = FastAPI(title="Bug Bounty Platform Backend")


# Initialize DB
@app.on_event("startup")
def on_startup():
    init_db()


RESULTS_DIR = Path(__file__).resolve().parent / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


@app.get("/health", summary="Health check")
def health_check():
    return {"status": "healthy", "version": "1.0.0"}


# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all for dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Security Config ---
SECRET_KEY = os.getenv(
    "SECRET_KEY", "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

# --- Schemas ---


class Token(BaseModel):
    access_token: str
    token_type: str


class UserCreate(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    is_active: bool

    class Config:
        from_attributes = True


class JobRequest(BaseModel):
    job_type: Literal["attack_surface", "sca", "smart_contract"] = Field(
        "attack_surface", description="Type of scan to run"
    )
    project_name: str = Field(..., description="Project name for reporting")
    target_url: Optional[str] = Field(
        None, description="URL or path (attack_surface URL / sca repo path)"
    )
    contract_source: Optional[str] = Field(
        None, description="Solidity source (for smart_contract jobs)"
    )
    accept_terms: bool = Field(
        ..., description="Must be true to confirm legal/ethical constraints"
    )
    scope: Optional[List[str]] = Field(
        None, description="Allowed domains or repo identifiers"
    )


class JobStatus(BaseModel):
    job_id: str
    project_name: str
    status: str
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    result: Dict[str, Any] | None = None
    user_id: Optional[int] = None


# --- Auth Utils ---


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    return user


# --- Endpoints ---


@app.post("/auth/register", response_model=UserResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = get_password_hash(user.password)
    new_user = User(email=user.email, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@app.post("/auth/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


def _domain_in_scope(url: str, scope_list: Optional[List[str]]) -> bool:
    if not url or not scope_list:
        return True  # allow if no scope provided (MVP behavior)
    try:
        host = urlparse(url).hostname or ""
    except Exception:
        return False
    host = host.lower()
    return any(host == s.lower() or host.endswith("." + s.lower()) for s in scope_list)


@app.post("/jobs", response_model=JobStatus, summary="Create a new scan job")
async def create_job(
    request: JobRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> JobStatus:
    if not request.accept_terms:
        raise HTTPException(status_code=400, detail="accept_terms must be true")

    if request.job_type == "attack_surface":
        if not request.target_url:
            raise HTTPException(status_code=400, detail="target_url is required")
        if not _domain_in_scope(request.target_url, request.scope):
            raise HTTPException(status_code=400, detail="target_url out of scope")

    if request.job_type == "sca":
        if not request.target_url:
            raise HTTPException(
                status_code=400, detail="target_url must be a local repo path for SCA"
            )

    if request.job_type == "smart_contract":
        if not request.contract_source:
            raise HTTPException(
                status_code=400, detail="contract_source is required for smart_contract"
            )

    job_id = str(uuid.uuid4())
    now = datetime.now()  # Using standard now for DB compatibility

    # Create DB Job
    db_job = Job(
        id=job_id,
        project_name=request.project_name,
        job_type=JobType(request.job_type),  # Ensure enum
        status=JobStatusEnum.PENDING,
        target_url=request.target_url,
        contract_source=request.contract_source,
        scope=request.scope,
        created_at=now,
        accept_terms=request.accept_terms,
        user_id=current_user.id,
    )
    db.add(db_job)
    db.commit()

    # Create response object
    job_status = JobStatus(
        job_id=job_id,
        project_name=request.project_name,
        status="pending",
        created_at=now,
        user_id=current_user.id,
    )

    background_tasks.add_task(_run_scans, job_id, request, db)
    return job_status


@app.get("/jobs", response_model=List[JobStatus], summary="List my jobs")
async def list_jobs(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    jobs = db.query(Job).filter(Job.user_id == current_user.id).all()
    return [
        JobStatus(
            job_id=job.id,
            project_name=job.project_name,
            status=job.status.value,
            created_at=job.created_at,
            finished_at=job.finished_at,
            result=job.result,
            user_id=job.user_id,
        )
        for job in jobs
    ]


@app.get("/jobs/{job_id}", response_model=JobStatus, summary="Retrieve job status")
async def get_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> JobStatus:
    job = db.query(Job).filter(Job.id == job_id).first()
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    # Check ownership
    if job.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this job")

    if job.status == JobStatusEnum.COMPLETED and job.result is None:
        # Fallback to file system if result not in DB (legacy)
        result_file = RESULTS_DIR / f"{job_id}.json"
        if result_file.exists():
            job.result = json.loads(result_file.read_text())

    return JobStatus(
        job_id=job.id,
        project_name=job.project_name,
        status=job.status.value if hasattr(job.status, "value") else job.status,
        created_at=job.created_at,
        started_at=job.started_at,
        finished_at=job.finished_at,
        result=job.result,
        user_id=job.user_id,
    )


async def _run_scans(job_id: str, request: JobRequest, db: Session = None) -> None:
    # Need a new session if running in background?
    # Actually, SQLAlchemy sessions are not thread-safe.
    # For background tasks, it's better to create a new session.
    # But for MVP simplicity, we'll try to use a fresh session context here.

    # Re-instantiate session for background task
    db_gen = get_db()
    bg_db = next(db_gen)

    try:
        job = bg_db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return

        job.status = JobStatusEnum.RUNNING
        job.started_at = datetime.now()
        bg_db.commit()

        result: Dict[str, Any] = {
            "project_name": request.project_name,
            "job_type": request.job_type,
            "target_url": request.target_url,
            "web_scan": None,
            "nuclei": None,
            "sca": None,
            "contract_analysis": None,
        }

        if request.job_type == "attack_surface":
            # Run scans concurrently to reduce total time
            zap_task = run_zap_scan(request.target_url)  # type: ignore[arg-type]
            nuclei_task = run_nuclei_scan(request.target_url)  # type: ignore[arg-type]
            result["web_scan"], result["nuclei"] = await asyncio.gather(
                zap_task, nuclei_task
            )

        elif request.job_type == "sca":
            result["sca"] = await run_sca_scan(request.target_url)  # type: ignore[arg-type]

        elif request.job_type == "smart_contract":
            result["contract_analysis"] = await run_mythril_scan(
                request.contract_source or ""
            )

        job.finished_at = datetime.now()
        job.status = JobStatusEnum.COMPLETED
        job.result = result
        bg_db.commit()

        # Also save to disk for legacy support
        with open(RESULTS_DIR / f"{job_id}.json", "w") as f:
            json.dump(result, f, indent=2)

        _notify_slack(job_id, request, result)

    except Exception as e:
        if job:
            job.status = JobStatusEnum.FAILED
            job.error_message = str(e)
            bg_db.commit()
        print(f"Error in job {job_id}: {e}")
    finally:
        bg_db.close()


def _notify_slack(job_id: str, request: JobRequest, result: Dict[str, Any]) -> None:
    """Post a short summary to Slack if SLACK_WEBHOOK_URL is set."""
    webhook = os.environ.get("SLACK_WEBHOOK_URL")
    if not webhook:
        return
    try:
        import requests  # lazy import

        counts = []
        if result.get("web_scan"):
            ws = result["web_scan"]
            v = len(ws.get("vulnerabilities", [])) if isinstance(ws, dict) else 0
            counts.append(f"web:{v}")
        if result.get("nuclei"):
            nu = result["nuclei"]
            v = len(nu.get("findings", [])) if isinstance(nu, dict) else 0
            counts.append(f"nuclei:{v}")
        if result.get("sca"):
            sca = result["sca"]
            if (
                isinstance(sca, dict)
                and "results" in sca
                and isinstance(sca["results"], dict)
            ):
                v = len(sca["results"].get("vulnerabilities", []))
            else:
                v = len(sca.get("vulnerabilities", [])) if isinstance(sca, dict) else 0
            counts.append(f"sca:{v}")
        if result.get("contract_analysis"):
            ca = result["contract_analysis"]
            v = len(ca.get("issues", [])) if isinstance(ca, dict) else 0
            counts.append(f"contract:{v}")

        text = (
            f"bounty_platform: job {job_id}\n"
            f"type: {request.job_type} | project: {request.project_name}\n"
            f"summary: {' '.join(counts) if counts else 'done'}"
        )
        requests.post(webhook, json={"text": text}, timeout=5)
    except Exception:
        # Silent: notifications should never break the job
        pass
