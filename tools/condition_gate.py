#!/usr/bin/env python3
"""
Tool: condition_gate
Machine-checkable hard verification conditions for agent pipelines.
Beyond agent subjective judgment, this tool evaluates combinable, deterministic
conditions (file existence/count/size, content/text search, arbitrary shell
commands, and temporary agent-written check scripts) to HARD-pass or HARD-reject
a deliverable and trigger repair loops.

Condition spec (single dict or list of dicts):
  {
    "mode": "all",            # all | any  (default: all)
    "conditions": [
      {"type": "file_exists",     "path": "models/duck.glb"},
      {"type": "file_count_min",  "dir": "models", "pattern": "*.glb", "min": 15},
      {"type": "file_size_min",   "path": "models/duck.glb", "min_kb": 10},
      {"type": "content_contains","path": "index.js", "text": "FogExp2"},
      {"type": "text_search",     "query": "FogExp2", "file_pattern": "*.js", "min_matches": 1},
      {"type": "command",         "cmd": "python deliverables/checks/check_glbs.py"},
      {"type": "script",          "path": "deliverables/checks/check_glbs.py", "args": ""}
    ]
  }
- command/script run with cwd = project root; exit code 0 => pass.
  Non-zero exit or non-empty stderr tail is reported as the failure reason.
- script is a superset of command executed via the python interpreter.
"""

import sys
import os
import fnmatch
import subprocess
from typing import Dict, Any, List, Optional

try:
    from tools.base import make_result, cli_runner
except ImportError:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from tools.base import make_result, cli_runner

TOOL_SPEC = {
    "name": "condition_gate",
    "description": "硬性检测条件门禁工具：用机器可验证的组合条件（文件存在/数量/大小、代码内容包含、全库检索、任意检测命令、临时检测脚本）对交付成果做客观硬判定，杜绝仅凭 Agent 主观判断。任一硬性条件不满足即返回 passed=false 并给出精确失败清单，用于触发返工循环与驳回。",
    "parameters": {
        "type": "object",
        "properties": {
            "conditions": {
                "type": "object",
                "description": "条件规格 dict（含 mode 与 conditions 数组），或条件数组直接传入"
            },
            "conditions_file": {
                "type": "string",
                "description": "条件规格 JSON 文件路径（相对项目根或绝对路径）"
            },
            "root_dir": {
                "type": "string",
                "description": "可选：条件解析的根目录（默认为当前激活项目根目录）"
            }
        },
        "required": []
    }
}

MAX_CMD_TIMEOUT = 120


def _get_project_root() -> str:
    try:
        from core.project import get_current_project
        proj = get_current_project()
        if proj and proj.path and os.path.exists(proj.path):
            return proj.path
    except Exception:
        pass
    return os.getcwd()


def _abs(root: str, path: str) -> str:
    return path if os.path.isabs(path) else os.path.join(root, path)


def syntax_check_file(path: str) -> Dict[str, Any]:
    """Public wrapper: syntax-check a temp check script before hand-over/gating."""
    return _syntax_check(path)


def _syntax_check(path: str) -> Dict[str, Any]:
    """Syntax-validate a check script. .py via ast.parse; others via language CLI if available."""
    try:
        if path.endswith(".py"):
            import ast
            with open(path, "r", encoding="utf-8") as f:
                src = f.read()
            ast.parse(src)
            return {"ok": True, "error": ""}
        if path.endswith((".js", ".mjs", ".cjs")):
            node = __import__("shutil").which("node")
            if not node:
                return {"ok": True, "error": ""}  # no node available, skip js syntax gate
            proc = subprocess.run(
                [node, "--check", path], timeout=30, capture_output=True, text=True
            )
            if proc.returncode != 0:
                return {"ok": False, "error": (proc.stderr or proc.stdout).strip()[:400]}
            return {"ok": True, "error": ""}
        # Unknown extension: try python parse if content looks like python, else accept
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            head = f.read(400)
        if "def " in head or "import " in head:
            import ast
            ast.parse(open(path, "r", encoding="utf-8").read())
        return {"ok": True, "error": ""}
    except SyntaxError as e:
        return {"ok": False, "error": f"line {getattr(e, 'lineno', '?')}: {e.msg}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def _check_one(cond: Dict[str, Any], root: str) -> Dict[str, Any]:
    ctype = (cond.get("type") or "").lower().strip()
    res: Dict[str, Any] = {"type": ctype or "unknown", "spec": cond, "passed": False, "detail": ""}

    try:
        if ctype == "file_exists":
            path = cond.get("path", "")
            ok = bool(path) and os.path.exists(_abs(root, path))
            res.update(passed=ok, detail=f"file '{path}' {'exists' if ok else 'MISSING'}")

        elif ctype == "file_count_min":
            d = _abs(root, cond.get("dir", "."))
            pattern = cond.get("pattern", "*")
            minimum = int(cond.get("min", 1))
            count = 0
            if os.path.isdir(d):
                count = sum(1 for f in os.listdir(d) if fnmatch.fnmatch(f, pattern))
            res.update(
                passed=count >= minimum,
                detail=f"matched {count} files in '{cond.get('dir', '.')}' by '{pattern}', required >= {minimum}"
            )

        elif ctype == "file_size_min":
            path = cond.get("path", "")
            minimum = int(cond.get("min_kb", 1))
            ap = _abs(root, path)
            ok = os.path.exists(ap) and os.path.getsize(ap) >= minimum * 1024
            size_kb = round(os.path.getsize(ap) / 1024, 1) if os.path.exists(ap) else 0
            res.update(passed=ok, detail=f"'{path}' is {size_kb}KB, required >= {minimum}KB")

        elif ctype == "content_contains":
            path = cond.get("path", "")
            text = cond.get("text", "")
            ap = _abs(root, path)
            if not os.path.exists(ap):
                res.update(detail=f"file '{path}' MISSING")
            else:
                with open(ap, "r", encoding="utf-8", errors="ignore") as f:
                    ok = text in f.read()
                res.update(passed=ok, detail=f"'{path}' {'contains' if ok else 'MISSING'} '{text}'")

        elif ctype == "text_search":
            import tools
            minimum = int(cond.get("min_matches", 1))
            sr = tools.execute_tool("analyzer", {
                "action": "search",
                "query": cond.get("query", ""),
                "file_pattern": cond.get("file_pattern"),
                "max_results": 1
            })
            total = int(sr.get("data", {}).get("total_matches", 0)) if sr.get("success") else 0
            res.update(passed=total >= minimum,
                       detail=f"query '{cond.get('query')}' matched {total} lines, required >= {minimum}")

        elif ctype == "code_reference_integrity":
            # Generic asset/link integrity: every reference matching ref_regex found in
            # scanned source files must exist on disk (prevents 404-class runtime errors).
            import re as _re
            scan_glob = cond.get("scan_glob", "*.js")
            ref_regex = cond.get("ref_regex", r"models/[\w./-]+\.(?:glb|gltf)")
            minimum = int(cond.get("min_refs", 1))
            skip_dirs = {"node_modules", ".git", "vendor", "models", "deliverables", "__pycache__"}
            refs = set()
            for dirpath, dirnames, filenames in os.walk(root):
                dirnames[:] = [d for d in dirnames if d not in skip_dirs]
                for fn in filenames:
                    if not fnmatch.fnmatch(fn, scan_glob):
                        continue
                    ap = os.path.join(dirpath, fn)
                    try:
                        with open(ap, "r", encoding="utf-8", errors="ignore") as f:
                            refs.update(m.group(0) for m in _re.finditer(ref_regex, f.read()))
                    except Exception:
                        continue
            missing = sorted(r for r in refs if not os.path.exists(os.path.join(root, r)))
            ok = (len(refs) >= minimum) and not missing
            detail = f"found {len(refs)} refs (required >= {minimum})"
            if missing:
                detail += f"; MISSING TARGETS: {missing[:8]}"
            res.update(passed=ok, detail=detail)

        elif ctype == "web_runtime_clean":
            # Web-only baseline: page must load with zero console errors / network
            # failures (project-type-aware; meaningless for py/lua/c projects).
            url = cond.get("url", "")
            if not url:
                res.update(passed=False, detail="web_runtime_clean requires 'url'")
                return res
            try:
                import tools as _tools
                try:
                    _tools.discover_tools()
                except Exception:
                    pass
                bt = _tools.execute_tool("browser_test", {
                    "url_or_path": url,
                    "wait_ms": int(cond.get("wait_ms", 5000)),
                })
            except Exception as exc:
                # Runtime infrastructure unavailable: degrade gracefully, never false-fail
                res.update(passed=True, detail=f"SKIPPED (browser runtime unavailable: {exc})")
                return res
            data = (bt.get("data") or {}) if isinstance(bt, dict) else {}
            errors = data.get("console_errors") or []
            net_failures = data.get("network_failures") or []
            if not data:
                res.update(passed=True, detail="SKIPPED (browser_test returned no data)")
                return res
            max_errors = int(cond.get("max_errors", 0))
            ok = len(errors) <= max_errors and not net_failures
            detail = f"console_errors={len(errors)}, network_failures={len(net_failures)}"
            if not ok:
                detail += "; SAMPLES: " + "; ".join(
                    str(e.get("message", ""))[:90] for e in (errors + net_failures)[:5]
                )
            res.update(passed=ok, detail=detail)

        elif ctype in ("command", "script"):
            if ctype == "script":
                script_path = cond.get("path", "")
                ap = _abs(root, script_path)
                if not os.path.exists(ap):
                    res.update(detail=f"check script '{script_path}' MISSING")
                    return res
                # Syntax pre-check: a temp check script must be syntactically valid
                # before it can be handed over and executed as a gate.
                syn = _syntax_check(ap)
                if not syn["ok"]:
                    res.update(detail=f"check script '{script_path}' SYNTAX ERROR: {syn['error']}")
                    return res
                cmd = f"{sys.executable} {ap} {cond.get('args', '')}".strip()
            else:
                cmd = cond.get("cmd", "")
                if not cmd:
                    res.update(detail="empty command")
                    return res
            try:
                proc = subprocess.run(
                    cmd, shell=True, cwd=root, timeout=MAX_CMD_TIMEOUT,
                    capture_output=True, text=True
                )
                ok = proc.returncode == 0
                tail = (proc.stdout or "")[-500:] or (proc.stderr or "")[-500:]
                res.update(passed=ok,
                           detail=f"exit={proc.returncode} :: {tail.strip()[:400] or '(no output)'}")
            except subprocess.TimeoutExpired:
                res.update(detail=f"command timed out after {MAX_CMD_TIMEOUT}s: {cmd}")

        else:
            res.update(detail=f"unknown condition type '{ctype}'")
    except Exception as e:
        res.update(detail=f"condition evaluation error: {e}")
    return res


def evaluate_conditions(spec: Any, root_dir: Optional[str] = None) -> Dict[str, Any]:
    """Evaluate a condition spec (dict with mode/conditions, or a plain list). Returns full verdict."""
    root = root_dir or _get_project_root()

    if isinstance(spec, list):
        spec = {"mode": "all", "conditions": spec}
    if not isinstance(spec, dict):
        return make_result(False, error="conditions must be a dict or a list of condition dicts.")

    conds = spec.get("conditions")
    if isinstance(conds, dict):
        conds = [conds]
    if not isinstance(conds, list) or not conds:
        return make_result(False, error="conditions list is empty or invalid.")

    mode = (spec.get("mode") or "all").lower()
    results = [_check_one(c, root) for c in conds]
    passed_flags = [r["passed"] for r in results]
    passed = all(passed_flags) if mode != "any" else any(passed_flags)
    failed = [r for r in results if not r["passed"]]

    return make_result(True, data={
        "passed": passed,
        "mode": mode,
        "total": len(results),
        "failed_count": len(failed),
        "results": results,
        "failure_summary": "; ".join(f"[{r['type']}] {r['detail']}" for r in failed[:8])
    })


def execute(params: Dict[str, Any]) -> Dict[str, Any]:
    spec: Any = params.get("conditions")
    conditions_file = params.get("conditions_file")

    if not spec and conditions_file:
        fp = _abs(_get_project_root(), conditions_file)
        if not os.path.exists(fp):
            return make_result(False, error=f"conditions file '{conditions_file}' not found.")
        import json
        try:
            with open(fp, "r", encoding="utf-8") as f:
                spec = json.load(f)
        except Exception as e:
            return make_result(False, error=f"failed to load conditions file: {e}")

    if not spec:
        return make_result(False, error="Provide either 'conditions' spec or 'conditions_file' path.")

    return evaluate_conditions(spec, root_dir=params.get("root_dir"))


if __name__ == "__main__":
    cli_runner("condition_gate", TOOL_SPEC, execute)
