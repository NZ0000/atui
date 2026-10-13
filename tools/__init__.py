"""
Tools registry and dynamic loader for atui.
Auto-discovers any tool defined in the tools/ directory.
"""

import os
import sys
import importlib.util
from typing import Dict, Any, List, Optional, Callable

_TOOLS: Dict[str, Dict[str, Any]] = {}

def discover_tools(tools_dir: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
    """Scan tools_dir for .py files containing TOOL_SPEC and execute function."""
    global _TOOLS
    if not tools_dir:
        tools_dir = os.path.dirname(os.path.abspath(__file__))

    if not os.path.exists(tools_dir):
        return _TOOLS

    for filename in os.listdir(tools_dir):
        if filename.startswith("_") or not filename.endswith(".py") or filename == "base.py":
            continue
        tool_name = filename[:-3]
        file_path = os.path.join(tools_dir, filename)

        try:
            spec = importlib.util.spec_from_file_location(f"tools.{tool_name}", file_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                if hasattr(module, "TOOL_SPEC") and hasattr(module, "execute"):
                    _TOOLS[tool_name] = {
                        "name": tool_name,
                        "spec": module.TOOL_SPEC,
                        "execute": module.execute,
                        "module": module,
                        "path": file_path
                    }
        except Exception as e:
            print(f"[Warning] Failed to load tool '{tool_name}' from {file_path}: {e}", file=sys.stderr)

    return _TOOLS

def get_tool(name: str) -> Optional[Dict[str, Any]]:
    if not _TOOLS:
        discover_tools()
    return _TOOLS.get(name)

def list_tools() -> List[str]:
    if not _TOOLS:
        discover_tools()
    return sorted(list(_TOOLS.keys()))

def get_tool_specs(allowed_tools: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    if not _TOOLS:
        discover_tools()
    specs = []
    for name, tool_info in _TOOLS.items():
        if allowed_tools is None or name in allowed_tools or "*" in allowed_tools:
            specs.append({
                "type": "function",
                "function": tool_info["spec"]
            })
    return specs

def execute_tool(name: str, params: Dict[str, Any]) -> Dict[str, Any]:
    tool_info = get_tool(name)
    if not tool_info:
        return {
            "success": False,
            "data": None,
            "error": f"Tool '{name}' is not registered or not found."
        }
    try:
        return tool_info["execute"](params)
    except Exception as e:
        return {
            "success": False,
            "data": None,
            "error": f"Error executing tool '{name}': {e}"
        }

# Initial discovery
discover_tools()
