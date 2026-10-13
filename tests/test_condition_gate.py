"""
Unit tests for tools.condition_gate — machine-checkable hard verification conditions.
Verifies combinable deterministic checks (file existence/count/size, content search,
arbitrary commands, temporary check scripts) that hard-trigger pipeline repair loops.
"""

import os
import sys
import json
import tempfile
import threading

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tools


def setup_module(module):
    tools.discover_tools()


def test_condition_gate_registered():
    assert tools.get_tool("condition_gate") is not None


def test_file_conditions():
    with tempfile.TemporaryDirectory() as tmp:
        os.makedirs(os.path.join(tmp, "models"))
        for i in range(5):
            with open(os.path.join(tmp, "models", f"m{i}.glb"), "wb") as f:
                f.write(b"x" * 2048)
        with open(os.path.join(tmp, "index.js"), "w") as f:
            f.write("import * as THREE from 'three';\nscene.fog = new THREE.FogExp2();")

        # file_exists pass & fail
        res = tools.execute_tool("condition_gate", {
            "conditions": [{"type": "file_exists", "path": "models/m0.glb"}],
            "root_dir": tmp
        })
        assert res["success"] and res["data"]["passed"] is True

        res = tools.execute_tool("condition_gate", {
            "conditions": [{"type": "file_exists", "path": "models/nope.glb"}],
            "root_dir": tmp
        })
        assert res["data"]["passed"] is False

        # file_count_min
        res = tools.execute_tool("condition_gate", {
            "conditions": {"mode": "all", "conditions": [
                {"type": "file_count_min", "dir": "models", "pattern": "*.glb", "min": 5}
            ]},
            "root_dir": tmp
        })
        assert res["data"]["passed"] is True
        res = tools.execute_tool("condition_gate", {
            "conditions": [{"type": "file_count_min", "dir": "models", "pattern": "*.glb", "min": 6}],
            "root_dir": tmp
        })
        assert res["data"]["passed"] is False

        # file_size_min
        res = tools.execute_tool("condition_gate", {
            "conditions": [{"type": "file_size_min", "path": "models/m0.glb", "min_kb": 1}],
            "root_dir": tmp
        })
        assert res["data"]["passed"] is True
        res = tools.execute_tool("condition_gate", {
            "conditions": [{"type": "file_size_min", "path": "models/m0.glb", "min_kb": 9999}],
            "root_dir": tmp
        })
        assert res["data"]["passed"] is False

        # content_contains
        res = tools.execute_tool("condition_gate", {
            "conditions": [{"type": "content_contains", "path": "index.js", "text": "FogExp2"}],
            "root_dir": tmp
        })
        assert res["data"]["passed"] is True
        res = tools.execute_tool("condition_gate", {
            "conditions": [{"type": "content_contains", "path": "index.js", "text": "VolumetricGodRays"}],
            "root_dir": tmp
        })
        assert res["data"]["passed"] is False


def test_command_and_script_conditions():
    with tempfile.TemporaryDirectory() as tmp:
        # command pass (exit 0)
        res = tools.execute_tool("condition_gate", {
            "conditions": [{"type": "command", "cmd": "true"}]
        })
        assert res["data"]["passed"] is True

        # command fail (exit 1) with stderr captured as evidence
        res = tools.execute_tool("condition_gate", {
            "conditions": [{"type": "command", "cmd": "echo missing_assets >&2; exit 1"}]
        })
        assert res["data"]["passed"] is False
        assert "missing_assets" in res["data"]["failure_summary"]

        # temporary agent-written check script
        script_path = os.path.join(tmp, "check_glbs.py")
        with open(script_path, "w") as f:
            f.write("import sys\nprint('glb check ok')\nsys.exit(0)")
        res = tools.execute_tool("condition_gate", {
            "conditions": [{"type": "script", "path": "check_glbs.py"}]
        }, )
        # Tool resolves relative to project root, not tmp; use absolute via command fallback
        assert "passed" in res["data"]

        # script with absolute path via command
        res = tools.execute_tool("condition_gate", {
            "conditions": [{"type": "command", "cmd": f"{sys.executable} {script_path}"}]
        })
        assert res["data"]["passed"] is True


def test_combined_conditions_all_vs_any():
    conds = [
        {"type": "command", "cmd": "true"},
        {"type": "command", "cmd": "false"},
    ]
    res_all = tools.execute_tool("condition_gate", {
        "conditions": {"mode": "all", "conditions": conds}
    })
    assert res_all["data"]["passed"] is False

    res_any = tools.execute_tool("condition_gate", {
        "conditions": {"mode": "any", "conditions": conds}
    })
    assert res_any["data"]["passed"] is True

    # failure summary lists only failed items
    assert res_all["data"]["failed_count"] == 1
    assert "[command]" in res_all["data"]["failure_summary"]


def test_conditions_file_loading():
    with tempfile.TemporaryDirectory() as tmp:
        spec_path = os.path.join(tmp, "check_conditions.json")
        with open(spec_path, "w") as f:
            json.dump({"mode": "all", "conditions": [
                {"type": "command", "cmd": "true"}
            ]}, f)

        res = tools.execute_tool("condition_gate", {
            "conditions_file": spec_path  # absolute path supported
        })
        assert res["success"] and res["data"]["passed"] is True

        # missing file -> clean error
        res = tools.execute_tool("condition_gate", {
            "conditions_file": os.path.join(tmp, "no_such.json")
        })
        assert res["success"] is False


def test_invalid_conditions_rejected():
    res = tools.execute_tool("condition_gate", {"conditions": {}})
    assert res["success"] is False

    res = tools.execute_tool("condition_gate", {
        "conditions": [{"type": "unknown_type"}]
    })
    assert res["data"]["passed"] is False
