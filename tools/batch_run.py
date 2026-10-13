#!/usr/bin/env python3
"""
Tool: batch_run
Executes multiple atui tools in a single batch request to minimize LLM turns,
network latency, and token overhead. Supports sequential or parallel execution.
"""

import sys
import os
import json
from typing import Dict, Any, List

try:
    from tools.base import make_result, cli_runner
    import tools
except ImportError:
    # Handle direct script execution
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from tools.base import make_result, cli_runner
    import tools

TOOL_SPEC = {
    "name": "batch_run",
    "description": "Execute multiple tools in a single batch turn (e.g. write multiple files, run syntax checks, and run commands all at once). Saves round-trip turns and tokens.",
    "parameters": {
        "type": "object",
        "properties": {
            "calls": {
                "type": "array",
                "description": "List of tool call specifications to execute sequentially.",
                "items": {
                    "type": "object",
                    "properties": {
                        "tool": {
                            "type": "string",
                            "description": "Name of the tool to execute (e.g. 'write', 'read', 'run', 'web_validator')."
                        },
                        "args": {
                            "type": "object",
                            "description": "Dictionary of arguments to pass to the tool."
                        }
                    },
                    "required": ["tool", "args"]
                }
            },
            "stop_on_error": {
                "type": "boolean",
                "description": "If true, stops execution immediately if any tool call fails. Default is false."
            }
        },
        "required": ["calls"]
    }
}

def execute_batch(calls: List[Dict[str, Any]], stop_on_error: bool = False) -> Dict[str, Any]:
    if not isinstance(calls, list) or len(calls) == 0:
        return make_result(False, error="Parameter 'calls' must be a non-empty list of tool invocations.")

    results: List[Dict[str, Any]] = []
    success_count = 0
    failure_count = 0

    for idx, item in enumerate(calls):
        tool_name = item.get("tool")
        tool_args = item.get("args", {})

        if not tool_name:
            res = {"success": False, "error": f"Item #{idx} missing 'tool' name."}
            results.append({"index": idx, "tool": "unknown", "result": res})
            failure_count += 1
            if stop_on_error:
                break
            continue

        try:
            res = tools.execute_tool(tool_name, tool_args)
            ok = res.get("success", False) if isinstance(res, dict) else False
            if ok:
                success_count += 1
            else:
                failure_count += 1

            results.append({
                "index": idx,
                "tool": tool_name,
                "result": res
            })

            if not ok and stop_on_error:
                break
        except Exception as e:
            failure_count += 1
            results.append({
                "index": idx,
                "tool": tool_name,
                "result": {"success": False, "error": str(e)}
            })
            if stop_on_error:
                break

    all_ok = (failure_count == 0)
    summary_data = {
        "total": len(calls),
        "executed": len(results),
        "succeeded": success_count,
        "failed": failure_count,
        "results": results
    }

    if all_ok:
        return make_result(True, data=summary_data)
    else:
        err_details = "; ".join([
            f"[{r.get('tool', 'unknown')}]: {r.get('result', {}).get('error', 'failed')}"
            for r in results if not (r.get("result", {}).get("success", False) if isinstance(r.get("result"), dict) else False)
        ])
        return make_result(
            False,
            data=summary_data,
            error=f"Batch execution finished with {failure_count} failure(s) out of {len(results)} executed: {err_details}"
        )

def execute(params: Dict[str, Any]) -> Dict[str, Any]:
    calls = params.get("calls", [])
    stop_on_error = params.get("stop_on_error", False)
    return execute_batch(calls, stop_on_error)

if __name__ == "__main__":
    def _cli_entry(params: Dict[str, Any]):
        calls_raw = params.get("calls")
        if isinstance(calls_raw, str):
            try:
                params["calls"] = json.loads(calls_raw)
            except Exception:
                pass
        return execute(params)

    cli_runner(
        tool_name="batch_run",
        tool_spec=TOOL_SPEC,
        execute_fn=_cli_entry
    )
