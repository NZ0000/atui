#!/usr/bin/env python3
"""
Tool: run
Executes shell commands in a specified working directory with timeout handling.
Supports both Python function calling and CLI argument invocation.
"""

import os
import sys
import time
import subprocess
from typing import Dict, Any, Optional

try:
    from tools.base import make_result, cli_runner
except ImportError:
    from base import make_result, cli_runner

TOOL_SPEC = {
    "name": "run",
    "description": "Execute a terminal shell command with a timeout, returning stdout, stderr, and exit code.",
    "parameters": {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "The command string to execute in bash/shell."
            },
            "cwd": {
                "type": "string",
                "description": "Working directory. Defaults to current directory."
            },
            "timeout": {
                "type": "integer",
                "description": "Timeout in seconds. Defaults to 60."
            }
        },
        "required": ["command"]
    }
}

DANGEROUS_PATTERNS = [
    "rm -rf /",
    "rm -rf /*",
    ":(){ :|:& };:",
    "> /dev/sda",
    "mkfs."
]

def run_command(command: str, cwd: Optional[str] = None, timeout: int = 60) -> Dict[str, Any]:
    if not command or not command.strip():
        return make_result(False, error="Command cannot be empty.")

    # Guard against obvious destructive disaster commands
    for pattern in DANGEROUS_PATTERNS:
        if pattern in command:
            return make_result(False, error=f"Command blocked by safety filter: contains '{pattern}'")

    working_dir = os.path.abspath(cwd) if cwd else os.getcwd()
    if not os.path.exists(working_dir):
        return make_result(False, error=f"Working directory does not exist: {working_dir}")

    start_time = time.time()
    try:
        proc = subprocess.run(
            command,
            shell=True,
            cwd=working_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
            executable="/bin/bash" if os.path.exists("/bin/bash") else None
        )
        elapsed = round(time.time() - start_time, 3)
        return make_result(
            success=(proc.returncode == 0),
            data={
                "command": command,
                "exit_code": proc.returncode,
                "stdout": proc.stdout,
                "stderr": proc.stderr,
                "duration_seconds": elapsed,
                "cwd": working_dir
            },
            error=f"Command exited with non-zero code {proc.returncode}" if proc.returncode != 0 else ""
        )
    except subprocess.TimeoutExpired as e:
        elapsed = round(time.time() - start_time, 3)
        stdout = e.stdout if isinstance(e.stdout, str) else (e.stdout.decode("utf-8", "replace") if e.stdout else "")
        stderr = e.stderr if isinstance(e.stderr, str) else (e.stderr.decode("utf-8", "replace") if e.stderr else "")
        return make_result(
            False,
            data={
                "command": command,
                "exit_code": -1,
                "stdout": stdout,
                "stderr": stderr,
                "duration_seconds": elapsed,
                "timed_out": True
            },
            error=f"Command timed out after {timeout} seconds."
        )
    except Exception as e:
        elapsed = round(time.time() - start_time, 3)
        return make_result(False, error=f"Execution error: {e}", data={"duration_seconds": elapsed})

def execute(params: Dict[str, Any]) -> Dict[str, Any]:
    command = params.get("command")
    if not command:
        return make_result(False, error="Parameter 'command' is required.")
    cwd = params.get("cwd")
    timeout = params.get("timeout", 60)
    try:
        timeout = int(timeout)
    except (ValueError, TypeError):
        timeout = 60
    return run_command(command, cwd, timeout)

if __name__ == "__main__":
    cli_runner("run", TOOL_SPEC, execute)
