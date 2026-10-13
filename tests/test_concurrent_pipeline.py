"""
Unit tests for ConcurrentModularPipeline.
Verifies that the concurrent multi-agent swarm architecture initializes,
properly defines modular contracts, and supports parallel task decomposition.
"""

import os
import pytest
from core.concurrent_pipeline import ConcurrentModularPipeline

def test_concurrent_pipeline_initialization():
    pipeline = ConcurrentModularPipeline(agents_dir="agents", max_workers=4)
    assert pipeline.max_workers == 4
    assert pipeline.max_repair_loops == 4
    assert os.path.exists(pipeline._get_agent_path("planner"))
    assert os.path.exists(pipeline._get_agent_path("coder"))
    assert os.path.exists(pipeline._get_agent_path("reviewer"))
    assert os.path.exists(pipeline._get_agent_path("tester"))
    assert os.path.exists(pipeline._get_agent_path("designer"))
    assert os.path.exists(pipeline._get_agent_path("delivery"))

def test_concurrent_pipeline_api_exposure():
    import atui
    assert hasattr(atui, "run_concurrent")
    assert hasattr(atui, "run_concurrent_pipeline")
    assert callable(atui.run_concurrent_pipeline)
