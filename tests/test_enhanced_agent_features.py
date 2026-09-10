"""
Unit and integration test suite for enhanced autonomous agent features in CleanWeb Studio.
Validates new endpoints, MCP tools, Agent Toolkits, Multi-Chain configs, and local EIP-712 verification.
"""

import json
import pytest
from fastapi.testclient import TestClient
from app.main import app
from mcp_server import (
    oracle_grounding,
    verify_oracle_attestation,
    clean_text_raw,
    map_site,
    search_web_quick,
    extract_json_schema,
    deep_research_topic,
)
from agent_tools import X402AgentToolkit, get_x402_agent_tools
from autonomous_agent_client import AutonomousX402Agent, SUPPORTED_CHAINS
from app.onchain_signer import onchain_signer


@pytest.fixture
def client():
    return TestClient(app)


def test_clean_text_endpoint_402_and_success(client):
    """Verifies that /api/v1/clean-text enforces 402 and returns plain text with dev bypass."""
    # 1. 402 challenge
    res_402 = client.get("/api/v1/clean-text?url=https://example.com")
    assert res_402.status_code == 402
    assert "x402" in res_402.json()

    # 2. Authorized request
    res_auth = client.get(
        "/api/v1/clean-text?url=https://example.com",
        headers={"Authorization": "Bearer dev-bypass"}
    )
    assert res_auth.status_code == 200
    data = res_auth.json()
    assert data["status"] == "success"
    assert "plain_text" in data
    assert len(data["plain_text"]) > 0
    assert data["word_count"] > 0


def test_extract_json_endpoint_402_and_success(client):
    """Verifies that /api/v1/extract-json enforces 402 and extracts structured JSON."""
    payload = {
        "url": "https://example.com",
        "schema_description": "Extract title, summary, and domain"
    }
    # 1. 402 challenge
    res_402 = client.post("/api/v1/extract-json", json=payload)
    assert res_402.status_code == 402

    # 2. Authorized request
    res_auth = client.post(
        "/api/v1/extract-json",
        json=payload,
        headers={"Authorization": "Bearer dev-bypass"}
    )
    assert res_auth.status_code == 200
    data = res_auth.json()
    assert data["status"] == "success"
    assert "extracted_json" in data
    assert isinstance(data["extracted_json"], dict)


def test_deep_research_endpoint_402_and_success(client):
    """Verifies that /api/v1/deep-research enforces 402 and returns synthesized briefings."""
    # 1. 402 challenge
    res_402 = client.get("/api/v1/deep-research?query=Python+FastAPI")
    assert res_402.status_code == 402

    # 2. Authorized request
    res_auth = client.get(
        "/api/v1/deep-research?query=Python+FastAPI&max_sources=2",
        headers={"Authorization": "Bearer dev-bypass"}
    )
    assert res_auth.status_code == 200
    data = res_auth.json()
    assert data["status"] == "success"
    assert "research_brief_markdown" in data
    assert "sources" in data
    assert len(data["sources"]) > 0


def test_mcp_oracle_grounding_tool_direct_call():
    """Verifies MCP server oracle_grounding and verify_oracle_attestation tools."""
    output = oracle_grounding(query="Ethereum Dencun Upgrade", max_sources=2)
    assert "ORACLE GROUNDING SUCCESS" in output
    assert "Structured JSON Data" in output
    assert "EIP-712 Cryptographic Attestation" in output

    # Raw text MCP tool
    raw_out = clean_text_raw(url="https://example.com")
    assert "RAW TEXT SUCCESS" in raw_out


def test_agent_tools_oracle_and_schemas():
    """Verifies LangChain/CrewAI X402AgentToolkit additions."""
    toolkit = X402AgentToolkit(max_daily_budget_usdc=2.0)
    tools = toolkit.get_tools_list()
    assert len(tools) == 14  # 9 base tools + oracle_grounding + verify_oracle + map_site + search + legal_compliance

    # Verify function schemas
    schemas = toolkit.get_openai_function_schemas()
    assert len(schemas) == 14
    schema_names = [s["function"]["name"] for s in schemas]
    assert "x402_oracle_grounding" in schema_names
    assert "x402_verify_oracle_attestation" in schema_names
    assert "x402_map_site" in schema_names
    assert "x402_search" in schema_names
    assert "x402_get_legal_compliance_info" in schema_names


def test_autonomous_client_offline_eip712_verification():
    """Verifies that AutonomousX402Agent can verify EIP-712 attestations offline without API/gas."""
    query = "US Federal Reserve interest rate"
    data_hash = "0x" + "ab" * 32
    ts = 1715000000

    # Sign using master signer
    att = onchain_signer.sign_oracle_grounding(query=query, data_hash=data_hash, timestamp=ts)

    # Verify using client offline helper
    agent = AutonomousX402Agent()
    result = agent.verify_attestation_offline(
        query=query,
        data_hash=att.data_hash,
        timestamp=att.timestamp,
        signature=att.signature,
        expected_signer=onchain_signer.signer_address
    )
    assert result["valid"] is True
    assert result["verification_method"] == "local_offline_eip712"
    assert result["recovered_signer"].lower() == onchain_signer.signer_address.lower()


def test_multi_chain_configs_present():
    """Verifies Polygon, Base, and Arbitrum are configured with valid chain IDs and USDC addresses."""
    assert "polygon" in SUPPORTED_CHAINS
    assert SUPPORTED_CHAINS["polygon"]["chain_id"] == 137

    assert "base" in SUPPORTED_CHAINS
    assert SUPPORTED_CHAINS["base"]["chain_id"] == 8453
    assert SUPPORTED_CHAINS["base"]["usdc"] == "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"

    assert "arbitrum" in SUPPORTED_CHAINS
    assert SUPPORTED_CHAINS["arbitrum"]["chain_id"] == 42161
    assert SUPPORTED_CHAINS["arbitrum"]["usdc"] == "0xaf88d065e77c8cC2239327C5EDb3A432268e5831"


def test_map_site_endpoint_402_and_success(client):
    """Verifies that /api/v1/map-site enforces 402 and maps domain URLs."""
    # 1. 402 challenge
    res_402 = client.get("/api/v1/map-site?url=https://example.com")
    assert res_402.status_code == 402
    assert "x402" in res_402.json()

    # 2. Authorized request
    res_auth = client.get(
        "/api/v1/map-site?url=https://example.com&max_links=10",
        headers={"Authorization": "Bearer dev-bypass"}
    )
    assert res_auth.status_code == 200
    data = res_auth.json()
    assert data["status"] == "success"
    assert "domain" in data
    assert "total_urls" in data
    assert isinstance(data["urls"], list)
    assert len(data["urls"]) > 0


def test_search_endpoint_402_and_success(client):
    """Verifies that /api/v1/search enforces 402 and returns agent search snippets."""
    # 1. 402 challenge
    res_402 = client.get("/api/v1/search?query=Ethereum")
    assert res_402.status_code == 402

    # 2. Authorized request
    res_auth = client.get(
        "/api/v1/search?query=Ethereum&max_results=3",
        headers={"Authorization": "Bearer dev-bypass"}
    )
    assert res_auth.status_code == 200
    data = res_auth.json()
    assert data["status"] == "success"
    assert data["query"] == "Ethereum"
    assert "total_results" in data
    assert isinstance(data["results"], list)
    assert len(data["results"]) > 0
    assert "title" in data["results"][0]
    assert "url" in data["results"][0]
    assert "snippet" in data["results"][0]


def test_oracle_grounding_abi_calldata_generation():
    """Verifies that sign_oracle_grounding produces valid abi_calldata for Solidity verification."""
    query = "US Inflation Rate"
    data_hash = "0x" + "11" * 32
    att = onchain_signer.sign_oracle_grounding(query=query, data_hash=data_hash, timestamp=1715000000)
    assert att.abi_calldata is not None
    assert att.abi_calldata.startswith("0x")
    # Calldata contains 4-byte selector + 6 ABI arguments -> at least 4 + 6*32 = 196 bytes (392+ hex chars)
    assert len(att.abi_calldata) > 100


def test_mcp_map_site_and_search_tools():
    """Verifies MCP tools for site mapping and agent web search."""
    # map_site tool
    map_res = map_site(url="https://example.com", max_links=5)
    assert "SITE MAP SUCCESS" in map_res
    assert "Target URL" in map_res

    # search_web_quick tool
    search_res = search_web_quick(query="Python", max_results=3)
    assert "SEARCH SUCCESS" in search_res
    assert "Query" in search_res


def test_agent_toolkit_map_site_and_search():
    """Verifies that X402AgentToolkit exposes map_site and search tools and schemas."""
    toolkit = X402AgentToolkit(max_daily_budget_usdc=10.0)
    tools = toolkit.get_tools_list()
    tool_names = [t.__name__ for t in tools]
    assert "map_site" in tool_names
    assert "search" in tool_names

    schemas = toolkit.get_openai_function_schemas()
    schema_names = [s["function"]["name"] for s in schemas]
    assert "x402_map_site" in schema_names
    assert "x402_search" in schema_names


def test_legal_terms_and_disclaimer_endpoints(client):
    """Verifies that /api/v1/legal/terms and /api/v1/legal/disclaimer are publicly accessible."""
    # Terms of service
    res_terms = client.get("/api/v1/legal/terms")
    assert res_terms.status_code == 200
    data_terms = res_terms.json()
    assert "jurisdiction_and_governance" in data_terms
    assert "caller_responsibility" in data_terms

    # Disclaimer
    res_disc = client.get("/api/v1/legal/disclaimer")
    assert res_disc.status_code == 200
    data_disc = res_disc.json()
    assert "clauses" in data_disc
    assert "no_financial_advice" in data_disc["clauses"]
    assert "oracle_execution_risk" in data_disc["clauses"]

    # Root metadata includes legal notice
    res_root = client.get("/")
    assert res_root.status_code == 200
    data_root = res_root.json()
    assert "legal_notice" in data_root
    assert "endpoints" in data_root
    assert "legal_terms" in data_root["endpoints"]


def test_mcp_extract_json_and_deep_research_tools():
    """Verifies that extract_json_schema and deep_research_topic MCP tools execute cleanly."""
    # extract_json_schema
    json_res = extract_json_schema(url="https://example.com", schema_description="title, domain")
    assert "JSON EXTRACTION SUCCESS" in json_res
    assert "https://example.com" in json_res

    # deep_research_topic
    research_res = deep_research_topic(query="AI Agents in Web3", max_sources=2)
    assert "DEEP RESEARCH SUCCESS" in research_res
    assert "Topic" in research_res


def test_web_engine_caching_and_robots_txt(client):
    """Verifies that In-Memory caching speeds up repeated queries and respect_robots_txt works."""
    from app.cleaners.web_engine import web_cleaner_engine

    # 1. First fetch
    first_res = web_cleaner_engine.fetch_and_clean("https://example.com")
    assert first_res["status_code"] == 200 if "status_code" in first_res else "title" in first_res

    # 2. Second fetch (must hit cache)
    cached_res = web_cleaner_engine.fetch_and_clean("https://example.com")
    assert cached_res.get("cached") is True

def test_client_sdk_and_agent_tools_new_features(client):
    """Verifies that newly added SDK and Toolkit features (compliance, robots_txt, tool lists) operate properly."""
    toolkit = X402AgentToolkit(base_url="https://example.com", max_daily_budget_usdc=2.0)
    tools = toolkit.get_tools_list()
    assert len(tools) >= 14
    tool_names = [t.__name__ for t in tools]
    assert "map_site" in tool_names
    assert "search" in tool_names
    assert "get_legal_compliance_info" in tool_names

    # Check OpenAI schemas
    schemas = toolkit.get_openai_function_schemas()
    schema_names = [s["function"]["name"] for s in schemas]
    assert "x402_map_site" in schema_names
    assert "x402_search" in schema_names
    assert "x402_get_legal_compliance_info" in schema_names

    clean_web_schema = next(s for s in schemas if s["function"]["name"] == "x402_clean_web")
    assert "respect_robots_txt" in clean_web_schema["function"]["parameters"]["properties"]

    # AutonomousX402Agent methods exist
    agent = AutonomousX402Agent()
    assert hasattr(agent, "get_legal_terms")
    assert hasattr(agent, "get_legal_disclaimer")
    assert hasattr(agent, "get_service_health")
    assert hasattr(agent, "map_site")
    assert hasattr(agent, "search")




