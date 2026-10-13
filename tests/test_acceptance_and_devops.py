"""
Unit tests for Acceptance Criteria Burn-Down Engine and DevOps Environment Manager.
"""

import os
import sys
import unittest
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.acceptance import (
    AcceptanceCriterion,
    AcceptanceChecklist,
    evaluate_burn_down_gate
)
from tools.env_manager import (
    probe_environment,
    start_http_service,
    list_active_services,
    stop_service_by_port
)

class TestAcceptanceEngine(unittest.TestCase):
    def test_checklist_add_and_burn_down(self):
        cl = AcceptanceChecklist("Test Project Acceptance")
        cl.add_item("Implement core logic", category="functional", item_id="AC-1")
        cl.add_item("Rich lighting with no pitch black surfaces", category="aesthetic", item_id="AC-2")
        cl.add_item("HTTP server ready with no CORS errors", category="environment", item_id="AC-3")

        status = cl.get_status()
        self.assertEqual(status["total"], 3)
        self.assertEqual(status["passed"], 0)
        self.assertEqual(status["remaining"], 3)
        self.assertFalse(status["is_burned_down"])

        # Mark AC-1 as passed
        ok = cl.mark_item("AC-1", passed=True, rationale="Unit tests passed")
        self.assertTrue(ok)
        self.assertEqual(cl.get_status()["passed"], 1)
        self.assertEqual(cl.get_status()["remaining"], 2)

        # Mark remaining
        cl.mark_item("AC-2", passed=True)
        cl.mark_item("AC-3", passed=True)
        self.assertTrue(cl.get_status()["is_burned_down"])

    def test_markdown_parsing_and_gate(self):
        md = """# Acceptance Criteria
- [x] **[AC-1]** (Functional) Build parser
- [ ] **[AC-2]** (Aesthetic) Cyberpunk neon lighting with no dead blacks
"""
        with tempfile.NamedTemporaryFile("w+", suffix=".md", delete=False) as tf:
            tf.write(md)
            temp_path = tf.name

        try:
            cl = AcceptanceChecklist.from_markdown(md)
            self.assertEqual(len(cl.items), 2)
            self.assertTrue(cl.items[0].passed)
            self.assertFalse(cl.items[1].passed)

            # Test gate evaluation
            gate_ok, gate_reason, status = evaluate_burn_down_gate(temp_path)
            self.assertFalse(gate_ok)
            self.assertIn("ACCEPTANCE BURN-DOWN GATE FAILED", gate_reason)
            self.assertIn("AC-2", gate_reason)

            # Mark all as passed and re-evaluate
            cl.mark_item("AC-2", passed=True)
            cl.save_to_file(temp_path)

            gate_ok2, gate_reason2, status2 = evaluate_burn_down_gate(temp_path)
            self.assertTrue(gate_ok2)
            self.assertIn("100% burned down", gate_reason2)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)


class TestEnvManager(unittest.TestCase):
    def test_probe(self):
        info = probe_environment()
        self.assertIn("os", info)
        self.assertIn("python_version", info)
        self.assertTrue(info["recommended_http_port"] > 0)

    def test_start_and_stop_http_service(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            res = start_http_service(directory=tmp_dir)
            self.assertTrue(res["success"])
            port = res["port"]
            self.assertTrue(port > 0)

            services = list_active_services()
            self.assertTrue(any(s["port"] == port for s in services))

            stop_res = stop_service_by_port(port)
            self.assertTrue(stop_res["success"])

if __name__ == "__main__":
    unittest.main()
