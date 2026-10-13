#!/usr/bin/env python3
"""
Tool: code_reviewer
Performs automated static code inspection, Git diff extraction,
anti-pattern detection, and mental simulation checklist validation.
Supports both Python function calling and CLI argument invocation.
"""

import os
import sys
import re
import ast
import subprocess
from typing import Dict, Any, List, Optional

try:
    from tools.base import make_result, cli_runner, resolve_project_path
except ImportError:
    from base import make_result, cli_runner, resolve_project_path

TOOL_SPEC = {
    "name": "code_reviewer",
    "description": "Extracts Git diff, inspects code modifications, checks for anti-patterns (e.g. test tampering, Three.js MSAA omission, TDZ scoping errors), and provides static code review reports before testing or compilation.",
    "parameters": {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Optional specific directory or file to review diff for. Defaults to current repository root."
            },
            "check_anti_patterns": {
                "type": "boolean",
                "description": "Whether to perform automated heuristic checks on modified files (default true)."
            },
            "cwd": {
                "type": "string",
                "description": "Working directory of the repository."
            }
        }
    }
}

def _run_git(args: list, cwd: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git"] + args,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=30
    )

def extract_diff(repo_dir: str, target_path: Optional[str] = None) -> Dict[str, Any]:
    """Extract staged, unstaged, and untracked file diffs."""
    cmd_diff = ["diff", "HEAD"]
    if target_path:
        cmd_diff.append(target_path)
    p = _run_git(cmd_diff, repo_dir)
    full_diff = p.stdout

    # If HEAD diff is empty, try unstaged diff
    if not full_diff.strip():
        cmd_unstaged = ["diff"]
        if target_path:
            cmd_unstaged.append(target_path)
        full_diff = _run_git(cmd_unstaged, repo_dir).stdout

    # Get status short for untracked / new files
    p_status = _run_git(["status", "--short"], repo_dir)
    status_lines = [l.strip() for l in p_status.stdout.splitlines() if l.strip()]

    # Extract changed file names
    changed_files = []
    for line in status_lines:
        parts = line.split(maxsplit=1)
        if len(parts) == 2:
            changed_files.append({"status": parts[0], "file": parts[1]})

    return {
        "diff": full_diff,
        "diff_length": len(full_diff),
        "changed_files": changed_files,
        "status_summary": status_lines
    }

def scan_anti_patterns(repo_dir: str, changed_files: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    """Heuristic static inspection on modified/new files."""
    issues = []

    for item in changed_files:
        rel_path = item["file"]
        abs_path = os.path.join(repo_dir, rel_path)
        if not os.path.isfile(abs_path):
            continue

        # Skip vendor assets, images, binaries
        if any(skip in rel_path for skip in ("vendor/", "node_modules/", ".git/", "models/")):
            continue
        if rel_path.endswith((".png", ".jpg", ".glb", ".gltf", ".wasm", ".bin")):
            continue

        try:
            with open(abs_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        except Exception:
            continue

        # 1. Anti-Pattern: Modifying existing test assertions without permission
        if "tests/" in rel_path and rel_path.endswith(".py"):
            if "pytest.skip" in content:
                issues.append({
                    "file": rel_path,
                    "severity": "CRITICAL",
                    "category": "TDD_TAMPERING",
                    "message": "Found 'pytest.skip' in test file. Skipping tests to forge PASS is strictly prohibited."
                })

        # 2. Anti-Pattern: Three.js EffectComposer without samples: 4 (Anti-Aliasing Jaggies)
        if rel_path.endswith((".html", ".js", ".ts", ".mjs")):
            if "EffectComposer" in content:
                if "samples:" not in content and "samples :" not in content and "FXAAPass" not in content:
                    issues.append({
                        "file": rel_path,
                        "severity": "HIGH",
                        "category": "GRAPHICS_ANTIALIASING",
                        "message": "EffectComposer is used without 'samples: 4' (MSAA) or FXAAPass in WebGLRenderTarget. This causes severe edge pixel aliasing (jaggies)."
                    })

        # 3. Anti-Pattern: High metalness without environment map
        if rel_path.endswith((".html", ".js", ".ts", ".mjs")):
            if ("MeshStandardMaterial" in content or "MeshPhysicalMaterial" in content) and "metalness" in content:
                if "RoomEnvironment" not in content and "scene.environment" not in content and "environment" not in content:
                    issues.append({
                        "file": rel_path,
                        "severity": "MEDIUM",
                        "category": "LIGHTING_DEAD_BLACK",
                        "message": "Metallic PBR material detected without RoomEnvironment or scene.environment. Back-facing surfaces will suffer dead-black shading when rotated."
                    })

        # 4. Anti-Pattern: JavaScript let variable used before declaration in animate loop
        if rel_path.endswith((".html", ".js")):
            # Look for animate() called in init(), but frameCount/fps declared later
            m_init = re.search(r'function\s+init\s*\(\)\s*\{[^}]*animate\(\)', content, re.DOTALL)
            if m_init:
                init_idx = m_init.start()
                m_var = re.search(r'let\s+(frameCount|fpsValue|fpsElem)\s*=', content)
                if m_var and m_var.start() > init_idx:
                    issues.append({
                        "file": rel_path,
                        "severity": "CRITICAL",
                        "category": "JS_TEMPORAL_DEAD_ZONE",
                        "message": f"Variable '{m_var.group(1)}' declared after init() call. This causes fatal 'ReferenceError: Cannot access before initialization' in render loop."
                    })

        # 5. Python Syntax quick check
        if rel_path.endswith(".py"):
            try:
                ast.parse(content, filename=abs_path)
            except SyntaxError as e:
                issues.append({
                    "file": rel_path,
                    "severity": "CRITICAL",
                    "category": "PYTHON_SYNTAX",
                    "message": f"SyntaxError at line {e.lineno}: {e.msg}"
                })

    return issues

def review_code(
    path: Optional[str] = None,
    check_anti_patterns: bool = True,
    cwd: Optional[str] = None
) -> Dict[str, Any]:
    """Execute complete diff extraction and static review."""
    repo_dir = os.path.abspath(cwd) if cwd else os.getcwd()
    if path:
        path = resolve_project_path(path)

    diff_data = extract_diff(repo_dir, path)
    issues = scan_anti_patterns(repo_dir, diff_data["changed_files"]) if check_anti_patterns else []

    has_critical = any(i["severity"] == "CRITICAL" for i in issues)
    passed = len(issues) == 0 or not has_critical

    return make_result(
        True,
        data={
            "passed": passed,
            "issues_count": len(issues),
            "critical_count": sum(1 for i in issues if i["severity"] == "CRITICAL"),
            "issues": issues,
            "changed_files_count": len(diff_data["changed_files"]),
            "changed_files": diff_data["changed_files"],
            "diff_preview": diff_data["diff"][:4000] if diff_data["diff"] else "(No git diff found - working tree clean or untracked)",
            "diff_full_length": diff_data["diff_length"]
        }
    )

def execute(args: Dict[str, Any]) -> Dict[str, Any]:
    path = args.get("path")
    check_anti_patterns = args.get("check_anti_patterns", True)
    cwd = args.get("cwd")
    return review_code(path=path, check_anti_patterns=check_anti_patterns, cwd=cwd)

if __name__ == "__main__":
    cli_runner("code_reviewer", TOOL_SPEC, execute)
