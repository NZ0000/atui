#!/usr/bin/env python3
"""
Tool: write
Creates, overwrites, appends, or replaces content in a file.
Supports both Python function calling and CLI argument invocation.
"""

import os
import sys
import difflib
from typing import Dict, Any, Optional

try:
    from tools.base import make_result, cli_runner, resolve_project_path
except ImportError:
    from base import make_result, cli_runner, resolve_project_path

TOOL_SPEC = {
    "name": "write",
    "description": "Write, overwrite, append, or replace text in a file. Creates parent directories if needed.",
    "parameters": {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Path to the target file."
            },
            "content": {
                "type": "string",
                "description": "Content to write or append."
            },
            "mode": {
                "type": "string",
                "enum": ["overwrite", "append", "replace"],
                "description": "Writing mode: 'overwrite' (default), 'append', or 'replace'."
            },
            "target_chunk": {
                "type": "string",
                "description": "Existing text chunk to replace when mode is 'replace'."
            },
            "replacement_chunk": {
                "type": "string",
                "description": "New text chunk to replace with when mode is 'replace'."
            }
        },
        "required": ["path"]
    }
}

def write_file(
    path: str,
    content: Optional[str] = None,
    mode: str = "overwrite",
    target_chunk: Optional[str] = None,
    replacement_chunk: Optional[str] = None
) -> Dict[str, Any]:
    path = resolve_project_path(path)
    parent = os.path.dirname(os.path.abspath(path))
    if parent and not os.path.exists(parent):
        try:
            os.makedirs(parent, exist_ok=True)
        except Exception as e:
            return make_result(False, error=f"Failed to create directory '{parent}': {e}")

    existed = os.path.exists(path)
    old_content = ""
    if existed:
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                old_content = f.read()
        except Exception as e:
            return make_result(False, error=f"Failed to read existing file '{path}': {e}")

    new_content = ""
    if mode == "append":
        if content is None:
            return make_result(False, error="'content' is required when mode is 'append'.")
        new_content = old_content + content
    elif mode == "replace":
        if not target_chunk:
            return make_result(False, error="'target_chunk' is required when mode is 'replace'.")
        if target_chunk not in old_content:
            return make_result(False, error=f"Target chunk not found in '{path}'.")
        replacement = replacement_chunk if replacement_chunk is not None else (content or "")
        new_content = old_content.replace(target_chunk, replacement, 1)
    else:  # overwrite
        if content is None:
            return make_result(False, error="'content' is required when mode is 'overwrite'.")
        new_content = content

    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(new_content)
    except Exception as e:
        return make_result(False, error=f"Failed to write file '{path}': {e}")

    # Generate unified diff summary
    diff_lines = list(difflib.unified_diff(
        old_content.splitlines(keepends=True),
        new_content.splitlines(keepends=True),
        fromfile=f"a/{os.path.basename(path)}",
        tofile=f"b/{os.path.basename(path)}",
        n=3
    ))
    diff_text = "".join(diff_lines)

    return make_result(True, data={
        "path": os.path.abspath(path),
        "created": not existed,
        "bytes_written": len(new_content.encode("utf-8")),
        "mode": mode,
        "diff": diff_text
    })

def execute(params: Dict[str, Any]) -> Dict[str, Any]:
    path = params.get("path")
    if not path:
        return make_result(False, error="Parameter 'path' is required.")
    content = params.get("content")
    mode = params.get("mode", "overwrite")
    target_chunk = params.get("target_chunk")
    replacement_chunk = params.get("replacement_chunk")
    return write_file(path, content, mode, target_chunk, replacement_chunk)

if __name__ == "__main__":
    cli_runner("write", TOOL_SPEC, execute)
