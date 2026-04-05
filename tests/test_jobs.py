"""
Tests for job creation and management endpoints.
All endpoints require OAuth2 Bearer auth, tested via auth_headers fixture.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


def test_health_check(client: TestClient):
    """Test health check endpoint (no auth required)"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_register_user(client: TestClient):
    """Test user registration"""
    response = client.post("/auth/register", json={
        "email": "newuser@example.com",
        "password": "securepassword123"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert data["is_active"] is True
    assert "id" in data


def test_register_duplicate_user(client: TestClient):
    """Test that duplicate registration fails"""
    payload = {"email": "dup@example.com", "password": "pass123"}
    client.post("/auth/register", json=payload)
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]


def test_login(client: TestClient):
    """Test user login and token generation"""
    client.post("/auth/register", json={
        "email": "logintest@example.com",
        "password": "mypassword"
    })
    response = client.post("/auth/token", data={
        "username": "logintest@example.com",
        "password": "mypassword"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client: TestClient):
    """Test login with wrong password fails"""
    client.post("/auth/register", json={
        "email": "wrongpw@example.com",
        "password": "correctpassword"
    })
    response = client.post("/auth/token", data={
        "username": "wrongpw@example.com",
        "password": "wrongpassword"
    })
    assert response.status_code == 401


def test_create_attack_surface_job(client: TestClient, auth_headers: dict, sample_job_payload: dict):
    """Test creating an attack surface scan job"""
    response = client.post("/jobs", json=sample_job_payload, headers=auth_headers)
    assert response.status_code == 200

    data = response.json()
    assert "job_id" in data
    assert data["project_name"] == "test_project"
    assert data["status"] == "pending"


def test_create_sca_job(client: TestClient, auth_headers: dict):
    """Test creating an SCA scan job"""
    payload = {
        "project_name": "test_sca",
        "job_type": "sca",
        "target_url": "/path/to/repo",
        "accept_terms": True
    }
    response = client.post("/jobs", json=payload, headers=auth_headers)
    assert response.status_code == 200


def test_create_smart_contract_job(client: TestClient, auth_headers: dict):
    """Test creating a smart contract scan job"""
    payload = {
        "project_name": "test_contract",
        "job_type": "smart_contract",
        "contract_source": "pragma solidity ^0.8.0; contract Test {}",
        "accept_terms": True
    }
    response = client.post("/jobs", json=payload, headers=auth_headers)
    assert response.status_code == 200


def test_reject_job_without_terms(client: TestClient, auth_headers: dict, sample_job_payload: dict):
    """Test that jobs are rejected if terms are not accepted"""
    sample_job_payload["accept_terms"] = False
    response = client.post("/jobs", json=sample_job_payload, headers=auth_headers)
    assert response.status_code == 400
    assert "accept_terms" in response.json()["detail"]


def test_reject_attack_surface_without_url(client: TestClient, auth_headers: dict):
    """Test that attack_surface jobs require target_url"""
    payload = {
        "project_name": "test",
        "job_type": "attack_surface",
        "accept_terms": True
    }
    response = client.post("/jobs", json=payload, headers=auth_headers)
    assert response.status_code == 400
    assert "target_url" in response.json()["detail"]


def test_reject_smart_contract_without_source(client: TestClient, auth_headers: dict):
    """Test that smart_contract jobs require contract_source"""
    payload = {
        "project_name": "test",
        "job_type": "smart_contract",
        "accept_terms": True
    }
    response = client.post("/jobs", json=payload, headers=auth_headers)
    assert response.status_code == 400
    assert "contract_source" in response.json()["detail"]


def test_reject_sca_without_url(client: TestClient, auth_headers: dict):
    """Test that SCA jobs require target_url"""
    payload = {
        "project_name": "test",
        "job_type": "sca",
        "accept_terms": True
    }
    response = client.post("/jobs", json=payload, headers=auth_headers)
    assert response.status_code == 400


def test_reject_out_of_scope_url(client: TestClient, auth_headers: dict):
    """Test that URLs outside defined scope are rejected"""
    payload = {
        "project_name": "test",
        "job_type": "attack_surface",
        "target_url": "https://evil.com",
        "accept_terms": True,
        "scope": ["example.com"]
    }
    response = client.post("/jobs", json=payload, headers=auth_headers)
    assert response.status_code == 400
    assert "out of scope" in response.json()["detail"]


def test_get_job(client: TestClient, auth_headers: dict, sample_job_payload: dict):
    """Test retrieving a job by ID"""
    create_response = client.post("/jobs", json=sample_job_payload, headers=auth_headers)
    job_id = create_response.json()["job_id"]

    get_response = client.get(f"/jobs/{job_id}", headers=auth_headers)
    assert get_response.status_code == 200

    data = get_response.json()
    assert data["job_id"] == job_id
    assert data["project_name"] == "test_project"


def test_get_nonexistent_job(client: TestClient, auth_headers: dict):
    """Test that getting a nonexistent job returns 404"""
    response = client.get("/jobs/nonexistent-id", headers=auth_headers)
    assert response.status_code == 404


def test_list_jobs(client: TestClient, auth_headers: dict, sample_job_payload: dict):
    """Test listing all jobs for the authenticated user"""
    for i in range(3):
        payload = sample_job_payload.copy()
        payload["project_name"] = f"project_{i}"
        client.post("/jobs", json=payload, headers=auth_headers)

    response = client.get("/jobs", headers=auth_headers)
    assert response.status_code == 200

    data = response.json()
    assert len(data) >= 3
    assert all("job_id" in job for job in data)


def test_unauthenticated_access_denied(client: TestClient, sample_job_payload: dict):
    """Test that unauthenticated requests to protected endpoints are rejected"""
    response = client.post("/jobs", json=sample_job_payload)
    assert response.status_code == 401

    response = client.get("/jobs")
    assert response.status_code == 401
