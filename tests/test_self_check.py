import pytest
import os
import json
from core.harness import AgentHarness
from core.role import Role
from core.tdd_gate import TddGate

def test_architecture_self_check_manifest():
    """
    ATUI 架构自检验证测试：
    验证项目架构中核心模块的完备性与正确性：
    1. 角色配置驱动与加载：验证 Role 能够正确从 agents/ 目录加载配置文件（如 planner.md）。
    2. 工具注册与插件机制：验证 tools 注册中心能正常调度基础工具（read, write, run）。
    3. TDD 门禁机制：验证 TddGate 在测试失败或缺少产出时的管控逻辑。
    4. 产出交付物检查：验证 deliverables/self_check_plan.md 是否存在。
    """
    # 1. 验证角色配置加载
    role_path = "agents/planner.md"
    assert os.path.exists(role_path), f"Role config {role_path} should exist."
    role = Role.from_file(role_path)
    assert role.name is not None

    # 2. 验证工具注册中心与插件机制
    import tools
    avail_tools = tools.list_tools()
    assert "read" in avail_tools
    assert "write" in avail_tools
    assert "run" in avail_tools

    # 3. 验证 TDD 门禁机制
    gate = TddGate(target_dir="tests")
    res = gate.run_verification(target="tests/test_role.py")
    assert isinstance(res, dict)
    assert "passed" in res

    # 4. 验证架构规划产出文件存在
    plan_file = "deliverables/self_check_plan.md"
    assert os.path.exists(plan_file), f"Deliverable {plan_file} must exist to pass gate."
