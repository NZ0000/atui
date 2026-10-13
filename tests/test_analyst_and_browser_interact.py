"""
Tests for browser_interact tool, analyst agent, and iteration pipeline workflow.
"""

import os
import sys
import unittest
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tools
from core.role import Role
from api.service import run_iteration_pipeline_workflow, interact_browser
from tools.browser_interact import TOOL_SPEC, execute as fn_browser_interact


class TestAnalystAndBrowserInteract(unittest.TestCase):
    def test_browser_interact_tool_registration(self):
        """Verify browser_interact is auto-discovered and registered."""
        tool = tools.get_tool("browser_interact")
        self.assertIsNotNone(tool)
        self.assertEqual(tool["name"], "browser_interact")
        self.assertIn("steps", tool["spec"]["parameters"]["properties"])
        self.assertIn("url", tool["spec"]["parameters"]["properties"])

    def test_analyst_role_definition(self):
        """Verify analyst agent exists and is configured properly."""
        role = Role.from_file("agents/analyst.md")
        self.assertEqual(role.name, "analyst")
        self.assertIn("browser_interact", role.tools)
        self.assertIn("read", role.tools)
        self.assertIn("code_reviewer", role.tools)
        # Analyst should have gate rules
        self.assertTrue(role.gate_rules.get("require_output_file", False))

    def test_other_agents_have_browser_interact(self):
        """Verify designer and tester agents have browser_interact."""
        designer = Role.from_file("agents/designer.md")
        self.assertIn("browser_interact", designer.tools)

        tester = Role.from_file("agents/tester.md")
        self.assertIn("browser_interact", tester.tools)

    def test_browser_interact_execution_validation(self):
        """Verify browser_interact handles empty or missing url gracefully."""
        res = fn_browser_interact({})
        self.assertFalse(res["success"])
        self.assertIn("url", res["error"].lower())

    def test_api_service_exports(self):
        """Verify high-level service API exports iteration functions."""
        import api.service as svc
        self.assertTrue(hasattr(svc, "run_iteration_pipeline_workflow"))
        self.assertTrue(hasattr(svc, "interact_browser"))

    def test_atui_cli_iterate_flag(self):
        """Verify atui CLI argument parser includes --iterate flag."""
        import atui
        # Inspect atui main / parse_args
        import argparse
        # Create a parser matching atui.py
        import inspect
        source = inspect.getsource(atui)
        self.assertIn("--iterate", source)
        self.assertIn("run_iteration_pipeline_workflow", source)


if __name__ == "__main__":
    unittest.main()
