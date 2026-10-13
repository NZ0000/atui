#!/usr/bin/env python3
"""
ATUI — Autonomous Terminal User & Agent Harness.

Features:
1. Claude-Code Style Interactive Terminal (REPL) when run without arguments or with -i/--interactive.
2. Unified Project Directory Management: set, switch, record, open project, and auto-inject rules.
3. Positional CLI:
   python atui.py <智能体.md> <本次任务提示词> <结果汇总.md> [使用的模型名称]
4. Named Flag CLI:
   python atui.py --agent <智能体.md> --task <任务提示词> [--project <项目目录>] [--output <结果汇总.md>]
5. Full Multi-Agent Lifecycle Pipeline CLI:
   python atui.py --pipeline --task <任务提示词> [--project <项目目录>]
6. Python Function Calling:
   from atui import run_agent, run_pipeline, run_tool, manage_project, switch_project
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
from core.project import manage_project, switch_project, get_current_project, ProjectContext
from core.event_bus import default_bus, Event, EventType
import tools
from api.service import (
    run_single_agent,
    run_pipeline_workflow,
    list_available_agents,
    list_available_tools,
    execute_tool_api,
    run_tools_batch,
    validate_web_code,
    test_browser_page,
    search_web_info
)
from ui.terminal import run_interactive_session, render_markdown, format_event_for_human

# Expose top-level programmatic functions
run_agent = run_single_agent
run_pipeline = run_pipeline_workflow
run_tool = execute_tool_api
run_batch = run_tools_batch
validate_web = validate_web_code
test_browser = test_browser_page
search_web = search_web_info

def _format_event_printer(event: Event):
    """Console printer for CLI feedback."""
    format_event_for_human(event)

def main():
    raw_args = sys.argv[1:]

    # 1. No arguments or interactive flag: Launch Claude Code styled TUI
    if len(raw_args) == 0 or (len(raw_args) == 1 and raw_args[0] in ("-i", "--interactive")):
        run_interactive_session()
        sys.exit(0)

    # 2. Check for quick project management CLI
    if len(raw_args) >= 2 and raw_args[0] in ("project", "cd"):
        res = manage_project("switch", raw_args[1])
        print(f"\033[32m✔ 已切换激活项目目录至:\033[0m {res['project']['path']}")
        if res['project'].get('rules_file'):
            print(f"\033[33m✔ 发现并注入项目规则:\033[0m {res['project']['rules_file']}")
        sys.exit(0)
    elif len(raw_args) == 1 and raw_args[0] in ("project", "pwd"):
        ctx = get_current_project()
        print(f"当前激活项目: {ctx.path} (Git: {ctx.git_branch or '无'}) 规则: {ctx.rules_file or '无'}")
        sys.exit(0)

    # Subscribe human-friendly console output
    default_bus.subscribe(_format_event_printer)

    # 3. Check if user called with standard positional arguments:
    # atui.py <agent.md> <task_prompt> <result_summary.md> [model_name]
    if len(raw_args) >= 3 and not raw_args[0].startswith("-"):
        first_arg = raw_args[0]
        if first_arg.lower() in ("pipeline", "all"):
            task = raw_args[1]
            output = raw_args[2]
            model = raw_args[3] if len(raw_args) > 3 else None
            print(f"\n\033[1;34m[*] 启动全生命周期流水线...\033[0m")
            res = run_pipeline(task=task, output_file=output, model=model)
            if res.get("success"):
                print(f"\n\033[32m✔ 流水线执行成功 (耗时: {res.get('elapsed_seconds')}s)\033[0m")
                print(f"\033[2m📄 最终交付汇总已保存至: {output}\033[0m")
            else:
                print(f"\n\033[31m✖ 流水线失败: {res.get('error')}\033[0m")
            sys.exit(0 if res.get("success") else 1)
        else:
            agent_md = raw_args[0]
            task = raw_args[1]
            output = raw_args[2]
            model = raw_args[3] if len(raw_args) > 3 else None

            print(f"\n\033[1;36m[*] 调度智能体: {agent_md} -> {output}\033[0m")
            res = run_agent(agent_file_or_name=agent_md, task=task, output_file=output, model=model)
            if res.get("success"):
                print(f"\n\033[32m✔ 执行完成 (步数: {res.get('turns')})\033[0m")
                render_markdown(res.get("last_message", ""))
                print(f"\033[2m📄 产出报告已保存至: {output}\033[0m")
            else:
                print(f"\n\033[31m✖ 执行异常: {res.get('error')}\033[0m")
                if res.get("last_message"):
                    render_markdown(res.get("last_message"))
            sys.exit(0 if res.get("success") else 1)

    # 4. Standard Argparse CLI
    parser = argparse.ArgumentParser(
        prog="atui",
        description="ATUI — Autonomous Terminal User & Agent Harness"
    )
    parser.add_argument("positional_agent", nargs="?", default=None, help="智能体角色文件（.md或.json）")
    parser.add_argument("positional_task", nargs="?", default=None, help="本次任务提示词")
    parser.add_argument("positional_output", nargs="?", default=None, help="产出结果汇总文件（.md）")
    parser.add_argument("positional_model", nargs="?", default=None, help="使用的模型名称")

    parser.add_argument("--interactive", "-i", action="store_true", help="启动类似 Claude Code 的交互式终端界面")
    parser.add_argument("--project", "-C", type=str, default=None, help="设置或切换指定项目工作目录（自动加载并注入该项目的 rules）")
    parser.add_argument("--agent", "-a", type=str, default=None, help="指定智能体角色配置（例如 agents/coder.md）")
    parser.add_argument("--task", "-t", type=str, default=None, help="本次任务提示词")
    parser.add_argument("--output", "-o", type=str, default="deliverables/summary.md", help="产出结果文件路径")
    parser.add_argument("--model", "-m", type=str, default=None, help="使用的模型名称（覆盖默认配置）")
    parser.add_argument("--pipeline", "-p", action="store_true", help="启动全生命周期多智能体流水线 (Plan->Code->Test->Git->Delivery)")
    parser.add_argument("--list-agents", action="store_true", help="列出所有可用智能体角色")
    parser.add_argument("--list-tools", action="store_true", help="列出所有可用插件工具")
    parser.add_argument("--json", action="store_true", help="输出完整机器可读的原始 JSON 结果")

    args = parser.parse_args()

    if args.interactive:
        run_interactive_session(
            default_role=args.agent or "orchestrator",
            default_model=args.model
        )
        sys.exit(0)

    if args.project:
        switch_project(args.project)
        print(f"\033[32m✔ 当前项目工作目录已设置为:\033[0m {get_current_project().path}")

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
        if args.json:
            print(json.dumps(res, ensure_ascii=False, indent=2))
        else:
            if res.get("success"):
                print(f"\n\033[32m✔ 流水线执行成功 (耗时: {res.get('elapsed_seconds')}s)\033[0m")
                print(f"\033[2m📄 最终交付报告: {output_dest}\033[0m")
            else:
                print(f"\n\033[31m✖ 流水线失败: {res.get('error')}\033[0m")
        sys.exit(0 if res.get("success") else 1)

    if agent_target and task_prompt:
        res = run_agent(agent_file_or_name=agent_target, task=task_prompt, output_file=output_dest, model=model_name)
        if args.json:
            print(json.dumps(res, ensure_ascii=False, indent=2))
        else:
            if res.get("success"):
                print(f"\n\033[32m✔ 执行完成 (步数: {res.get('turns')})\033[0m")
                render_markdown(res.get("last_message", ""))
                if output_dest:
                    print(f"\033[2m📄 产出记录已保存至: {output_dest}\033[0m")
            else:
                print(f"\n\033[31m✖ 执行异常: {res.get('error')}\033[0m")
                if res.get("last_message"):
                    render_markdown(res.get("last_message"))
        sys.exit(0 if res.get("success") else 1)

    # Default to interactive session if no task provided
    run_interactive_session()

if __name__ == "__main__":
    main()
