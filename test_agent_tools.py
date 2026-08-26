"""
Tests for AI Agent Tools and Budget Guard
"""

import sys
from agent_tools import BudgetGuard, X402AgentToolkit, get_x402_agent_tools

def test_budget_guard():
    print("Testing BudgetGuard...")
    guard = BudgetGuard(max_daily_budget_usdc=0.05)
    
    assert guard.can_spend(0.01) is True
    guard.record_spend(0.01, "Test clean_web", "0x111")
    
    assert guard.can_spend(0.02) is True
    guard.record_spend(0.02, "Test clean_youtube", "0x222")
    
    assert guard.can_spend(0.02) is True
    guard.record_spend(0.02, "Test clean_youtube", "0x333")
    
    # Exceeded
    assert guard.can_spend(0.01) is False
    try:
        guard.record_spend(0.01, "Should fail")
        assert False, "BudgetGuard failed to block spend exceeding limit!"
    except PermissionError:
        print("  [SUCCESS] BudgetGuard correctly blocked over-budget spending!")

    report = guard.get_report()
    assert report["total_spent_usdc"] == 0.05
    assert report["remaining_budget_usdc"] == 0.0
    assert report["transaction_count"] == 3
    print("  [SUCCESS] Budget report verified:", report)

def test_toolkit_schemas():
    print("\nTesting X402AgentToolkit schemas...")
    toolkit = X402AgentToolkit(private_key=None, max_daily_budget_usdc=1.0)
    tools = toolkit.get_tools_list()
    assert len(tools) == 9, f"Expected 9 tools, got {len(tools)}"
    print(f"  [SUCCESS] {len(tools)} callable agent tools loaded (clean_web, batch_clean, clean_youtube, clean_pdf, clean_text, extract_json, deep_research, mint_credit_pass, get_budget_status).")
    
    schemas = toolkit.get_openai_function_schemas()
    assert len(schemas) == 9, f"Expected 9 schemas, got {len(schemas)}"
    schema_names = [s["function"]["name"] for s in schemas]
    expected_names = [
        "x402_clean_web", "x402_batch_clean", "x402_clean_youtube", 
        "x402_clean_pdf", "x402_clean_text", "x402_extract_json", 
        "x402_deep_research", "x402_mint_credit_pass", "x402_get_budget_status"
    ]
    for exp in expected_names:
        assert exp in schema_names, f"Missing schema for {exp}"

    for s in schemas:
        assert "name" in s["function"]
        assert "description" in s["function"]
        assert "parameters" in s["function"]
    print("  [SUCCESS] All 9 OpenAI/Anthropic Function Calling schemas verified.")


if __name__ == "__main__":
    test_budget_guard()
    test_toolkit_schemas()
    print("\n[ALL TESTS PASSED SUCCESSFULLY]")

