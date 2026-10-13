# 项目工程规范与目标 (Cyber Robot 3D Showcase)

严格遵循全局通用规范（`rule/rule.md`）：
1. **测试驱动开发 (TDD) 与燃尽验收**：无测试用例不进入编码；规划阶段建立完整燃尽验收清单 (`deliverables/acceptance_criteria.md`)，各角色逐项核验。
2. **通用三维视觉第一性原理**：
   - **反积木/反简单几何体**：严禁仅堆叠光滑立方体/圆柱体；优先调用 `vendor_assets` 工具下载并装配工业级模型资产（如 `robot`），且必须编写异步容灾降级渲染逻辑；
   - **360° 环境光反射**：必须引入 `RoomEnvironment` + `PMREMGenerator` 离屏环境反射贴图，彻底消除金属材质旋转背光死黑；
   - **DRACO 离线压缩支持**：配置 `DRACOLoader` 结合本地 decoder 路径，支持高压缩率三维网格秒级解压；
   - **电影级后期辉光**：发光部件必须接入 `EffectComposer` + `UnrealBloomPass` 产生真实光学光晕。
3. **100% 离线自包含**：所有库与模型通过本地 Vendor 目录管理，杜绝外部网络单点故障与 404 阻断。
