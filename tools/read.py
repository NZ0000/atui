#!/usr/bin/env python3
"""
Tool: read
Reads file contents or lists directory entries.
Supports both Python function calling and CLI argument invocation.
"""

import os
import sys
from typing import Dict, Any, Optional

try:
    from tools.base import make_result, cli_runner, resolve_project_path
except ImportError:
    from base import make_result, cli_runner, resolve_project_path

TOOL_SPEC = {
    "name": "read",
    "description": "Read file contents or list files in a directory. Supports line range reading.",
    "parameters": {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Path to the file or directory to read."
            },
            "start_line": {
                "type": "integer",
                "description": "Optional 1-indexed starting line number for files."
            },
            "end_line": {
                "type": "integer",
                "description": "Optional 1-indexed ending line number for files."
            }
        },
        "required": ["path"]
    }
}

def read_path(path: str, start_line: Optional[int] = None, end_line: Optional[int] = None) -> Dict[str, Any]:
    path = resolve_project_path(path)
    if not os.path.exists(path):
        return make_result(False, error=f"Path not found: {path}")

    if os.path.isdir(path):
        try:
            entries = []
            for item in sorted(os.listdir(path)):
                item_path = os.path.join(path, item)
                is_dir = os.path.isdir(item_path)
                size = os.path.getsize(item_path) if not is_dir else 0
                entries.append({
                    "name": item,
                    "is_dir": is_dir,
                    "size_bytes": size
                })
            return make_result(True, data={
                "type": "directory",
                "path": os.path.abspath(path),
                "total_items": len(entries),
                "entries": entries
            })
        except Exception as e:
            return make_result(False, error=f"Failed to list directory '{path}': {e}")

    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()

        total_lines = len(lines)
        s = 1 if start_line is None or start_line < 1 else start_line
        e = total_lines if end_line is None or end_line > total_lines else end_line

        if s > total_lines:
            content = ""
        else:
            selected_lines = lines[s - 1:e]
            content = "".join(selected_lines)

        return make_result(True, data={
            "type": "file",
            "path": os.path.abspath(path),
            "total_lines": total_lines,
            "start_line": s,
            "end_line": e,
            "content": content
        })
    except Exception as e:
        return make_result(False, error=f"Failed to read file '{path}': {e}")

def execute(params: Dict[str, Any]) -> Dict[str, Any]:
    path = params.get("path")
    if not path:
        return make_result(False, error="Parameter 'path' is required.")
    start_line = params.get("start_line")
    end_line = params.get("end_line")
    return read_path(path, start_line, end_line)

if __name__ == "__main__":
    cli_runner("read", TOOL_SPEC, execute)
