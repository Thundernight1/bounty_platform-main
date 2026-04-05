"""
Tests for scanner utility functions.
Tests mock/heuristic paths since real tools (ZAP, Mythril, etc.) are not installed in CI.
"""

from __future__ import annotations

import pytest
import asyncio

from backend.utils.scanners import (
    run_zap_scan,
    run_mythril_scan,
    run_nuclei_scan,
    run_sca_scan,
)


@pytest.mark.asyncio
async def test_zap_scan_without_tool():
    """Test ZAP scan returns graceful fallback when tool is not installed"""
    result = await run_zap_scan("https://example.com")
    assert result["tool"] == "owasp_zap"
    assert "summary" in result
    assert isinstance(result.get("vulnerabilities", []), list)


@pytest.mark.asyncio
async def test_nuclei_scan_without_tool():
    """Test nuclei scan returns graceful fallback when tool is not installed"""
    result = await run_nuclei_scan("https://example.com")
    assert result["tool"] == "nuclei"
    assert "summary" in result
    assert isinstance(result.get("findings", []), list)


@pytest.mark.asyncio
async def test_mythril_scan_without_tool_no_pattern():
    """Test Mythril scan with clean contract source"""
    source = "pragma solidity ^0.8.0; contract Safe { function foo() public {} }"
    result = await run_mythril_scan(source)
    assert result["tool"] == "mythril"
    assert "summary" in result
    assert isinstance(result.get("issues", []), list)
    # No call.value pattern, so no heuristic issues
    assert len(result.get("issues", [])) == 0


@pytest.mark.asyncio
async def test_mythril_scan_without_tool_with_pattern():
    """Test Mythril scan detects call.value heuristic pattern"""
    source = """
    pragma solidity ^0.8.0;
    contract Vulnerable {
        function withdraw() public {
            msg.sender.call.value(1 ether)("");
        }
    }
    """
    result = await run_mythril_scan(source)
    assert result["tool"] == "mythril"
    assert len(result.get("issues", [])) > 0
    assert result["issues"][0]["id"] == "PATTERN_DETECTED"


@pytest.mark.asyncio
async def test_sca_scan_without_tool():
    """Test SCA scan returns graceful fallback when tool is not installed"""
    result = await run_sca_scan("/nonexistent/path")
    assert result["tool"] == "osv-scanner"
    assert "summary" in result


@pytest.mark.asyncio
async def test_concurrent_scans():
    """Test that multiple scans can run concurrently"""
    results = await asyncio.gather(
        run_zap_scan("https://example.com"),
        run_nuclei_scan("https://example.com"),
    )
    assert len(results) == 2
    assert results[0]["tool"] == "owasp_zap"
    assert results[1]["tool"] == "nuclei"
