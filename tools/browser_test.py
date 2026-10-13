#!/usr/bin/env python3
"""
Tool: browser_test
Automated Headless Browser Testing, Console Error & Exception Collector,
and Viewport Screenshot Capture Suite for atui.
Runs Chromium with SwiftShader WebGL fallback, captures console errors / 404s,
and produces high-resolution screenshots for multimodal visual inspection.
"""

import sys
import os
import json
import time
import socket
import base64
import asyncio
import subprocess
import threading
from http.server import SimpleHTTPRequestHandler, HTTPServer
from typing import Dict, Any, List, Optional
import urllib.request

try:
    import websockets
except ImportError:
    websockets = None

try:
    from tools.base import make_result, cli_runner, resolve_project_path
except ImportError:
    from base import make_result, cli_runner, resolve_project_path

TOOL_SPEC = {
    "name": "browser_test",
    "description": "Test web pages in a headless Chromium browser with WebGL enabled. Captures console errors, warnings, unhandled exceptions, network failures, and renders high-res screenshots for visual evaluation.",
    "parameters": {
        "type": "object",
        "properties": {
            "url_or_path": {
                "type": "string",
                "description": "URL (http://...) or local file path (e.g. 'index.html') to open and test."
            },
            "screenshot_path": {
                "type": "string",
                "description": "Output path for the viewport screenshot PNG. Defaults to 'screenshot.png'."
            },
            "wait_ms": {
                "type": "integer",
                "description": "Milliseconds to wait for 3D/WebGL animations and scripts to render before capturing. Default 2500."
            },
            "viewport_width": {
                "type": "integer",
                "description": "Browser viewport width in pixels. Default 1280."
            },
            "viewport_height": {
                "type": "integer",
                "description": "Browser viewport height in pixels. Default 800."
            }
        },
        "required": ["url_or_path"]
    }
}

def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]

class QuietHTTPHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # Suppress console clutter

def _start_local_server(directory: str, port: int) -> HTTPServer:
    class CustomDirHandler(QuietHTTPHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=directory, **kwargs)

    server = HTTPServer(("127.0.0.1", port), CustomDirHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server

async def _cdp_session(
    ws_url: str,
    target_url: str,
    wait_ms: int,
    screenshot_path: str,
    viewport_width: int,
    viewport_height: int
) -> Dict[str, Any]:
    console_errors = []
    warnings = []
    console_logs = []
    network_failures = []
    request_map = {}
    screenshot_base64 = ""

    async with websockets.connect(ws_url, max_size=20 * 1024 * 1024) as ws:
        msg_id = 1

        async def send_cmd(method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
            nonlocal msg_id
            cmd = {"id": msg_id, "method": method, "params": params or {}}
            msg_id += 1
            await ws.send(json.dumps(cmd))
            return cmd

        # Enable necessary CDP domains
        await send_cmd("Runtime.enable")
        await send_cmd("Console.enable")
        await send_cmd("Log.enable")
        await send_cmd("Page.enable")
        await send_cmd("Network.enable")

        # Set viewport
        await send_cmd("Emulation.setDeviceMetricsOverride", {
            "width": viewport_width,
            "height": viewport_height,
            "deviceScaleFactor": 1,
            "mobile": False
        })

        # Navigate
        nav_cmd = await send_cmd("Page.navigate", {"url": target_url})
        nav_id = nav_cmd["id"]

        start_time = time.time()
        wait_seconds = wait_ms / 1000.0

        # Event listening loop
        while time.time() - start_time < wait_seconds + 1.0:
            try:
                raw = await asyncio.wait_for(ws.recv(), timeout=0.2)
                data = json.loads(raw)

                method = data.get("method", "")
                params = data.get("params", {})

                if method == "Runtime.exceptionThrown":
                    details = params.get("exceptionDetails", {})
                    text = details.get("text", "")
                    exc = details.get("exception", {}).get("description", "")
                    line = details.get("lineNumber", 0)
                    console_errors.append({
                        "type": "UNCAUGHT_EXCEPTION",
                        "line": line,
                        "message": exc or text
                    })

                elif method == "Console.messageAdded":
                    msg = params.get("message", {})
                    level = msg.get("level", "")
                    text = msg.get("text", "")
                    line = msg.get("line", 0)
                    if level == "error":
                        console_errors.append({"type": "CONSOLE_ERROR", "line": line, "message": text})
                    elif level == "warning":
                        warnings.append({"type": "CONSOLE_WARN", "line": line, "message": text})
                    else:
                        console_logs.append({"level": level, "text": text})

                elif method == "Runtime.consoleAPICalled":
                    ctype = params.get("type", "")
                    args = params.get("args", [])
                    txt = " ".join([str(a.get("value", a.get("description", ""))) for a in args])
                    if ctype == "error":
                        console_errors.append({"type": "CONSOLE_ERROR", "message": txt})
                    elif ctype == "warning":
                        warnings.append({"type": "CONSOLE_WARN", "message": txt})
                    else:
                        console_logs.append({"level": ctype, "text": txt})

                elif method == "Network.requestWillBeSent":
                    req_id = params.get("requestId", "")
                    req_url = params.get("request", {}).get("url", "")
                    if req_id and req_url:
                        request_map[req_id] = req_url

                elif method == "Network.loadingFailed":
                    req_id = params.get("requestId", "")
                    err_text = params.get("errorText", "Network request failed")
                    is_canceled = params.get("canceled", False) or err_text == "net::ERR_ABORTED"
                    if not is_canceled:
                        req_url = request_map.get(req_id, req_id)
                        network_failures.append({
                            "url": req_url,
                            "error": err_text,
                            "type": params.get("type", "")
                        })

            except asyncio.TimeoutError:
                if time.time() - start_time >= wait_seconds:
                    break

        # Capture screenshot
        shot_cmd = await send_cmd("Page.captureScreenshot", {"format": "png"})
        shot_id = shot_cmd["id"]

        # Wait for screenshot response
        while True:
            try:
                raw = await asyncio.wait_for(ws.recv(), timeout=3.0)
                data = json.loads(raw)
                if data.get("id") == shot_id:
                    result = data.get("result", {})
                    screenshot_base64 = result.get("data", "")
                    break
            except asyncio.TimeoutError:
                break

    # Save screenshot to disk
    if screenshot_base64 and screenshot_path:
        os.makedirs(os.path.dirname(os.path.abspath(screenshot_path)), exist_ok=True)
        with open(screenshot_path, "wb") as f:
            f.write(base64.b64decode(screenshot_base64))

    return {
        "console_errors": console_errors,
        "warnings": warnings,
        "console_logs": console_logs[:20],
        "network_failures": network_failures,
        "screenshot_base64": screenshot_base64,
        "screenshot_path": screenshot_path if screenshot_base64 else None,
        "has_screenshot": bool(screenshot_base64)
    }

def run_browser_test(
    url_or_path: str,
    screenshot_path: Optional[str] = None,
    wait_ms: int = 2500,
    viewport_width: int = 1280,
    viewport_height: int = 800
) -> Dict[str, Any]:
    # Resolve URL or local file path
    server = None
    target_url = url_or_path
    if not url_or_path.startswith(("http://", "https://")):
        url_or_path = resolve_project_path(url_or_path)
        local_abs = os.path.abspath(url_or_path)
        if not os.path.exists(local_abs):
            return make_result(False, error=f"Target file does not exist: {url_or_path}")

        doc_dir = os.path.dirname(local_abs)
        file_name = os.path.basename(local_abs)
        port = _find_free_port()
        server = _start_local_server(doc_dir, port)
        target_url = f"http://127.0.0.1:{port}/{file_name}"

    if screenshot_path:
        screenshot_path = resolve_project_path(screenshot_path)
    else:
        screenshot_path = os.path.join(
            os.path.dirname(os.path.abspath(url_or_path)) if not url_or_path.startswith("http") else os.getcwd(),
            "screenshot.png"
        )
    screenshot_path = os.path.abspath(screenshot_path)

    cdp_port = _find_free_port()

    # Launch Chromium
    chrome_args = [
        "/usr/bin/chromium",
        "--headless=new",
        "--no-sandbox",
        "--disable-gpu",
        "--use-gl=angle",
        "--use-angle=swiftshader",
        f"--remote-debugging-port={cdp_port}",
        f"--window-size={viewport_width},{viewport_height}",
        "about:blank"
    ]

    proc = None
    try:
        proc = subprocess.Popen(
            chrome_args,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        # Wait for CDP to be ready
        ws_url = None
        for _ in range(30):
            time.sleep(0.1)
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{cdp_port}/json", timeout=0.5) as r:
                    pages = json.loads(r.read().decode())
                    if pages and len(pages) > 0:
                        ws_url = pages[0].get("webSocketDebuggerUrl")
                        if ws_url:
                            break
            except Exception:
                pass

        if not ws_url:
            return make_result(False, error="Failed to connect to Chromium DevTools Protocol (CDP).")

        # Run CDP session
        result_data = asyncio.run(_cdp_session(
            ws_url=ws_url,
            target_url=target_url,
            wait_ms=wait_ms,
            screenshot_path=screenshot_path,
            viewport_width=viewport_width,
            viewport_height=viewport_height
        ))

        error_count = len(result_data["console_errors"]) + len(result_data["network_failures"])
        passed = (error_count == 0)

        # Add metadata
        result_data["url"] = target_url
        result_data["error_count"] = error_count
        result_data["warning_count"] = len(result_data["warnings"])
        result_data["viewport"] = f"{viewport_width}x{viewport_height}"

        # Truncate raw base64 for lighter JSON output if screenshot file is written
        preview_base64 = result_data["screenshot_base64"]
        if preview_base64:
            result_data["screenshot_size_bytes"] = len(base64.b64decode(preview_base64))
            result_data["image_url"] = f"data:image/png;base64,{preview_base64}"
            # Keep only a sample in plain data to save token size
            result_data["screenshot_base64_preview"] = preview_base64[:100] + "..."

        return make_result(
            passed,
            data=result_data,
            error="" if passed else f"Browser test found {error_count} console/network error(s)."
        )

    except Exception as e:
        return make_result(False, error=f"Browser test failed with exception: {e}")
    finally:
        if proc:
            proc.terminate()
            try:
                proc.wait(timeout=2)
            except Exception:
                proc.kill()
        if server:
            server.shutdown()

def execute(params: Dict[str, Any]) -> Dict[str, Any]:
    url_or_path = params.get("url_or_path", "")
    screenshot_path = params.get("screenshot_path")
    wait_ms = params.get("wait_ms", 2500)
    viewport_width = params.get("viewport_width", 1280)
    viewport_height = params.get("viewport_height", 800)
    return run_browser_test(
        url_or_path=url_or_path,
        screenshot_path=screenshot_path,
        wait_ms=wait_ms,
        viewport_width=viewport_width,
        viewport_height=viewport_height
    )

if __name__ == "__main__":
    cli_runner(
        tool_name="browser_test",
        tool_spec=TOOL_SPEC,
        execute_fn=execute
    )
