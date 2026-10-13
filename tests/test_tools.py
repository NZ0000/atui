"""
Tests for atui tools.
Verifies both direct function invocation and CLI execution for all tools.
"""

import os
import sys
import json
import tempfile
import subprocess
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tools
from tools.read import execute as fn_read
from tools.write import execute as fn_write
from tools.run import execute as fn_run
from tools.test_runner import execute as fn_test_runner
from tools.git_tool import execute as fn_git
from tools.inspect_ref import execute as fn_inspect_ref

class TestTools(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def test_write_and_read_function(self):
        test_file = os.path.join(self.temp_dir, "sample.txt")
        w_res = fn_write({
            "path": test_file,
            "content": "Line 1\nLine 2\nLine 3\n"
        })
        self.assertTrue(w_res["success"])
        self.assertTrue(os.path.exists(test_file))

        r_res = fn_read({"path": test_file})
        self.assertTrue(r_res["success"])
        self.assertEqual(r_res["data"]["total_lines"], 3)
        self.assertIn("Line 2", r_res["data"]["content"])

        slice_res = fn_read({"path": test_file, "start_line": 2, "end_line": 2})
        self.assertTrue(slice_res["success"])
        self.assertEqual(slice_res["data"]["content"].strip(), "Line 2")

    def test_write_replace_and_append(self):
        test_file = os.path.join(self.temp_dir, "replace_test.txt")
        fn_write({"path": test_file, "content": "Hello World\n"})
        
        app_res = fn_write({"path": test_file, "mode": "append", "content": "Hello Again\n"})
        self.assertTrue(app_res["success"])

        rep_res = fn_write({
            "path": test_file,
            "mode": "replace",
            "target_chunk": "World",
            "replacement_chunk": "Universe"
        })
        self.assertTrue(rep_res["success"])
        
        r_res = fn_read({"path": test_file})
        self.assertIn("Hello Universe", r_res["data"]["content"])

    def test_run_command_function(self):
        res = fn_run({"command": "echo 'test run tool'"})
        self.assertTrue(res["success"])
        self.assertEqual(res["data"]["exit_code"], 0)
        self.assertIn("test run tool", res["data"]["stdout"])

        bad_res = fn_run({"command": "rm -rf /"})
        self.assertFalse(bad_res["success"])
        self.assertIn("safety filter", bad_res["error"])

    def test_tools_cli_invocation(self):
        p = subprocess.run(
            [sys.executable, "tools/read.py", "--path", "rule/rule.md"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        self.assertEqual(p.returncode, 0)
        data = json.loads(p.stdout)
        self.assertGreaterEqual(data["data"]["total_lines"], 6)
        self.assertIn("万物皆插件", data["data"]["content"])

    def test_test_runner_syntax(self):
        good_file = os.path.join(self.temp_dir, "good.py")
        bad_file = os.path.join(self.temp_dir, "bad.py")

        with open(good_file, "w") as f:
            f.write("def foo():\n    return 42\n")

        with open(bad_file, "w") as f:
            f.write("def foo() invalid syntax\n")

        res_good = fn_test_runner({"target": good_file, "mode": "syntax"})
        self.assertTrue(res_good["success"])
        self.assertTrue(res_good["data"]["passed"])

        res_bad = fn_test_runner({"target": bad_file, "mode": "syntax"})
        self.assertFalse(res_bad["success"])
        self.assertEqual(len(res_bad["data"]["syntax_errors"]), 1)

    def test_git_tool(self):
        res = fn_git({"action": "status"})
        self.assertTrue(res["success"])
        self.assertIn("short_status", res["data"])

    def test_inspect_ref_tool(self):
        res = fn_inspect_ref({"query": "万物皆插件", "subpath": "rule"})
        self.assertTrue(res["success"])
        self.assertGreaterEqual(res["data"]["total_matches"], 1)

if __name__ == "__main__":
    unittest.main()
