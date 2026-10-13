"""
Tests for code_reviewer tool and reviewer agent integration.
"""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tools
from tools.code_reviewer import execute as fn_code_reviewer, scan_anti_patterns
from core.role import Role

class TestCodeReview(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def test_reviewer_tool_registration(self):
        self.assertIn("code_reviewer", tools.list_tools())
        res = tools.execute_tool("code_reviewer", {})
        self.assertTrue(res["success"])
        self.assertIn("issues_count", res["data"])
        self.assertIn("changed_files", res["data"])

    def test_reviewer_anti_pattern_tdz_detection(self):
        bad_js = (
            "function init() {\n"
            "    animate();\n"
            "}\n"
            "init();\n"
            "let frameCount = 0;\n"
            "function animate() { frameCount++; }\n"
        )
        bad_file = os.path.join(self.temp_dir, "bad.js")
        with open(bad_file, "w", encoding="utf-8") as f:
            f.write(bad_js)

        issues = scan_anti_patterns(self.temp_dir, [{"file": "bad.js", "status": "M"}])
        categories = [i["category"] for i in issues]
        self.assertIn("JS_TEMPORAL_DEAD_ZONE", categories)

    def test_reviewer_anti_pattern_msaa_detection(self):
        bad_three_js = (
            "import * as THREE from 'three';\n"
            "import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';\n"
            "const composer = new EffectComposer(renderer);\n"
        )
        bad_file = os.path.join(self.temp_dir, "view.js")
        with open(bad_file, "w", encoding="utf-8") as f:
            f.write(bad_three_js)

        issues = scan_anti_patterns(self.temp_dir, [{"file": "view.js", "status": "M"}])
        categories = [i["category"] for i in issues]
        self.assertIn("GRAPHICS_ANTIALIASING", categories)

    def test_reviewer_role_loading(self):
        role_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "agents", "reviewer.md")
        self.assertTrue(os.path.exists(role_file))
        role = Role.from_file(role_file)
        self.assertEqual(role.name, "reviewer")
        self.assertIn("code_reviewer", role.tools)
        self.assertIn("git_tool", role.tools)

if __name__ == "__main__":
    unittest.main()
