"""
Tests for Project Context and directory management.
"""

import os
import sys
import unittest
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.project import manage_project, get_current_project, switch_project, ProjectContext

class TestProjectContext(unittest.TestCase):
    def setUp(self):
        self.repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        switch_project(self.repo_root)

    def test_current_project_detects_rules(self):
        ctx = get_current_project()
        self.assertTrue(os.path.exists(ctx.path))
        self.assertIsNotNone(ctx.rules_file)
        self.assertIn("万物皆插件", ctx.rules)

    def test_switch_project(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Create a rule file in the temp project
            rule_path = os.path.join(tmp_dir, "rule.md")
            with open(rule_path, "w") as f:
                f.write("# Temp Project Custom Rules\n- Rule A\n- Rule B\n")

            new_ctx = switch_project(tmp_dir)
            self.assertEqual(new_ctx.path, os.path.abspath(tmp_dir))
            self.assertEqual(new_ctx.rules_file, "rule.md")
            self.assertIn("Rule A", new_ctx.rules)

            # Test prompt injection format
            injection = new_ctx.format_prompt_injection()
            self.assertIn("ACTIVE PROJECT CONTEXT", injection)
            self.assertIn("Temp Project Custom Rules", injection)

    def test_manage_project_api(self):
        res = manage_project("get")
        self.assertTrue(res["success"])
        self.assertIn("path", res["project"])

if __name__ == "__main__":
    unittest.main()
