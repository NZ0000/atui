"""
Unified Project Directory and Context Manager for atui.
Manages:
1. Setting, switching, recording, and opening project directories.
2. Persisting current project session state.
3. Auto-discovering and injecting project rules (rule/rule.md, AGENTS.md, CLAUDE.md, etc.).
4. Resolving working directory for tool executions.
"""

import os
import json
import subprocess
from typing import Dict, Any, Optional, List, Tuple

STATE_FILE = os.path.expanduser("~/.atui_project_state.json")

RULE_CANDIDATE_FILES = [
    os.path.join("rule", "rule.md"),
    "rule.md",
    "AGENTS.md",
    "CLAUDE.md",
    ".rules.md",
    ".rules"
]

class ProjectContext:
    def __init__(self, path: str):
        self.path = os.path.abspath(path)
        self.name = os.path.basename(self.path)
        self.is_git, self.git_branch = self._detect_git()
        self.rules_file, self.rules = self._load_rules()

    def _detect_git(self) -> Tuple[bool, Optional[str]]:
        try:
            p = subprocess.run(
                ["git", "rev-parse", "--is-inside-work-tree"],
                cwd=self.path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=5
            )
            if p.returncode == 0:
                bp = subprocess.run(
                    ["git", "branch", "--show-current"],
                    cwd=self.path,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=5
                )
                branch = bp.stdout.strip() or "HEAD (detached)"
                return True, branch
        except Exception:
            pass
        return False, None

    def _load_rules(self) -> Tuple[Optional[str], str]:
        for candidate in RULE_CANDIDATE_FILES:
            full_path = os.path.join(self.path, candidate)
            if os.path.isfile(full_path):
                try:
                    with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                        content = f.read().strip()
                    if content:
                        return candidate, content
                except Exception:
                    continue
        return None, ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": self.path,
            "name": self.name,
            "is_git": self.is_git,
            "git_branch": self.git_branch,
            "rules_file": self.rules_file,
            "has_rules": bool(self.rules),
            "rules_preview": self.rules[:200] if self.rules else ""
        }

    def format_prompt_injection(self) -> str:
        """Constructs project rule injection header for agent system prompts."""
        parts = [
            f"\n[ACTIVE PROJECT CONTEXT]",
            f"Active Project Path: {self.path}",
            f"Active Project Name: {self.name}",
        ]
        if self.is_git:
            parts.append(f"Git Repository: Active (Branch: {self.git_branch})")
        if self.rules:
            parts.append(f"\n[PROJECT RULES INJECTED FROM {self.rules_file}]")
            parts.append(self.rules)
            parts.append("[END PROJECT RULES]\nAll actions MUST strictly respect these project rules.")
        return "\n".join(parts)


def _load_persisted_path() -> str:
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                p = data.get("current_project")
                if p and os.path.isdir(p):
                    return p
        except Exception:
            pass
    return os.getcwd()

def _save_persisted_path(path: str):
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump({"current_project": os.path.abspath(path)}, f, indent=2)
    except Exception as e:
        print(f"[Warning] Failed to persist project state: {e}")

_CURRENT_PROJECT: Optional[ProjectContext] = None

def get_current_project() -> ProjectContext:
    global _CURRENT_PROJECT
    if _CURRENT_PROJECT is None:
        p = _load_persisted_path()
        _CURRENT_PROJECT = ProjectContext(p)
    return _CURRENT_PROJECT

def switch_project(path: str) -> ProjectContext:
    """Switches active project directory, loads its rules, and persists state."""
    global _CURRENT_PROJECT
    target = os.path.abspath(path)
    if not os.path.exists(target):
        os.makedirs(target, exist_ok=True)
    if not os.path.isdir(target):
        raise NotADirectoryError(f"Target path is not a directory: {target}")

    _save_persisted_path(target)
    _CURRENT_PROJECT = ProjectContext(target)
    return _CURRENT_PROJECT

def manage_project(action: str = "get", path: Optional[str] = None) -> Dict[str, Any]:
    """
    Unified project management entrypoint:
    - 'get' / 'show': returns current project info
    - 'set' / 'switch' / 'open': changes current project to path
    - 'reload': re-reads project rules and git branch
    """
    global _CURRENT_PROJECT
    act = action.lower().strip()
    if act in ("set", "switch", "open") and path:
        ctx = switch_project(path)
        return {"success": True, "action": act, "project": ctx.to_dict()}
    elif act in ("get", "show", "current"):
        ctx = get_current_project()
        return {"success": True, "action": "get", "project": ctx.to_dict()}
    elif act == "reload":
        curr = get_current_project()
        _CURRENT_PROJECT = ProjectContext(curr.path)
        return {"success": True, "action": "reload", "project": _CURRENT_PROJECT.to_dict()}
    else:
        ctx = get_current_project()
        return {"success": True, "action": "get", "project": ctx.to_dict()}

if __name__ == "__main__":
    import sys
    args = sys.argv[1:]
    if len(args) >= 2 and args[0] in ("set", "switch", "open"):
        res = manage_project(args[0], args[1])
    else:
        res = manage_project("get")
    print(json.dumps(res, ensure_ascii=False, indent=2))
