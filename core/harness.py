"""
Single Agent Harness Loop.
Executes an agent (Role) with its designated tools and permissions.
Enforces Rule 8 output gates (must produce required .md artifact or diff),
and retries within the harness loop until the gate is satisfied.
"""

import os
import json
import time
from typing import Dict, Any, List, Optional, Union
import tools
from core.role import Role
from core.llm import LLMClient, default_client
from core.event_bus import default_bus, EventType

class AgentHarness:
    def __init__(
        self,
        role: Union[Role, str],
        model: Optional[str] = None,
        llm_client: Optional[LLMClient] = None,
        max_turns: int = 15,
        max_gate_retries: int = 3
    ):
        if isinstance(role, str):
            self.role = Role.from_file(role)
        else:
            self.role = role

        self.model = model or self.role.model
        self.client = llm_client or default_client
        self.max_turns = max_turns
        self.max_gate_retries = max_gate_retries

    def run(
        self,
        task: str,
        output_file: Optional[str] = None,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        default_bus.publish(
            EventType.AGENT_START,
            {"task": task, "output_file": output_file, "model": self.model},
            self.role.name
        )

        allowed_tools = self.role.tools
        tool_specs = tools.get_tool_specs(allowed_tools)

        system_instruction = self.role.system_prompt
        if output_file:
            system_instruction += (
                f"\n\n[MANDATORY OUTPUT REQUIREMENT]\n"
                f"You MUST use the 'write' tool to produce your final results in the file: `{output_file}`.\n"
                f"Failure to produce this file will result in a failed gate check."
            )

        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": system_instruction}
        ]

        user_content = f"任务要求：\n{task}"
        if context:
            user_content += f"\n\n上下文背景：\n{context}"
        if output_file:
            user_content += f"\n\n请将最终结论与详细产出写入文件：{output_file}"

        messages.append({"role": "user", "content": user_content})

        turn = 0
        gate_retries = 0

        while turn < self.max_turns:
            turn += 1
            default_bus.publish(EventType.AGENT_STEP, {"turn": turn}, self.role.name)

            response = self.client.chat_completion(
                messages=messages,
                tools=tool_specs if tool_specs else None,
                model=self.model,
                timeout=90
            )

            if not response.get("success"):
                error_msg = response.get("error", "Unknown LLM error")
                default_bus.publish(EventType.LOG, {"error": error_msg}, self.role.name)
                messages.append({"role": "system", "content": f"LLM error: {error_msg}. Please retry."})
                continue

            msg = response.get("message", {})
            messages.append(msg)

            tool_calls = msg.get("tool_calls")
            if tool_calls and len(tool_calls) > 0:
                for tc in tool_calls:
                    call_id = tc.get("id", f"call_{int(time.time()*1000)}")
                    fn_name = tc.get("function", {}).get("name", "")
                    fn_args_raw = tc.get("function", {}).get("arguments", "{}")

                    try:
                        fn_args = json.loads(fn_args_raw) if isinstance(fn_args_raw, str) else fn_args_raw
                    except Exception as e:
                        fn_args = {"_raw": fn_args_raw, "_parse_error": str(e)}

                    default_bus.publish(
                        EventType.TOOL_CALL,
                        {"tool": fn_name, "args": fn_args, "call_id": call_id},
                        self.role.name
                    )

                    if not self.role.is_tool_allowed(fn_name):
                        tool_result = {
                            "success": False,
                            "error": f"Permission denied: Tool '{fn_name}' is not allowed for role '{self.role.name}'."
                        }
                    else:
                        tool_result = tools.execute_tool(fn_name, fn_args)

                    default_bus.publish(
                        EventType.TOOL_RESULT,
                        {"tool": fn_name, "call_id": call_id, "result": tool_result},
                        self.role.name
                    )

                    messages.append({
                        "role": "tool",
                        "tool_call_id": call_id,
                        "content": json.dumps(tool_result, ensure_ascii=False)
                    })
                continue

            gate_ok, gate_reason = self._check_output_gate(output_file)
            default_bus.publish(
                EventType.GATE_CHECK,
                {"passed": gate_ok, "reason": gate_reason, "retry": gate_retries},
                self.role.name
            )

            if gate_ok:
                default_bus.publish(EventType.AGENT_FINISH, {"success": True, "turns": turn}, self.role.name)
                return {
                    "success": True,
                    "agent": self.role.name,
                    "turns": turn,
                    "output_file": output_file,
                    "last_message": msg.get("content", ""),
                    "messages": messages
                }
            else:
                gate_retries += 1
                if gate_retries > self.max_gate_retries:
                    return {
                        "success": False,
                        "agent": self.role.name,
                        "turns": turn,
                        "error": f"Output gate failed after {self.max_gate_retries} retries: {gate_reason}",
                        "last_message": msg.get("content", ""),
                        "messages": messages
                    }

                messages.append({
                    "role": "user",
                    "content": (
                        f"[GATE CHECK FAILED]\n"
                        f"{gate_reason}\n"
                        f"请立即使用相应工具完成产出（例如使用write工具写入{output_file}），满足门禁要求后方可退出。"
                    )
                })

        return {
            "success": False,
            "agent": self.role.name,
            "turns": turn,
            "error": f"Agent exceeded maximum turn limit ({self.max_turns}).",
            "messages": messages
        }

    def _check_output_gate(self, output_file: Optional[str]) -> (bool, str):
        rules = self.role.gate_rules

        if rules.get("require_output_file", True) and output_file:
            if not os.path.exists(output_file):
                return False, f"未检测到指定的产出文件 `{output_file}`。请使用 write 工具创建并写入该文件。"
            if os.path.getsize(output_file) == 0:
                return False, f"产出文件 `{output_file}` 内容为空。必须包含有效内容。"

        if rules.get("require_diff", False):
            diff_res = tools.execute_tool("git_tool", {"action": "diff"})
            unstaged = diff_res.get("data", {}).get("unstaged_diff", "")
            staged = diff_res.get("data", {}).get("staged_diff", "")
            if not unstaged.strip() and not staged.strip():
                return False, "门禁要求代码变更（diff），但未检测到任何代码修改。"

        return True, "Output gate passed."
