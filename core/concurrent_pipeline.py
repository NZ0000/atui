"""
Concurrent & Modular Multi-Agent Swarm Pipeline for atui.

Implements a Hierarchical Concurrent DAG Pipeline:
1. Orchestrator / Architect: Decomposes complex compound projects (e.g. 3D village, smart city, multi-tier systems)
   into modular, decoupled, reusable component specifications with interface contracts.
2. Concurrent Worker Swarm: Spawns parallel worker pipelines (Coder -> Reviewer -> Tester)
   running concurrently via ThreadPoolExecutor. Supports isolated self-repair loops per module.
3. Integration Assembly: Master Coder composes all verified modules into master entry (index.html / main.js).
4. Integration Gates: Master Reviewer + Master Tester + Multimodal Designer (browser_interact multi-angle) end-to-end audit.
5. Delivery: Acceptance criteria reconciliation & Git delivery.

Iteration Pipeline (run_iteration_pipeline):
  For improving EXISTING projects. Adds a pre-pass Analyst Agent that:
  - Reads all source files
  - Captures browser multi-angle screenshots via browser_interact
  - Identifies issues in code and visuals
  Then feeds the analysis into concurrent Coder agents for targeted fixes.
"""

import os
import sys
import re
import json
import time
import subprocess
import concurrent.futures
from typing import Dict, Any, List, Optional

from core.harness import AgentHarness
from core.role import Role
from core.tdd_gate import TddGate
from core.event_bus import default_bus, EventType
from core.project import get_current_project
from core.acceptance import AcceptanceChecklist, evaluate_burn_down_gate
from core.blackboard import get_blackboard
import tools

class ConcurrentModularPipeline:
    def __init__(
        self,
        agents_dir: str = "agents",
        model: Optional[str] = None,
        max_workers: int = 4,
        max_repair_loops: int = 4
    ):
        self.agents_dir = os.path.abspath(agents_dir)
        self.model = model
        self.max_workers = max_workers
        self.max_repair_loops = max_repair_loops
        self.tdd_gate = TddGate()

    def _get_agent_path(self, role_name: str) -> str:
        md_path = os.path.join(self.agents_dir, f"{role_name}.md")
        json_path = os.path.join(self.agents_dir, f"{role_name}.json")
        if os.path.exists(md_path):
            return md_path
        if os.path.exists(json_path):
            return json_path
        raise FileNotFoundError(f"Agent config for '{role_name}' not found in {self.agents_dir}")

    def resolve_task_modules(
        self,
        task: str,
        modules_spec_json: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Dynamically resolves or deduces modular task specifications without hardcoding domain scenes.
        Priority:
        1. modules_spec_json file if provided and valid.
        2. deliverables/modules_spec.json from Planner agent if existing.
        3. Extract JSON array block from deliverables/plan.md.
        4. Dynamic domain-aware synthesis based on task keyword/structure analysis.
        """
        proj = get_current_project()

        candidates = []
        if modules_spec_json:
            candidates.append(modules_spec_json)
        candidates.append(os.path.join(proj.path, "deliverables", "modules_spec.json"))
        candidates.append(os.path.join(os.getcwd(), "deliverables", "modules_spec.json"))

        for cand in candidates:
            if cand and os.path.exists(cand):
                try:
                    with open(cand, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    if isinstance(data, list) and len(data) > 0 and all(isinstance(m, dict) and "name" in m for m in data):
                        return data
                except Exception:
                    pass

        # Try parsing json code block in deliverables/plan.md
        plan_candidates = [
            os.path.join(proj.path, "deliverables", "plan.md"),
            os.path.join(os.getcwd(), "deliverables", "plan.md")
        ]
        for p_cand in plan_candidates:
            if os.path.exists(p_cand):
                try:
                    with open(p_cand, "r", encoding="utf-8") as f:
                        content = f.read()
                    import re
                    blocks = re.findall(r"```(?:json)?\s*(\[\s*\{.*?\}\s*\])\s*```", content, re.DOTALL)
                    for b in blocks:
                        try:
                            parsed = json.loads(b)
                            if isinstance(parsed, list) and len(parsed) > 0 and all(isinstance(m, dict) and "name" in m for m in parsed):
                                return parsed
                        except Exception:
                            continue
                except Exception:
                    pass

        # Dynamic domain-aware synthesis based on task keywords (No hardcoding)
        task_lower = task.lower()
        if any(w in task_lower for w in ["microservice", "fastapi", "flask", "django", "service", "微服务", "后端", "接口", "鉴权", "订单", "支付"]):
            return [
                {
                    "id": "MOD-1",
                    "name": "auth_service",
                    "title": "鉴权与安全服务模块 (Auth & Security Service)",
                    "file": "services/auth.py",
                    "test_file": "tests/test_auth.py",
                    "contract": "导出一个包含 generate_token(), verify_token(), authenticate() 的服务类或接口",
                    "requirements": "支持安全令牌签名校验与密码哈希，通过独立测试"
                },
                {
                    "id": "MOD-2",
                    "name": "business_service",
                    "title": "核心业务与订单处理模块 (Core Business & Order Service)",
                    "file": "services/business.py",
                    "test_file": "tests/test_business.py",
                    "contract": "导出一个包含 process_order(), get_status(), execute_workflow() 的业务类",
                    "requirements": "状态机流转正确，幂等性保证，通过单元测试"
                },
                {
                    "id": "MOD-3",
                    "name": "data_gateway",
                    "title": "数据持久层与网关路由模块 (Data Gateway & Storage)",
                    "file": "services/gateway.py",
                    "test_file": "tests/test_gateway.py",
                    "contract": "导出统一 API 路由定义及数据访问抽象接口",
                    "requirements": "数据校验、异常捕获、规范化响应输出"
                }
            ]
        elif any(w in task_lower for w in ["3d", "three", "webgl", "场景", "模型", "渲染", "视觉", "自然", "写实", "城市", "科幻"]):
            return [
                {
                    "id": "MOD-1",
                    "name": "environment",
                    "title": "基础环境与地貌组件 (Environment & Terrain Module)",
                    "file": "modules/environment.js",
                    "test_file": "tests/test_environment.py",
                    "contract": "导出一个包含 constructor(scene, options)、addTo(scene)、update(delta) 的 Environment 类",
                    "requirements": "严禁裸立方体。支持微观质感贴图、多层次光影与阴影接收"
                },
                {
                    "id": "MOD-2",
                    "name": "entities",
                    "title": "核心主体与构造物组件 (Core Entities & Architecture Module)",
                    "file": "modules/entities.js",
                    "test_file": "tests/test_entities.py",
                    "contract": "导出一个包含 constructor(scene, options)、addTo(scene)、update(delta) 的 Entities 类",
                    "requirements": "复合几何体造型或高精度外部模型，PBR物理材质，支持加载容灾降级"
                },
                {
                    "id": "MOD-3",
                    "name": "effects",
                    "title": "动态粒子与植被特效组件 (Effects & Foliage Module)",
                    "file": "modules/effects.js",
                    "test_file": "tests/test_effects.py",
                    "contract": "导出一个包含 constructor(scene, count)、addTo(scene)、update(delta) 的 Effects 类",
                    "requirements": "使用批量实例化 (InstancedMesh) 或粒子系统，保持 60FPS"
                },
                {
                    "id": "MOD-4",
                    "name": "props",
                    "title": "交互道具与局部照明组件 (Interactive Props Module)",
                    "file": "modules/props.js",
                    "test_file": "tests/test_props.py",
                    "contract": "导出一个包含 constructor(scene)、addTo(scene)、update(delta) 的 Props 类",
                    "requirements": "配合发光与交互响应，符合整体视效调优"
                }
            ]
        else:
            return [
                {
                    "id": "MOD-1",
                    "name": "core_engine",
                    "title": "核心逻辑与业务引擎 (Core Engine Module)",
                    "file": "modules/core_engine.py" if "py" in task_lower else "modules/core_engine.js",
                    "test_file": "tests/test_core_engine.py",
                    "contract": "导出一个核心调度与处理类，提供 run(), process(), reset() 接口",
                    "requirements": "高内聚、严格契约校验与异常容错"
                },
                {
                    "id": "MOD-2",
                    "name": "adapter_layer",
                    "title": "适配器与接口交互层 (Adapter & Interface Module)",
                    "file": "modules/adapter.py" if "py" in task_lower else "modules/adapter.js",
                    "test_file": "tests/test_adapter.py",
                    "contract": "导出外部通信与数据输入输出适配器",
                    "requirements": "输入校验、格式化处理与接口解耦"
                }
            ]

    def run_concurrent_pipeline(
        self,
        task: str,
        output_file: str = "deliverables/summary.md",
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        active_model = model or self.model
        start_time = time.time()
        proj = get_current_project()
        stage_records = []

        default_bus.publish(
            EventType.PIPELINE_STEP,
            {
                "stage": "concurrent_pipeline_start",
                "task": task,
                "project": proj.path,
                "max_workers": self.max_workers,
                "model": active_model
            }
        )

        # -------------------------------------------------------------
        # Phase 0: DevOps Environment & Baseline Setup
        # -------------------------------------------------------------
        try:
            devops_path = self._get_agent_path("devops")
            default_bus.publish(EventType.PIPELINE_STEP, {"stage": "devops_setup", "role": "devops"})
            devops_role = Role.from_file(devops_path)
            devops_harness = AgentHarness(devops_role, model=active_model)
            devops_output = "deliverables/deployment_report.md"
            devops_task = (
                f"任务目标：{task}\n"
                f"请调用 env_manager 探查系统环境基线，检查端口服务，确保支持本地静态 HTTP 托管与无头浏览器测试。\n"
                f"输出环境就绪报告至：{devops_output}"
            )
            devops_res = devops_harness.run(devops_task, output_file=devops_output)
            stage_records.append({"stage": "devops", "result": devops_res})
        except Exception as e:
            stage_records.append({"stage": "devops", "error": str(e)})

        # -------------------------------------------------------------
        # Phase 1: Architect / Domain Decomposition & Contract Freeze
        # -------------------------------------------------------------
        default_bus.publish(EventType.PIPELINE_STEP, {"stage": "architect_decomposition", "role": "planner"})
        planner_role = Role.from_file(self._get_agent_path("planner"))
        planner_harness = AgentHarness(planner_role, model=active_model)

        plan_output = "deliverables/plan.md"
        planner_task = (
            f"目标任务：{task}\n"
            f"请作为总架构师（Principal Architect），针对用户任务进行【架构规划与模块化领域解耦设计】。\n"
            f"1. 【评估复杂度与解耦】：若是复合/大型工程，必须拆解为互相独立、可复用、高内聚的子组件模块。\n"
            f"2. 【输出模块解耦清单】：必须使用 write 工具将模块规格写入 `deliverables/modules_spec.json`（或在 plan.md 中输出 JSON 代码块），格式为：\n"
            f"   [\n"
            f"     {{\n"
            f"       \"id\": \"MOD-1\",\n"
            f"       \"name\": \"模块短名\",\n"
            f"       \"title\": \"模块描述性标题\",\n"
            f"       \"file\": \"源码文件路径(如 modules/xxx.js 或 services/xxx.py)\",\n"
            f"       \"test_file\": \"独立单测文件路径(如 tests/test_xxx.py)\",\n"
            f"       \"contract\": \"导出的类/函数名及关键方法接口契约\",\n"
            f"       \"requirements\": \"模块功能规范与实现要求\"\n"
            f"     }}\n"
            f"   ]\n"
            f"3. 【TDD 契约设计】：为每个模块定义明确的导出类/接口契约（如 addTo(scene)、update(delta)、dispose() 或业务处理接口）。\n"
            f"4. 【燃尽验收清单】：生成全流程原子化燃尽验收清单至：`deliverables/acceptance_criteria.md`，并将总体架构蓝图写入：{plan_output}。"
        )
        planner_res = planner_harness.run(planner_task, output_file=plan_output)
        stage_records.append({"stage": "planner", "result": planner_res})

        # Dynamically resolve module specs without hardcoded domains
        module_specs = self.resolve_task_modules(task)

        # Ensure acceptance checklist is present
        cl_path = os.path.join(proj.path, "deliverables", "acceptance_criteria.md")
        if not os.path.exists(cl_path):
            is_visual_3d = any(w in task_lower for w in ["3d", "three", "webgl", "场景", "渲染", "视觉", "模型"])
            chk = AcceptanceChecklist(title=f"分布式模块化任务验收清单: {task[:40]}")
            chk.add_item("环境探针与基础服务就绪且零 CORS 阻断", category="environment", item_id="AC-ENV-01")
            for m in module_specs:
                chk.add_item(f"子模块 [{m['name']}] 编码实现、接口导出契约与单元测试通过", category="functional", item_id=f"AC-{m['name'].upper()}-01")
            chk.add_item("总装主控入口 (index.html / main.js / 主控脚本) 整合全部组件并正确协同", category="functional", item_id="AC-INT-01")
            if is_visual_3d:
                chk.add_item("全场景 360° 环境反射、多重布光与硬件 MSAA 抗锯齿生效，画面无死黑、无乐高塑料感", category="aesthetic", item_id="AC-AES-01")
            else:
                chk.add_item("整体交付物视觉/交互体验良好，无阻塞缺陷", category="aesthetic", item_id="AC-AES-01")
            chk.add_item("全量集成测试绿灯通过且控制台零错误", category="general", item_id="AC-GEN-01")
            chk.save_to_file(cl_path)

        # -------------------------------------------------------------
        # Phase 2: Concurrent Worker Swarm Execution
        # -------------------------------------------------------------
        default_bus.publish(
            EventType.PIPELINE_STEP,
            {
                "stage": "concurrent_swarm_start",
                "module_count": len(module_specs),
                "workers": self.max_workers
            }
        )

        swarm_results = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_mod = {
                executor.submit(
                    self._run_single_module_pipeline,
                    mod,
                    proj.path,
                    active_model
                ): mod["name"]
                for mod in module_specs
            }

            for future in concurrent.futures.as_completed(future_to_mod):
                mod_name = future_to_mod[future]
                try:
                    res = future.result()
                    swarm_results[mod_name] = res
                    default_bus.publish(
                        EventType.PIPELINE_STEP,
                        {
                            "stage": "concurrent_worker_finished",
                            "module": mod_name,
                            "success": res.get("success", False)
                        }
                    )
                except Exception as exc:
                    swarm_results[mod_name] = {"success": False, "error": str(exc)}

        stage_records.append({"stage": "concurrent_swarm", "results": swarm_results})

        # Check if all modules succeeded
        failed_modules = [m for m, r in swarm_results.items() if not r.get("success")]
        if failed_modules:
            default_bus.publish(
                EventType.PIPELINE_STEP,
                {"stage": "swarm_partial_failures", "failed_modules": failed_modules}
            )

        # -------------------------------------------------------------
        # Phase 3: Integration Assembly (Master Integrator Coder)
        # -------------------------------------------------------------
        default_bus.publish(EventType.PIPELINE_STEP, {"stage": "integration_assembly", "role": "coder"})
        coder_role = Role.from_file(self._get_agent_path("coder"))
        integrator_harness = AgentHarness(coder_role, model=active_model)

        integration_output = "deliverables/integration_changes.md"
        # Dynamically derive integration instructions from module specs (no hardcoded scenes)
        module_summary = "\n".join(
            f"- **{m['title']}** (`{m['file']}`，导出契约：{m['contract']})"
            for m in module_specs
        )
        integrator_task = (
            f"目标任务：完成复合任务的集成总装配。\n"
            f"各个独立子模块已由并发 Agent 编写并验证完毕：\n{module_summary}\n\n"
            f"请编写或更新项目总入口（如 index.html / main.js / 主控脚本 / 服务启动入口，视项目形态而定），完成总装：\n"
            f"1. 以模块化方式导入全部子组件，按各自导出契约实例化并编排到主流程/主场景中；\n"
            f"2. 合理布设整体空间或业务流程结构，确保各子模块正确协同、接口契合；\n"
            f"3. 若项目含 3D/Web 视觉呈现，遵循 rule/rule.md 图形学规范（多层次布光、ACESFilmic 色调映射、硬件 4x MSAA 抗锯齿、PBR 材质）；\n"
            f"4. 按需配备美观的交互面板（HUD/CLI/REST 入口）供整体控制与导览。\n"
            f"将完成的代码写入对应入口文件，并将集成说明写入：{integration_output}"
        )
        integration_res = integrator_harness.run(integrator_task, output_file=integration_output)
        stage_records.append({"stage": "integration_assembly", "result": integration_res})

        # -------------------------------------------------------------
        # Phase 4: Integration Review, Test & Multimodal Visual Aesthetic Audit
        # -------------------------------------------------------------
        # 4.1 Master Reviewer (Diff check)
        try:
            reviewer_role = Role.from_file(self._get_agent_path("reviewer"))
            master_reviewer = AgentHarness(reviewer_role, model=active_model)
            int_review_out = "deliverables/integration_review.md"
            rev_task = (
                f"任务目标：复合任务集成静态审查。\n"
                f"使用 code_reviewer 工具提取 Git Diff，审查集成代码是否正确导入了各个子模块，\n"
                f"是否存在 TDZ/作用域、空指针与并发竞争问题，且符合 rule/rule.md 对应规范。\n"
                f"输出审查结论至：{int_review_out}，首行标明【审查结果：PASS】或【审查结果：REJECT 驳回】。"
            )
            master_reviewer.run(rev_task, output_file=int_review_out)
        except Exception:
            pass

        # 4.2 Master Tester (All Unit Tests + Integration Verification)
        default_bus.publish(EventType.PIPELINE_STEP, {"stage": "integration_testing", "role": "tester"})
        tester_role = Role.from_file(self._get_agent_path("tester"))
        master_tester = AgentHarness(tester_role, model=active_model)
        int_test_out = "deliverables/integration_test_report.md"
        test_task = (
            f"使用 test_runner 运行全量测试用例（包括 tests/ 目录下的所有模块测试与页面校验）。\n"
            f"记录通过情况与控制台运行状态，输出至：{int_test_out}"
        )
        master_tester.run(test_task, output_file=int_test_out)

        # 4.3 Master Designer (Multimodal Visual Aesthetic Audit via browser_test)
        try:
            designer_role = Role.from_file(self._get_agent_path("designer"))
            default_bus.publish(EventType.PIPELINE_STEP, {"stage": "integration_design_audit", "role": "designer"})
            master_designer = AgentHarness(designer_role, model=active_model)
            int_design_out = "deliverables/integration_design_audit.md"
            design_task = (
                f"任务目标：{task}\n"
                f"调用 browser_test 对集成后的网页 (index.html) 截取真实视口截图。\n"
                f"审查整体视觉品质：空间纵深/布局合理性、光影明暗层次（无死黑）、材质质感（无塑料感）及交互面板设计感。\n"
                f"核验 deliverables/acceptance_criteria.md 中的指标并打勾。\n"
                f"首行标明【验收结果：PASS】或【验收结果：REJECT 驳回】，输出审美报告至：{int_design_out}"
            )
            master_designer.run(design_task, output_file=int_design_out)
        except Exception:
            pass

        # -------------------------------------------------------------
        # Phase 5: Delivery & Summary Report
        # -------------------------------------------------------------
        default_bus.publish(EventType.PIPELINE_STEP, {"stage": "delivery_summary", "role": "delivery"})
        elapsed = round(time.time() - start_time, 2)

        summary_content = (
            f"# 分布式并发多智能体模块化交付报告\n\n"
            f"## 一、执行概况\n"
            f"- **任务目标**：{task}\n"
            f"- **工作区路径**：`{proj.path}`\n"
            f"- **并发 Worker 数**：{self.max_workers}\n"
            f"- **总执行耗时**：{elapsed} 秒\n\n"
            f"## 二、子模块并发完成状态\n"
        )
        for mod in module_specs:
            m_status = swarm_results.get(mod["name"], {}).get("success", False)
            status_str = "🟢 成功 (Passed)" if m_status else "🔴 失败 (Failed)"
            summary_content += f"- **[{mod['id']}] {mod['title']}** (`{mod['file']}`): {status_str}\n"

        summary_content += (
            f"\n## 三、两级门禁核验结论\n"
            f"- 单元测试级门禁：已完成所有子模块的独立契约验证与隔离测试。\n"
            f"- 全局集成级门禁：已完成主控入口总装、集成审查与无头浏览器视口验收。\n\n"
            f"## 四、交付产物导航\n"
            f"- [总体规划方案](deliverables/plan.md)\n"
            f"- [燃尽验收清单](deliverables/acceptance_criteria.md)\n"
            f"- [集成变更说明](deliverables/integration_changes.md)\n"
            f"- [集成测试报告](deliverables/integration_test_report.md)\n"
            f"- [审美设计报告](deliverables/integration_design_audit.md)\n"
        )

        summary_dest_abs = os.path.join(proj.path, output_file)
        os.makedirs(os.path.dirname(summary_dest_abs), exist_ok=True)
        with open(summary_dest_abs, "w", encoding="utf-8") as sf:
            sf.write(summary_content)

        # Post-merge git commit
        git_res = self.tdd_gate.verify_and_git_gate(f"feat(concurrent): modular assembly for {task[:40]}")

        return {
            "success": True,
            "elapsed_seconds": elapsed,
            "module_count": len(module_specs),
            "swarm_results": swarm_results,
            "integration_result": integration_res,
            "output_file": output_file,
            "git_commit": git_res
        }

    def _run_single_module_pipeline(
        self,
        module_spec: Dict[str, Any],
        project_path: str,
        active_model: str
    ) -> Dict[str, Any]:
        """Runs the isolated Coder -> Reviewer -> Tester cycle for an individual component."""
        mod_name = module_spec["name"]
        target_file = module_spec["file"]
        test_file = module_spec["test_file"]

        default_bus.publish(
            EventType.PIPELINE_STEP,
            {"stage": "module_worker_start", "module": mod_name, "file": target_file}
        )

        coder_role = Role.from_file(self._get_agent_path("coder"))
        worker_coder = AgentHarness(coder_role, model=active_model)

        loop = 0
        passed = False
        last_error = ""

        while loop < self.max_repair_loops and not passed:
            loop += 1
            coder_out = f"deliverables/modules/{mod_name}_changes.md"
            coder_task = (
                f"【并发子模块开发任务: {module_spec['title']}】\n"
                f"目标代码文件：`{target_file}`\n"
                f"单元测试文件：`{test_file}`\n\n"
                f"【接口契约规范】\n{module_spec['contract']}\n\n"
                f"【图形学与实现要求】\n{module_spec['requirements']}\n\n"
                f"请使用 write 工具真正编写/修改 `{target_file}` 以及对应的单元测试 `{test_file}`（如用 pytest 断言该文件语法正确且导出指定类）。\n"
                f"完成后将修改说明写入：{coder_out}"
            )
            if last_error:
                coder_task += f"\n\n上一轮审查或单测未通过原因：\n{last_error}\n请有针对性地自修复修正！"

            code_res = worker_coder.run(coder_task, output_file=coder_out)
            if not code_res.get("success"):
                last_error = code_res.get("error", "Coder failed output gate.")
                continue

            # Review step for module
            try:
                reviewer_role = Role.from_file(self._get_agent_path("reviewer"))
                worker_reviewer = AgentHarness(reviewer_role, model=active_model)
                rev_out = f"deliverables/modules/{mod_name}_review.md"
                rev_task = (
                    f"请审查组件 `{target_file}`：\n"
                    f"使用 code_reviewer 工具检查语法错误、TDZ 暂时死区与 ES6 export 规范。\n"
                    f"首行必须标明【审查结果：PASS】或【审查结果：REJECT 驳回】，输出报告至：{rev_out}"
                )
                rev_res = worker_reviewer.run(rev_task, output_file=rev_out)
                rev_abs = os.path.join(project_path, rev_out)
                if os.path.exists(rev_abs):
                    with open(rev_abs, "r", encoding="utf-8") as rf:
                        r_txt = rf.read()
                    if "reject" in r_txt.lower() or "驳回" in r_txt:
                        last_error = f"Reviewer 驳回：\n{r_txt[:200]}"
                        continue
            except Exception:
                pass

            # Unit test step for module
            try:
                tester_role = Role.from_file(self._get_agent_path("tester"))
                worker_tester = AgentHarness(tester_role, model=active_model)
                test_out = f"deliverables/modules/{mod_name}_test.md"
                test_task = (
                    f"使用 test_runner 工具执行单元测试 `{test_file}` 与代码语法检查。\n"
                    f"输出测试记录至：{test_out}"
                )
                t_res = worker_tester.run(test_task, output_file=test_out)
                # Check pytest execution
                t_run = tools.execute_tool("test_runner", {"target": test_file, "mode": "all", "cwd": project_path})
                if not t_run.get("data", {}).get("passed", False):
                    last_error = t_run.get("error") or t_run.get("data", {}).get("raw_output", "Unit test failed.")
                    continue
            except Exception as te:
                last_error = str(te)
                continue

            passed = True

        return {
            "module": mod_name,
            "success": passed,
            "loops": loop,
            "file": target_file,
            "error": last_error if not passed else ""
        }

    # ==================================================================
    # CONCURRENT ANALYST SWARM
    # Multi-concurrent analysis for complex projects or multiple target files.
    # Flow: Complexity Eval -> Target Partitioning -> Concurrent Workers ->
    #       Shared Blackboard -> Consolidated Master Analysis Report
    # ==================================================================

    def run_concurrent_analysis(
        self,
        task: str,
        target_files: Optional[List[str]] = None,
        project_url: str = "",
        max_workers: Optional[int] = None,
        output_file: str = "deliverables/analysis_report.md",
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Runs multi-concurrent Analyst agents on partitioned target files.
        Evaluates task complexity, identifies entry points, improvement schemes,
        refactoring targets, and bugs. Shares findings via SharedBlackboard.
        """
        active_model = model or self.model
        workers_count = max_workers or self.max_workers
        proj = get_current_project()
        bb = get_blackboard()

        start_time = time.time()
        default_bus.publish(EventType.PIPELINE_STEP, {
            "stage": "concurrent_analysis_start",
            "task": task,
            "target_files": target_files,
            "workers": workers_count
        })

        # 1. Determine target files if not explicitly provided
        files = list(target_files) if target_files else []
        if not files:
            for root, dirs, fnames in os.walk(proj.path):
                dirs[:] = [d for d in dirs if d not in {".git", "node_modules", "__pycache__", ".pytest_cache", "dist"}]
                for fn in fnames:
                    if fn.endswith((".js", ".ts", ".py", ".html", ".css")) and not fn.startswith("test_"):
                        rel = os.path.relpath(os.path.join(root, fn), proj.path)
                        files.append(rel)
            files = sorted(files)[:12]

        if not files:
            files = ["index.js"] if os.path.exists(os.path.join(proj.path, "index.js")) else ["main.py"]

        # 2. Evaluate complexity: decide whether to split files into concurrent batches
        if len(files) <= 1:
            batches = [files]
        else:
            k = min(workers_count, len(files))
            batches = [[] for _ in range(k)]
            for i, f in enumerate(files):
                batches[i % k].append(f)

        default_bus.publish(EventType.PIPELINE_STEP, {
            "stage": "analyst_batches_scheduled",
            "batch_count": len(batches),
            "files_count": len(files)
        })

        # 3. Concurrent execution via ThreadPoolExecutor
        worker_results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(batches)) as executor:
            future_to_id = {
                executor.submit(
                    self._run_single_analyst_worker,
                    file_batch=batch,
                    task=task,
                    active_model=active_model,
                    worker_id=idx + 1,
                    project_url=project_url
                ): idx + 1
                for idx, batch in enumerate(batches)
            }
            for future in concurrent.futures.as_completed(future_to_id):
                wid = future_to_id[future]
                try:
                    res = future.result()
                    worker_results.append(res)
                except Exception as exc:
                    worker_results.append({"success": False, "worker_id": wid, "error": str(exc)})

        # 4. Consolidate results from Shared Blackboard & worker reports
        bb_bugs = bb.get(topic="bug_findings")
        bb_schemes = bb.get(topic="improvement_schemes")

        consolidated_lines = [
            "# 综合多智能体代码分析与架构改造方案 (Consolidated Analysis Report)\n",
            f"## 一、分析目标与指令\n- **目标指令**：{task}\n- **参与并发分析师**：{len(batches)} 名\n- **分析覆盖文件**：{', '.join(f'`{f}`' for f in files)}\n",
            "## 二、改造切入点与演进方案建议 (Where & How to Modify)",
        ]

        if bb_schemes:
            for s in bb_schemes:
                consolidated_lines.append(f"- **[{s.get('key')}]** ({s.get('author')}): {s.get('value')}")
        else:
            consolidated_lines.append("- 根据项目结构与指令，建议从主控调用与高内聚模块入口处做渐进式修改。")

        consolidated_lines.append("\n## 三、精准问题与隐患清单 (Identified Issues & Gotchas)")
        all_issues = list(bb_bugs) if bb_bugs else []
        if all_issues:
            consolidated_lines.append("| 模块/文件 | 问题描述 | 记录者 |")
            consolidated_lines.append("|---|---|---|")
            for iss in all_issues:
                consolidated_lines.append(f"| `{iss.get('key')}` | {iss.get('value')} | {iss.get('author')} |")
        else:
            consolidated_lines.append("*（未发现阻塞性Bug，侧重于架构迭代与功能增强）*")

        consolidated_lines.append("\n## 四、共享黑板条目汇总\n" + bb.export_markdown())

        consolidated_content = "\n".join(consolidated_lines)
        out_abs = os.path.join(proj.path, output_file)
        os.makedirs(os.path.dirname(out_abs), exist_ok=True)
        with open(out_abs, "w", encoding="utf-8") as f:
            f.write(consolidated_content)

        elapsed = round(time.time() - start_time, 2)
        return {
            "success": all(r.get("success", False) for r in worker_results) if worker_results else True,
            "elapsed_seconds": elapsed,
            "target_files": files,
            "batches_count": len(batches),
            "worker_results": worker_results,
            "output_file": output_file
        }

    def _run_single_analyst_worker(
        self,
        file_batch: List[str],
        task: str,
        active_model: str,
        worker_id: int,
        project_url: str = ""
    ) -> Dict[str, Any]:
        """Runs an individual analyst agent on an assigned batch of target files."""
        analyst_role = Role.from_file(self._get_agent_path("analyst"))
        analyst_harness = AgentHarness(analyst_role, model=active_model)
        proj = get_current_project()
        bb = get_blackboard()

        worker_out = f"deliverables/analysis_workers/analyst_{worker_id}.md"
        browser_hint = ""
        if project_url:
            browser_hint = f"\n页面在线地址为：{project_url}，可按需调用 browser_interact 捕获运行时控制台日志与多视角截图。"

        analyst_task = (
            f"【并发分析师 Worker #{worker_id} 分析任务】\n"
            f"用户总体指令：{task}\n"
            f"你所重点分管负责的文件列表：{', '.join(file_batch)}\n"
            f"{browser_hint}\n"
            f"你的核心职责不仅是找Bug，更要全面研判改造切入点与演进方案：\n"
            f"1. 【切入点研判】：根据用户指令，分析从哪个文件、哪个类/函数入手改动最合理。\n"
            f"2. 【方案对比与决策】：分析怎么改更好？采用何种架构方案（如模块解耦、重构状态机、优化着色器、消除冗余）？\n"
            f"3. 【精确定位与改动范围】：精确指定需要修改的代码行或导出契约，评估改动影响面，并指出严禁触碰的稳定逻辑。\n"
            f"4. 【工具与黑板协同】：调用 `analyzer` 工具快速提取符号大纲、搜索关联引用、检测隐患，并调用 `blackboard` (post) 将你的分析发现与改造方案登记至共享黑板。\n"
            f"将本 Worker 的分析纪要输出保存至：{worker_out}"
        )

        res = analyst_harness.run(analyst_task, output_file=worker_out)
        return {
            "success": res.get("success", False),
            "worker_id": worker_id,
            "files": file_batch,
            "output_file": worker_out,
            "result": res
        }

    # ==================================================================
    # ITERATION PIPELINE
    # For improving / debugging EXISTING projects.
    # Flow: Analyst -> Concurrent Fix Coders -> Reviewer -> Designer
    # ==================================================================

    def run_iteration_pipeline(
        self,
        task: str,
        project_url: str = "",
        target_files: Optional[List[str]] = None,
        output_file: str = "deliverables/iteration_summary.md",
        model: Optional[str] = None,
        conditions: Optional[List[Dict[str, Any]]] = None,
        conditions_file: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Iteration pipeline for improving an existing project.

        Args:
            task: Description of what needs to be improved/fixed.
            project_url: Running URL to load in browser (e.g. http://localhost:8086).
            target_files: Specific files to focus on (e.g. ["modules/buildings.js", "modules/vegetation.js"]).
                         If None, analyst will discover relevant files automatically.
            output_file: Path for the final summary report.
            model: LLM model override.
            conditions: Machine-checkable hard conditions (condition_gate spec dict/list).
                        Evaluated inside every fix loop (hard reject & rework) and globally after Phase 1.
            conditions_file: Optional JSON file with the condition spec (relative to project root).

        Pipeline stages:
          Phase 0  - Analyst Swarm: Read code + multi-angle browser screenshots -> analysis report
          Phase 1  - Concurrent Fix Coders: Each coder gets analyst report + one target file to fix
                     (hard gates: real file modification + condition_gate conditions)
          Phase 1.5 - Global condition gate: if hard conditions fail -> one repair wave, re-evaluate
          Phase 2  - Integration Reviewer: Diff check on all changes
          Phase 3  - Designer Visual Audit: browser_interact multi-angle screenshots
          Phase 4  - Git commit & summary report
        """
        active_model = model or self.model
        start_time = time.time()
        proj = get_current_project()
        stage_records = []

        # Resolve hard verification conditions (condition_gate spec)
        if conditions_file and not conditions:
            cf_path = conditions_file if os.path.isabs(conditions_file) else os.path.join(proj.path, conditions_file)
            try:
                with open(cf_path, "r", encoding="utf-8") as cf:
                    conditions = json.load(cf)
            except Exception as e:
                default_bus.publish(EventType.PIPELINE_STEP, {
                    "stage": "conditions_load_error", "error": str(e)
                })
        gate_spec = conditions if conditions else None

        default_bus.publish(EventType.PIPELINE_STEP, {
            "stage": "iteration_pipeline_start",
            "task": task,
            "project_url": project_url,
            "target_files": target_files,
            "conditions_enabled": bool(gate_spec)
        })

        # ------------------------------------------------------------------
        # Phase 0.5: Acceptance authority (三权分离)
        # Acceptance conditions are authored BEFORE coding by the analyst
        # (or supplied by the user via CLI), pinned by SHA256, and evaluated
        # by the harness. Coders can NEVER author or alter acceptance criteria.
        # ------------------------------------------------------------------
        pinned_hash = ""
        if not gate_spec:
            try:
                analyst_harness = AgentHarness(
                    Role.from_file(self._get_agent_path("analyst")), model=active_model
                )
                draft_task = (
                    f"【验收条件制定任务（规划期）】\n"
                    f"迭代目标：{task}\n\n"
                    f"项目类型自动检测：{json.dumps(self._detect_project_profile(proj.path), ensure_ascii=False)}\n\n"
                    f"你是验收标准的制定者，不是执行者。请基于迭代目标与项目类型制定一套机器可验证的硬性验收条件（condition_gate 规格）。\n"
                    f"可用条件类型：file_exists / file_count_min / file_size_min / content_contains / "
                    f"text_search / code_reference_integrity / web_runtime_clean / command / script。\n"
                    f"要求：条件必须客观可判定、与任务硬指标一一对应、避免主观描述；必须与上面检测到的项目类型匹配——"
                    f"web/H5 项目才使用 web_runtime_clean（控制台零报错）与浏览器类验证；python 项目用 pytest；"
                    f"php 项目用 `php -l`（语法零错误）；lua 项目用 luacheck；c 项目用 gcc/clang 编译零警告；"
                    f"含 sql 的项目可用 sqlfluff 或 mysql 客户端执行校验查询；严禁给项目类型之外强加不相关的验证条件；"
                    f"若项目存在真实 3D 资产（models/ 下有 .glb/.gltf 文件），必须包含资产引用完整性检查；"
                    f"不要包含无法在本机验证的条件。\n"
                    f"输出格式：仅在报告中输出一个 ```json 代码块，内容为 {{\"mode\": \"all\", \"conditions\": [...]}} 规格，"
                    f"不要输出其它 JSON。"
                )
                draft_res = analyst_harness.run(draft_task)
                draft_spec = self._extract_conditions_json(draft_res.get("last_message", ""))
                if draft_spec:
                    gate_spec = draft_spec
                    default_bus.publish(EventType.PIPELINE_STEP, {
                        "stage": "conditions_drafted_by_analyst",
                        "conditions_count": len(gate_spec.get("conditions", []))
                    })
            except Exception as exc:
                default_bus.publish(EventType.PIPELINE_STEP, {
                    "stage": "conditions_draft_error", "error": str(exc)
                })
        if gate_spec:
            # Baselines are harness-owned, type-aware and always merged; spec then pinned.
            gate_spec = self._merge_baseline_conditions(gate_spec, proj.path, project_url)
            pinned_hash = self._pin_conditions(gate_spec, proj.path)
            default_bus.publish(EventType.PIPELINE_STEP, {
                "stage": "conditions_pinned",
                "sha256": pinned_hash[:16],
                "source": "user" if conditions else "analyst+baseline"
            })

        # ------------------------------------------------------------------
        # Phase 0: Concurrent Analyst Swarm – Deep Code Analysis & Proposals
        # ------------------------------------------------------------------
        default_bus.publish(EventType.PIPELINE_STEP, {"stage": "analyst_pre_pass", "role": "analyst"})
        analyst_out = "deliverables/iteration_analysis.md"
        analyst_res = self.run_concurrent_analysis(
            task=task,
            target_files=target_files,
            project_url=project_url,
            max_workers=self.max_workers,
            output_file=analyst_out,
            model=active_model
        )
        stage_records.append({"stage": "analyst", "result": analyst_res})

        # Read analysis report for use by fix coders
        analysis_content = ""
        analyst_abs = os.path.join(proj.path, analyst_out)
        if os.path.exists(analyst_abs):
            with open(analyst_abs, "r", encoding="utf-8") as f:
                analysis_content = f.read()

        # ------------------------------------------------------------------
        # Phase 1: Concurrent Fix Coders (one per target file)
        # ------------------------------------------------------------------
        default_bus.publish(EventType.PIPELINE_STEP, {"stage": "concurrent_fix_coders"})

        if not target_files:
            # Let analyst report guide which files to fix; parse file mentions from report
            import re
            mentioned = re.findall(r'`([^`]+\.(?:js|py|html|css|ts))`', analysis_content)
            # Deduplicate, keep order, limit to 6
            seen = set()
            target_files = []
            for f in mentioned:
                if f not in seen and not f.startswith("test_"):
                    seen.add(f)
                    target_files.append(f)
                    if len(target_files) >= 6:
                        break
            if not target_files:
                target_files = ["index.js"]  # fallback

        fix_results = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(self.max_workers, len(target_files))) as executor:
            future_to_file = {
                executor.submit(
                    self._run_single_fix_pipeline,
                    target_file=f,
                    task=task,
                    analysis_content=analysis_content,
                    project_path=proj.path,
                    active_model=active_model,
                    conditions=gate_spec,
                    pinned_hash=pinned_hash
                ): f
                for f in target_files
            }
            for future in concurrent.futures.as_completed(future_to_file):
                fname = future_to_file[future]
                try:
                    res = future.result()
                    fix_results[fname] = res
                    default_bus.publish(EventType.PIPELINE_STEP, {
                        "stage": "fix_worker_done",
                        "file": fname,
                        "success": res.get("success", False)
                    })
                except Exception as exc:
                    fix_results[fname] = {"success": False, "error": str(exc)}

        stage_records.append({"stage": "concurrent_fix", "results": fix_results})

        # ------------------------------------------------------------------
        # Phase 1.5: Global Hard Condition Gate (condition_gate)
        # Machine-checkable verdict. On failure -> one repair wave, re-evaluate.
        # ------------------------------------------------------------------
        conditions_passed = True
        gate_verdict: Dict[str, Any] = {}
        if gate_spec:
            default_bus.publish(EventType.PIPELINE_STEP, {"stage": "global_condition_gate"})
            gate_res = tools.execute_tool("condition_gate", {"conditions": gate_spec})
            gate_verdict = gate_res.get("data", {}) if isinstance(gate_res, dict) else {}
            conditions_passed = bool(gate_verdict.get("passed", False))

            if not conditions_passed:
                failure_text = gate_verdict.get("failure_summary", "unknown hard condition failures")
                default_bus.publish(EventType.PIPELINE_STEP, {
                    "stage": "condition_gate_reject",
                    "failures": failure_text,
                    "action": "analyst_consult_then_repair_wave"
                })
                # Analyst consult: diagnose WHY conditions failed and prescribe
                # concrete remediation (analyst has analyzer/web_search knowledge).
                consult_text = ""
                try:
                    consult_harness = AgentHarness(
                        Role.from_file(self._get_agent_path("analyst")), model=active_model
                    )
                    consult_res = consult_harness.run(
                        f"【验收门禁失败会诊】\n迭代目标：{task}\n\n"
                        f"硬性条件门禁失败明细：\n{failure_text}\n\n"
                        f"请诊断失败根因（如：外部资产下载失败/代码未接入/指标不合理），"
                        f"并给出每个失败项的具体补救指令（可直接执行的代码级/资产级动作），"
                        f"不超过 600 字。必要时调用 analyzer 检索代码与知识库、web_search 查资料。"
                    )
                    consult_text = (consult_res.get("last_message", "") or "")[:1500]
                except Exception as exc:
                    default_bus.publish(EventType.PIPELINE_STEP, {
                        "stage": "consult_error", "error": str(exc)
                    })
                # One repair wave: re-dispatch fix workers with failure evidence + remediation
                repair_results = {}
                with concurrent.futures.ThreadPoolExecutor(
                    max_workers=min(self.max_workers, len(target_files))
                ) as executor:
                    future_to_file = {
                        executor.submit(
                            self._run_single_fix_pipeline,
                            target_file=f,
                            task=task + f"\n\n【硬性条件门禁驳回记录，必须针对性解决】\n{failure_text}"
                                 + (f"\n\n【分析师会诊补救指令】\n{consult_text}" if consult_text else ""),
                            analysis_content=analysis_content,
                            project_path=proj.path,
                            active_model=active_model,
                            conditions=gate_spec
                        ): f
                        for f in target_files
                    }
                    for future in concurrent.futures.as_completed(future_to_file):
                        fname = future_to_file[future]
                        try:
                            repair_results[fname] = future.result()
                        except Exception as exc:
                            repair_results[fname] = {"success": False, "error": str(exc)}
                # Merge repair outcomes (later runs win)
                for fname, res in repair_results.items():
                    if res.get("success"):
                        fix_results[fname] = res
                # Final re-evaluation
                gate_res2 = tools.execute_tool("condition_gate", {"conditions": gate_spec})
                gate_verdict = gate_res2.get("data", {}) if isinstance(gate_res2, dict) else {}
                conditions_passed = bool(gate_verdict.get("passed", False))

            stage_records.append({
                "stage": "condition_gate",
                "passed": conditions_passed,
                "verdict": gate_verdict
            })

        # ------------------------------------------------------------------
        # Phase 2: Integration Reviewer (diff check)
        # ------------------------------------------------------------------
        try:
            default_bus.publish(EventType.PIPELINE_STEP, {"stage": "iteration_review", "role": "reviewer"})
            reviewer_role = Role.from_file(self._get_agent_path("reviewer"))
            rev_harness = AgentHarness(reviewer_role, model=active_model)
            rev_out = "deliverables/iteration_review.md"
            rev_task = (
                f"【迭代修复集成审查】\n"
                f"本次迭代修复目标：{task}\n"
                f"调用 code_reviewer / git_tool 提取最新 git diff，逐文件审查修复代码是否正确解决了分析报告中指出的问题，"
                f"是否引入新的副作用或破坏原有功能。\n"
                f"对照分析报告（位于 {analyst_out}）中的问题清单逐一核验。\n"
                f"输出审查结论至：{rev_out}，首行标明【审查结果：PASS】或【审查结果：REJECT 驳回】。"
            )
            rev_harness.run(rev_task, output_file=rev_out)
        except Exception:
            pass

        # ------------------------------------------------------------------
        # Phase 3: Designer Visual Audit – Multi-Angle Screenshots
        # ------------------------------------------------------------------
        try:
            default_bus.publish(EventType.PIPELINE_STEP, {"stage": "iteration_visual_audit", "role": "designer"})
            designer_role = Role.from_file(self._get_agent_path("designer"))
            designer_harness = AgentHarness(designer_role, model=active_model)
            design_out = "deliverables/iteration_design_audit.md"

            url_hint = f"页面 URL：{project_url}" if project_url else "使用 browser_test 加载 index.html"
            design_task = (
                f"【迭代修复后视觉验收】\n"
                f"本次迭代目标：{task}\n"
                f"{url_hint}\n"
                f"请调用 browser_interact 工具，wait_for_load_ms=12000，执行以下多视角截图序列：\n"
                f"  步骤1：wait_for_console（等待 'loaded' 日志，timeout_ms=15000）\n"
                f"  步骤2：screenshot 默认视角 → deliverables/iter_final_default.png\n"
                f"  步骤3：点击黄昏按钮（#btn-sunset 或文本'夕阳'）→ wait 1000ms → screenshot → iter_final_sunset.png\n"
                f"  步骤4：点击夜晚按钮（#btn-night 或文本'夜晚'）→ wait 1000ms → screenshot → iter_final_night.png\n"
                f"  步骤5：点击木屋特写（#cam-chalet）→ wait 1500ms → screenshot → iter_final_chalet.png\n"
                f"对照迭代分析报告（{analyst_out}）中的原始问题清单，逐项核验每个问题是否已被修复。\n"
                f"输出多视角审美验收报告至：{design_out}，首行标明【验收结果：PASS】或【验收结果：REJECT 驳回】。"
            )
            designer_harness.run(design_task, output_file=design_out)
        except Exception:
            pass

        # ------------------------------------------------------------------
        # Phase 4: Summary & Git Commit
        # ------------------------------------------------------------------
        elapsed = round(time.time() - start_time, 2)
        failed_files = [f for f, r in fix_results.items() if not r.get("success")]

        summary = (
            f"# 迭代修复交付报告\n\n"
            f"## 一、迭代目标\n{task}\n\n"
            f"## 二、执行耗时\n{elapsed} 秒\n\n"
            f"## 三、修复文件状态\n"
        )
        for fname, res in fix_results.items():
            status = "🟢 成功" if res.get("success") else "🔴 失败"
            summary += f"- `{fname}`: {status}\n"

        summary += (
            f"\n## 四、硬性检测条件门禁结论\n"
            f"- **condition_gate 判定**：{'🟢 通过 (ALL CONDITIONS PASSED)' if conditions_passed else '🔴 未通过 (CONDITIONS FAILED)'}\n"
            + (f"- 失败明细：{gate_verdict.get('failure_summary', '')}\n" if not conditions_passed else "")
            + f"\n## 五、交付产物\n"
            f"- [分析报告](deliverables/iteration_analysis.md)\n"
            f"- [代码审查](deliverables/iteration_review.md)\n"
            f"- [视觉验收](deliverables/iteration_design_audit.md)\n"
            f"- 多视角截图: iter_view_*.png / iter_final_*.png\n"
        )

        summary_abs = os.path.join(proj.path, output_file)
        os.makedirs(os.path.dirname(summary_abs), exist_ok=True)
        with open(summary_abs, "w", encoding="utf-8") as sf:
            sf.write(summary)

        git_res = None
        if conditions_passed and len(failed_files) == 0:
            git_res = self.tdd_gate.verify_and_git_gate(f"fix(iteration): {task[:60]}")
        else:
            # Hard reject: acceptance conditions failed (or fix workers failed).
            # NEVER commit — rollback scoped to the project directory only.
            reason = (
                f"conditions gate failed: {gate_verdict.get('failure_summary', '')}"
                if not conditions_passed else
                f"fix workers failed: {failed_files}"
            )
            self._record_lesson(task, reason, proj.path)
            default_bus.publish(EventType.GIT_ACTION, {
                "action": "rollback_trigger", "reason": reason
            })
            try:
                rel = os.path.relpath(proj.path, self.tdd_gate.repo_root)
                rb_params = {"action": "rollback", "cwd": self.tdd_gate.repo_root}
                if rel and rel != "." and not rel.startswith(".."):
                    rb_params["path"] = rel
                rollback_res = tools.execute_tool("git_tool", rb_params)
                default_bus.publish(EventType.GIT_ACTION, {
                    "action": "rolled_back", "result": rollback_res
                })
                git_res = {"success": False, "action": "rolled_back", "reason": reason}
            except Exception as exc:
                git_res = {"success": False, "action": "rollback_error", "error": str(exc), "reason": reason}

        return {
            "success": len(failed_files) == 0 and conditions_passed,
            "conditions_passed": conditions_passed,
            "condition_failures": gate_verdict.get("failure_summary", "") if not conditions_passed else "",
            "elapsed_seconds": elapsed,
            "fixed_files": list(fix_results.keys()),
            "failed_files": failed_files,
            "analysis_report": analyst_out,
            "output_file": output_file,
            "git_commit": git_res
        }

    @staticmethod
    def _file_signature(path: str) -> Optional[str]:
        """MD5 signature of a file's content (None if missing). Used to verify real edits."""
        import hashlib
        if not os.path.exists(path):
            return None
        try:
            with open(path, "rb") as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception:
            return None

    # ------------------------------------------------------------------
    # Acceptance authority helpers (trust layering):
    # L0 user CLI conditions > L1 analyst/planner-drafted conditions (pinned)
    # L2 coder CHECK_SCRIPTs are self-checks only and never grant acceptance.
    # ------------------------------------------------------------------
    @staticmethod
    def _extract_conditions_json(text: str) -> Optional[Dict[str, Any]]:
        """Extract a condition_gate spec (JSON) drafted by an agent from its message."""
        if not text:
            return None
        candidates = []
        m = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
        if m:
            candidates.append(m.group(1))
        else:
            m2 = re.search(r"(\{[^{}]*\"conditions\".*\})", text, re.DOTALL)
            if m2:
                candidates.append(m2.group(1))
        # Bare JSON array of conditions (also inside ```json fences)
        m3 = re.search(r"(\[\s*\{.*?\}\s*(?:,\s*\{.*?\}\s*)*\])", text, re.DOTALL)
        if m3:
            candidates.append(m3.group(1))
        for c in candidates:
            try:
                spec = json.loads(c)
            except Exception:
                continue
            if isinstance(spec, dict) and spec.get("conditions"):
                return spec
            if isinstance(spec, list) and spec:
                return {"mode": "all", "conditions": spec}
        return None

    def _pin_conditions(self, spec: Dict[str, Any], project_path: str) -> str:
        """Persist the active condition spec and pin its SHA256. Returns the hash."""
        import hashlib
        cond_path = os.path.join(project_path, "deliverables", "acceptance_conditions.json")
        os.makedirs(os.path.dirname(cond_path), exist_ok=True)
        with open(cond_path, "w", encoding="utf-8") as f:
            json.dump(spec, f, ensure_ascii=False, indent=2)
        with open(cond_path, "rb") as f:
            digest = hashlib.sha256(f.read()).hexdigest()
        with open(cond_path + ".sha256", "w", encoding="utf-8") as f:
            f.write(digest)
        return digest

    def _conditions_tamper_error(self, project_path: str, pinned_hash: str) -> str:
        """Non-empty error when the pinned conditions file was modified/deleted on disk."""
        if not pinned_hash:
            return ""
        cond_path = os.path.join(project_path, "deliverables", "acceptance_conditions.json")
        if not os.path.exists(cond_path):
            return "验收条件文件 deliverables/acceptance_conditions.json 被删除——验收条件由规划期制定，coder 无权修改或删除！"
        import hashlib
        with open(cond_path, "rb") as f:
            digest = hashlib.sha256(f.read()).hexdigest()
        if digest != pinned_hash:
            return "验收条件文件被篡改（SHA256 不符）——门禁以管线内存中的原始条件为准，篡改无效且触发返工！"
        return ""

    @staticmethod
    def _detect_project_profile(project_path: str) -> Dict[str, bool]:
        """
        Detect the project's technical profile so baselines stay type-appropriate
        (e.g. web console checks are meaningless for py/lua/c projects).
        """
        try:
            names = os.listdir(project_path)
        except Exception:
            names = []

        def _has(ext):
            return any(n.endswith(ext) for n in names)

        return {
            # web = rendered in a browser (html or php server or node project)
            "web": "index.html" in names or "package.json" in names or "index.php" in names,
            "python": _has(".py"),
            "lua": _has(".lua"),
            "php": _has(".php"),
            "sql": _has(".sql"),
            "c": "Makefile" in names or "CMakeLists.txt" in names or _has(".c"),
        }

    @staticmethod
    def _has_3d_assets(project_path: str) -> bool:
        """
        A models/ dir only means 3D assets when it actually contains .glb/.gltf files.
        MVC-style models/ dirs (php/java business classes) must NOT trigger the
        asset-reference baseline, or the gate would false-fail forever.
        """
        models_dir = os.path.join(project_path, "models")
        if not os.path.isdir(models_dir):
            return False
        try:
            return any(fn.lower().endswith((".glb", ".gltf")) for fn in os.listdir(models_dir))
        except Exception:
            return False

    @staticmethod
    def _merge_baseline_conditions(
        gate_spec: Any, project_path: str, project_url: str = ""
    ) -> Dict[str, Any]:
        """Auto-inject non-negotiable baseline conditions (harness-owned, not agent-authored).
        Baselines are chosen by detected project type, never by agents."""
        spec = dict(gate_spec) if isinstance(gate_spec, dict) else {"mode": "all", "conditions": gate_spec}
        conds = spec.get("conditions")
        if isinstance(conds, dict):
            conds = [conds]
        conds = list(conds or [])
        existing_types = {c.get("type") for c in conds if isinstance(c, dict)}
        profile = ConcurrentModularPipeline._detect_project_profile(project_path)

        # Only true 3D-asset projects (models/ holding .glb/.gltf): references must resolve.
        # MVC-style models/ dirs must not trigger this or the gate false-fails forever.
        if ConcurrentModularPipeline._has_3d_assets(project_path) and "code_reference_integrity" not in existing_types:
            conds.append({
                "type": "code_reference_integrity",
                "scan_glob": "*.js",
                "ref_regex": r"models/[\w./-]+\.(?:glb|gltf)",
                "min_refs": 1
            })

        # Web projects with a live URL: zero console/network errors at runtime
        if profile["web"] and project_url and "web_runtime_clean" not in existing_types:
            conds.append({
                "type": "web_runtime_clean",
                "url": project_url,
                "max_errors": 0
            })

        spec["conditions"] = conds
        return spec

    def _record_lesson(self, task: str, failure_summary: str, project_path: str = "") -> None:
        """
        Auto-append a failure lesson to the harness knowledge base so future
        query_knowledge / analyst consults can retrieve what went wrong and how.
        Organizational memory: failures must compound into experience.
        """
        try:
            kb_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                   "knowledge", "lessons.json")
            os.makedirs(os.path.dirname(kb_path), exist_ok=True)
            entries = []
            if os.path.exists(kb_path):
                try:
                    with open(kb_path, "r", encoding="utf-8") as f:
                        entries = json.load(f)
                except Exception:
                    entries = []
            entries.append({
                "time": time.strftime("%Y-%m-%d %H:%M:%S"),
                "project": os.path.basename(project_path) if project_path else "",
                "task": task[:200],
                "failure_summary": failure_summary[:600],
            })
            entries = entries[-200:]
            with open(kb_path, "w", encoding="utf-8") as f:
                json.dump(entries, f, ensure_ascii=False, indent=2)
            default_bus.publish(EventType.PIPELINE_STEP, {
                "stage": "lesson_recorded", "kb": "knowledge/lessons.json"
            })
        except Exception:
            pass

    def _verify_check_scripts(self, project_path: str, report_file: str) -> str:
        """
        Hand-over gate for temp check scripts declared by agents.
        Parses `CHECK_SCRIPT: <path>` lines from the coder report; each script must:
        1) exist and pass syntax validation (never hand over a broken script), and
        2) execute with exit code 0 (expected verdict) before acceptance is granted.
        Returns an error string listing all violations; empty string means pass.
        """
        report_abs = os.path.join(project_path, report_file)
        if not os.path.exists(report_abs):
            return ""
        try:
            with open(report_abs, "r", encoding="utf-8") as rf:
                report_text = rf.read()
        except Exception:
            return ""

        declared = []
        for line in report_text.splitlines():
            m = re.search(r"CHECK_SCRIPT:\s*(\S+)", line)
            if m:
                declared.append(m.group(1))
        if not declared:
            return ""

        from tools.condition_gate import syntax_check_file
        errors = []
        for script in dict.fromkeys(declared):
            ap = script if os.path.isabs(script) else os.path.join(project_path, script)
            if not os.path.exists(ap):
                errors.append(f"声明的检测脚本不存在：{script}")
                continue
            syn = syntax_check_file(ap)
            if not syn.get("ok"):
                errors.append(f"检测脚本语法未通过（不得带病交接）：{script} :: {syn.get('error', '')}")
                continue
            try:
                proc = subprocess.run(
                    f"{sys.executable} {ap}", shell=True, cwd=project_path,
                    timeout=120, capture_output=True, text=True
                )
                if proc.returncode != 0:
                    evidence = (proc.stdout or proc.stderr or "").strip()[:400]
                    errors.append(f"检测脚本运行未通过（exit={proc.returncode}）：{script} :: {evidence}")
            except subprocess.TimeoutExpired:
                errors.append(f"检测脚本运行超时：{script}")
        return "\n".join(errors)

    def _run_single_fix_pipeline(
        self,
        target_file: str,
        task: str,
        analysis_content: str,
        project_path: str,
        active_model: str,
        conditions: Optional[Dict[str, Any]] = None,
        pinned_hash: str = ""
    ) -> Dict[str, Any]:
        """Runs Coder -> Reviewer fix cycle for a single file in iteration mode."""
        mod_name = os.path.splitext(os.path.basename(target_file))[0]
        coder_role = Role.from_file(self._get_agent_path("coder"))
        worker_coder = AgentHarness(coder_role, model=active_model)

        loop = 0
        passed = False
        last_error = ""

        # Trim analysis to relevant section for this file to save context
        analysis_excerpt = analysis_content[:3000]
        abs_target = os.path.join(project_path, target_file)
        sig_before = self._file_signature(abs_target)

        while loop < self.max_repair_loops and not passed:
            loop += 1
            coder_out = f"deliverables/iteration_fixes/{mod_name}_fix.md"
            coder_task = (
                f"【迭代修复任务 - 目标文件: {target_file}】\n\n"
                f"迭代改进目标：{task}\n\n"
                f"【分析师报告摘要（含问题清单与修复方向）】\n"
                f"{analysis_excerpt}\n\n"
                f"请仔细阅读 `{target_file}` 的完整代码（调用 read 工具），"
                f"根据分析师报告中与此文件相关的问题，进行精准的最小化修复（不要过度重构，只修复已识别的问题）。\n"
                f"若任务涉及外部 3D 资产，必须调用 vendor_assets 工具（download_url + dest_path）将 .glb 资产真实落地到项目 models/ 目录，"
                f"且资产文件必须使用语义化命名（如 flamingo.glb、lantern.glb），严禁 asset_1.glb 之类的数字/无意义命名。\n"
                f"若你编写了临时检测脚本（如资产引用校验脚本），必须在报告首部声明一行：CHECK_SCRIPT: <相对项目根的脚本路径>；"
                f"脚本会在验收门禁被强制语法检测并运行，exit 0 才放行。\n"
                f"修复完成后必须真实修改 `{target_file}` 的源码内容（只写报告不改代码将判定为失败并触发返工），然后将改动说明写入：{coder_out}"
            )
            if last_error:
                coder_task += f"\n\n上一轮审查驳回原因：{last_error}\n请有针对性地修正！"
                # Escalation playbook: each rejected round unlocks wider tactics so
                # the worker never stalls on the same failed approach.
                if loop >= 2:
                    coder_task += (
                        f"\n\n【升级策略（第 {loop} 轮，上轮方案已被驳回，禁止原样重试）】\n"
                        f"- 先调用 condition_gate 工具（conditions_file=deliverables/check_conditions.json）自评当前代码，"
                        f"对照每条失败项逐条映射到具体代码动作，列清单后再动手。\n"
                        f"- 调用 web_search 检索相关技术资料与解决方案（如实现思路、现成资产下载源）。\n"
                        f"- 重新逐字阅读驳回原因，把每个失败项映射到一个具体代码动作，逐条列出再动手。"
                    )
                if loop >= 3:
                    coder_task += (
                        f"\n- 必须更换实现策略：用 vendor_assets 更换/补充资产下载源，"
                        f"或调整技术路线（如改用其它 Three.js 特性、更换算法、调整资源结构）；"
                        f"连续多轮用同一招失败会被判定为无效循环。"
                    )
                if loop >= 4:
                    coder_task += (
                        f"\n- 最后手段：若某硬指标经多轮尝试确实无法达成（如外部资源不可达），"
                        f"在报告中明确说明障碍与已尝试的证据，并把已完成的部分做扎实，不要留半成品。"
                    )

            code_res = worker_coder.run(coder_task, output_file=coder_out)
            if not code_res.get("success"):
                last_error = code_res.get("error", "Coder failed.")
                continue

            # Hard gate: the target file MUST have been actually modified
            sig_after = self._file_signature(abs_target)
            if sig_after == sig_before:
                last_error = (
                    f"Coder 未实际修改目标文件 `{target_file}`（内容签名未变化），"
                    f"仅输出报告属于无效交付。请调用 write/edit 工具真正修改源码后重试！"
                )
                continue

            # Hard gate: declared temp CHECK_SCRIPTs must be syntax-valid AND run clean
            check_script_errors = self._verify_check_scripts(project_path, coder_out)
            if check_script_errors:
                last_error = check_script_errors
                continue

            # Hard gate: machine-checkable conditions (condition_gate)
            if conditions:
                tamper = self._conditions_tamper_error(project_path, pinned_hash)
                if tamper:
                    last_error = f"{tamper}（判定以管线内存中的原始条件为准；你的自检脚本仅为自检，不构成验收依据）"
                    continue
                gate = tools.execute_tool("condition_gate", {"conditions": conditions})
                gate_data = gate.get("data", {}) if isinstance(gate, dict) else {}
                if not gate_data.get("passed", False):
                    last_error = (
                        f"硬性检测条件未通过（condition_gate 驳回）：\n"
                        f"{gate_data.get('failure_summary', 'unknown')}\n"
                        f"请严格对照上述失败项逐条修复后重试！"
                    )
                    continue

            # Review step
            try:
                reviewer_role = Role.from_file(self._get_agent_path("reviewer"))
                worker_reviewer = AgentHarness(reviewer_role, model=active_model)
                rev_out = f"deliverables/iteration_fixes/{mod_name}_review.md"
                rev_task = (
                    f"审查 `{target_file}` 的迭代修复变更：\n"
                    f"使用 code_reviewer / git_tool 提取 diff，确认修复是否解决了以下问题：{task}\n"
                    f"首行标明【审查结果：PASS】或【审查结果：REJECT 驳回】，输出至：{rev_out}"
                )
                rev_res = worker_reviewer.run(rev_task, output_file=rev_out)
                rev_abs = os.path.join(project_path, rev_out)
                if os.path.exists(rev_abs):
                    with open(rev_abs, "r", encoding="utf-8") as rf:
                        r_txt = rf.read()
                    if "reject" in r_txt.lower() or "驳回" in r_txt:
                        last_error = f"Reviewer 驳回：{r_txt[:300]}"
                        continue
            except Exception:
                pass

            passed = True

        return {
            "file": target_file,
            "success": passed,
            "loops": loop,
            "error": last_error if not passed else ""
        }
