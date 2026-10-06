"""
Unit tests for LangChain x402 CleanWeb Tool
--------------------------------------------------------------------------------
Tests both direct invocation and mocked responses for LangChain compliance.
"""

import pytest
import unittest
from unittest.mock import patch, MagicMock
from integrations.langchain.x402_cleanweb_tool import X402CleanWebTool, X402CleanWebInput


class TestX402CleanWebTool(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.tool = X402CleanWebTool(gateway_url="https://mock-gateway.local", vault_key="TEST_KEY")

    def test_tool_metadata(self):
        """Verify tool adheres to LangChain naming and schema standards."""
        self.assertEqual(self.tool.name, "x402_clean_web")
        self.assertTrue("token-reduced clean Markdown" in self.tool.description)
        self.assertEqual(self.tool.args_schema, X402CleanWebInput)

    @patch("requests.get")
    def test_run_success_200(self, mock_get):
        """Verify standard 200 OK clean web extraction."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "title": "Sample Article",
            "clean_markdown": "# Great Work\nHere is the essence of great work.",
            "estimated_token_savings": "88.5%"
        }
        mock_get.return_value = mock_response

        result = self.tool._run(url="https://example.com/article")
        self.assertIn("Sample Article", result)
        self.assertIn("88.5%", result)
        self.assertIn("# Great Work", result)

    @patch("requests.get")
    def test_run_payment_required_402(self, mock_get):
        """Verify proper handling of HTTP 402 challenge."""
        mock_response = MagicMock()
        mock_response.status_code = 402
        mock_response.headers = {"content-type": "application/json"}
        mock_response.json.return_value = {
            "error": "Payment Required",
            "price_usdc": 0.001,
            "recipient": "411ksMz9RHYVtVMe6RUUErzZYtrU9zzvkgzswKbqx9qp"
        }
        mock_get.return_value = mock_response

        result = self.tool._run(url="https://example.com/paid-article")
        self.assertIn("[x402 Payment Required]", result)
        self.assertIn("Free trial quota exhausted", result)

    @pytest.mark.asyncio
    async def test_async_arun(self):
        """Verify asynchronous invocation works properly."""
        with patch.object(self.tool, "_run", return_value="Async Success Content") as mock_run:
            result = await self.tool._arun(url="https://example.com")
            self.assertEqual(result, "Async Success Content")
            mock_run.assert_called_once_with("https://example.com", True)


if __name__ == "__main__":
    unittest.main()
