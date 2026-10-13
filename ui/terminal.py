"""
Interactive Claude-Code Style Terminal UI for atui.
Provides:
1. Human-friendly, aesthetic terminal interaction (banners, spinners, clean markdown rendering).
2. Live project directory management (/cd, /project, /pwd, rule injection display).
3. Slash command dispatch (/role, /model, /pipeline, /git, /test, /help, /exit).
4. No messy raw JSON dumps — clean, professional developer experience.
"""

import sys
import os
import readline
import shutil
from typing import Optional, Dict, Any

from core.project import get_current_project, switch_project, manage_project
from core.role import Role
from core.harness import AgentHarness
from core.pipeline import PipelineOrchestrator
from core.event_bus import default_bus, Event, EventType
import tools
from api.service import list_available_agents, list_available_tools

# ANSI Color Codes
CYAN = "\033[36m"
BLUE = "\033[34m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
MAGENTA = "\033[35m"
RED = "\033[31m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"

def print_banner(role_name: str, model_name: str):
    proj = get_current_project()
    term_width = min(shutil.get_terminal_size((80, 20)).columns, 90)
    border = "─" * (term_width - 2)

    branch_str = f" ({proj.git_branch})" if proj.is_git else ""
    rule_str = proj.rules_file or "无项目规则"
    
    print(f"\n{CYAN}╭{border}╮{RESET}")
    print(f"{CYAN}│{RESET} {BOLD}▲ ATUI Harness{RESET} — Autonomous Terminal Agent {DIM}(Claude Code Mode){RESET}".ljust(term_width + 10) + f"{CYAN}│{RESET}")
    print(f"{CYAN}│{RESET} {DIM}项目目录 :{RESET} {GREEN}{proj.path}{branch_str}{RESET}".ljust(term_width + 19) + f"{CYAN}│{RESET}")
    print(f"{CYAN}│{RESET} {DIM}规则注入 :{RESET} {YELLOW}{rule_str}{RESET} {DIM}(已自动注入提示词){RESET}".ljust(term_width + 19) + f"{CYAN}│{RESET}")
    print(f"{CYAN}│{RESET} {DIM}当前角色 :{RESET} {MAGENTA}{role_name}{RESET}  │  {DIM}模型 :{RESET} {BLUE}{model_name}{RESET}".ljust(term_width + 28) + f"{CYAN}│{RESET}")
    print(f"{CYAN}╰{border}╯{RESET}")
    print(f"{DIM}输入提示词即可对话；输入 {CYAN}/help{RESET}{DIM} 查看命令，输入 {CYAN}/cd <目录>{RESET}{DIM} 切换项目{RESET}\n")

def format_event_for_human(event: Event):
    t = event.type
    agent = f"[{event.agent_name}]" if event.agent_name else ""
    if t == EventType.AGENT_START.value:
        pass
    elif t == EventType.TOOL_CALL.value:
        tool_name = event.data.get("tool")
        args = event.data.get("args", {})
        # Format concise action descriptions
        desc = ""
        if tool_name == "read":
            desc = f"读取: {args.get('path')}"
        elif tool_name == "write":
            desc = f"写入: {args.get('path')}"
        elif tool_name == "run":
            cmd = args.get("command", "")
            desc = f"终端: {cmd[:60]}" + ("..." if len(cmd) > 60 else "")
        elif tool_name == "git_tool":
            desc = f"Git: {args.get('action')}"
        elif tool_name == "test_runner":
            desc = f"测试: {args.get('target')} ({args.get('mode', 'all')})"
        else:
            brief = str(args)[:50]
            desc = f"{tool_name} {brief}"
        print(f"  {CYAN}●{RESET} ⚙️  {DIM}{agent}{RESET} \033[1m{tool_name}\033[0m ➜ {desc}")
    elif t == EventType.TOOL_RESULT.value:
        res = event.data.get("result", {})
        tool_name = event.data.get("tool")
        if res.get("success"):
            print(f"  {GREEN}✔{RESET} {DIM}{tool_name} 执行成功{RESET}")
        else:
            err = res.get("error", "Failed")
            print(f"  {RED}✖{RESET} {DIM}{tool_name} 失败: {err[:60]}{RESET}")
    elif t == EventType.GATE_CHECK.value:
        passed = event.data.get("passed")
        if passed:
            print(f"  {GREEN}✔ 产出门禁通过{RESET}")
        else:
            print(f"  {YELLOW}⚠ 产出门禁检查: {event.data.get('reason')}{RESET}")
    elif t == EventType.TDD_CYCLE.value:
        phase = event.data.get("phase") or event.data.get("status")
        print(f"  {YELLOW}🧪 TDD 状态:{RESET} {phase}")
    elif t == EventType.GIT_ACTION.value:
        act = event.data.get("action")
        print(f"  {MAGENTA}🌿 Git 审查动作:{RESET} {act}")
        if act in ("rollback_trigger", "rolled_back") and event.data.get("reason"):
            print(f"    {YELLOW}↳ 原因: {str(event.data.get('reason'))[:400]}{RESET}")
    elif t == EventType.PIPELINE_STEP.value:
        stage = event.data.get("stage")
        print(f"\n{BLUE}▶ 流水线步骤:{RESET} {BOLD}{stage}{RESET}")
        # Observability: surface rich payloads (gate failures, consult notes)
        for key in ("failures", "reason", "error", "summary", "detail"):
            val = event.data.get(key)
            if val and key != "stage":
                print(f"  {YELLOW}↳ {key}:{RESET} {str(val)[:500]}")

def render_markdown(text: str):
    """Clean terminal markdown rendering."""
    print()
    lines = text.split("\n")
    for line in lines:
        if line.startswith("# "):
            print(f"\n{BOLD}{CYAN}{line[2:]}{RESET}")
        elif line.startswith("## "):
            print(f"\n{BOLD}{BLUE}{line[3:]}{RESET}")
        elif line.startswith("### "):
            print(f"\n{BOLD}{MAGENTA}{line[4:]}{RESET}")
        elif line.startswith("- ") or line.startswith("* "):
            print(f"  {CYAN}•{RESET} {line[2:]}")
        elif line.startswith("```"):
            print(f"{DIM}{line}{RESET}")
        elif line.startswith("> "):
            print(f"  {DIM}│ {line[2:]}{RESET}")
        else:
            print(line)
    print()

def show_help():
    print(f"\n{BOLD}ATUI 终端命令指引：{RESET}")
    print(f"  {CYAN}/project [path]{RESET}    查看或切换当前激活的项目工作目录")
    print(f"  {CYAN}/cd <path>{RESET}         快捷切换项目工作目录（自动加载并注入该项目的 rules）")
    print(f"  {CYAN}/pwd{RESET}               打印当前项目路径、Git 分支与规则文件")
    print(f"  {CYAN}/rules{RESET}             查看当前项目已注入的规则守则全文")
    print(f"  {CYAN}/role [name]{RESET}        切换角色 (planner, coder, tester, git_agent, delivery, orchestrator)")
    print(f"  {CYAN}/model [name]{RESET}       切换大模型 (如 gemini-2.5-flash-lite, gpt-4o-mini 等)")
    print(f"  {CYAN}/pipeline <任务>{RESET}    在当前项目上启动完整的 TDD 5阶段智能体流水线")
    print(f"  {CYAN}/git [status/diff]{RESET} 审查当前项目的 Git 状态或代码差异")
    print(f"  {CYAN}/test{RESET}              在当前项目运行自动化测试套件")
    print(f"  {CYAN}/tools{RESET}             列出当前已注册的所有 Function Call 插件")
    print(f"  {CYAN}/clear{RESET}             清空终端屏幕")
    print(f"  {CYAN}/exit 或 /quit{RESET}     退出终端\n")

def run_interactive_session(default_role: str = "orchestrator", default_model: Optional[str] = None):
    current_role = default_role
    current_model = default_model or "gemini-2.5-flash-lite"

    # Setup terminal event formatting
    default_bus.subscribe(format_event_for_human)

    print_banner(current_role, current_model)

    while True:
        proj = get_current_project()
        branch_tag = f"[{proj.git_branch}] " if proj.is_git else ""
        prompt_str = f"{BOLD}{CYAN}atui{RESET} {DIM}{branch_tag}{proj.name}{RESET} ({MAGENTA}{current_role}{RESET}) {BOLD}❯{RESET} "

        try:
            user_input = input(prompt_str).strip()
        except (KeyboardInterrupt, EOFError):
            print(f"\n{DIM}退出 ATUI 终端。再见！{RESET}")
            break

        if not user_input:
            continue

        # Handle slash commands
        if user_input.startswith("/"):
            parts = user_input.split(maxsplit=1)
            cmd = parts[0].lower()
            arg = parts[1].strip() if len(parts) > 1 else ""

            if cmd in ("/exit", "/quit"):
                print(f"{DIM}退出 ATUI 终端。再见！{RESET}")
                break
            elif cmd in ("/help", "/?"):
                show_help()
            elif cmd in ("/cd", "/project"):
                if arg:
                    try:
                        new_proj = switch_project(arg)
                        print(f"{GREEN}✔ 已成功切换项目目录至:{RESET} {new_proj.path}")
                        if new_proj.rules_file:
                            print(f"{YELLOW}✔ 发现项目规则文件:{RESET} {new_proj.rules_file} (已自动注入)")
                        else:
                            print(f"{DIM}提示: 该项目未检测到 rule/rule.md 或 AGENTS.md，使用通用守则{RESET}")
                    except Exception as e:
                        print(f"{RED}切换目录失败:{RESET} {e}")
                else:
                    curr = get_current_project()
                    print(f"{CYAN}当前激活项目:{RESET} {curr.path}")
                    print(f"  Git 分支: {curr.git_branch or '非Git仓库'}")
                    print(f"  规则文件: {curr.rules_file or '无'}")
            elif cmd == "/pwd":
                curr = get_current_project()
                print(f"{GREEN}{curr.path}{RESET} {DIM}(Branch: {curr.git_branch}){RESET}")
            elif cmd == "/rules":
                curr = get_current_project()
                if curr.rules:
                    print(f"\n{YELLOW}=== 项目规则 ({curr.rules_file}) ==={RESET}\n{curr.rules}\n")
                else:
                    print(f"{DIM}当前项目没有定义规则文件 (可创建 rule/rule.md 或 AGENTS.md){RESET}")
            elif cmd == "/role":
                if arg:
                    current_role = arg
                    print(f"{GREEN}✔ 已切换当前角色为:{RESET} {BOLD}{current_role}{RESET}")
                else:
                    agents = list_available_agents()
                    print(f"\n{BOLD}可用角色列表：{RESET}")
                    for a in agents:
                        mark = f"{GREEN}*(当前)*{RESET}" if a["id"] == current_role else ""
                        print(f"  • {CYAN}{a['id']}{RESET} {mark}: {a.get('description', '')}")
                    print()
            elif cmd == "/model":
                if arg:
                    current_model = arg
                    print(f"{GREEN}✔ 已切换模型为:{RESET} {BOLD}{current_model}{RESET}")
                else:
                    print(f"当前模型: {BOLD}{current_model}{RESET}")
            elif cmd == "/clear":
                os.system("clear" if os.name == "posix" else "cls")
                print_banner(current_role, current_model)
            elif cmd == "/tools":
                avail = list_available_tools()
                print(f"\n{BOLD}已注册工具插件：{RESET}")
                for t in avail:
                    print(f"  • {CYAN}{t['name']}{RESET}: {t.get('description', '')}")
                print()
            elif cmd == "/git":
                curr = get_current_project()
                act = arg if arg else "status"
                res = tools.execute_tool("git_tool", {"action": act, "cwd": curr.path})
                if res.get("success"):
                    print(f"\n{res.get('data', {}).get('short_status') or res.get('data', {}).get('full_status') or str(res.get('data'))}\n")
                else:
                    print(f"{RED}Git 执行错误: {res.get('error')}{RESET}")
            elif cmd == "/test":
                curr = get_current_project()
                print(f"{DIM}在项目 {curr.path} 中执行测试...{RESET}")
                res = tools.execute_tool("test_runner", {"target": curr.path, "mode": "all", "cwd": curr.path})
                if res.get("data", {}).get("passed"):
                    print(f"{GREEN}✔ 所有测试通过 (PASS){RESET}\n{res.get('data', {}).get('raw_output')}")
                else:
                    print(f"{RED}✖ 测试失败 (FAIL){RESET}\n{res.get('data', {}).get('raw_output')}")
            elif cmd == "/pipeline":
                if not arg:
                    print(f"{YELLOW}用法: /pipeline <任务描述>{RESET}")
                else:
                    print(f"\n{BOLD}{BLUE}🚀 在当前项目启动 TDD 多智能体流水线...{RESET}")
                    orch = PipelineOrchestrator(model=current_model)
                    res = orch.run_pipeline(arg, model=current_model)
                    if res.get("success"):
                        print(f"\n{GREEN}✔ 流水线执行成功！总耗时: {res.get('elapsed_seconds')}s{RESET}")
                        print(f"{DIM}最终交付报告保存在: {res.get('output_file')}{RESET}")
                    else:
                        print(f"\n{RED}✖ 流水线失败阶段: {res.get('stage_failed')} 错误: {res.get('error')}{RESET}")
            else:
                print(f"{RED}未知命令: {cmd}，输入 /help 查看支持的命令{RESET}")
            continue

        # Normal prompt execution
        print(f"\n{DIM}智能体思考中...{RESET}")
        try:
            agent_file = os.path.join("agents", f"{current_role}.md")
            if not os.path.exists(agent_file):
                agent_file = current_role
            role = Role.from_file(agent_file)
            harness = AgentHarness(role, model=current_model)
            
            output_dest = os.path.join("deliverables", f"{current_role}_output.md")
            res = harness.run(user_input, output_file=output_dest)

            if res.get("success"):
                reply = res.get("last_message", "")
                render_markdown(reply)
                if os.path.exists(output_dest):
                    print(f"{DIM}📄 结构化产出已记录在: {output_dest}{RESET}\n")
            else:
                print(f"\n{RED}智能体执行受阻:{RESET} {res.get('error')}\n")
                if res.get("last_message"):
                    render_markdown(res.get("last_message"))
        except Exception as e:
            print(f"\n{RED}执行异常:{RESET} {e}\n")

if __name__ == "__main__":
    run_interactive_session()
