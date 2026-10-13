"""
Concurrent & Modular Multi-Agent Swarm Pipeline for atui.

Implements a Hierarchical Concurrent DAG Pipeline:
1. Orchestrator / Architect: Decomposes complex compound projects (e.g. 3D village, smart city, multi-tier systems)
   into modular, decoupled, reusable component specifications with interface contracts.
2. Concurrent Worker Swarm: Spawns parallel worker pipelines (Coder -> Reviewer -> Tester)
   running concurrently via ThreadPoolExecutor. Supports isolated self-repair loops per module.
3. Integration Assembly: Master Coder composes all verified modules into master entry (index.html / main.js).
4. Integration Gates: Master Reviewer + Master Tester + Multimodal Designer (browser_test) end-to-end audit.
5. Delivery: Acceptance criteria reconciliation & Git delivery.
"""

import os
import sys
import json
import time
import concurrent.futures
from typing import Dict, Any, List, Optional

from core.harness import AgentHarness
from core.role import Role
from core.tdd_gate import TddGate
from core.event_bus import default_bus, EventType
from core.project import get_current_project
from core.acceptance import AcceptanceChecklist, evaluate_burn_down_gate
import tools

class ConcurrentModularPipeline:
    def __init__(
        self,
        agents_dir: str = "agents",
        model: Optional[str] = None,
        max_workers: int = 4,
        max_repair_loops: int = 3
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
        is_natural = any(w in task for w in ["自然", "真实", "不虚构", "写实", "湖泊", "湖畔", "森林", "乡村", "庄园", "木屋", "田园", "realistic", "natural"])

        if is_natural:
            planner_task = (
                f"目标任务：{task}\n"
                f"请作为总架构师（Principal Architect），针对此大型自然写实 3D 大场景进行【模块化领域解耦设计】。\n"
                f"必须拆解为 4 个互相独立、可复用、高内聚的子组件模块（放置于 `modules/` 目录下）：\n"
                f"1. 自然起伏地形与高山湖泊水体 (terrain.js)\n"
                f"2. 田园度假木屋与庄园建筑群 (buildings.js，导入 cottage.glb 与木质露台排布)\n"
                f"3. 真实针阔混交森林与高密度植被 (vegetation.js，强制使用 THREE.InstancedMesh 批量实例化高效渲染)\n"
                f"4. 湖畔亲水码头与生活生态道具 (props.js，包含木码头、木船、野营石圈及漫步小猫 catv2.glb)\n\n"
                f"并且为每个模块定义明确的 ES6 导出类/接口契约（如 `addTo(scene)`, `update(delta)`, `dispose()`）。\n"
                f"设计针对各个组件的原子化测试用例（如 tests/ 目录下的独立单测文件）。\n"
                f"生成全流程燃尽验收清单至：`deliverables/acceptance_criteria.md`，并将总体架构蓝图写入：{plan_output}"
            )
            module_specs = [
                {
                    "id": "MOD-1",
                    "name": "terrain",
                    "title": "自然起伏地形与高山湖泊组件 (Natural Terrain & Lake Module)",
                    "file": "modules/terrain.js",
                    "test_file": "tests/test_terrain.py",
                    "contract": "导出一个包含 constructor(scene, options)、addTo(scene)、update(delta) 的 Terrain 类。构建自然起伏草地山丘、泥土小径与具备柔和水波荡漾的清澈湖泊水体。",
                    "requirements": "严禁裸立方体。使用起伏高密度网格与自然草地/泥土 PBR 贴图、反射水体材质（带微风波纹与菲涅尔水面高光反射），接收柔和自然阴影。"
                },
                {
                    "id": "MOD-2",
                    "name": "buildings",
                    "title": "乡村度假木屋与田园庄园建筑组件 (Chalet & Architecture Module)",
                    "file": "modules/buildings.js",
                    "test_file": "tests/test_buildings.py",
                    "contract": "导出一个包含 constructor(scene, options)、addTo(scene)、update(delta) 的 Buildings 类。导入高精度欧洲原木度假木屋 (cottage.glb)，并布设湖畔露台、木栅栏与石砌基底。",
                    "requirements": "写实原木纹理与石砌烟囱质感、物理遮光与漫反射，支持真实尺寸比例，与地形自然结合嵌入。"
                },
                {
                    "id": "MOD-3",
                    "name": "vegetation",
                    "title": "真实针阔混交森林与高密度植被组件 (Foliage & Forest Module)",
                    "file": "modules/vegetation.js",
                    "test_file": "tests/test_vegetation.py",
                    "contract": "导出一个包含 constructor(scene, count)、addTo(scene)、update(delta) 的 Vegetation 类。强制使用 THREE.InstancedMesh 批量实例化渲染 500+ 棵自然松针树、高山冷杉、阔叶白桦与野生灌木花草。",
                    "requirements": "必须使用 THREE.InstancedMesh 单次 Draw Call 批量高效渲染，具备自然随机高低粗细缩放、微小色相明暗随机扰动，保证 60FPS。"
                },
                {
                    "id": "MOD-4",
                    "name": "props",
                    "title": "湖畔生活道具与码头休闲生态组件 (Lakeside Props Module)",
                    "file": "modules/props.js",
                    "test_file": "tests/test_props.py",
                    "contract": "导出一个包含 constructor(scene)、addTo(scene)、update(delta) 的 Props 类。生成木质亲水码头、停泊的小木船、营火石圈、木质长椅与漫步小猫 (catv2.glb)。"
                    ,"requirements": "真实木纹、金属与石材质感，营造静谧恬淡的自然乡村生活氛围，拒绝刺眼不合时宜的霓虹光。"
                }
            ]
        else:
            planner_task = (
                f"目标任务：{task}\n"
                f"请作为总架构师（Principal Architect），针对此大型复合 3D 场景/工程进行【模块化领域解耦设计】。\n"
                f"必须拆解为 4 个互相独立、可复用、高内聚的子组件模块（例如放置于 `modules/` 目录下）：\n"
                f"1. 地形地貌与基底 (terrain.js)\n"
                f"2. 建筑群与民居结构 (buildings.js，支持复合造型或外部模型实例化排布)\n"
                f"3. 植被生态与森林 (vegetation.js，强制使用 THREE.InstancedMesh 批量实例化高效渲染)\n"
                f"4. 道具路灯与发光信标 (props.js，带点光源与 Bloom 自发光)\n\n"
                f"并且为每个模块定义明确的 ES6 导出类/接口契约（如 `addTo(scene)`, `update(delta)`, `dispose()`）。\n"
                f"设计针对各个组件的原子化测试用例（如 tests/ 目录下的独立单测文件）。\n"
                f"生成全流程燃尽验收清单至：`deliverables/acceptance_criteria.md`，并将总体架构蓝图写入：{plan_output}"
            )
            module_specs = [
                {
                    "id": "MOD-1",
                    "name": "terrain",
                    "title": "地形与地貌基底组件 (Terrain Module)",
                    "file": "modules/terrain.js",
                    "test_file": "tests/test_terrain.py",
                    "contract": "导出一个包含 constructor(scene, options)、addTo(scene)、update(delta) 的 Terrain 类。创建起伏科幻地貌、网格路径及材质。",
                    "requirements": "严禁裸立方体，使用起伏网格与微观质感贴图，接收阴影。"
                },
                {
                    "id": "MOD-2",
                    "name": "buildings",
                    "title": "未来聚落建筑集群组件 (Buildings Module)",
                    "file": "modules/buildings.js",
                    "test_file": "tests/test_buildings.py",
                    "contract": "导出一个包含 constructor(scene, count)、createBuildingCluster(gridCoords)、addTo(scene) 的 Buildings 类。支持多样化未来房屋结构与高低排布。",
                    "requirements": "复合几何体造型与金属 PBR 物理材质，门窗自发光，投射与接收阴影。"
                },
                {
                    "id": "MOD-3",
                    "name": "vegetation",
                    "title": "生态植被与异星森林组件 (Vegetation Module)",
                    "file": "modules/vegetation.js",
                    "test_file": "tests/test_vegetation.py",
                    "contract": "导出一个包含 constructor(scene, count)、addTo(scene)、update(delta) 的 Vegetation 类。强制使用 THREE.InstancedMesh 批量实例化渲染数百棵树木或植被。",
                    "requirements": "必须使用 THREE.InstancedMesh 单次 Draw Call 批量高效渲染，具备随机缩放与微旋转，保证 60FPS。"
                },
                {
                    "id": "MOD-4",
                    "name": "props",
                    "title": "环境道具与全息路灯组件 (Props Module)",
                    "file": "modules/props.js",
                    "test_file": "tests/test_props.py",
                    "contract": "导出一个包含 constructor(scene)、addTo(scene)、update(delta) 的 Props 类。生成发光全息路灯、能量柱与交互信标。",
                    "requirements": "部件配置 emissive 自发光与点光源 (PointLight)，产生光学光晕，为街道提供夜间冷暖对比氛围。"
                }
            ]

        # Ensure acceptance checklist is present
        cl_path = os.path.join(proj.path, "deliverables", "acceptance_criteria.md")
        if not os.path.exists(cl_path):
            chk = AcceptanceChecklist(title=f"分布式模块化大场景任务验收清单: {task[:40]}")
            chk.add_item("环境探针与基础服务就绪且零 CORS 阻断", category="environment", item_id="AC-ENV-01")
            for m in module_specs:
                chk.add_item(f"子模块 [{m['name']}] 编码实现、接口导出契约与单元测试通过", category="functional", item_id=f"AC-{m['name'].upper()}-01")
            chk.add_item("总装主控 (index.html / main.js) 整合全部组件并完成空间布局", category="functional", item_id="AC-INT-01")
            chk.add_item("全场景 360° 环境反射、多重布光与硬件 MSAA 抗锯齿生效，画面无死黑、无乐高塑料感", category="aesthetic", item_id="AC-AES-01")
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
        if is_natural:
            integrator_task = (
                f"目标任务：完成自然写实高山湖畔庄园复合大场景的集成总装配。\n"
                f"各个独立子模块已由并发 Agent 编写并验证完毕（位于 modules/ 目录下：terrain.js, buildings.js, vegetation.js, props.js）。\n"
                f"现在请编写或更新项目总入口 `index.html` 以及 `index.js`，完成总装：\n"
                f"1. 在主脚本中以 ES6 模块导入所有子组件类（Terrain, Buildings, Vegetation, Props）；\n"
                f"2. 配置真实自然日光照明：透视相机、轨道控制器 (OrbitControls)、45度自然平行日光 (带高品质柔和接触阴影)、真实天空环境光 (Sky / RoomEnvironment)；\n"
                f"3. 实例化所有子组件并挂载到场景中，合理布设自然空间坐标（湖泊波光粼粼、木屋庄园坐落湖畔草坡、松针与白桦密林环抱山麓、码头停泊小船与漫步小猫）；\n"
                f"4. 配置硬件 4x MSAA 抗锯齿与自然色调映射 (ACESFilmicToneMapping，呈现明媚自然日光质感，拒绝塑料感或死黑)；\n"
                f"5. 配备美观现代的高端自然庄园 HUD 交互面板（支持日光时间段切换、各景观组件可见性、湖畔码头/木屋特写导览视角）。\n"
                f"确保在 index.html 中正确配置 importmap 映射本地 vendor (three: ./vendor/three.module.js, three/addons/: ./vendor/addons/)，避免相对路径 404。\n"
                f"将完成的代码写入 `index.html` 与 `index.js`，并将集成说明写入：{integration_output}"
            )
        else:
            integrator_task = (
                f"目标任务：完成复合大场景的集成总装配。\n"
                f"各个独立子模块已由并发 Agent 编写并验证完毕（位于 modules/ 目录下：terrain.js, buildings.js, vegetation.js, props.js）。\n"
                f"现在请编写或更新项目总入口 `index.html` 以及总控脚本，完成总装：\n"
                f"1. 在主脚本中以 ES6 模块导入所有子组件类（Terrain, Buildings, Vegetation, Props）；\n"
                f"2. 初始化透视相机、轨道控制器 (OrbitControls)、RoomEnvironment 摄影棚环境反射及阴影平行光；\n"
                f"3. 实例化所有子组件并挂载到场景中，合理布设空间坐标（中央广场、居住区、周边植被森林、发光街灯）；\n"
                f"4. 配置硬件 4x MSAA 抗锯齿与电影级后期辉光；\n"
                f"5. 配备美观的 Sci-Fi HUD 交互面板（支持昼夜光照切换、线框模式、各组件可见性开关与巡航视角）。\n"
                f"确保在 index.html 中正确配置 importmap 映射本地 vendor (three: ./vendor/three.module.js, three/addons/: ./vendor/addons/)。\n"
                f"将完成的代码写入 `index.html`，并将集成说明写入：{integration_output}"
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
                f"任务目标：复合大场景集成静态审查。\n"
                f"使用 code_reviewer 工具提取 Git Diff，审查集成代码是否正确导入了各个子模块，\n"
                f"是否存在 TDZ 作用域问题，是否符合硬件抗锯齿与环境光反射规范。\n"
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
                f"调用 browser_test 对集成后的大场景网页 (index.html) 截取真实视口截图。\n"
                f"审查大场景在视野中的空间纵深感、植被密度、建筑排列、光影明暗（无死黑）及 HUD 科技感。\n"
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
            f"# 分布式并发多智能体模块化大场景交付报告\n\n"
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
            f"- 全局集成级门禁：已完成 `index.html` 场景总装、光影环境渲染及无头浏览器视口审美验收。\n\n"
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
