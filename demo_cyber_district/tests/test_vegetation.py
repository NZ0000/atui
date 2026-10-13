import os
import pytest

def test_vegetation_module_exists():
    path = "modules/vegetation.js"
    assert os.path.exists(path), f"TDD RED: Expected module {path} to exist."

def test_vegetation_syntax_and_export():
    path = "modules/vegetation.js"
    if not os.path.exists(path):
        pytest.fail(f"TDD RED: {path} not yet implemented.")
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "InstancedMesh" in content, "Vegetation module MUST use THREE.InstancedMesh for batch rendering."
    assert "addTo" in content, "Vegetation module must implement addTo(scene)."
    assert "update" in content, "Vegetation module must implement update(delta)."
