"""
Unit tests for CrewAI x402 CleanWeb Tool
--------------------------------------------------------------------------------
Tests metadata schema and mocked HTTP responses.
"""

import unittest
from unittest.mock import patch, MagicMock
from integrations.crewai.x402_cleanweb_tool import X402CleanWebTool, X402CleanWebToolInput


class TestCrewAIX402CleanWebTool(unittest.TestCase):
    def setUp(self):
        self.tool = X402CleanWebTool(gateway_url="https://mock-gateway.local", vault_key="CREW_KEY")

    def test_metadata(self):
        """Verify CrewAI tool name and input schema."""
        self.assertEqual(self.tool.name, "x402_clean_web")
        self.assertTrue("high-quality, noise-free Markdown" in self.tool.description)
        self.assertEqual(self.tool.args_schema, X402CleanWebToolInput)

    @patch("requests.get")
    def test_run_success(self, mock_get):
        """Verify successful response formatting for CrewAI agents."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "title": "Autonomous Agents Report",
            "clean_markdown": "## Findings\nAI swarms require clean web extraction.",
            "estimated_token_savings": "86.8%"
        }
        mock_get.return_value = mock_resp

        output = self.tool._run(url="https://arxiv.org/abs/sample")
        self.assertIn("Autonomous Agents Report", output)
        self.assertIn("86.8%", output)
        self.assertIn("## Findings", output)

    @patch("requests.get")
    def test_run_402_payment_challenge(self, mock_get):
        """Verify 402 challenge formatting."""
        mock_resp = MagicMock()
        mock_resp.status_code = 402
        mock_resp.headers = {"content-type": "application/json"}
        mock_resp.json.return_value = {"error": "Payment Required", "price_usdc": 0.001}
        mock_get.return_value = mock_resp

        output = self.tool._run(url="https://example.com/premium")
        self.assertIn("[x402 Payment Required]", output)
        self.assertIn("Free trial exhausted", output)


if __name__ == "__main__":
    unittest.main()
