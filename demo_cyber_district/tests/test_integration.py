import os
import pytest

def test_integration_and_index():
    index_path = "index.html"
    assert os.path.exists(index_path), f"TDD RED: Expected {index_path} to exist."
    with open(index_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "script" in content.lower(), "index.html should contain scripts."
    
    js_path = "index.js"
    assert os.path.exists(js_path), f"Expected {js_path} to exist."
    with open(js_path, "r", encoding="utf-8") as f:
        js_content = f.read()
    assert "Terrain" in js_content, "index.js should import Terrain."
    assert "Buildings" in js_content, "index.js should import Buildings."
