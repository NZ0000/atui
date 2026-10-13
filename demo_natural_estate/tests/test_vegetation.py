import pytest
import os

def test_vegetation_module_exists():
    assert os.path.exists("modules/vegetation.js"), "modules/vegetation.js must exist"

def test_vegetation_syntax():
    with open("modules/vegetation.js", "r") as f:
        content = f.read()
    assert "class Vegetation" in content
    assert "addTo" in content
    assert "update" in content
    assert "InstancedMesh" in content
