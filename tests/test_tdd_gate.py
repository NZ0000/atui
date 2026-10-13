"""
Tests for TDD Gate and Git Rollback mechanism.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.tdd_gate import TddGate

class TestTddGate(unittest.TestCase):
    def setUp(self):
        self.gate = TddGate(target_dir="tests")

    def test_run_verification_on_valid_suite(self):
        verif = self.gate.run_verification(target="tests/test_role.py")
        self.assertTrue(verif["passed"])
        self.assertIn("passed", verif["summary"])

    def test_gate_detects_broken_syntax(self):
        temp_bad = "tests/_tmp_bad_syntax.py"
        try:
            with open(temp_bad, "w") as f:
                f.write("def broken(:\n    pass\n")
            verif = self.gate.run_verification(target=temp_bad)
            self.assertFalse(verif["passed"])
        finally:
            if os.path.exists(temp_bad):
                os.remove(temp_bad)

    def test_git_gate_rollback_on_failure(self):
        temp_bad = "tests/_tmp_bad_test.py"
        with open(temp_bad, "w") as f:
            f.write("import unittest\nclass BadTest(unittest.TestCase):\n    def test_fail(self):\n        self.assertEqual(1, 2)\n")

        try:
            res = self.gate.verify_and_git_gate("Attempting broken commit", target=temp_bad, rollback_path=temp_bad)
            self.assertFalse(res["success"])
            self.assertEqual(res["action"], "rolled_back")
        finally:
            if os.path.exists(temp_bad):
                os.remove(temp_bad)

if __name__ == "__main__":
    unittest.main()
