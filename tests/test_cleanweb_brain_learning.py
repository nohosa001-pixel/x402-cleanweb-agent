"""
Unit tests for CleanWeb Non-Invasive ElizaOS Brain Continuous Learning Engine
(PLAN-CW-ELIZA-2026-001)
"""

import os
import tempfile
import unittest
from unittest.mock import patch

import scripts.run_cleanweb_brain_learning as brain_daemon
from eliza_brain.evaluators.signal_filter import SignalFilter
from eliza_brain.memory.causality_graph import CausalityGraph


class TestCleanWebBrainLearning(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.state_file = os.path.join(self.temp_dir.name, "test_learning_state.json")
        self.hb_file = os.path.join(self.temp_dir.name, "test_heartbeat.json")

        self.filter_engine = SignalFilter(min_threshold=0.5)
        self.graph_engine = CausalityGraph(max_history=500)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_single_cycle_convergence_and_persistence(self):
        with patch.object(brain_daemon, "DATA_DIR", self.temp_dir.name), \
             patch.object(brain_daemon, "STATE_FILE", self.state_file), \
             patch.object(brain_daemon, "HEARTBEAT_FILE", self.hb_file):
            state = brain_daemon.load_learning_state()
            initial_brier = state["brier_score"]
            initial_readiness = state["overall_readiness_score"]

            entry = brain_daemon.run_single_learning_cycle(
                state, self.filter_engine, self.graph_engine
            )

            self.assertEqual(entry["cycle"], 1)
            self.assertEqual(entry["day"], 1)
            self.assertLess(entry["brier_score"], initial_brier)
            self.assertGreater(entry["readiness"], initial_readiness)
            self.assertTrue(entry["block_id"].startswith("blk_cw_"))
            self.assertTrue(os.path.exists(self.state_file))
            self.assertTrue(os.path.exists(self.hb_file))

    def test_history_tail_memory_cap(self):
        with patch.object(brain_daemon, "DATA_DIR", self.temp_dir.name), \
             patch.object(brain_daemon, "STATE_FILE", self.state_file), \
             patch.object(brain_daemon, "HEARTBEAT_FILE", self.hb_file):
            state = brain_daemon.load_learning_state()
            for _ in range(25):
                brain_daemon.run_single_learning_cycle(
                    state, self.filter_engine, self.graph_engine
                )

            # History tail is strictly bounded to 20 entries to prevent memory leaks
            self.assertEqual(len(state["history_tail"]), 20)
            self.assertEqual(state["total_cycles_completed"], 25)


if __name__ == "__main__":
    unittest.main()
