"""
Tests for Autonomous Agent Discovery, Reflection & Arbitrage Endpoints
"""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_well_known_manifests():
    # 1. Agent Manifest (A2A / ERC-8004 spec)
    res = client.get("/.well-known/agent.json")
    assert res.status_code == 200
    data = res.json()
    assert data["agent_id"] == "x402-cleanweb-agent"
    assert "economic_model" in data
    assert len(data["capabilities"]) == 14

    # 2. OpenAI AI Plugin
    res = client.get("/.well-known/ai-plugin.json")
    assert res.status_code == 200
    data = res.json()
    assert data["name_for_model"] == "x402_cleanweb_agent"
    assert "api" in data

    # 3. MCP Server Card
    res = client.get("/.well-known/mcp/server-card.json")
    assert res.status_code == 200
    data = res.json()
    assert data["name"] == "x402-cleanweb-agent"
    assert data["tools_count"] == 14

    # 4. MCP alias
    res = client.get("/.well-known/mcp.json")
    assert res.status_code == 200
    assert res.json()["name"] == "x402-cleanweb-agent"

def test_agent_capabilities_reflection():
    res = client.get("/api/v1/agent/capabilities")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "active"
    assert data["tools_count"] == 14
    assert len(data["tools"]) == 14
    assert len(data["supported_chains"]) == 3
    assert data["trial_policy"]["vip_trial_code"] == "WELCOME100"

def test_agent_pricing_catalog():
    res = client.get("/api/v1/agent/pricing-catalog")
    assert res.status_code == 200
    data = res.json()
    assert data["currency"] == "USDC"
    assert "rates" in data
    assert "volume_passes" in data
    assert len(data["volume_passes"]) == 3

def test_agent_arbitrage_roi():
    res = client.get("/api/v1/agent/arbitrage-roi?input_tokens=100000&llm_price_per_million=3.00")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "economically_optimal"
    assert data["routing_recommendation"] == "ROUTE_VIA_X402"
    assert data["benchmark"]["raw_tokens"] == 100000
    assert data["financial_analysis"]["net_dollar_savings"] > 0
    print("  Arbitrage ROI Output:", data["financial_analysis"])

def test_agent_framework_integrations():
    frameworks = ["langchain", "crewai", "autogen", "smolagents", "elizaos", "curl", "python"]
    for fw in frameworks:
        res = client.get(f"/api/v1/agent/integrations/{fw}")
        assert res.status_code == 200
        data = res.json()
        assert data["framework"] == fw
        assert "code_snippet" in data
        assert len(data["code_snippet"]) > 20
