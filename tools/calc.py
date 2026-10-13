"""
Calculator and Statistical Analysis Tool for atui.
Supports arithmetic operations (add, subtract, multiply, divide, power) and statistical analysis.
Follows the standard plugin interface and CLI runner contract.
"""

import statistics
import json
from typing import Any, Dict, List, Union
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from tools.base import make_result, cli_runner
except ImportError:
    from base import make_result, cli_runner

TOOL_SPEC = {
    "name": "calc",
    "description": "Perform basic arithmetic calculations and statistical analysis on numbers.",
    "parameters": {
        "type": "object",
        "properties": {
            "operation": {
                "type": "string",
                "description": "Operation type: add, subtract, multiply, divide, power, stats",
                "enum": ["add", "subtract", "multiply", "divide", "power", "stats"]
            },
            "a": {
                "type": "number",
                "description": "First operand for binary arithmetic"
            },
            "b": {
                "type": "number",
                "description": "Second operand for binary arithmetic"
            },
            "values": {
                "type": "string",
                "description": "Comma-separated string or JSON list of numbers for statistical analysis"
            }
        },
        "required": ["operation"]
    }
}

def execute(args: Dict[str, Any]) -> Dict[str, Any]:
    operation = args.get("operation")
    if not operation:
        return make_result(False, error="Missing required parameter 'operation'.")

    operation = operation.lower()

    try:
        if operation in ["add", "+"]:
            a = float(args.get("a", 0))
            b = float(args.get("b", 0))
            return make_result(True, a + b)

        elif operation in ["subtract", "sub", "-"]:
            a = float(args.get("a", 0))
            b = float(args.get("b", 0))
            return make_result(True, a - b)

        elif operation in ["multiply", "mul", "*"]:
            a = float(args.get("a", 1))
            b = float(args.get("b", 1))
            return make_result(True, a * b)

        elif operation in ["divide", "div", "/"]:
            a = float(args.get("a", 0))
            b = float(args.get("b", 1))
            if b == 0:
                return make_result(False, error="Division by zero is not allowed.")
            return make_result(True, a / b)

        elif operation in ["power", "pow", "^"]:
            a = float(args.get("a", 0))
            b = float(args.get("b", 0))
            return make_result(True, a ** b)

        elif operation == "stats":
            raw_values = args.get("values")
            if raw_values is None:
                return make_result(False, error="Missing 'values' parameter for statistical analysis.")
            
            # Parse values if passed as string
            if isinstance(raw_values, str):
                raw_values = raw_values.strip()
                if raw_values.startswith("["):
                    try:
                        parsed_list = json.loads(raw_values)
                    except Exception:
                        parsed_list = [float(x.strip()) for x in raw_values.split(",") if x.strip()]
                else:
                    parsed_list = [float(x.strip()) for x in raw_values.split(",") if x.strip()]
                values = parsed_list
            elif isinstance(raw_values, (list, tuple)):
                values = [float(x) for x in raw_values]
            else:
                return make_result(False, error="Invalid format for 'values'. Expected list or comma-separated string.")

            if not values:
                return make_result(False, error="Values list cannot be empty.")

            count = len(values)
            total_sum = sum(values)
            mean = statistics.mean(values)
            median = statistics.median(values)
            minimum = min(values)
            maximum = max(values)
            variance = statistics.variance(values) if count > 1 else 0.0
            stdev = statistics.stdev(values) if count > 1 else 0.0

            stats_result = {
                "count": count,
                "sum": total_sum,
                "mean": mean,
                "median": median,
                "min": minimum,
                "max": maximum,
                "variance": variance,
                "stdev": stdev
            }
            return make_result(True, stats_result)

        else:
            return make_result(False, error=f"Unsupported operation: '{operation}'. Supported: add, subtract, multiply, divide, power, stats.")

    except (ValueError, TypeError) as e:
        return make_result(False, error=f"Invalid argument type or conversion error: {e}")
    except Exception as e:
        return make_result(False, error=f"Calculation error: {e}")

if __name__ == "__main__":
    cli_runner("calc", TOOL_SPEC, execute)
