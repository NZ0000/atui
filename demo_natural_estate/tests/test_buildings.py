import os
import pytest

def test_buildings_file_exists():
    assert os.path.exists("modules/buildings.js"), "modules/buildings.js must exist"

def test_buildings_syntax_and_content():
    with open("modules/buildings.js", "r", encoding="utf-8") as f:
        content = f.read()
    assert "class Buildings" in content
    assert "constructor" in content
    assert "addTo" in content
    assert "update" in content
    assert "cottage.glb" in content or "GLTFLoader" in content
