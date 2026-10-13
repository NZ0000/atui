import os
import pytest

def test_props_module_exists():
    path = os.path.join("modules", "props.js")
    assert os.path.exists(path), f"{path} does not exist"

def test_props_js_syntax_and_export():
    path = os.path.join("modules", "props.js")
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "class Props" in content or "export class Props" in content or "const Props" in content
    assert "constructor" in content
    assert "addTo" in content
    assert "update" in content
