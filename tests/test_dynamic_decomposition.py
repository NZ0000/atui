"""
Unit tests for dynamic task decomposition and concurrent analyst scheduling.
Verifies that:
1. Tasks are decomposed dynamically without hardcoding scene domains.
2. Concurrent analysts can analyze separate file sets and report to the shared blackboard.
3. System decides whether to split based on task complexity.
"""

import os
import sys
import json
import pytest
import tempfile
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.concurrent_pipeline import ConcurrentModularPipeline
from core.blackboard import get_blackboard


def test_dynamic_module_specs_generation():
    """
    Ensure ConcurrentModularPipeline loads module specs dynamically from JSON or generates
    modular specs from arbitrary user tasks without hardcoding 'is_natural' or 3D scene names.
    """
    pipeline = ConcurrentModularPipeline()

    # Case 1: Custom backend microservices task
    backend_task = "构建基于FastAPI的用户鉴权、订单处理与支付网关分布式微服务系统"
    specs = pipeline.resolve_task_modules(backend_task, modules_spec_json=None)
    assert len(specs) >= 2
    # Ensure it didn't hardcode terrain.js / lake / trees for backend task!
    module_names = [m["name"].lower() for m in specs]
    assert "terrain" not in module_names
    assert "vegetation" not in module_names

    # Case 2: Reading from explicit planner output deliverables/modules_spec.json
    custom_specs = [
        {
            "id": "MOD-AUTH",
            "name": "auth_service",
            "file": "services/auth.py",
            "test_file": "tests/test_auth.py",
            "contract": "JWT token issue & verify",
            "requirements": "Argon2 password hashing"
        },
        {
            "id": "MOD-ORDER",
            "name": "order_service",
            "file": "services/order.py",
            "test_file": "tests/test_order.py",
            "contract": "Order state machine",
            "requirements": "Idempotent payment webhook"
        }
    ]
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as tf:
        json.dump(custom_specs, tf)
        tmp_spec_file = tf.name

    try:
        loaded_specs = pipeline.resolve_task_modules("任意任务", modules_spec_json=tmp_spec_file)
        assert len(loaded_specs) == 2
        assert loaded_specs[0]["name"] == "auth_service"
        assert loaded_specs[1]["name"] == "order_service"
    finally:
        if os.path.exists(tmp_spec_file):
            os.remove(tmp_spec_file)


def test_concurrent_analyst_dispatch_and_blackboard():
    """
    Verify run_concurrent_analysis can partition files, dispatch multiple analysts concurrently,
    and consolidate blackboard findings.
    """
    pipeline = ConcurrentModularPipeline(max_workers=2)
    bb = get_blackboard()
    bb.clear()

    target_files = ["modules/comp_a.js", "modules/comp_b.js", "modules/comp_c.js"]

    # Mock analyst execution so we don't invoke real LLM API in unit tests
    def mock_run_analyst_worker(file_batch, task, active_model, worker_id, **kwargs):
        for f in file_batch:
            bb.post(
                topic="analysis_findings",
                key=f,
                value=f"Analyzed {f}: discovered 1 interface contract and 0 bugs",
                author=f"analyst-{worker_id}"
            )
        return {"success": True, "files": file_batch, "worker_id": worker_id}

    with patch.object(pipeline, "_run_single_analyst_worker", side_effect=mock_run_analyst_worker):
        res = pipeline.run_concurrent_analysis(
            task="分析优化多个模块并消除潜在问题",
            target_files=target_files,
            max_workers=2
        )
        assert res["success"] is True
        assert len(res["worker_results"]) >= 2
        # Verify blackboard collected all findings
        findings = bb.get(topic="analysis_findings")
        assert len(findings) == 3
        keys = [item["key"] for item in findings]
        for f in target_files:
            assert f in keys


def test_fix_worker_requires_real_file_modification():
    """
    Iteration fix coders must NOT be marked success if they only write a report
    without actually modifying the target source file (anti-lazy output gate).
    """
    import tempfile
    pipeline = ConcurrentModularPipeline(max_workers=1)

    with tempfile.TemporaryDirectory() as tmp:
        target = os.path.join(tmp, "mod.js")
        with open(target, "w", encoding="utf-8") as f:
            f.write("export const a = 1;")

        calls = {"n": 0}

        class FakeHarness:
            def __init__(self, role, model=None):
                pass

            def run(self, task, output_file=None):
                calls["n"] += 1
                # Simulates a lazy coder: writes report but never touches mod.js
                with open(os.path.join(tmp, "report.md"), "w", encoding="utf-8") as f:
                    f.write("# fix report")
                return {"success": True, "last_message": "ok"}

        with patch("core.concurrent_pipeline.Role"), \
             patch("core.concurrent_pipeline.AgentHarness", FakeHarness):
            res = pipeline._run_single_fix_pipeline(
                target_file="mod.js",
                task="fix something",
                analysis_content="",
                project_path=tmp,
                active_model="test-model"
            )

        assert res["success"] is False
        assert calls["n"] >= 1
        assert "未实际修改" in res["error"]


def test_file_signature_helper():
    """_file_signature returns None for missing files and changes when content changes."""
    import tempfile
    pipeline = ConcurrentModularPipeline()
    with tempfile.TemporaryDirectory() as tmp:
        p = os.path.join(tmp, "x.js")
        assert pipeline._file_signature(p) is None
        with open(p, "w", encoding="utf-8") as f:
            f.write("const a = 1;")
        sig1 = pipeline._file_signature(p)
        assert sig1 is not None
        with open(p, "w", encoding="utf-8") as f:
            f.write("const a = 2;")
        assert pipeline._file_signature(p) != sig1
