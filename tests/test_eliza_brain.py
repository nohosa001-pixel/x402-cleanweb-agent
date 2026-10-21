"""
Unit tests for Eliza Brain Cognitive Layer & Priority 0 A.GRID Dispatch
"""
import unittest
import asyncio
from eliza_brain.evaluators.signal_filter import SignalFilter, GroundTruthSignal
from eliza_brain.memory.causality_graph import CausalityGraph
from eliza_brain.providers.cleanweb_feed import CleanWebIntelligenceFeed

class TestElizaBrain(unittest.TestCase):
    def setUp(self):
        self.filter = SignalFilter(min_threshold=0.4)
        self.graph = CausalityGraph()
        self.feed = CleanWebIntelligenceFeed(filter_threshold=0.4)

    def test_eudr_signal_evaluation(self):
        sample_text = (
            "BREAKING: European Parliament proposes emergency due diligence grace period amendment "
            "for EUDR compliance deadline and geolocation requirements, easing trader penalties."
        )
        signal = self.filter.evaluate(
            clean_text=sample_text,
            source_url="https://ec.europa.eu/environment/forests/eudr-update.html"
        )
        self.assertIsNotNone(signal)
        self.assertEqual(signal.signal_type, "EUDR_POLICY_SHIFT")
        self.assertGreaterEqual(signal.importance_score, 0.4)
        self.assertTrue(signal.merkle_root.startswith("0x"))
        self.assertIn("EUDR compliance risk", signal.actionable_intent)

    def test_mineral_disruption_causality(self):
        sample_text = (
            "URGENT: Government announces immediate critical mineral export ban on unrefined cobalt "
            "and lithium ore following major mine shutdown and refinery strikes."
        )
        signal = self.filter.evaluate(
            clean_text=sample_text,
            source_url="https://mining.gov.example/press-release"
        )
        self.assertIsNotNone(signal)
        self.assertEqual(signal.signal_type, "MINERAL_SUPPLY_DISRUPTION")

        prediction = self.graph.record_and_predict(signal)
        self.assertIn("prediction", prediction)
        self.assertEqual(prediction["prediction"]["predicted_lag_hours"], 2)
        self.assertIn("minerals-oracle-x402", prediction["prediction"]["recommended_action"])

    def test_full_feed_pipeline(self):
        async def _run():
            sample_text = (
                "Notice: Panama Canal congestion causes temporary port freight index spike "
                "requiring maritime transport re-routing and strict e-seal inspection."
            )
            result = await self.feed.ingest_and_broadcast(
                clean_text=sample_text,
                source_url="https://freight-news.example/panama",
                sync_to_agrid=False  # Local unit test without real network
            )
            self.assertIsNotNone(result)
            self.assertEqual(result["signal"]["type"], "GEO_TRADE_ANOMALY")
            self.assertIn("predicted_lag_hours", result["prediction"])

        asyncio.run(_run())

    def test_agrid_early_signal_dispatch_live_mock(self):
        from unittest.mock import patch, MagicMock
        from app.agrid_ops_client import dispatch_early_signal_to_agrid_async

        async def _run():
            mock_res = MagicMock()
            mock_res.is_success = True
            mock_res.status_code = 200
            mock_res.json.return_value = {
                "status": "DISPATCHED",
                "signal_id": "sig_test_123",
                "priority": "P0_IMMEDIATE"
            }

            with patch("httpx.AsyncClient.post", return_value=mock_res):
                res = await dispatch_early_signal_to_agrid_async(
                    signal_type="EUDR_POLICY_SHIFT",
                    importance_score=0.95,
                    summary_clean_text="EU Parliament postpones reporting deadline by 6 months.",
                    merkle_root="0x1234abcd",
                    source_url="https://ec.europa.eu/forests"
                )
                self.assertIsNotNone(res)
                self.assertEqual(res["status"], "DISPATCHED")

        asyncio.run(_run())

    def test_agrid_early_signal_dispatch_graceful_fallback(self):
        from unittest.mock import patch
        from app.agrid_ops_client import dispatch_early_signal_to_agrid_async

        async def _run():
            with patch("httpx.AsyncClient.post", side_effect=Exception("Network Timeout")):
                res = await dispatch_early_signal_to_agrid_async(
                    signal_type="MINERAL_SUPPLY_DISRUPTION",
                    importance_score=0.88,
                    summary_clean_text="Cobalt export tariff hike announced.",
                    merkle_root="0xdeadbeef",
                    source_url="https://mining.gov.example"
                )
                self.assertIsNone(res)

        asyncio.run(_run())

if __name__ == "__main__":
    unittest.main()

