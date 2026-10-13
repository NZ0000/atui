import os
import pytest

def test_buildings_module_exists():
    path = "modules/buildings.js"
    assert os.path.exists(path), f"TDD RED: Expected module {path} to exist."

def test_buildings_interface_contract():
    path = "modules/buildings.js"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "class Buildings" in content, "Buildings class must be defined."
    assert "constructor" in content, "Buildings must have a constructor."
    assert "createBuildingCluster" in content, "Buildings must support createBuildingCluster."
    assert "addTo" in content, "Buildings must implement addTo(scene)."
