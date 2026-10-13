"""
Unit tests for batch_run, web_validator, and vendor_assets.
"""

import os
import sys
import unittest
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.batch_run import execute_batch
from tools.web_validator import validate_target
from tools.vendor_assets import vendor_three

class TestWebAndBatchTools(unittest.TestCase):
    def test_batch_run_success(self):
        calls = [
            {"tool": "calc", "args": {"operation": "add", "a": 10, "b": 20}},
            {"tool": "calc", "args": {"operation": "multiply", "a": 5, "b": 6}}
        ]
        res = execute_batch(calls)
        self.assertTrue(res["success"])
        self.assertEqual(res["data"]["succeeded"], 2)
        self.assertEqual(res["data"]["failed"], 0)

    def test_batch_run_with_error_and_stop(self):
        calls = [
            {"tool": "calc", "args": {"operation": "invalid_op"}},
            {"tool": "calc", "args": {"operation": "add", "a": 1, "b": 2}}
        ]
        res = execute_batch(calls, stop_on_error=True)
        self.assertFalse(res["success"])
        self.assertEqual(res["data"]["executed"], 1)

    def test_web_validator_html(self):
        valid_html = "<!DOCTYPE html><html><head><title>Test</title></head><body><h1>Hello</h1></body></html>"
        res = validate_target("", content=valid_html, file_type="html")
        self.assertTrue(res["success"])
        self.assertEqual(res["data"]["error_count"], 0)

        invalid_html = "<div><p>Unclosed paragraph</div>"
        res_err = validate_target("", content=invalid_html, file_type="html")
        self.assertFalse(res_err["success"])
        self.assertGreater(res_err["data"]["error_count"], 0)

    def test_web_validator_js(self):
        valid_js = "const greeting = 'hello'; console.log(greeting);"
        res = validate_target("", content=valid_js, file_type="js")
        self.assertTrue(res["success"])

        invalid_js = "const a = { x: "
        res_err = validate_target("", content=invalid_js, file_type="js")
        self.assertFalse(res_err["success"])

    def test_batch_run_detailed_error(self):
        calls = [
            {"tool": "calc", "args": {"operation": "invalid_op"}}
        ]
        res = execute_batch(calls)
        self.assertFalse(res["success"])
        self.assertIn("[calc]:", res["error"])

    def test_resolve_project_path(self):
        from tools.base import resolve_project_path
        from core.project import switch_project
        repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        switch_project(repo_root)

        # Test relative path that exists
        resolved = resolve_project_path("pytest.ini")
        self.assertEqual(resolved, os.path.join(repo_root, "pytest.ini"))

        # Test absolute path
        abs_p = "/tmp/test.txt"
        self.assertEqual(resolve_project_path(abs_p), abs_p)

if __name__ == "__main__":
    unittest.main()

