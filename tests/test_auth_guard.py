"""
Tests for authentication guard and access control.
Uses the main app with OAuth2 bearer token authentication.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


def test_protected_endpoints_require_auth(client: TestClient):
    """Test that all protected endpoints require authentication"""
    job_payload = {
        "project_name": "demo",
        "job_type": "attack_surface",
        "target_url": "https://example.com",
        "accept_terms": True,
    }

    # POST /jobs without auth
    resp = client.post("/jobs", json=job_payload)
    assert resp.status_code == 401

    # GET /jobs without auth
    resp = client.get("/jobs")
    assert resp.status_code == 401

    # GET /jobs/{id} without auth
    resp = client.get("/jobs/some-id")
    assert resp.status_code == 401


def test_invalid_token_rejected(client: TestClient):
    """Test that invalid bearer tokens are rejected"""
    headers = {"Authorization": "Bearer invalid-token-here"}
    resp = client.get("/jobs", headers=headers)
    assert resp.status_code == 401


def test_expired_or_malformed_token(client: TestClient):
    """Test that malformed tokens are rejected"""
    headers = {
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.payload"
    }
    resp = client.get("/jobs", headers=headers)
    assert resp.status_code == 401


def test_health_check_no_auth_required(client: TestClient):
    """Test that /health does not require authentication"""
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"


def test_auth_register_no_auth_required(client: TestClient):
    """Test that /auth/register does not require authentication"""
    resp = client.post(
        "/auth/register",
        json={"email": "guard_test@example.com", "password": "password123"},
    )
    assert resp.status_code == 200


def test_authenticated_user_can_access_jobs(client: TestClient, auth_headers: dict):
    """Test that an authenticated user can access protected endpoints"""
    resp = client.get("/jobs", headers=auth_headers)
    assert resp.status_code == 200


def test_job_ownership_enforced(client: TestClient, auth_headers: dict):
    """Test that users can only see their own jobs"""
    # Create a job as user 1
    payload = {
        "project_name": "owned_project",
        "job_type": "attack_surface",
        "target_url": "https://example.com",
        "accept_terms": True,
        "scope": ["example.com"],
    }
    resp = client.post("/jobs", json=payload, headers=auth_headers)
    assert resp.status_code == 200
    job_id = resp.json()["job_id"]

    # Register and login as user 2
    client.post(
        "/auth/register", json={"email": "user2@example.com", "password": "pass2"}
    )
    login_resp = client.post(
        "/auth/token", data={"username": "user2@example.com", "password": "pass2"}
    )
    token2 = login_resp.json()["access_token"]
    headers2 = {"Authorization": f"Bearer {token2}"}

    # User 2 should not be able to see user 1's job
    resp = client.get(f"/jobs/{job_id}", headers=headers2)
    assert resp.status_code == 403
