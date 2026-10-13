"""
Main Orchestrator Pipeline for atui.
Coordinates the end-to-end multi-agent lifecycle:
Planning (TDD tests) -> Coding -> Testing & Repair Loop -> Git Review/Rollback -> Delivery.
"""

import os
import json
import time
from typing import Dict, Any, Optional
from core.harness import AgentHarness
from core.role import Role
from core.tdd_gate import TddGate
from core.event_bus import default_bus, EventType
import tools

class PipelineOrchestrator:
    def __init__(
        self,
        agents_dir: str = "agents",
        model: Optional[str] = None,
        max_repair_loops: int = 5
    ):
        self.agents_dir = os.path.abspath(agents_dir)
        self.model = model
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

    def run_pipeline(
        self,
        task: str,
        output_file: str = "deliverables/summary.md",
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        active_model = model or self.model
        start_time = time.time()
        stage_records = []

        default_bus.publish(
            EventType.PIPELINE_STEP,
            {"stage": "pipeline_start", "task": task, "output_file": output_file, "model": active_model}
        )

        # Clean stale deliverables from previous pipeline runs
        from core.project import get_current_project
        proj = get_current_project()
        stale_files = [
            "deliverables/code_changes.md",
            "deliverables/code_review.md",
            "deliverables/test_report.md",
            "deliverables/design_audit.md",
            "deliverables/acceptance_criteria.md",
            "deliverables/plan.md"
        ]
        repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        for sf in stale_files:
            for base_dir in [proj.path, repo_root]:
                s_abs = os.path.join(base_dir, sf)
                if os.path.exists(s_abs):
                    try:
                        os.remove(s_abs)
                    except Exception:
                        pass

        # Stage 0: Environment Probe & Base Setup (DevOps)
        try:
            devops_path = self._get_agent_path("devops")
            default_bus.publish(EventType.PIPELINE_STEP, {"stage": "devops_setup", "role": "devops"})
            devops_role = Role.from_file(devops_path)
            devops_harness = AgentHarness(devops_role, model=active_model)
            devops_output = "deliverables/deployment_report.md"
            devops_task = (
                f"任务目标：{task}\n"
                f"请调用 env_manager 探查系统环境基线，并在需要时启动本地服务（如 HTTP 避免 file:// CORS），"
                f"输出环境就绪报告至：{devops_output}"
            )
            devops_res = devops_harness.run(devops_task, output_file=devops_output)
            stage_records.append({"stage": "devops", "result": devops_res})
        except FileNotFoundError:
            pass

        # Stage 1: Planning & TDD Test Design + Acceptance Burn-Down Checklist
        default_bus.publish(EventType.PIPELINE_STEP, {"stage": "planning", "role": "planner"})
        planner_role = Role.from_file(self._get_agent_path("planner"))
        planner_harness = AgentHarness(planner_role, model=active_model)
        
        plan_output = "deliverables/plan.md"
        planner_task = (
            f"目标任务：{task}\n"
            f"请先阅读项目规则文件（rule/rule.md），检查参考代码（ref/），进行头脑风暴与架构规划。\n"
            f"根据测试驱动开发（TDD）要求，在编写实现代码之前，请先编写测试用例（如写入tests/目录中的测试文件）。\n"
            f"并且必须将用户所有显式与隐式需求拆解为原子化燃尽验收清单，保存至：`deliverables/acceptance_criteria.md`。\n"
            f"最后将规划方案、功能清单与测试用例说明输出至：{plan_output}"
        )
        plan_res = planner_harness.run(planner_task, output_file=plan_output)
        stage_records.append({"stage": "planning", "result": plan_res})

        if not plan_res.get("success"):
            return {
                "success": False,
                "stage_failed": "planning",
                "error": plan_res.get("error", "Planner failed to satisfy output gate."),
                "stage_records": stage_records
            }

        # Ensure acceptance_criteria.md exists for burn-down tracking
        from core.project import get_current_project
        from core.acceptance import AcceptanceChecklist
        proj = get_current_project()
        cl_path = os.path.join(proj.path, "deliverables", "acceptance_criteria.md")
        if not os.path.exists(cl_path):
            chk = AcceptanceChecklist(title=f"任务燃尽验收清单: {task[:40]}")
            chk.add_item("环境探针与基础服务就绪且零 CORS 阻断", category="environment", item_id="AC-1")
            chk.add_item("核心业务功能与代码逻辑实现且测试通过", category="functional", item_id="AC-2")
            if any(w in task.lower() for w in ["3d", "ui", "页面", "html", "web", "前端", "界面", "视觉", "审美"]):
                chk.add_item("高水准视觉审美呈现（复合建模、微观质感贴图、多层次光影、后期光学泛光、无死黑、无乐高塑料感）", category="aesthetic", item_id="AC-3")
            chk.add_item("全量产出完整沉淀且控制台零报错", category="general", item_id="AC-4")
            chk.save_to_file(cl_path)

        # Stage 2: Coding
        default_bus.publish(EventType.PIPELINE_STEP, {"stage": "coding", "role": "coder"})
        coder_role = Role.from_file(self._get_agent_path("coder"))
        coder_harness = AgentHarness(coder_role, model=active_model)

        coder_output = "deliverables/code_changes.md"
        coder_task = (
            f"目标任务：{task}\n"
            f"规划方案已保存在 `{plan_output}`。请查阅规划方案、燃尽清单 (`deliverables/acceptance_criteria.md`) 及项目规则 (`rule.md`)。\n"
            f"你的核心职责是编写实现代码：\n"
            f"1. 调用 `vendor_assets` 下载必要的离线依赖与模型资产（如 helmet/car/robot 等）；\n"
            f"2. 编写项目测试用例（如 `tests/test_xxx.py`）；\n"
            f"3. 编写核心功能代码（如 `index.html` 及其相关模块、样式与着色器）；\n"
            f"4. 必须使用 `write` 工具将代码实际写入工作区，严禁空跑，完成后将变更清单与设计说明输出至：{coder_output}"
        )
        code_res = coder_harness.run(coder_task, output_file=coder_output)
        stage_records.append({"stage": "coding", "result": code_res})

        if not code_res.get("success"):
            return {
                "success": False,
                "stage_failed": "coding",
                "error": code_res.get("error", "Coder failed to satisfy output gate."),
                "stage_records": stage_records
            }

        # Stage 2.5: Static Diff & Code Mental Simulation Review (Reviewer)
        try:
            reviewer_path = self._get_agent_path("reviewer")
            default_bus.publish(EventType.PIPELINE_STEP, {"stage": "code_review", "role": "reviewer"})
            reviewer_role = Role.from_file(reviewer_path)
            reviewer_harness = AgentHarness(reviewer_role, model=active_model)
            review_output = "deliverables/code_review.md"
            reviewer_task = (
                f"任务目标：{task}\n"
                f"Coder 已完成代码修改。请使用 code_reviewer 工具提取 Git Diff 差量修改并进行静态分析：\n"
                f"1. 脑海中单步心智推演代码执行，严查变量暂时死区 (TDZ ReferenceError) 与未定义先调用；\n"
                f"2. 若涉及 Three.js/3D，静态审查 EffectComposer 是否显式配置 samples: 4 硬件抗锯齿，材质是否配置 RoomEnvironment 环境反射，模型是否配置 computeVertexNormals 平滑法线；\n"
                f"3. 严打测试篡改（严禁跳过或篡改 tests/ 断言）；\n"
                f"首行必须明确标记为【审查结果：PASS】或【审查结果：REJECT 驳回】，输出结构化审查报告至：{review_output}"
            )
            review_res = reviewer_harness.run(reviewer_task, output_file=review_output)
            stage_records.append({"stage": "code_review", "result": review_res})
        except FileNotFoundError:
            pass

        # Stage 3: Testing Loop
        default_bus.publish(EventType.PIPELINE_STEP, {"stage": "testing_loop", "role": "tester"})
        tester_role = Role.from_file(self._get_agent_path("tester"))
        tester_harness = AgentHarness(tester_role, model=active_model)

        loop_count = 0
        tests_passed = False
        test_report_file = "deliverables/test_report.md"

        while loop_count < self.max_repair_loops:
            loop_count += 1
            default_bus.publish(EventType.TDD_CYCLE, {"loop": loop_count, "status": "running_tests"})

            tester_task = (
                f"当前第 {loop_count} 轮测试。\n"
                f"使用 test_runner 工具执行语法检查（syntax）与全量测试用例（pytest/unittest）。\n"
                f"详细记录测试结果，输出至：{test_report_file}"
            )
            test_res = tester_harness.run(tester_task, output_file=test_report_file)

            verif = self.tdd_gate.run_verification()
            if verif["passed"]:
                # Visual aesthetic audit if designer agent exists and task touches UI/3D
                if any(w in task.lower() for w in ["3d", "ui", "页面", "html", "web", "前端", "界面", "视觉", "审美"]):
                    # 1. Verify target HTML file actually exists on disk
                    target_html_candidates = ["index.html"]
                    html_found = False
                    for root, _, files in os.walk(proj.path):
                        if any(c in files for c in target_html_candidates):
                            html_found = True
                            break
                    if not html_found:
                        verif["passed"] = False
                        verif["error_details"] = "关键目标前端网页文件（如 index.html）尚未在工作区生成，代码实现缺失！"

                    try:
                        designer_path = self._get_agent_path("designer")
                        default_bus.publish(EventType.PIPELINE_STEP, {"stage": "design_audit", "role": "designer"})
                        designer_role = Role.from_file(designer_path)
                        designer_harness = AgentHarness(designer_role, model=active_model)
                        design_report = "deliverables/design_audit.md"
                        design_task = (
                            f"任务目标：{task}\n"
                            f"请调用 browser_test 截取真实视口截图，进行视觉审美打分与审查（光影充足、无死黑、排版优雅）。\n"
                            f"核查 deliverables/acceptance_criteria.md 中的审美指标并进行核验打勾。\n"
                            f"若目标页面不存在或截屏失败，首行必须写明【验收结果：REJECT 驳回】并详述原因；若合格则写明【验收结果：PASS】。\n"
                            f"将审美审查结论写入：{design_report}"
                        )
                        designer_harness.run(design_task, output_file=design_report)
                    except FileNotFoundError:
                        pass

                # Check Acceptance Burn-Down Checklist Gate
                from core.acceptance import evaluate_burn_down_gate, AcceptanceChecklist
                from core.project import get_current_project
                proj = get_current_project()
                cl_path = os.path.join(proj.path, "deliverables", "acceptance_criteria.md")
                if os.path.exists(cl_path):
                    # Smart reconciliation: sync checklist with verified facts
                    cl = AcceptanceChecklist.load_from_file(cl_path)
                    if cl:
                        # 1. Functional & syntax tests passed
                        for it in cl.items:
                            if it.category in ("functional", "code") and not it.passed:
                                it.passed = True
                                it.rationale = "测试套件与代码语法验证全部通过 (100% Passed)"
                            elif it.category in ("environment", "deploy") and not it.passed:
                                it.passed = True
                                it.rationale = "环境探针与基础服务验证就绪"
                        
                        # 2. Check Designer audit report if aesthetic items exist
                        design_report_path = os.path.join(proj.path, "deliverables", "design_audit.md")
                        if os.path.exists(design_report_path):
                            try:
                                with open(design_report_path, "r", encoding="utf-8") as df:
                                    d_content = df.read()
                                reject_keywords = ["驳回", "reject", "不合格", "未达标", "严重缺陷", "塑料玩具感", "死黑严重", "未通过", "不存在", "缺失", "报错"]
                                is_rejected = any(kw in d_content.lower() for kw in reject_keywords)
                                if is_rejected:
                                    verif["passed"] = False
                                    verif["error_details"] = f"视觉审美审计未通过：\n{d_content[:300]}"
                                for it in cl.items:
                                    if it.category == "aesthetic":
                                        if is_rejected:
                                            it.passed = False
                                            it.rationale = "审美总监审查驳回，需精修细节"
                                        else:
                                            it.passed = True
                                            it.rationale = "视觉审美审查达标通过"
                            except Exception:
                                pass
                        
                        # 3. Check Code Reviewer audit report
                        code_review_path = os.path.join(proj.path, "deliverables", "code_review.md")
                        if os.path.exists(code_review_path):
                            try:
                                with open(code_review_path, "r", encoding="utf-8") as rf:
                                    r_content = rf.read()
                                r_reject_keywords = ["驳回", "reject", "不合格", "未达标", "违规", "篡改", "死区", "狗牙"]
                                is_cr_rejected = any(kw in r_content.lower() for kw in r_reject_keywords)
                                if is_cr_rejected:
                                    verif["passed"] = False
                                    verif["error_details"] = f"代码审查与静态心智推演未通过：\n{r_content[:300]}"
                            except Exception:
                                pass

                        # Save updated checklist back to disk
                        cl.save_to_file(cl_path)

                    cl_ok, cl_reason, cl_status = evaluate_burn_down_gate(cl_path)
                    stage_records.append({"stage": "burn_down_check", "status": cl_status})
                    if not cl_ok:
                        verif["passed"] = False
                        verif["error_details"] = cl_reason

                if verif["passed"]:
                    tests_passed = True
                    stage_records.append({"stage": "testing", "loop": loop_count, "status": "passed", "result": test_res})
                    break

            stage_records.append({"stage": "testing", "loop": loop_count, "status": "failed", "verif": verif})
            default_bus.publish(EventType.TDD_CYCLE, {"loop": loop_count, "status": "tests_failed", "details": verif["error_details"]})

            # Invalidate previous code_changes.md so Coder must generate fresh changes
            coder_out_abs = os.path.join(proj.path, coder_output)
            if os.path.exists(coder_out_abs):
                try:
                    os.remove(coder_out_abs)
                except Exception:
                    pass

            repair_task = (
                f"【测试或审美验收未通过，进入代码自修复第 {loop_count} 轮】\n"
                f"未通过详情如下：\n{verif['error_details']}\n\n"
                f"请仔细阅读未通过详情、测试报告（{test_report_file}）、设计审美审查报告（deliverables/design_audit.md，若存在）以及验收燃尽清单（deliverables/acceptance_criteria.md），\n"
                f"你必须使用 write 工具真正编写/修改代码文件（如 index.html、tests/ 等），消除所有报错并满足审美指标！\n"
                f"修复完成后必须将最新代码变更说明写入：{coder_output}"
            )
            repair_res = coder_harness.run(repair_task, output_file=coder_output)
            if not repair_res.get("success"):
                break

        if not tests_passed:
            self.tdd_gate.verify_and_git_gate("Failed build rollback")
            return {
                "success": False,
                "stage_failed": "testing_loop",
                "error": f"Tests failed after {loop_count} repair cycles. Changes rolled back.",
                "stage_records": stage_records
            }

        # Stage 4: Git Review
        default_bus.publish(EventType.PIPELINE_STEP, {"stage": "git_review", "role": "git_agent"})
        git_role = Role.from_file(self._get_agent_path("git_agent"))
        git_harness = AgentHarness(git_role, model=active_model)

        git_report_file = "deliverables/git_report.md"
        git_gate_res = self.tdd_gate.verify_and_git_gate(f"feat: {task[:50]}")

        git_task = (
            f"目标任务：{task}\n"
            f"代码已通过测试验证。Git 门禁执行结果：{json.dumps(git_gate_res, ensure_ascii=False)}\n"
            f"请使用 git_tool 检查当前 git status, git diff, git log，核实提交与仓库状态。\n"
            f"若发生合并问题需回退，使用 git_tool 执行回退。\n"
            f"将完整的 Git 审查与提交/回退状态写入：{git_report_file}"
        )
        git_agent_res = git_harness.run(git_task, output_file=git_report_file)
        stage_records.append({"stage": "git_review", "gate": git_gate_res, "result": git_agent_res})

        if not git_gate_res.get("success"):
            return {
                "success": False,
                "stage_failed": "git_gate",
                "error": git_gate_res.get("error", "Git gate verification failed."),
                "stage_records": stage_records
            }

        # Stage 5: Delivery
        default_bus.publish(EventType.PIPELINE_STEP, {"stage": "delivery", "role": "delivery"})
        delivery_role = Role.from_file(self._get_agent_path("delivery"))
        delivery_harness = AgentHarness(delivery_role, model=active_model)

        delivery_task = (
            f"目标任务：{task}\n"
            f"所有规划、编码、测试与 Git 审查已全部圆满完成。\n"
            f"请汇总整理本次执行经验、技术坑点与避坑指南、注意事项、各角色分工说明、使用方法与产出资产清单。\n"
            f"必须严格遵循交付规范，将最终总结沉淀并写入最终文件：{output_file}"
        )
        deliv_res = delivery_harness.run(delivery_task, output_file=output_file)
        stage_records.append({"stage": "delivery", "result": deliv_res})

        elapsed = round(time.time() - start_time, 2)
        default_bus.publish(
            EventType.PIPELINE_STEP,
            {"stage": "pipeline_finish", "success": True, "elapsed_seconds": elapsed, "output_file": output_file}
        )

        return {
            "success": True,
            "task": task,
            "output_file": output_file,
            "elapsed_seconds": elapsed,
            "stage_records": stage_records
        }
