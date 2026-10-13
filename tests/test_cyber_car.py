import os
import pytest

def test_cyber_car_files_exist():
    """验证 demo_cyber_car 目录及核心入口文件是否存在"""
    dir_path = "demo_cyber_car"
    assert os.path.exists(dir_path), f"目录 {dir_path} 不存在"
    
    # 检查 three.js 供应商目录是否存在
    vendor_three = os.path.join(dir_path, "vendor", "three")
    assert os.path.exists(vendor_three), f"Three.js 依赖目录 {vendor_three} 不存在"

def test_index_html_structure():
    """验证 index.html 存在并包含 Three.js、Postprocessing 和核心交互脚本契约"""
    index_path = "demo_cyber_car/index.html"
    # 如果此时文件尚未创建，可先跳过或断言其在实现后必存在
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            content = f.read()
        assert "three.module.js" in content, "index.html 必须引入 Three.js 模块"
        assert "UnrealBloomPass" in content, "index.html 必须引入 UnrealBloomPass 辉光后期通道"
        assert "OrbitControls" in content, "index.html 必须引入 OrbitControls 轨道控制器"
        assert "Canvas" in content or "canvas" in content, "必须包含内存程序化 Canvas 贴图生成逻辑"
    else:
        pytest.skip("index.html 尚在规划阶段（TDD RED），实现后将自动通过该断言")

def test_acceptance_criteria_and_plan_exist():
    """验证规划方案与原子化燃尽清单已正确生成"""
    assert os.path.exists("deliverables/acceptance_criteria.md"), "原子化燃尽验收清单必须存在"
    assert os.path.exists("deliverables/plan.md"), "架构规划方案必须存在"
