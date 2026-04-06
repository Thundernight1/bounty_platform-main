"""
Tests for the Airflow DAG definition.
Validates DAG structure without requiring a running Airflow instance.
"""

from __future__ import annotations

import pytest
import sys
from unittest.mock import MagicMock

# Mock airflow modules so tests run without airflow installed
airflow_mock = MagicMock()
sys.modules["airflow"] = airflow_mock
sys.modules["airflow.operators"] = MagicMock()
sys.modules["airflow.operators.python"] = MagicMock()

# Create a proper DAG mock that acts as context manager
mock_dag = MagicMock()
mock_dag.__enter__ = MagicMock(return_value=mock_dag)
mock_dag.__exit__ = MagicMock(return_value=False)
airflow_mock.DAG.return_value = mock_dag


def test_dag_module_loads():
    """Test that the DAG module can be imported without errors"""
    # Reset modules to allow fresh import
    if "airflow.dags.bounty_pipeline" in sys.modules:
        del sys.modules["airflow.dags.bounty_pipeline"]

    # This should not raise
    import importlib

    spec = importlib.util.spec_from_file_location(
        "bounty_pipeline",
        "/Users/mehmetzumrut/Desktop/Zumrut2/bounty_platform-main/airflow/dags/bounty_pipeline.py",
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # Verify task functions exist
    assert callable(module.run_web_scan)
    assert callable(module.run_contract_scan)
    assert callable(module.calculate_score)
    assert callable(module.store_on_chain)


def test_run_web_scan_function():
    """Test the web scan task function"""
    import importlib

    spec = importlib.util.spec_from_file_location(
        "bounty_pipeline",
        "/Users/mehmetzumrut/Desktop/Zumrut2/bounty_platform-main/airflow/dags/bounty_pipeline.py",
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    context = {"params": {"target_url": "https://example.com"}}
    result = module.run_web_scan(**context)
    assert result["status"] == "completed"
    assert "vulnerabilities" in result


def test_run_contract_scan_function():
    """Test the contract scan task function"""
    import importlib

    spec = importlib.util.spec_from_file_location(
        "bounty_pipeline",
        "/Users/mehmetzumrut/Desktop/Zumrut2/bounty_platform-main/airflow/dags/bounty_pipeline.py",
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    context = {"params": {"contract_source": "pragma solidity ^0.8.0;"}}
    result = module.run_contract_scan(**context)
    assert result["status"] == "completed"
    assert "issues" in result


def test_calculate_score_function():
    """Test the scoring function"""
    import importlib

    spec = importlib.util.spec_from_file_location(
        "bounty_pipeline",
        "/Users/mehmetzumrut/Desktop/Zumrut2/bounty_platform-main/airflow/dags/bounty_pipeline.py",
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    mock_ti = MagicMock()
    mock_ti.xcom_pull.side_effect = lambda task_ids: {
        "web_scan": {"vulnerabilities": ["v1", "v2"]},
        "contract_scan": {"issues": ["i1"]},
    }[task_ids]

    context = {"ti": mock_ti}
    score = module.calculate_score(**context)
    assert score == 3  # 2 web vulnerabilities + 1 contract issue


def test_store_on_chain_function():
    """Test the on-chain storage function"""
    import importlib

    spec = importlib.util.spec_from_file_location(
        "bounty_pipeline",
        "/Users/mehmetzumrut/Desktop/Zumrut2/bounty_platform-main/airflow/dags/bounty_pipeline.py",
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    mock_ti = MagicMock()
    mock_ti.xcom_pull.return_value = 5

    context = {"ti": mock_ti}
    result = module.store_on_chain(**context)
    assert result is True
