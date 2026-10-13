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
    "description": "Vendors local frontend dependencies (like Three.js, RoomEnvironment) and downloads 3D model assets (.glb/.gltf) into project to eliminate external CDN dependencies and ensure offline operation.",
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
            },
            "model": {
                "type": "string",
                "enum": ["car", "ferrari", "helmet", "robot"],
                "description": "Preset 3D model name to download into project (e.g. 'car' downloads ferrari.glb)."
            },
            "download_url": {
                "type": "string",
                "description": "Direct URL of an external 3D model or asset to download and vendor locally."
            },
            "dest_path": {
                "type": "string",
                "description": "Destination file path for the downloaded asset (e.g. 'models/car.glb')."
            }
        }
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
    "addons/loaders/OBJLoader.js": "https://unpkg.com/three@0.160.0/examples/jsm/loaders/OBJLoader.js",
    "addons/loaders/DRACOLoader.js": "https://unpkg.com/three@0.160.0/examples/jsm/loaders/DRACOLoader.js",
    "addons/libs/draco/gltf/draco_decoder.wasm": "https://unpkg.com/three@0.160.0/examples/jsm/libs/draco/gltf/draco_decoder.wasm",
    "addons/libs/draco/gltf/draco_wasm_wrapper.js": "https://unpkg.com/three@0.160.0/examples/jsm/libs/draco/gltf/draco_wasm_wrapper.js",
    "addons/libs/draco/gltf/draco_decoder.js": "https://unpkg.com/three@0.160.0/examples/jsm/libs/draco/gltf/draco_decoder.js",
    "addons/utils/BufferGeometryUtils.js": "https://unpkg.com/three@0.160.0/examples/jsm/utils/BufferGeometryUtils.js",
    "addons/environments/RoomEnvironment.js": "https://unpkg.com/three@0.160.0/examples/jsm/environments/RoomEnvironment.js"
}

MODEL_PRESETS = {
    "car": ("https://cdn.jsdelivr.net/gh/mrdoob/three.js@r160/examples/models/gltf/ferrari.glb", "models/ferrari.glb"),
    "ferrari": ("https://cdn.jsdelivr.net/gh/mrdoob/three.js@r160/examples/models/gltf/ferrari.glb", "models/ferrari.glb"),
    "helmet": ("https://cdn.jsdelivr.net/gh/mrdoob/three.js@r160/examples/models/gltf/DamagedHelmet/glTF/DamagedHelmet.gltf", "models/DamagedHelmet.gltf"),
    "robot": ("https://cdn.jsdelivr.net/gh/mrdoob/three.js@r160/examples/models/gltf/RobotExpressive/RobotExpressive.glb", "models/RobotExpressive.glb")
}

def download_file(url: str, out_path: str) -> Dict[str, Any]:
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    if os.path.exists(out_path) and os.path.getsize(out_path) > 1000:
        return {"file": out_path, "status": "cached", "size": os.path.getsize(out_path)}
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp, open(out_path, "wb") as f:
        f.write(resp.read())
    return {"file": out_path, "status": "downloaded", "size": os.path.getsize(out_path)}

def vendor_three(dest_dir: str) -> Dict[str, Any]:
    os.makedirs(dest_dir, exist_ok=True)
    downloaded = []
    failed = []

    for rel_path, url in THREE_FILES.items():
        out_path = os.path.join(dest_dir, rel_path)
        try:
            res = download_file(url, out_path)
            downloaded.append({"file": rel_path, **res})
        except Exception as e:
            failed.append({"file": rel_path, "error": str(e)})

    return {
        "dest_dir": dest_dir,
        "success": len(failed) == 0,
        "downloaded": downloaded,
        "failed": failed
    }

def execute(params: Dict[str, Any]) -> Dict[str, Any]:
    # 1. Direct custom asset download if download_url provided
    download_url = params.get("download_url")
    dest_path = params.get("dest_path")
    if download_url and dest_path:
        dest_abs = resolve_project_path(dest_path)
        try:
            res = download_file(download_url, dest_abs)
            return make_result(True, data={"asset": res}, error="")
        except Exception as e:
            return make_result(False, error=f"Failed to download asset: {e}")

    # 2. Preset 3D model download
    model_name = params.get("model")
    if model_name:
        model_key = model_name.lower().strip()
        if model_key in MODEL_PRESETS:
            url, rel_dest = MODEL_PRESETS[model_key]
            dest_abs = resolve_project_path(params.get("dest_path") or rel_dest)
            try:
                res = download_file(url, dest_abs)
                return make_result(True, data={"model": model_key, "asset": res}, error="")
            except Exception as e:
                return make_result(False, error=f"Failed to download preset model '{model_key}': {e}")
        else:
            return make_result(False, error=f"Unknown model preset '{model_name}'. Available: {list(MODEL_PRESETS.keys())}")

    # 3. Default Three.js vendor library
    target_dir = resolve_project_path(params.get("target_dir", "vendor/three"))
    res = vendor_three(target_dir)
    return make_result(res["success"], data=res, error="" if res["success"] else f"Failed to vendor: {res['failed']}")

if __name__ == "__main__":
    cli_runner("vendor_assets", TOOL_SPEC, execute)
