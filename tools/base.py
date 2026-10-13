"""
Base tool interfaces and CLI helpers for atui tools.
Every tool in atui:
1. Is a standalone Python module.
2. Can be imported and called directly as a Python function: execute(args: dict) -> dict.
3. Can be executed from the command line: python tools/<tool_name>.py --arg1 val1 ...
4. Exposes TOOL_SPEC compatible with OpenAI / Function Calling schemas.
"""

import json
import argparse
import sys
from typing import Any, Dict, Callable

def make_result(success: bool, data: Any = None, error: str = "") -> Dict[str, Any]:
    return {
        "success": success,
        "data": data,
        "error": error
    }

def cli_runner(tool_name: str, tool_spec: Dict[str, Any], execute_fn: Callable[[Dict[str, Any]], Dict[str, Any]]):
    """
    Standard CLI parser generator for atui tools.
    Parses CLI flags or JSON string input and calls execute_fn.
    """
    parser = argparse.ArgumentParser(
        prog=tool_name,
        description=tool_spec.get("description", f"ATUI Tool: {tool_name}")
    )
    
    # Allow passing arguments as a single JSON blob via --json
    parser.add_argument("--json", dest="_json_input", type=str, default=None,
                        help="Pass all arguments as a JSON string")
    
    # Also register individual properties from parameters
    props = tool_spec.get("parameters", {}).get("properties", {})
    
    for prop_name, prop_def in props.items():
        prop_type = prop_def.get("type", "string")
        prop_desc = prop_def.get("description", "")
        arg_name = f"--{prop_name.replace('_', '-')}"
        
        if prop_type == "boolean":
            parser.add_argument(arg_name, dest=prop_name, action="store_true", help=prop_desc)
        elif prop_type == "integer":
            parser.add_argument(arg_name, dest=prop_name, type=int, default=None, help=prop_desc)
        elif prop_type == "number":
            parser.add_argument(arg_name, dest=prop_name, type=float, default=None, help=prop_desc)
        else:
            parser.add_argument(arg_name, dest=prop_name, type=str, default=None, help=prop_desc)

    args = parser.parse_args()
    
    if args._json_input:
        try:
            params = json.loads(args._json_input)
        except Exception as e:
            print(json.dumps(make_result(False, error=f"Invalid JSON input: {e}"), ensure_ascii=False, indent=2))
            sys.exit(1)
    else:
        params = {}
        for prop_name in props.keys():
            val = getattr(args, prop_name, None)
            if val is not None:
                params[prop_name] = val
                
    result = execute_fn(params)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not result.get("success", False):
        sys.exit(1)
