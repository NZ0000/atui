#!/usr/bin/env python3
"""
Tool: git_tool
Provides Git version control operations: status, diff, commit, log, and rollback.
Supports both Python function calling and CLI argument invocation.
"""

import os
import sys
import subprocess
from typing import Dict, Any, Optional

try:
    from tools.base import make_result, cli_runner
except ImportError:
    from base import make_result, cli_runner

TOOL_SPEC = {
    "name": "git_tool",
    "description": "Git operations: status, diff, commit, log, and rollback (revert changes or reset).",
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["status", "diff", "commit", "log", "rollback", "add"],
                "description": "The git action to perform."
            },
            "message": {
                "type": "string",
                "description": "Commit message when action is 'commit'."
            },
            "path": {
                "type": "string",
                "description": "Optional specific path or file for diff, add, or rollback."
            },
            "commit_id": {
                "type": "string",
                "description": "Target commit hash or ref (e.g. 'HEAD~1') for rollback/reset."
            },
            "cwd": {
                "type": "string",
                "description": "Working directory of the repository."
            }
        },
        "required": ["action"]
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

def git_operations(
    action: str,
    message: Optional[str] = None,
    path: Optional[str] = None,
    commit_id: Optional[str] = None,
    cwd: Optional[str] = None
) -> Dict[str, Any]:
    repo_dir = os.path.abspath(cwd) if cwd else os.getcwd()

    # Ensure git repo exists
    check_repo = _run_git(["rev-parse", "--is-inside-work-tree"], repo_dir)
    if check_repo.returncode != 0:
        return make_result(False, error=f"Not a git repository: {repo_dir}")

    if action == "status":
        p = _run_git(["status", "--short"], repo_dir)
        full_p = _run_git(["status"], repo_dir)
        return make_result(True, data={
            "action": "status",
            "short_status": p.stdout.strip(),
            "full_status": full_p.stdout.strip()
        })

    elif action == "diff":
        cmd = ["diff"]
        if path:
            cmd.append(path)
        p = _run_git(cmd, repo_dir)
        # Also check staged diff
        cmd_staged = ["diff", "--cached"]
        if path:
            cmd_staged.append(path)
        p_staged = _run_git(cmd_staged, repo_dir)
        return make_result(True, data={
            "action": "diff",
            "unstaged_diff": p.stdout,
            "staged_diff": p_staged.stdout
        })

    elif action == "add":
        target = path if path else "."
        p = _run_git(["add", target], repo_dir)
        if p.returncode != 0:
            return make_result(False, error=f"Git add failed: {p.stderr}")
        return make_result(True, data={"action": "add", "target": target})

    elif action == "commit":
        if not message:
            return make_result(False, error="Commit message is required for action 'commit'.")
        target = path if path else "."
        _run_git(["add", target], repo_dir)
        p = _run_git(["commit", "-m", message], repo_dir)
        if p.returncode != 0:
            if "nothing to commit" in p.stdout or "nothing to commit" in p.stderr:
                return make_result(True, data={"action": "commit", "message": "Nothing to commit, working tree clean."})
            return make_result(False, error=f"Git commit failed: {p.stderr or p.stdout}")
        
        log_p = _run_git(["rev-parse", "HEAD"], repo_dir)
        commit_hash = log_p.stdout.strip()
        return make_result(True, data={
            "action": "commit",
            "commit_id": commit_hash,
            "output": p.stdout.strip()
        })

    elif action == "rollback":
        if commit_id:
            p = _run_git(["reset", "--hard", commit_id], repo_dir)
            if p.returncode != 0:
                return make_result(False, error=f"Git reset to {commit_id} failed: {p.stderr}")
            return make_result(True, data={"action": "rollback", "target": commit_id, "output": p.stdout.strip()})
        elif path:
            # Rollback specific path safely
            if os.path.exists(os.path.join(repo_dir, path)):
                # If untracked, remove file; if tracked, restore
                check_tracked = _run_git(["ls-files", path], repo_dir)
                if check_tracked.stdout.strip():
                    p_restore = _run_git(["restore", path], repo_dir)
                    return make_result(True, data={"action": "rollback", "path": path, "restore": p_restore.stdout.strip()})
                else:
                    target_file = os.path.join(repo_dir, path)
                    if os.path.isfile(target_file):
                        os.remove(target_file)
                    return make_result(True, data={"action": "rollback", "path": path, "removed_untracked": True})
            return make_result(True, data={"action": "rollback", "path": path, "message": "Path did not exist."})
        else:
            # Revert tracked modifications — NEVER repo-wide. Scope to the active
            # project dir only, so harness files and other projects can't be wiped
            # by an agent or gate invoking rollback without explicit arguments.
            has_head = (_run_git(["rev-parse", "--verify", "HEAD"], repo_dir).returncode == 0)
            if has_head:
                try:
                    from tools.condition_gate import _get_project_root
                    project_root = _get_project_root()
                except Exception:
                    project_root = None
                scope = "."
                if project_root:
                    try:
                        rel = os.path.relpath(project_root, repo_dir)
                        if rel and rel != "." and not rel.startswith("..") and os.path.exists(os.path.join(repo_dir, rel)):
                            scope = rel
                    except Exception:
                        scope = "."
                p_restore = _run_git(["restore", scope], repo_dir)
                return make_result(True, data={
                    "action": "rollback",
                    "message": f"Reverted modified tracked files (scoped to '{scope}'; harness files untouched).",
                    "restore": p_restore.stdout.strip()
                })
            else:
                return make_result(True, data={
                    "action": "rollback",
                    "message": "No HEAD commit found; skipped full destructive clean."
                })

    elif action == "log":
        has_head = (_run_git(["rev-parse", "--verify", "HEAD"], repo_dir).returncode == 0)
        if not has_head:
            return make_result(True, data={"action": "log", "commits": "No commits yet."})
        p = _run_git(["log", "-n", "10", "--oneline"], repo_dir)
        return make_result(True, data={
            "action": "log",
            "commits": p.stdout.strip()
        })

    else:
        return make_result(False, error=f"Unsupported git action: {action}")

def execute(params: Dict[str, Any]) -> Dict[str, Any]:
    action = params.get("action")
    if not action:
        return make_result(False, error="Parameter 'action' is required.")
    return git_operations(
        action=action,
        message=params.get("message"),
        path=params.get("path"),
        commit_id=params.get("commit_id"),
        cwd=params.get("cwd")
    )

if __name__ == "__main__":
    cli_runner("git_tool", TOOL_SPEC, execute)
