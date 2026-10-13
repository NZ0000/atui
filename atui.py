#!/usr/bin/env python3
"""
ATUI — Autonomous Terminal User & Agent Harness.

Supports both CLI argument execution and Python function invocation:
1. Positional CLI:
   python atui.py <智能体.md> <本次任务提示词> <结果汇总.md> [使用的模型名称]
2. Named Flag CLI:
   python atui.py --agent <智能体.md> --task <任务提示词> --output <结果汇总.md> [--model <模型>]
3. Full Multi-Agent Lifecycle Pipeline CLI:
   python atui.py --pipeline --task <任务提示词> [--output <结果汇总.md>] [--model <模型>]
4. Python Function Calling:
   from atui import run_agent, run_pipeline, run_tool
"""

import sys
import os
import json
import argparse
from typing import Dict, Any, Optional, Callable

# Ensure current directory is on PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.role import Role
from core.harness import AgentHarness
from core.pipeline import PipelineOrchestrator
from core.event_bus import default_bus, Event, EventType
import tools
from api.service import (
    run_single_agent,
    run_pipeline_workflow,
    list_available_agents,
    list_available_tools,
    execute_tool_api
)

# Expose top-level programmatic functions
run_agent = run_single_agent
run_pipeline = run_pipeline_workflow
run_tool = execute_tool_api

def _format_event_printer(event: Event):
    """Console printer for CLI real-time streaming feedback."""
    t = event.type
    agent = f"[{event.agent_name}]" if event.agent_name else "[System]"
    if t == EventType.AGENT_START.value:
        print(f"\n🚀 {agent} 启动智能体: {event.data.get('task')[:60]}... (模型: {event.data.get('model')})")
    elif t == EventType.TOOL_CALL.value:
        tool_name = event.data.get("tool")
        args_brief = str(event.data.get("args", {}))
        if len(args_brief) > 80:
            args_brief = args_brief[:77] + "..."
        print(f"  🔧 {agent} 调用工具: \033[36m{tool_name}\033[0m 参数: {args_brief}")
    elif t == EventType.TOOL_RESULT.value:
        res = event.data.get("result", {})
        status_icon = "✅" if res.get("success") else "❌"
        tool_name = event.data.get("tool")
        print(f"  {status_icon} 工具执行完成: {tool_name}")
    elif t == EventType.GATE_CHECK.value:
        passed = event.data.get("passed")
        status_str = "\033[32m通过\033[0m" if passed else "\033[31m未通过\033[0m"
        print(f"  🚪 {agent} 产出门禁检查: {status_str} ({event.data.get('reason')})")
    elif t == EventType.TDD_CYCLE.value:
        phase = event.data.get("phase") or event.data.get("status")
        print(f"  🧪 {agent} TDD 循环事件: \033[33m{phase}\033[0m")
    elif t == EventType.GIT_ACTION.value:
        act = event.data.get("action")
        print(f"  🌿 {agent} Git 动作: \033[35m{act}\033[0m")
    elif t == EventType.PIPELINE_STEP.value:
        stage = event.data.get("stage")
        print(f"\n======================================================\n📋 流水线阶段: \033[1;34m{stage}\033[0m\n======================================================")
    elif t == EventType.AGENT_FINISH.value:
        print(f"🏁 {agent} 智能体执行结束 (耗时步数: {event.data.get('turns')})")

def main():
    raw_args = sys.argv[1:]

    default_bus.subscribe(_format_event_printer)

    if len(raw_args) >= 3 and not raw_args[0].startswith("-"):
        first_arg = raw_args[0]
        if first_arg.lower() in ("pipeline", "all"):
            task = raw_args[1]
            output = raw_args[2]
            model = raw_args[3] if len(raw_args) > 3 else None
            print(f"[*] 启动全生命周期流水线...")
            res = run_pipeline(task=task, output_file=output, model=model)
            print("\n执行结果：\n" + json.dumps(res, ensure_ascii=False, indent=2))
            sys.exit(0 if res.get("success") else 1)
        else:
            agent_md = raw_args[0]
            task = raw_args[1]
            output = raw_args[2]
            model = raw_args[3] if len(raw_args) > 3 else None

            print(f"[*] 调度单智能体: {agent_md} -> {output}")
            res = run_agent(agent_file_or_name=agent_md, task=task, output_file=output, model=model)
            print("\n执行结果：\n" + json.dumps(res, ensure_ascii=False, indent=2))
            sys.exit(0 if res.get("success") else 1)

    parser = argparse.ArgumentParser(
        prog="atui",
        description="ATUI — Autonomous Terminal User & Agent Harness"
    )
    parser.add_argument("positional_agent", nargs="?", default=None, help="智能体角色文件（.md或.json）")
    parser.add_argument("positional_task", nargs="?", default=None, help="本次任务提示词")
    parser.add_argument("positional_output", nargs="?", default=None, help="产出结果汇总文件（.md）")
    parser.add_argument("positional_model", nargs="?", default=None, help="使用的模型名称")

    parser.add_argument("--agent", "-a", type=str, default=None, help="指定智能体角色配置（例如 agents/coder.md）")
    parser.add_argument("--task", "-t", type=str, default=None, help="本次任务提示词")
    parser.add_argument("--output", "-o", type=str, default="deliverables/summary.md", help="产出结果文件路径")
    parser.add_argument("--model", "-m", type=str, default=None, help="使用的模型名称（覆盖默认配置）")
    parser.add_argument("--pipeline", "-p", action="store_true", help="启动全生命周期多智能体流水线 (Plan->Code->Test->Git->Delivery)")
    parser.add_argument("--list-agents", action="store_true", help="列出所有可用智能体角色")
    parser.add_argument("--list-tools", action="store_true", help="列出所有可用插件工具")

    args = parser.parse_args()

    if args.list_agents:
        agents = list_available_agents()
        print(json.dumps(agents, ensure_ascii=False, indent=2))
        sys.exit(0)

    if args.list_tools:
        avail_tools = list_available_tools()
        print(json.dumps(avail_tools, ensure_ascii=False, indent=2))
        sys.exit(0)

    agent_target = args.agent or args.positional_agent
    task_prompt = args.task or args.positional_task
    output_dest = args.output or args.positional_output
    model_name = args.model or args.positional_model

    if args.pipeline:
        if not task_prompt:
            print("[错误] 启动流水线模式必须提供任务提示词 (--task)", file=sys.stderr)
            sys.exit(1)
        res = run_pipeline(task=task_prompt, output_file=output_dest, model=model_name)
        print("\n流水线执行结果：\n" + json.dumps(res, ensure_ascii=False, indent=2))
        sys.exit(0 if res.get("success") else 1)

    if agent_target and task_prompt:
        res = run_agent(agent_file_or_name=agent_target, task=task_prompt, output_file=output_dest, model=model_name)
        print("\n智能体执行结果：\n" + json.dumps(res, ensure_ascii=False, indent=2))
        sys.exit(0 if res.get("success") else 1)

    parser.print_help()

if __name__ == "__main__":
    main()
