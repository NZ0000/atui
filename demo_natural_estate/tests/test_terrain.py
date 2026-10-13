import os
import pytest

def test_terrain_module_exists():
    path = "modules/terrain.js"
    assert os.path.exists(path), f"Module {path} does not exist"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "class Terrain" in content
    assert "constructor" in content
    assert "addTo" in content
    assert "update" in content
    assert "export" in content
