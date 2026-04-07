"""
Tests for the CLI (Bug Bounty Platform CLI) module.
"""

from __future__ import annotations

import os
import pytest
import sys
from unittest.mock import patch, MagicMock
from io import StringIO

# Add scripts directory to path so we can import bp module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from bp import main


def test_cli_run_attack_surface_missing_url():
    """Test that attack_surface type requires --url"""
    with patch(
        "sys.argv", ["bp", "run", "--project", "test", "--type", "attack_surface"]
    ):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 2


def test_cli_run_sca_missing_url():
    """Test that sca type requires --url"""
    with patch("sys.argv", ["bp", "run", "--project", "test", "--type", "sca"]):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 2


def test_cli_run_smart_contract_missing_source():
    """Test that smart_contract type requires --source"""
    with patch(
        "sys.argv", ["bp", "run", "--project", "test", "--type", "smart_contract"]
    ):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 2


def test_cli_run_attack_surface_success():
    """Test successful attack_surface job submission"""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "job_id": "abc-123",
        "project_name": "test",
        "status": "pending",
    }
    mock_response.raise_for_status.return_value = None

    with patch(
        "sys.argv",
        [
            "bp",
            "run",
            "--project",
            "test",
            "--type",
            "attack_surface",
            "--url",
            "https://example.com",
        ],
    ):
        with patch("requests.post", return_value=mock_response) as mock_post:
            captured = StringIO()
            with patch("sys.stdout", captured):
                main()

            # Verify the API was called
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert "/jobs" in call_args[0][0]
            payload = call_args[1]["json"]
            assert payload["project_name"] == "test"
            assert payload["job_type"] == "attack_surface"
            assert payload["target_url"] == "https://example.com"
            assert payload["accept_terms"] is True


def test_cli_run_with_scope():
    """Test job submission with scope"""
    mock_response = MagicMock()
    mock_response.json.return_value = {"job_id": "def-456", "project_name": "scoped"}
    mock_response.raise_for_status.return_value = None

    with patch(
        "sys.argv",
        [
            "bp",
            "run",
            "--project",
            "scoped",
            "--type",
            "attack_surface",
            "--url",
            "https://example.com",
            "--scope",
            "example.com",
            "sub.example.com",
        ],
    ):
        with patch("requests.post", return_value=mock_response) as mock_post:
            with patch("sys.stdout", StringIO()):
                main()

            payload = mock_post.call_args[1]["json"]
            assert payload["scope"] == ["example.com", "sub.example.com"]


def test_cli_run_no_accept():
    """Test that --no-accept sets accept_terms to False"""
    mock_response = MagicMock()
    mock_response.json.return_value = {"job_id": "no-accept"}
    mock_response.raise_for_status.return_value = None

    with patch(
        "sys.argv",
        [
            "bp",
            "run",
            "--project",
            "test",
            "--type",
            "attack_surface",
            "--url",
            "https://example.com",
            "--no-accept",
        ],
    ):
        with patch("requests.post", return_value=mock_response) as mock_post:
            with patch("sys.stdout", StringIO()):
                main()

            payload = mock_post.call_args[1]["json"]
            assert payload["accept_terms"] is False


def test_cli_help():
    """Test that --help flag works"""
    with patch("sys.argv", ["bp", "--help"]):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0
