"""
Unit Tests for Solana Agent Kit & ElizaOS Tooling
"""

import unittest
from integrations.solana.x402_solana_agent import (
    X402SolanaAgentTool,
    SOLANA_VAULT_PROGRAM,
    SOLANA_TREASURY_PUBKEY,
    SOLANA_USDC_MINT
)

class TestSolanaAgentIntegration(unittest.TestCase):
    def setUp(self):
        self.tool = X402SolanaAgentTool(agent_nonce="solana_unit_test_nonce_2026")

    def test_solana_constants(self):
        self.assertEqual(SOLANA_VAULT_PROGRAM, "7oZ16YaazQzN6z5uA1nAZWD9oGUDXyvHwXGJLFYyWi3y")
        self.assertEqual(SOLANA_TREASURY_PUBKEY, "411ksMz9RHYVtVMe6RUUErzZYtrU9zzvkgzswKbqx9qp")
        self.assertEqual(SOLANA_USDC_MINT, "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v")

    def test_solana_capabilities_discovery(self):
        status = self.tool.get_solana_agent_status()
        self.assertEqual(status["chain"], "solana")
        self.assertIn("vault", status["programs"])
        self.assertEqual(status["programs"]["vault"], SOLANA_VAULT_PROGRAM)

    def test_scrape_clean_markdown_sandbox(self):
        res = self.tool.scrape_clean_markdown("https://news.ycombinator.com")
        self.assertIn(res["status"], ["success", "payment_required"])
        if res["status"] == "success":
            self.assertEqual(res["status_code"], 200)
            self.assertIn("Hacker News", res["markdown"])

if __name__ == "__main__":
    unittest.main()
