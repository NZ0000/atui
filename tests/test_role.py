"""
Tests for Role parser and agent markdown specifications.
"""

import os
import sys
import unittest
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.role import Role

class TestRole(unittest.TestCase):
    def test_load_existing_roles(self):
        roles_to_check = ["planner", "coder", "tester", "git_agent", "delivery", "orchestrator"]
        for rname in roles_to_check:
            path = os.path.join("agents", f"{rname}.md")
            self.assertTrue(os.path.exists(path), f"Role file missing: {path}")
            role = Role.from_file(path)
            self.assertEqual(role.name, rname)
            self.assertTrue(len(role.system_prompt) > 0)
            self.assertTrue(len(role.tools) > 0)

    def test_role_permissions_and_tools(self):
        coder = Role.from_file("agents/coder.md")
        self.assertTrue(coder.is_tool_allowed("read"))
        self.assertTrue(coder.is_tool_allowed("write"))
        self.assertTrue(coder.is_tool_allowed("run"))
        self.assertTrue(coder.has_permission("read"))

    def test_custom_markdown_role(self):
        md_text = """---
name: custom_agent
description: 测试用自定义Agent
tools:
  - read
  - write
permissions:
  - read
gate_rules:
  require_output_file: true
---

# 系统提示词
这是测试角色的详细指令。
"""
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as f:
            f.write(md_text)
            temp_path = f.name

        try:
            role = Role.from_file(temp_path)
            self.assertEqual(role.name, "custom_agent")
            self.assertEqual(role.description, "测试用自定义Agent")
            self.assertEqual(role.tools, ["read", "write"])
            self.assertTrue(role.is_tool_allowed("read"))
            self.assertFalse(role.is_tool_allowed("run"))
            self.assertIn("这是测试角色的详细指令", role.system_prompt)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

if __name__ == "__main__":
    unittest.main()
