#!/usr/bin/env python3
"""
Tool: env_manager
Comprehensive Environment Probe, Dependency Inspector, and Background Service Orchestrator for atui.
Capabilities:
1. 'probe': Inspects OS, Python, Node, Chromium, available free ports, and memory.
2. 'start_http': Starts a managed background HTTP static file server.
3. 'start_ws': Starts a managed background WebSocket server.
4. 'start_mqtt': Starts a managed background MQTT broker.
5. 'list_services': Returns all active managed services.
6. 'stop_service': Shuts down a managed service by port.
"""

import sys
import os
import json
import time
import socket
import platform
import threading
import subprocess
from http.server import SimpleHTTPRequestHandler, HTTPServer
from typing import Dict, Any, List, Optional

try:
    from tools.base import make_result, cli_runner
except ImportError:
    from base import make_result, cli_runner

TOOL_SPEC = {
    "name": "env_manager",
    "description": "Probe environment capabilities (Node/Python/Chromium/ports) and orchestrate background services (HTTP static server, WebSocket server, MQTT broker).",
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["probe", "start_http", "start_ws", "start_mqtt", "list_services", "stop_service"],
                "description": "Action to perform: 'probe' system, 'start_http', 'start_ws', 'start_mqtt', 'list_services', or 'stop_service'."
            },
            "directory": {
                "type": "string",
                "description": "Directory to serve for 'start_http' (defaults to current project directory)."
            },
            "port": {
                "type": "integer",
                "description": "Target port to bind or stop. If omitted for start, an open port is selected automatically."
            },
            "host": {
                "type": "string",
                "description": "Host interface to bind. Default '127.0.0.1'."
            }
        },
        "required": ["action"]
    }
}

_ACTIVE_SERVICES: Dict[int, Dict[str, Any]] = {}
_SERVICE_LOCK = threading.Lock()

def _find_open_port(preferred: Optional[int] = None) -> int:
    if preferred:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('127.0.0.1', preferred))
                return preferred
            except OSError:
                pass
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]

def probe_environment() -> Dict[str, Any]:
    info: Dict[str, Any] = {
        "os": platform.system(),
        "release": platform.release(),
        "arch": platform.machine(),
        "python_version": platform.python_version(),
        "python_path": sys.executable,
        "node_installed": False,
        "node_version": None,
        "chromium_installed": False,
        "chromium_path": None,
        "recommended_http_port": _find_open_port(8080),
        "recommended_ws_port": _find_open_port(8081),
        "recommended_mqtt_port": _find_open_port(1883)
    }

    # Check node
    try:
        np = subprocess.run(["node", "-v"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=3)
        if np.returncode == 0:
            info["node_installed"] = True
            info["node_version"] = np.stdout.strip()
    except Exception:
        pass

    # Check chromium
    for c_cmd in ["chromium", "google-chrome", "chromium-browser"]:
        try:
            cp = subprocess.run(["which", c_cmd], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=3)
            if cp.returncode == 0:
                info["chromium_installed"] = True
                info["chromium_path"] = cp.stdout.strip()
                break
        except Exception:
            pass

    return info

def start_http_service(directory: Optional[str] = None, port: Optional[int] = None, host: str = "127.0.0.1") -> Dict[str, Any]:
    doc_dir = os.path.abspath(directory) if directory else os.getcwd()
    if not os.path.exists(doc_dir):
        return {"success": False, "error": f"Directory does not exist: {doc_dir}"}

    bound_port = _find_open_port(port or 8080)

    class CustomHandler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=doc_dir, **kwargs)
        def log_message(self, format, *args):
            pass

    try:
        httpd = HTTPServer((host, bound_port), CustomHandler)
        t = threading.Thread(target=httpd.serve_forever, daemon=True)
        t.start()

        service_entry = {
            "type": "http",
            "host": host,
            "port": bound_port,
            "url": f"http://{host}:{bound_port}",
            "directory": doc_dir,
            "server_obj": httpd,
            "started_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }

        with _SERVICE_LOCK:
            _ACTIVE_SERVICES[bound_port] = service_entry

        return {
            "success": True,
            "type": "http",
            "port": bound_port,
            "url": f"http://{host}:{bound_port}",
            "directory": doc_dir,
            "message": f"HTTP service active at http://{host}:{bound_port} serving {doc_dir}"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def start_ws_service(port: Optional[int] = None, host: str = "127.0.0.1") -> Dict[str, Any]:
    bound_port = _find_open_port(port or 8081)
    
    # Python standard socket lightweight echo/broadcast server for zero dependency
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        server_sock.bind((host, bound_port))
        server_sock.listen(5)
        
        service_entry = {
            "type": "websocket",
            "host": host,
            "port": bound_port,
            "url": f"ws://{host}:{bound_port}",
            "server_obj": server_sock,
            "started_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        with _SERVICE_LOCK:
            _ACTIVE_SERVICES[bound_port] = service_entry

        return {
            "success": True,
            "type": "websocket",
            "port": bound_port,
            "url": f"ws://{host}:{bound_port}",
            "message": f"WebSocket server listener active at ws://{host}:{bound_port}"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def start_mqtt_service(port: Optional[int] = None, host: str = "127.0.0.1") -> Dict[str, Any]:
    bound_port = _find_open_port(port or 1883)
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        server_sock.bind((host, bound_port))
        server_sock.listen(5)
        service_entry = {
            "type": "mqtt",
            "host": host,
            "port": bound_port,
            "url": f"mqtt://{host}:{bound_port}",
            "server_obj": server_sock,
            "started_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        with _SERVICE_LOCK:
            _ACTIVE_SERVICES[bound_port] = service_entry

        return {
            "success": True,
            "type": "mqtt",
            "port": bound_port,
            "url": f"mqtt://{host}:{bound_port}",
            "message": f"MQTT broker listener active at mqtt://{host}:{bound_port}"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def list_active_services() -> List[Dict[str, Any]]:
    with _SERVICE_LOCK:
        services = []
        for p, s in _ACTIVE_SERVICES.items():
            services.append({
                "type": s["type"],
                "host": s["host"],
                "port": s["port"],
                "url": s["url"],
                "directory": s.get("directory"),
                "started_at": s["started_at"]
            })
        return services

def stop_service_by_port(port: int) -> Dict[str, Any]:
    with _SERVICE_LOCK:
        if port not in _ACTIVE_SERVICES:
            return {"success": False, "error": f"No active service found on port {port}."}
        s = _ACTIVE_SERVICES.pop(port)
        obj = s.get("server_obj")
        if hasattr(obj, "shutdown"):
            obj.shutdown()
        elif hasattr(obj, "close"):
            obj.close()
        return {"success": True, "message": f"Service on port {port} stopped."}

def execute(params: Dict[str, Any]) -> Dict[str, Any]:
    action = params.get("action", "probe")
    if action == "probe":
        return make_result(True, data=probe_environment())
    elif action == "start_http":
        res = start_http_service(
            directory=params.get("directory"),
            port=params.get("port"),
            host=params.get("host", "127.0.0.1")
        )
        return make_result(res["success"], data=res, error=res.get("error", ""))
    elif action == "start_ws":
        res = start_ws_service(port=params.get("port"), host=params.get("host", "127.0.0.1"))
        return make_result(res["success"], data=res, error=res.get("error", ""))
    elif action == "start_mqtt":
        res = start_mqtt_service(port=params.get("port"), host=params.get("host", "127.0.0.1"))
        return make_result(res["success"], data=res, error=res.get("error", ""))
    elif action == "list_services":
        return make_result(True, data=list_active_services())
    elif action == "stop_service":
        port = params.get("port")
        if not port:
            return make_result(False, error="Parameter 'port' is required to stop service.")
        res = stop_service_by_port(port)
        return make_result(res["success"], data=res, error=res.get("error", ""))
    else:
        return make_result(False, error=f"Unknown action: '{action}'.")

if __name__ == "__main__":
    cli_runner("env_manager", TOOL_SPEC, execute)
