"""
Tests for x402-cleanweb-agent Management CLI
"""

import sys
import pytest
from unittest.mock import patch
import x402_cleanweb_agent
from x402_cleanweb_agent import (
    cmd_status,
    cmd_pricing,
    cmd_balance,
    cmd_test,
    main
)


def test_cli_module_exports():
    """Verify official module exports and version string"""
    assert hasattr(x402_cleanweb_agent, "__version__")
    assert hasattr(x402_cleanweb_agent, "AutonomousX402Agent")
    assert hasattr(x402_cleanweb_agent, "AutonomousAgentClient")
    assert hasattr(x402_cleanweb_agent, "main")


def test_cmd_status_execution(capsys):
    """Test live status check via CLI"""
    cmd_status()
    captured = capsys.readouterr().out
    assert "[x402 CLI] Checking Production Gateway Status" in captured
    assert "Gateway Status" in captured
    assert "Chains Connected" in captured


def test_cmd_pricing_execution(capsys):
    """Test live pricing catalog fetch via CLI"""
    cmd_pricing()
    captured = capsys.readouterr().out
    assert "Machine-to-Machine B2A Pricing" in captured
    assert "web_clean_markdown" in captured
    assert "STARTER" in captured


def test_cmd_balance_demo_account(capsys):
    """Test querying demo account balance via CLI"""
    cmd_balance("vault_key_demo_agent_sandbox_2026")
    captured = capsys.readouterr().out
    assert "Querying Agent Payment Vault" in captured
    assert "Available Balance" in captured
    assert "Session Key" in captured


def test_cmd_test_execution(capsys):
    """Test instant extraction command via CLI"""
    cmd_test("https://news.ycombinator.com")
    captured = capsys.readouterr().out
    assert "Testing Instant Clean Web Extraction" in captured
    assert "Extraction Success" in captured
    assert "Title" in captured


def test_main_cli_routing_status(capsys):
    """Test main() CLI dispatching status"""
    with patch.object(sys, "argv", ["x402-cli", "status"]):
        main()
    captured = capsys.readouterr().out
    assert "Checking Production Gateway Status" in captured


def test_main_cli_routing_pricing(capsys):
    """Test main() CLI dispatching pricing"""
    with patch.object(sys, "argv", ["x402-cli", "pricing"]):
        main()
    captured = capsys.readouterr().out
    assert "Machine-to-Machine B2A Pricing" in captured
