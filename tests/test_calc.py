import pytest
import subprocess
import json
import sys
import os

from tools.calc import execute, TOOL_SPEC

def test_tool_spec():
    assert TOOL_SPEC["name"] == "calc"
    assert "operation" in TOOL_SPEC["parameters"]["required"]

def test_add():
    res = execute({"operation": "add", "a": 2.5, "b": 3.5})
    assert res["success"] is True
    assert res["data"] == 6.0

def test_subtract():
    res = execute({"operation": "subtract", "a": 10.0, "b": 4.0})
    assert res["success"] is True
    assert res["data"] == 6.0

def test_multiply():
    res = execute({"operation": "multiply", "a": 3.0, "b": 4.0})
    assert res["success"] is True
    assert res["data"] == 12.0

def test_divide():
    res = execute({"operation": "divide", "a": 10.0, "b": 2.0})
    assert res["success"] is True
    assert res["data"] == 5.0

    # Test divide by zero
    res_zero = execute({"operation": "divide", "a": 10.0, "b": 0.0})
    assert res_zero["success"] is False
    assert "zero" in res_zero["error"].lower()

def test_power():
    res = execute({"operation": "power", "a": 2.0, "b": 3.0})
    assert res["success"] is True
    assert res["data"] == 8.0

def test_stats():
    res = execute({"operation": "stats", "values": [1, 2, 3, 4, 5]})
    assert res["success"] is True
    data = res["data"]
    assert data["count"] == 5
    assert data["sum"] == 15.0
    assert data["mean"] == 3.0
    assert data["median"] == 3.0
    assert data["min"] == 1.0
    assert data["max"] == 5.0
    assert data["stdev"] > 0

    # Test string or comma-separated values input
    res_str = execute({"operation": "stats", "values": "1,2,3,4,5"})
    assert res_str["success"] is True
    assert res_str["data"]["mean"] == 3.0

def test_invalid_operation():
    res = execute({"operation": "unknown"})
    assert res["success"] is False

def test_cli_execution():
    cmd = [sys.executable, "tools/calc.py", "--operation", "add", "--a", "10", "--b", "5"]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    assert proc.returncode == 0
    output = json.loads(proc.stdout)
    assert output["success"] is True
    assert output["data"] == 15.0

    # Test JSON CLI
    json_arg = json.dumps({"operation": "multiply", "a": 6, "b": 7})
    cmd_json = [sys.executable, "tools/calc.py", "--json", json_arg]
    proc_json = subprocess.run(cmd_json, capture_output=True, text=True)
    assert proc_json.returncode == 0
    output_json = json.loads(proc_json.stdout)
    assert output_json["success"] is True
    assert output_json["data"] == 42.0
