"""
Unit tests for LlamaIndex x402 CleanWeb Reader
--------------------------------------------------------------------------------
Tests document loading, metadata structure, and error handling for LlamaIndex compliance.
"""

import unittest
from unittest.mock import patch, MagicMock
from integrations.llamaindex.x402_cleanweb_reader import X402CleanWebReader, Document


class TestX402CleanWebReader(unittest.TestCase):
    def setUp(self):
        self.reader = X402CleanWebReader(gateway_url="https://mock-gateway.local", vault_key="TEST_VAULT_KEY")

    @patch("requests.get")
    def test_load_data_success_200(self, mock_get):
        """Verify successful LlamaIndex Document generation with complete provenance metadata."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "url": "https://example.com/ai-agents",
            "title": "Autonomous Agents in 2026",
            "markdown_content": "# Autonomous Agents\nThey pay for web queries using x402.",
            "word_count": 120,
            "estimated_reading_time_sec": 30,
            "security_audit": {
                "is_safe": True,
                "content_hash": "0xabc123def456"
            },
            "token_analytics": {
                "token_reduction_percent": 88.2
            },
            "spa_hydration": {
                "framework": "Next.js"
            }
        }
        mock_get.return_value = mock_resp

        docs = self.reader.load_data("https://example.com/ai-agents")
        self.assertEqual(len(docs), 1)
        doc = docs[0]
        
        self.assertIn("Autonomous Agents", doc.text)
        self.assertEqual(doc.metadata["source"], "https://example.com/ai-agents")
        self.assertEqual(doc.metadata["title"], "Autonomous Agents in 2026")
        self.assertEqual(doc.metadata["content_hash"], "0xabc123def456")
        self.assertEqual(doc.metadata["token_reduction_percent"], 88.2)
        self.assertEqual(doc.metadata["spa_framework"], "Next.js")
        self.assertTrue(doc.metadata["is_safe"])

    @patch("requests.get")
    def test_load_data_payment_required_402(self, mock_get):
        """Verify 402 payment challenge handled gracefully into document metadata."""
        mock_resp = MagicMock()
        mock_resp.status_code = 402
        mock_resp.text = "Payment required"
        mock_get.return_value = mock_resp

        docs = self.reader.load_data(["https://example.com/paywalled"])
        self.assertEqual(len(docs), 1)
        self.assertIn("[x402 Payment Required]", docs[0].text)
        self.assertEqual(docs[0].metadata["error"], "402_payment_required")


if __name__ == "__main__":
    unittest.main()
