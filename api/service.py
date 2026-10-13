"""
API Service Layer for atui.
Provides clean Python programmatic entrypoints, introspection, and event subscriptions
for external clients (Web H5, Electron desktop, Tauri, mobile App, TUI, or REST APIs).
"""

import os
from typing import Dict, Any, List, Optional, Callable
from core.role import Role
from core.harness import AgentHarness
from core.pipeline import PipelineOrchestrator
from core.event_bus import default_bus, Event, EventType
from core.project import (
    manage_project,
    get_current_project,
    switch_project,
    ProjectContext
)
import tools

def list_available_agents(agents_dir: str = "agents") -> List[Dict[str, Any]]:
    results = []
    if not os.path.exists(agents_dir):
        return results

    for f in sorted(os.listdir(agents_dir)):
        if f.endswith((".md", ".json")):
            path = os.path.join(agents_dir, f)
            try:
                role = Role.from_file(path)
                results.append({
                    "id": role.name,
                    "file": f,
                    "path": path,
                    "description": role.description,
                    "model": role.model,
                    "tools": role.tools,
                    "permissions": role.permissions
                })
            except Exception as e:
                results.append({"id": f, "file": f, "error": str(e)})
    return results

def get_agent_info(agent_name_or_file: str, agents_dir: str = "agents") -> Optional[Dict[str, Any]]:
    target_path = agent_name_or_file
    if not os.path.exists(target_path):
        target_path = os.path.join(agents_dir, f"{agent_name_or_file}.md")
        if not os.path.exists(target_path):
            target_path = os.path.join(agents_dir, f"{agent_name_or_file}.json")
            if not os.path.exists(target_path):
                return None

    role = Role.from_file(target_path)
    return role.to_dict()

def list_available_tools() -> List[Dict[str, Any]]:
    results = []
    for name in tools.list_tools():
        tinfo = tools.get_tool(name)
        if tinfo:
            results.append({
                "name": name,
                "description": tinfo["spec"].get("description", ""),
                "parameters": tinfo["spec"].get("parameters", {}),
                "path": tinfo.get("path")
            })
    return results

def execute_tool_api(tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
    return tools.execute_tool(tool_name, params)

def run_tools_batch(calls: List[Dict[str, Any]], stop_on_error: bool = False) -> Dict[str, Any]:
    """Execute multiple tools in batch sequentially or stop on error."""
    return tools.execute_tool("batch_run", {"calls": calls, "stop_on_error": stop_on_error})

def validate_web_code(path: str, content: Optional[str] = None, file_type: str = "auto") -> Dict[str, Any]:
    """Validate HTML, CSS, JS syntax with V8 engine and strict parser."""
    return tools.execute_tool("web_validator", {"path": path, "content": content, "file_type": file_type})

def test_browser_page(url_or_path: str, screenshot_path: Optional[str] = None, wait_ms: int = 2500) -> Dict[str, Any]:
    """Run headless browser test, capture console errors and screenshot."""
    return tools.execute_tool("browser_test", {"url_or_path": url_or_path, "screenshot_path": screenshot_path, "wait_ms": wait_ms})

def search_web_info(query: str, max_results: int = 5, fetch_url: Optional[str] = None) -> Dict[str, Any]:
    """Search the internet for technical code samples, documentation, and references."""
    return tools.execute_tool("web_search", {"query": query, "max_results": max_results, "fetch_url": fetch_url})

def subscribe_events(callback: Callable[[Event], None]):
    default_bus.subscribe(callback)

def unsubscribe_events(callback: Callable[[Event], None]):
    default_bus.unsubscribe(callback)

def run_single_agent(
    agent_file_or_name: str,
    task: str,
    output_file: Optional[str] = None,
    model: Optional[str] = None,
    event_callback: Optional[Callable[[Event], None]] = None
) -> Dict[str, Any]:
    if event_callback:
        subscribe_events(event_callback)

    try:
        agent_path = agent_file_or_name
        if not os.path.exists(agent_path):
            candidate_md = os.path.join("agents", f"{agent_file_or_name}.md")
            if os.path.exists(candidate_md):
                agent_path = candidate_md

        role = Role.from_file(agent_path)
        harness = AgentHarness(role, model=model)
        result = harness.run(task, output_file=output_file)
        return result
    finally:
        if event_callback:
            unsubscribe_events(event_callback)

def run_pipeline_workflow(
    task: str,
    output_file: str = "deliverables/summary.md",
    model: Optional[str] = None,
    event_callback: Optional[Callable[[Event], None]] = None
) -> Dict[str, Any]:
    if event_callback:
        subscribe_events(event_callback)

    try:
        orchestrator = PipelineOrchestrator(model=model)
        result = orchestrator.run_pipeline(task, output_file=output_file, model=model)
        return result
    finally:
        if event_callback:
            unsubscribe_events(event_callback)

def run_concurrent_pipeline_workflow(
    task: str,
    output_file: str = "deliverables/summary.md",
    model: Optional[str] = None,
    max_workers: int = 4,
    event_callback: Optional[Callable[[Event], None]] = None
) -> Dict[str, Any]:
    """Execute distributed concurrent modular multi-agent pipeline."""
    if event_callback:
        subscribe_events(event_callback)

    try:
        from core.concurrent_pipeline import ConcurrentModularPipeline
        pipeline = ConcurrentModularPipeline(model=model, max_workers=max_workers)
        result = pipeline.run_concurrent_pipeline(task, output_file=output_file, model=model)
        return result
    finally:
        if event_callback:
            unsubscribe_events(event_callback)


def run_iteration_pipeline_workflow(
    task: str,
    project_url: str = "",
    target_files: Optional[list] = None,
    output_file: str = "deliverables/iteration_summary.md",
    model: Optional[str] = None,
    max_workers: int = 4,
    event_callback: Optional[Callable[[Event], None]] = None
) -> Dict[str, Any]:
    """
    Execute iteration pipeline on an EXISTING project.

    Analyst reads code + captures multi-angle browser screenshots,
    then concurrent Coders apply targeted fixes, followed by Reviewer
    and Designer visual audit.

    Args:
        task: What to improve/fix (e.g. "修复浮动窗口元素，优化植被遮挡问题").
        project_url: URL of running project (e.g. "http://localhost:8086").
        target_files: List of files to focus on. If None, Analyst auto-detects.
        output_file: Path for iteration summary report.
        model: LLM model override.
        max_workers: Number of concurrent fix workers.
    """
    if event_callback:
        subscribe_events(event_callback)

    try:
        from core.concurrent_pipeline import ConcurrentModularPipeline
        pipeline = ConcurrentModularPipeline(model=model, max_workers=max_workers)
        result = pipeline.run_iteration_pipeline(
            task=task,
            project_url=project_url,
            target_files=target_files,
            output_file=output_file,
            model=model
        )
        return result
    finally:
        if event_callback:
            unsubscribe_events(event_callback)


def interact_browser(
    url: str,
    steps: Optional[list] = None,
    wait_for_load_ms: int = 3000,
    screenshot_path: Optional[str] = None
) -> Dict[str, Any]:
    """Interact with browser: click elements, take multi-angle screenshots."""
    return tools.execute_tool("browser_interact", {
        "url": url,
        "steps": steps,
        "wait_for_load_ms": wait_for_load_ms,
        "screenshot_path": screenshot_path
    })
