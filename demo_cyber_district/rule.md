# 复合多模型大场景工程规范与目标 (Sci-Fi Cyber District 3D Composite Showcase)

严格遵循全局通用规范（`rule/rule.md`）与分布式模块化架构：

## 一、组件模块化与代码复用规范
1. **ES6 模块高内聚组件化**：
   - 严禁单体巨型单文件，各个领域功能必须抽象为独立可复用类并放置于 `modules/` 目录：
     - `modules/terrain.js`：地形地貌、起伏科技网格与基底底盘；
     - `modules/buildings.js`：未来建筑集群，支持结构参数化与网格空间排布；
     - `modules/vegetation.js`：异星森林与生态植被，**强制使用 `THREE.InstancedMesh` 批量实例化高效渲染**，实现数百株植被单次 Draw Call 60FPS 流畅运行；
     - `modules/props.js`：环境道具、全息路灯与能量信标，配备点光源与 Bloom 自发光。
2. **标准化生命周期契约**：
   - 每个模块统一实现 `addTo(scene)`、`update(delta)` 等标准化生命周期接口。

## 二、两级门禁与质量守门 (Two-Tier Quality Gates)
1. **第一级（单元级门禁）**：
   - 每个子模块必须在 `tests/` 目录下配有独立单元测试（`test_terrain.py`, `test_buildings.py`, `test_vegetation.py`, `test_props.py`），验证类导出与语法。
   - Reviewer 智能体对各模块进行增量 Diff 走查与 TDZ 静态心智推演。
2. **第二级（全局集成级门禁）**：
   - 总装主控 `index.html` 导入全部子组件并布设合理空间坐标；
   - 配置 `RoomEnvironment` 360° 摄影棚环境反射贴图，彻底消除金属旋转背光死黑；
   - 启用 WebGL 2 硬件 4x MSAA 抗锯齿与电影级后期辉光；
   - 必须通过 `browser_test` 在真实无头浏览器环境下进行多模态审美审查（全景与细节透视）。
