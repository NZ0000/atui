#!/usr/bin/env python3
"""
Tool: write
Creates, overwrites, appends, or replaces content in a file.
Supports both Python function calling and CLI argument invocation.
"""

import os
import sys
import difflib
import threading
from typing import Dict, Any, Optional

try:
    from tools.base import make_result, cli_runner, resolve_project_path
except ImportError:
    from base import make_result, cli_runner, resolve_project_path

# ---------------------------------------------------------------------------
# Cross-agent file ownership registry (in-process, thread-safe).
# Files assigned to a worker are locked for the duration of that worker's run:
# any OTHER agent attempting to write them gets FILE_LOCKED and must wait for
# the owner to finish (retry later) or coordinate via the blackboard.
# Unassigned files carry no lock and may be modified by anyone.
# ---------------------------------------------------------------------------
_FILE_LOCKS: Dict[str, str] = {}
_LOCK_GUARD = threading.Lock()


def acquire_write_lock(path: str, owner: str) -> bool:
    """Claim exclusive write ownership of an absolute path. Returns False if held."""
    ap = os.path.abspath(path)
    with _LOCK_GUARD:
        holder = _FILE_LOCKS.get(ap)
        if holder and holder != owner:
            return False
        _FILE_LOCKS[ap] = owner
        return True


def release_write_lock(path: str, owner: str) -> None:
    ap = os.path.abspath(path)
    with _LOCK_GUARD:
        if _FILE_LOCKS.get(ap) == owner:
            del _FILE_LOCKS[ap]


def lock_holder(path: str) -> Optional[str]:
    with _LOCK_GUARD:
        return _FILE_LOCKS.get(os.path.abspath(path))


# Thread-local writer identity: the pipeline stamps each worker thread with its
# owner id so write_file can distinguish the rightful owner from cross-writers.
_WRITER_CTX = threading.local()


def set_current_writer(owner: str) -> None:
    _WRITER_CTX.owner = owner


def clear_current_writer() -> None:
    _WRITER_CTX.owner = None


def _current_writer() -> Optional[str]:
    return getattr(_WRITER_CTX, "owner", None)

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
    # Ownership guard: deny cross-writes to files locked by another agent.
    # The rightful owner (stamped via thread-local) may write its own file;
    # files with no lock are free for anyone.
    holder = lock_holder(path)
    if holder and holder != _current_writer():
        return make_result(False, error=(
            f"FILE_LOCKED: '{path}' is being modified by '{holder}'. "
            f"Do not cross-edit concurrently — wait until that worker finishes "
            f"(retry later) or coordinate via the blackboard tool."
        ))
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
    path = (
        params.get("path")
        or params.get("file")
        or params.get("file_path")
        or params.get("filename")
        or params.get("target")
    )
    if not path:
        return make_result(False, error="Parameter 'path' is required.")
    content = (
        params.get("content")
        if "content" in params
        else (params.get("text") or params.get("code") or params.get("body") or "")
    )
    mode = params.get("mode", "overwrite")
    target_chunk = params.get("target_chunk")
    replacement_chunk = params.get("replacement_chunk")
    return write_file(path, content, mode, target_chunk, replacement_chunk)

if __name__ == "__main__":
    cli_runner("write", TOOL_SPEC, execute)
