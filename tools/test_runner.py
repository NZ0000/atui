#!/usr/bin/env python3
"""
Tool: test_runner
Performs syntax checking, byte-compilation checks, and test suite execution (pytest or unittest).
Supports both Python function calling and CLI argument invocation.
"""

import os
import sys
import ast
import py_compile
import subprocess
from typing import Dict, Any, List, Optional

try:
    from tools.base import make_result, cli_runner
except ImportError:
    from base import make_result, cli_runner

TOOL_SPEC = {
    "name": "test_runner",
    "description": "Run Python syntax validation, py_compile checks, and test runner (pytest/unittest). Returns structured results and errors.",
    "parameters": {
        "type": "object",
        "properties": {
            "target": {
                "type": "string",
                "description": "File or directory path to test or check."
            },
            "mode": {
                "type": "string",
                "enum": ["all", "syntax", "pytest", "unittest"],
                "description": "Testing mode: 'all' (default, syntax check + test run), 'syntax', 'pytest', or 'unittest'."
            },
            "cwd": {
                "type": "string",
                "description": "Working directory. Defaults to current directory."
            }
        },
        "required": ["target"]
    }
}

def check_syntax(path: str) -> List[Dict[str, Any]]:
    """Check Python syntax via ast.parse and py_compile for files or directory."""
    errors = []
    py_files = []

    if os.path.isfile(path):
        if path.endswith(".py"):
            py_files.append(path)
    elif os.path.isdir(path):
        for root, _, files in os.walk(path):
            for f in files:
                if f.endswith(".py"):
                    py_files.append(os.path.join(root, f))

    for py_file in py_files:
        # Check 1: AST Parse
        try:
            with open(py_file, "r", encoding="utf-8", errors="replace") as f:
                source = f.read()
            ast.parse(source, filename=py_file)
        except SyntaxError as e:
            errors.append({
                "file": py_file,
                "type": "SyntaxError",
                "line": e.lineno,
                "offset": e.offset,
                "message": str(e)
            })
            continue

        # Check 2: Byte compilation
        try:
            py_compile.compile(py_file, doraise=True)
        except py_compile.PyCompileError as e:
            errors.append({
                "file": py_file,
                "type": "PyCompileError",
                "line": getattr(e, "lineno", None),
                "message": str(e)
            })

    return errors

def run_tests(target: str, mode: str = "all", cwd: Optional[str] = None) -> Dict[str, Any]:
    working_dir = os.path.abspath(cwd) if cwd else os.getcwd()
    syntax_errors = []

    # 1. Syntax check first
    if mode in ("all", "syntax"):
        target_check = target if os.path.isabs(target) else os.path.join(working_dir, target)
        if os.path.exists(target_check):
            syntax_errors = check_syntax(target_check)
            if syntax_errors:
                return make_result(
                    False,
                    data={
                        "stage": "syntax_check",
                        "passed": False,
                        "syntax_errors": syntax_errors,
                        "test_output": "Syntax checks failed before running tests."
                    },
                    error=f"Found {len(syntax_errors)} syntax/compilation error(s)."
                )
        if mode == "syntax":
            return make_result(
                True,
                data={
                    "stage": "syntax_check",
                    "passed": True,
                    "syntax_errors": [],
                    "message": "All syntax checks passed."
                }
            )

    # 2. Run tests via pytest (preferred) or unittest
    has_pytest = False
    try:
        check_p = subprocess.run([sys.executable, "-m", "pytest", "--version"],
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        has_pytest = (check_p.returncode == 0)
    except Exception:
        has_pytest = False

    if mode == "unittest" or (not has_pytest and mode in ("all", "pytest")):
        if os.path.isdir(target):
            test_runner_cmd = [sys.executable, "-m", "unittest", "discover", "-s", target]
        else:
            test_runner_cmd = [sys.executable, "-m", "unittest", target]
        framework = "unittest"
    else:
        test_runner_cmd = [sys.executable, "-m", "pytest", "-v", target]
        framework = "pytest"

    env = os.environ.copy()
    current_pp = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = f"{working_dir}:{current_pp}" if current_pp else working_dir

    try:
        proc = subprocess.run(
            test_runner_cmd,
            cwd=working_dir,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=120
        )
        passed = (proc.returncode == 0)
        output = (proc.stdout or "") + ("\n" + proc.stderr if proc.stderr else "")
        
        return make_result(
            passed,
            data={
                "stage": "test_run",
                "framework": framework,
                "command": " ".join(test_runner_cmd),
                "passed": passed,
                "exit_code": proc.returncode,
                "raw_output": output.strip(),
                "syntax_errors": syntax_errors
            },
            error="" if passed else f"Tests failed with exit code {proc.returncode}."
        )
    except subprocess.TimeoutExpired:
        return make_result(
            False,
            data={
                "stage": "test_run",
                "framework": framework,
                "passed": False,
                "timed_out": True
            },
            error="Test suite timed out after 120 seconds."
        )
    except Exception as e:
        return make_result(False, error=f"Failed to execute tests: {e}")

def execute(params: Dict[str, Any]) -> Dict[str, Any]:
    target = params.get("target")
    if not target:
        return make_result(False, error="Parameter 'target' is required.")
    mode = params.get("mode", "all")
    cwd = params.get("cwd")
    return run_tests(target, mode, cwd)

if __name__ == "__main__":
    cli_runner("test_runner", TOOL_SPEC, execute)
