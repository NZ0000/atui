#!/usr/bin/env python3
"""
Tool: vendor_assets
Manages and vendors local offline frontend libraries (e.g. Three.js, Chart.js, etc.)
to eliminate external CDN single-point failures and enable 100% air-gapped execution.
"""

import sys
import os
import shutil
import urllib.request
from typing import Dict, Any, List, Optional

try:
    from tools.base import make_result, cli_runner, resolve_project_path
except ImportError:
    from base import make_result, cli_runner, resolve_project_path

TOOL_SPEC = {
    "name": "vendor_assets",
    "description": "Vendors local frontend dependencies (like Three.js) into project to eliminate external CDN dependencies and ensure offline operation.",
    "parameters": {
        "type": "object",
        "properties": {
            "target_dir": {
                "type": "string",
                "description": "Project directory where vendor assets should be stored (e.g. 'vendor/three')."
            },
            "library": {
                "type": "string",
                "enum": ["threejs", "all"],
                "description": "Library package to vendor. Default is 'threejs'."
            }
        },
        "required": ["target_dir"]
    }
}

THREE_FILES = {
    "three.module.js": "https://unpkg.com/three@0.160.0/build/three.module.js",
    "addons/controls/OrbitControls.js": "https://unpkg.com/three@0.160.0/examples/jsm/controls/OrbitControls.js",
    "addons/postprocessing/EffectComposer.js": "https://unpkg.com/three@0.160.0/examples/jsm/postprocessing/EffectComposer.js",
    "addons/postprocessing/RenderPass.js": "https://unpkg.com/three@0.160.0/examples/jsm/postprocessing/RenderPass.js",
    "addons/postprocessing/ShaderPass.js": "https://unpkg.com/three@0.160.0/examples/jsm/postprocessing/ShaderPass.js",
    "addons/postprocessing/UnrealBloomPass.js": "https://unpkg.com/three@0.160.0/examples/jsm/postprocessing/UnrealBloomPass.js",
    "addons/postprocessing/Pass.js": "https://unpkg.com/three@0.160.0/examples/jsm/postprocessing/Pass.js",
    "addons/postprocessing/MaskPass.js": "https://unpkg.com/three@0.160.0/examples/jsm/postprocessing/MaskPass.js",
    "addons/shaders/CopyShader.js": "https://unpkg.com/three@0.160.0/examples/jsm/shaders/CopyShader.js",
    "addons/shaders/LuminosityHighPassShader.js": "https://unpkg.com/three@0.160.0/examples/jsm/shaders/LuminosityHighPassShader.js",
    "addons/loaders/GLTFLoader.js": "https://unpkg.com/three@0.160.0/examples/jsm/loaders/GLTFLoader.js",
    "addons/loaders/OBJLoader.js": "https://unpkg.com/three@0.160.0/examples/jsm/loaders/OBJLoader.js"
}

def vendor_three(dest_dir: str) -> Dict[str, Any]:
    os.makedirs(dest_dir, exist_ok=True)
    downloaded = []
    failed = []

    for rel_path, url in THREE_FILES.items():
        out_path = os.path.join(dest_dir, rel_path)
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        if os.path.exists(out_path) and os.path.getsize(out_path) > 1000:
            downloaded.append({"file": rel_path, "status": "cached", "size": os.path.getsize(out_path)})
            continue

        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=15) as resp, open(out_path, "wb") as f:
                f.write(resp.read())
            downloaded.append({"file": rel_path, "status": "downloaded", "size": os.path.getsize(out_path)})
        except Exception as e:
            failed.append({"file": rel_path, "error": str(e)})

    return {
        "dest_dir": dest_dir,
        "success": len(failed) == 0,
        "downloaded": downloaded,
        "failed": failed
    }

def execute(params: Dict[str, Any]) -> Dict[str, Any]:
    target_dir = resolve_project_path(params.get("target_dir", "vendor/three"))
    res = vendor_three(target_dir)
    return make_result(res["success"], data=res, error="" if res["success"] else f"Failed to vendor: {res['failed']}")

if __name__ == "__main__":
    cli_runner("vendor_assets", TOOL_SPEC, execute)
