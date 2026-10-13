#!/usr/bin/env python3
"""
Tool: browser_interact
Playwright-powered browser interaction tool for interactive UI testing.

Allows agents to:
  - Navigate to a URL
  - Click buttons / elements (by text, CSS selector, or id)
  - Wait for conditions (e.g. JS expression to be truthy, time)
  - Evaluate JavaScript to read state
  - Capture screenshots after each interaction step
  - Generate multi-angle screenshot sequences for 3D / interactive web apps

Returns a structured JSON result with per-step screenshots (base64 embedded)
and a console log summary.

Usage examples:
  Single screenshot:
    {"url": "http://localhost:8086", "wait_for_load_ms": 12000, "screenshot_path": "deliverables/screenshot.png"}

  Multi-step interaction (3D view switching):
    {
      "url": "http://localhost:8086",
      "wait_for_load_ms": 12000,
      "steps": [
        {"action": "screenshot", "label": "initial_view", "path": "deliverables/view_initial.png"},
        {"action": "click", "selector": "#btn-sunset", "label": "sunset_mode"},
        {"action": "wait_ms", "ms": 1000},
        {"action": "screenshot", "label": "sunset_view", "path": "deliverables/view_sunset.png"},
        {"action": "click", "selector": "#btn-night"},
        {"action": "wait_ms", "ms": 1000},
        {"action": "screenshot", "label": "night_view", "path": "deliverables/view_night.png"},
        {"action": "click", "selector": "#cam-chalet"},
        {"action": "wait_ms", "ms": 1500},
        {"action": "screenshot", "label": "chalet_closeup", "path": "deliverables/view_chalet.png"},
        {"action": "eval", "expression": "document.title", "label": "page_title"}
      ]
    }
"""

import os
import sys
import base64
import json
import socket
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from typing import Dict, Any, List, Optional

try:
    from tools.base import make_result, cli_runner, resolve_project_path
except ImportError:
    from base import make_result, cli_runner, resolve_project_path


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]


class _QuietHTTPHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass


def _start_local_server(directory: str, port: int) -> HTTPServer:
    class CustomDirHandler(_QuietHTTPHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=directory, **kwargs)

    server = HTTPServer(("127.0.0.1", port), CustomDirHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server

TOOL_SPEC = {
    "name": "browser_interact",
    "description": (
        "Playwright-powered interactive browser tool. Navigates to a URL, waits for 3D/WebGL content to load, "
        "then executes a sequence of interaction steps (click, wait, evaluate JS, screenshot). "
        "Returns structured per-step results with screenshots embedded as base64. "
        "Perfect for multi-angle visual testing of interactive 3D scenes, desktop-like web apps, or complex UIs. "
        "Use this instead of browser_test when you need to CLICK buttons or INTERACT with the page before screenshots."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "URL to navigate to (http://... or file path). Required."
            },
            "wait_for_load_ms": {
                "type": "integer",
                "description": (
                    "Milliseconds to wait after page load before executing steps. "
                    "Use higher values (10000-15000) for 3D scenes that load external GLB assets. "
                    "Default: 3000."
                )
            },
            "screenshot_path": {
                "type": "string",
                "description": "If no steps provided, take a single screenshot and save here."
            },
            "viewport_width": {
                "type": "integer",
                "description": "Browser viewport width. Default: 1280."
            },
            "viewport_height": {
                "type": "integer",
                "description": "Browser viewport height. Default: 800."
            },
            "steps": {
                "type": "array",
                "description": (
                    "Ordered list of interaction steps to execute. Each step is an object with an 'action' field:\n"
                    "  - {\"action\": \"screenshot\", \"path\": \"out.png\", \"label\": \"my_label\"} — capture screenshot\n"
                    "  - {\"action\": \"click\", \"selector\": \"#btn-id\"} — click by CSS selector\n"
                    "  - {\"action\": \"click_text\", \"text\": \"夕阳余晖\"} — click first element containing text\n"
                    "  - {\"action\": \"wait_ms\", \"ms\": 1500} — pause for N milliseconds\n"
                    "  - {\"action\": \"wait_for_console\", \"contains\": \"model loaded\", \"timeout_ms\": 15000} — wait until console log appears\n"
                    "  - {\"action\": \"eval\", \"expression\": \"document.title\", \"label\": \"title\"} — evaluate JS and record result\n"
                    "  - {\"action\": \"hover\", \"selector\": \"#element\"} — hover over element\n"
                    "  - {\"action\": \"type\", \"selector\": \"#input\", \"text\": \"hello\"} — type into input\n"
                ),
                "items": {"type": "object"}
            },
            "console_filter": {
                "type": "string",
                "description": "If set, only console messages containing this string are returned. Default: return all."
            }
        },
        "required": ["url"]
    }
}


def _save_screenshot_b64(page, path: str) -> str:
    """Take a screenshot, save to path, and return base64 string."""
    if path:
        abs_path = resolve_project_path(path)
        os.makedirs(os.path.dirname(os.path.abspath(abs_path)), exist_ok=True)
        page.screenshot(path=abs_path, full_page=False)
        with open(abs_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        return b64
    else:
        png_bytes = page.screenshot(full_page=False)
        return base64.b64encode(png_bytes).decode()


def run_browser_interact(
    url: str,
    wait_for_load_ms: int = 3000,
    screenshot_path: Optional[str] = None,
    viewport_width: int = 1280,
    viewport_height: int = 800,
    steps: Optional[List[Dict[str, Any]]] = None,
    console_filter: Optional[str] = None
) -> Dict[str, Any]:
    try:
        from playwright.sync_api import sync_playwright, TimeoutError as PWTimeoutError
    except ImportError:
        return make_result(False, error=(
            "playwright is not installed. Run: pip install playwright && playwright install chromium"
        ))

    if not url or not url.strip():
        return make_result(False, error="Parameter 'url' is required.")

    console_logs = []
    console_errors = []
    step_results = []

    # Resolve local file paths to HTTP URLs to support ES modules / CORS
    server = None
    target_url = url.strip()
    if not target_url.startswith(("http://", "https://")):
        abs_path = os.path.abspath(resolve_project_path(target_url))
        if not os.path.exists(abs_path):
            return make_result(False, error=f"File not found: {abs_path}")
        doc_dir = os.path.dirname(abs_path) if os.path.isfile(abs_path) else abs_path
        file_name = os.path.basename(abs_path) if os.path.isfile(abs_path) else ""
        port = _find_free_port()
        server = _start_local_server(doc_dir, port)
        target_url = f"http://127.0.0.1:{port}/{file_name}"

    p_ctx = sync_playwright()
    p = p_ctx.__enter__()
    try:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-gpu",
                "--enable-unsafe-swiftshader",
                "--disable-dev-shm-usage",
                f"--window-size={viewport_width},{viewport_height}"
            ]
        )
        page = browser.new_page(viewport={"width": viewport_width, "height": viewport_height})

        # Capture console output
        def on_console(msg):
            entry = {"type": msg.type, "text": msg.text}
            if console_filter is None or console_filter in msg.text:
                console_logs.append(entry)
            if msg.type == "error":
                console_errors.append(entry)

        def on_pageerror(err):
            console_errors.append({"type": "uncaught_exception", "text": str(err)})

        page.on("console", on_console)
        page.on("pageerror", on_pageerror)

        # Navigate
        try:
            page.goto(target_url, wait_until="domcontentloaded", timeout=30000)
        except Exception as e:
            browser.close()
            return make_result(False, error=f"Navigation failed: {e}")

        # Wait for initial load (3D assets, WebGL init, etc.)
        if wait_for_load_ms > 0:
            page.wait_for_timeout(wait_for_load_ms)

        # If no steps, just take a screenshot and return
        if not steps:
            path = screenshot_path or "screenshot.png"
            b64 = _save_screenshot_b64(page, path)
            browser.close()
            return make_result(True, data={
                "url": target_url,
                "screenshot_path": resolve_project_path(path),
                "screenshot_base64": b64[:200] + "..." if len(b64) > 200 else b64,
                "image_url": f"data:image/png;base64,{b64}",
                "console_logs": console_logs[-30:],
                "console_errors": console_errors,
                "steps": []
            })

        # Execute steps
        for i, step in enumerate(steps):
            action = step.get("action", "screenshot")
            label = step.get("label", f"step_{i}")
            step_result = {"step": i, "action": action, "label": label, "success": False}

            try:
                if action == "screenshot":
                    path = step.get("path", f"deliverables/screenshot_step_{i}.png")
                    b64 = _save_screenshot_b64(page, path)
                    step_result.update({
                        "success": True,
                        "screenshot_path": resolve_project_path(path),
                        "image_url": f"data:image/png;base64,{b64}",
                        "screenshot_base64": b64[:200] + "..." if len(b64) > 200 else b64
                    })

                elif action == "click":
                    selector = step.get("selector", "")
                    try:
                        page.locator(selector).first.click(force=True, no_wait_after=True, timeout=3000)
                    except Exception:
                        page.evaluate(
                            "sel => { const el = document.querySelector(sel); if (!el) throw new Error('Element not found: ' + sel); el.click(); }",
                            selector
                        )
                    step_result["success"] = True
                    step_result["selector"] = selector

                elif action == "click_text":
                    text = step.get("text", "")
                    try:
                        page.get_by_text(text, exact=False).first.click(force=True, no_wait_after=True, timeout=3000)
                    except Exception:
                        page.evaluate(
                            "txt => { const els = Array.from(document.querySelectorAll('button, a, div, span, input')); const target = els.find(e => e.textContent && e.textContent.includes(txt)); if (!target) throw new Error('Text not found: ' + txt); target.click(); }",
                            text
                        )
                    step_result["success"] = True
                    step_result["text"] = text

                elif action == "wait_ms":
                    ms = step.get("ms", 1000)
                    page.wait_for_timeout(ms)
                    step_result["success"] = True
                    step_result["waited_ms"] = ms

                elif action == "wait_for_console":
                    target_text = step.get("contains", "")
                    timeout_ms = step.get("timeout_ms", 15000)
                    found = False
                    waited = 0
                    interval = 500
                    while waited < timeout_ms:
                        page.wait_for_timeout(interval)
                        waited += interval
                        if any(target_text in e["text"] for e in console_logs):
                            found = True
                            break
                    step_result["success"] = found
                    step_result["found"] = found
                    step_result["waited_ms"] = waited

                elif action == "eval":
                    expression = step.get("expression", "document.title")
                    result = page.evaluate(expression)
                    step_result["success"] = True
                    step_result["result"] = str(result)

                elif action == "hover":
                    selector = step.get("selector", "")
                    page.hover(selector, timeout=5000)
                    step_result["success"] = True

                elif action == "type":
                    selector = step.get("selector", "")
                    text = step.get("text", "")
                    page.fill(selector, text, timeout=5000)
                    step_result["success"] = True

                else:
                    step_result["error"] = f"Unknown action: {action}"

            except Exception as e:
                step_result["error"] = str(e)

            step_results.append(step_result)

        browser.close()
    finally:
        try:
            p_ctx.__exit__(None, None, None)
        except Exception:
            pass
        if server:
            try:
                server.shutdown()
            except Exception:
                pass

    screenshots = [s for s in step_results if s.get("screenshot_path")]
    error_count = len(console_errors)
    passed = all(s.get("success", False) for s in step_results)

    return make_result(passed, data={
        "url": target_url,
        "steps_executed": len(step_results),
        "steps_passed": sum(1 for s in step_results if s.get("success")),
        "screenshots_captured": len(screenshots),
        "screenshot_paths": [s["screenshot_path"] for s in screenshots],
        "console_errors": console_errors,
        "console_error_count": error_count,
        "console_logs": console_logs[-30:],
        "step_results": step_results
    }, error="" if passed else f"Some steps failed or {error_count} console error(s) found.")


def execute(params: Dict[str, Any]) -> Dict[str, Any]:
    return run_browser_interact(
        url=params.get("url", ""),
        wait_for_load_ms=params.get("wait_for_load_ms", 3000),
        screenshot_path=params.get("screenshot_path"),
        viewport_width=params.get("viewport_width", 1280),
        viewport_height=params.get("viewport_height", 800),
        steps=params.get("steps"),
        console_filter=params.get("console_filter")
    )


if __name__ == "__main__":
    cli_runner(
        tool_name="browser_interact",
        tool_spec=TOOL_SPEC,
        execute_fn=execute
    )
