#!/usr/bin/env python3
"""
Tool: inspect_ref
Inspects reference repositories (e.g. in ref/), searches keywords, reads files,
and finds implementation patterns for planning and brainstorming.
Supports both Python function calling and CLI argument invocation.
"""

import os
import re
import sys
from typing import Dict, Any, List, Optional

try:
    from tools.base import make_result, cli_runner
except ImportError:
    from base import make_result, cli_runner

TOOL_SPEC = {
    "name": "inspect_ref",
    "description": "Inspect and search reference repositories (ref/) for architectures, patterns, and code examples.",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search keyword or regex pattern across reference files."
            },
            "subpath": {
                "type": "string",
                "description": "Subdirectory under ref/ or workspace (e.g., 'ref/tianshu-harness/src'). Defaults to 'ref'."
            },
            "max_results": {
                "type": "integer",
                "description": "Maximum number of search matches to return. Defaults to 15."
            }
        },
        "required": ["query"]
    }
}

def search_ref(query: str, subpath: str = "ref", max_results: int = 15) -> Dict[str, Any]:
    search_dir = os.path.abspath(subpath)
    if not os.path.exists(search_dir):
        return make_result(False, error=f"Directory '{search_dir}' does not exist.")

    pattern = re.compile(query, re.IGNORECASE)
    matches = []
    total_files_scanned = 0

    for root, dirs, files in os.walk(search_dir):
        dirs[:] = [d for d in dirs if d not in (".git", "node_modules", ".venv", "__pycache__", "dist", "build")]
        for f in files:
            if f.endswith((".ts", ".js", ".py", ".md", ".json", ".yaml", ".yml", ".toml", ".txt")):
                total_files_scanned += 1
                file_path = os.path.join(root, f)
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as fp:
                        for line_no, line in enumerate(fp, start=1):
                            if pattern.search(line):
                                rel_path = os.path.relpath(file_path, os.getcwd())
                                matches.append({
                                    "file": rel_path,
                                    "line": line_no,
                                    "content": line.strip()[:180]
                                })
                                if len(matches) >= max_results:
                                    break
                except Exception:
                    continue
            if len(matches) >= max_results:
                break
        if len(matches) >= max_results:
            break

    return make_result(True, data={
        "query": query,
        "scanned_directory": search_dir,
        "files_scanned": total_files_scanned,
        "total_matches": len(matches),
        "matches": matches
    })

def execute(params: Dict[str, Any]) -> Dict[str, Any]:
    query = params.get("query")
    if not query:
        return make_result(False, error="Parameter 'query' is required.")
    subpath = params.get("subpath", "ref")
    max_results = params.get("max_results", 15)
    try:
        max_results = int(max_results)
    except (ValueError, TypeError):
        max_results = 15
    return search_ref(query, subpath, max_results)

if __name__ == "__main__":
    cli_runner("inspect_ref", TOOL_SPEC, execute)
