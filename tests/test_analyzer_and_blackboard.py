"""
Unit tests for tools.analyzer, core.blackboard, tools.blackboard,
and role tool isolation (Analyst vs other agents).
Follows TDD RED -> GREEN methodology.
"""

import os
import sys
import json
import pytest
import tempfile
import threading

# Ensure project root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.role import Role
import tools


def test_role_context_isolation():
    """
    Ensure analyzer tool is ONLY assigned to analyst role to reduce context
    overhead for other agents (coder, tester, reviewer, designer, etc.).
    """
    analyst_role = Role.from_file("agents/analyst.md")
    coder_role = Role.from_file("agents/coder.md")
    tester_role = Role.from_file("agents/tester.md")
    reviewer_role = Role.from_file("agents/reviewer.md")
    designer_role = Role.from_file("agents/designer.md")

    # Analyst must have analyzer and blackboard tools
    assert "analyzer" in analyst_role.tools
    assert "blackboard" in analyst_role.tools
    assert "web_search" in analyst_role.tools

    # Other agents MUST NOT have analyzer tool to prevent token context bloat
    assert "analyzer" not in coder_role.tools
    assert "analyzer" not in tester_role.tools
    assert "analyzer" not in reviewer_role.tools
    assert "analyzer" not in designer_role.tools


def test_blackboard_core_and_thread_safety():
    """
    Verify SharedBlackboard thread-safe operations, posting, querying, and markdown export.
    """
    from core.blackboard import SharedBlackboard

    bb = SharedBlackboard()
    bb.clear()

    # Concurrent posting across multiple threads
    def worker_post(worker_id):
        bb.post(
            topic="bug_findings",
            key=f"bug_from_worker_{worker_id}",
            value=f"Detected critical null dereference in worker {worker_id}",
            author=f"analyst-{worker_id}",
            tags=["critical", "memory"]
        )

    threads = [threading.Thread(target=worker_post, args=(i,)) for i in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    items = bb.get(topic="bug_findings")
    assert len(items) == 10
    topics = bb.list_topics()
    assert "bug_findings" in topics

    md = bb.export_markdown()
    assert "## 主题: bug_findings" in md
    assert "analyst-" in md

    # Persistence check
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tf:
        tmp_path = tf.name
    try:
        bb.save_to_file(tmp_path)
        assert os.path.exists(tmp_path)
        bb2 = SharedBlackboard()
        bb2.load_from_file(tmp_path)
        assert len(bb2.get(topic="bug_findings")) == 10
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def test_blackboard_tool_registration_and_execution():
    """
    Verify tools.blackboard is registered and operates via execute_tool.
    """
    tools.discover_tools()
    tool = tools.get_tool("blackboard")
    assert tool is not None

    # Post an entry
    res = tools.execute_tool("blackboard", {
        "action": "post",
        "topic": "architecture",
        "key": "contract_terrain",
        "value": "Terrain class must export addTo and update methods",
        "author": "analyst-01"
    })
    assert res["success"] is True

    # Retrieve entry
    res_get = tools.execute_tool("blackboard", {
        "action": "get",
        "topic": "architecture",
        "key": "contract_terrain"
    })
    assert res_get["success"] is True
    assert "addTo and update" in str(res_get["data"])


def test_analyzer_tool_search_and_extract():
    """
    Verify tools.analyzer can perform project text search, symbol extraction,
    and pitfall detection.
    """
    tools.discover_tools()
    analyzer_tool = tools.get_tool("analyzer")
    assert analyzer_tool is not None

    # 1. Text search across project
    res_search = tools.execute_tool("analyzer", {
        "action": "search",
        "query": "AgentHarness",
        "file_pattern": "*.py"
    })
    assert res_search["success"] is True
    assert res_search["data"]["total_matches"] > 0

    # 2. Extract symbols from core/harness.py
    res_symbols = tools.execute_tool("analyzer", {
        "action": "extract_symbols",
        "file_path": "core/harness.py"
    })
    assert res_symbols["success"] is True
    symbols = res_symbols["data"].get("classes", [])
    assert "AgentHarness" in symbols

    # 3. Pitfall detection
    res_pitfalls = tools.execute_tool("analyzer", {
        "action": "detect_pitfalls",
        "file_path": "agents/analyst.md"
    })
    assert res_pitfalls["success"] is True

    # 4. Knowledge query
    res_know = tools.execute_tool("analyzer", {
        "action": "query_knowledge",
        "topic": "threejs_anti_aliasing"
    })
    assert res_know["success"] is True
    assert "samples: 4" in str(res_know["data"])


def test_analyzer_asset_audit():
    """asset_audit inventories glb assets, code refs, placements and missing refs."""
    import struct as _struct

    with tempfile.TemporaryDirectory() as tmp:
        os.makedirs(os.path.join(tmp, "models"))
        meta = json.dumps({"asset": {"version": "2.0"}, "nodes": [{"name": "Flamingo"}], "meshes": []}).encode()
        glb = b"glTF" + _struct.pack("<II", 2, 12 + 8 + len(meta)) + _struct.pack("<I", len(meta)) + b"JSON" + meta
        with open(os.path.join(tmp, "models", "flamingo.glb"), "wb") as f:
            f.write(glb)
        with open(os.path.join(tmp, "models", "unused.glb"), "wb") as f:
            f.write(glb)
        with open(os.path.join(tmp, "index.js"), "w") as f:
            f.write("loader.load('models/flamingo.glb', g => { g.scene.position.set(2, 1.5, 3); });\n"
                    "loader.load('models/ghost.glb', g => {});")

        res = tools.execute_tool("analyzer", {"action": "asset_audit", "root_dir": tmp})
        data = res["data"]
        assert data["asset_count"] == 2
        flamingo = next(a for a in data["assets"] if a["file"] == "models/flamingo.glb")
        assert flamingo["embedded_name"] == "Flamingo"
        assert "index.js" in flamingo["referenced_by"]
        assert flamingo["placements"] and flamingo["placements"][0]["y"] == 1.5
        assert any(m["ref"] == "models/ghost.glb" for m in data["missing_refs"])
        assert "models/unused.glb" in data["unreferenced_assets"]


def test_analyzer_asset_audit_empty_project():
    res = tools.execute_tool("analyzer", {"action": "asset_audit", "root_dir": tempfile.mkdtemp()})
    assert res["success"] is True
    assert res["data"]["asset_count"] == 0
