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
        cfg_turns = self.client.config.get("harness", {}).get("max_turns", 25)
        self.max_turns = max_turns if max_turns != 15 else cfg_turns
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

        from core.project import get_current_project
        proj = get_current_project()

        system_instruction = self.role.system_prompt + "\n" + proj.format_prompt_injection()
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

                    if isinstance(fn_args, dict):
                        if "cwd" in fn_args and not fn_args["cwd"]:
                            fn_args["cwd"] = proj.path
                        elif "cwd" not in fn_args:
                            fn_args["cwd"] = proj.path

                        # Resolve relative file paths to active project path
                        if "path" in fn_args and isinstance(fn_args["path"], str) and not os.path.isabs(fn_args["path"]):
                            fn_args["path"] = os.path.join(proj.path, fn_args["path"])

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

                    # Prepare tool result for message payload
                    clean_result = tool_result
                    b64_img = None
                    if isinstance(tool_result, dict) and isinstance(tool_result.get("data"), dict):
                        b64_img = tool_result["data"].get("screenshot_base64")
                        if b64_img:
                            # Avoid duplicate massive base64 in tool string
                            clean_result = dict(tool_result)
                            clean_data = dict(clean_result["data"])
                            clean_data["screenshot_base64"] = f"<PNG image {clean_data.get('screenshot_size_bytes', 0)} bytes captured>"
                            clean_result["data"] = clean_data

                    messages.append({
                        "role": "tool",
                        "tool_call_id": call_id,
                        "content": json.dumps(clean_result, ensure_ascii=False)
                    })

                    # Inject multimodal visual feedback turn if image was produced
                    if b64_img:
                        messages.append({
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": (
                                        f"[视觉多模态感知回传 - Visual Render Observation]\n"
                                        f"以下是浏览器无头环境实时渲染截取的真实视口画面（保存路径: {tool_result['data'].get('screenshot_path')}）。\n"
                                        f"请从专业设计师与资深图形学工程师视角审查该画面：\n"
                                        f"1. 3D 场景光影是否清晰可见？是否存在画面过暗（黑黢麻黑）或过曝？\n"
                                        f"2. 几何体模型结构是否饱满、材质金属度/粗糙度是否合理？\n"
                                        f"3. HUD 与文字排版是否协调？如发现任何视觉缺陷，请立即针对性修改代码优化！"
                                    )
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {"url": f"data:image/png;base64,{b64_img}"}
                                }
                            ]
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
            from core.project import get_current_project
            proj = get_current_project()
            if not os.path.isabs(output_file) and proj and proj.path:
                target_p = os.path.join(proj.path, output_file)
            else:
                target_p = output_file

            if not os.path.exists(target_p) or os.path.getsize(target_p) == 0:
                return False, f"未检测到指定的产出文件 `{output_file}`（预期绝对路径: {target_p}）。请使用 write 工具创建并写入该文件。"

        if rules.get("require_diff", False):
            diff_res = tools.execute_tool("git_tool", {"action": "diff"})
            unstaged = diff_res.get("data", {}).get("unstaged_diff", "")
            staged = diff_res.get("data", {}).get("staged_diff", "")
            if not unstaged.strip() and not staged.strip():
                return False, "门禁要求代码变更（diff），但未检测到任何代码修改。"

        if rules.get("require_burn_down", False):
            from core.acceptance import evaluate_burn_down_gate
            from core.project import get_current_project
            proj = get_current_project()
            for cand in [
                os.path.join(proj.path, "deliverables", "acceptance_criteria.md"),
                os.path.join(proj.path, "acceptance_criteria.md")
            ]:
                if os.path.exists(cand):
                    burn_ok, burn_reason, _ = evaluate_burn_down_gate(cand)
                    if not burn_ok:
                        return False, burn_reason
                    break

        return True, "Output gate passed."
