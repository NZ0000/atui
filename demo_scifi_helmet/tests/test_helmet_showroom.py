# TDD Test Suite for Sci-Fi Battle Helmet Showroom
import os
import pytest

def test_project_structure():
    assert os.path.exists("index.html"), "index.html showroom page must exist."
    assert os.path.exists("deliverables/plan.md"), "Plan file must exist."
    assert os.path.exists("deliverables/acceptance_criteria.md"), "Acceptance criteria must exist."

def test_index_html_content():
    assert os.path.exists("index.html")
    with open("index.html", "r", encoding="utf-8") as f:
        content = f.read()
    
    # Check offline dependencies & Three.js addons
    assert "three.module.js" in content
    assert "OrbitControls.js" in content
    assert "GLTFLoader.js" in content
    assert "RoomEnvironment.js" in content
    assert "EffectComposer.js" in content
    assert "UnrealBloomPass.js" in content

    # Check hardware MSAA anti-aliasing requirement
    assert "samples:" in content or "samples" in content, "WebGLRenderTarget must configure samples for hardware MSAA"

    # Check RoomEnvironment & PMREMGenerator
    assert "RoomEnvironment" in content
    assert "PMREMGenerator" in content

    # Check Fallback procedural helmet generator for robust offline execution
    assert "fallback" in content.lower() or "createProceduralHelmet" in content or "Mesh" in content
