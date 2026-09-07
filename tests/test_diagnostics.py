"""
Tests for Automated Diagnostic Engine and Health Watchdog.
"""

import pytest
from app.diagnostics import diagnostic_engine


def test_diagnostic_engine_full_run():
    """Verifies that diagnostic_engine inspects all 5 pipelines and returns a valid report."""
    report = diagnostic_engine.run_full_diagnostic()
    
    assert "system_health" in report
    assert "overall_score" in report
    assert "pipelines" in report
    assert "summary" in report
    assert len(report["pipelines"]) == 5
    
    # Check that individual pipeline checkers work
    pipeline_names = [p["name"] for p in report["pipelines"]]
    assert any("Security Gate" in name for name in pipeline_names)
    assert any("Gemini" in name for name in pipeline_names)
    assert any("EIP-712" in name for name in pipeline_names)
    assert any("Storage" in name for name in pipeline_names)
    assert any("3-Chain" in name for name in pipeline_names)

    # Check that none of the core pipelines failed critically
    for p in report["pipelines"]:
        assert p["status"] in ("HEALTHY", "DEGRADED"), f"Pipeline {p['name']} is CRITICAL: {p.get('error')}"


def test_individual_checkers():
    """Verifies each pipeline checker method directly."""
    res_sec = diagnostic_engine.check_security_gate()
    assert res_sec["status"] in ("HEALTHY", "DEGRADED")
    
    res_gem = diagnostic_engine.check_gemini_engine()
    assert res_gem["status"] in ("HEALTHY", "DEGRADED")

    res_sig = diagnostic_engine.check_onchain_signer()
    assert res_sig["status"] == "HEALTHY"
    assert res_sig.get("signature_verified") is True

    res_db = diagnostic_engine.check_storage_ledger()
    assert res_db["status"] == "HEALTHY"
