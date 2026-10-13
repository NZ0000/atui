# 项目工程规范与目标 (Sci-Fi Battle Helmet 3D Showcase)

严格遵循全局通用工程与智能体协作规范（`rule/rule.md`）：
1. **测试驱动开发 (TDD) 与燃尽验收**：无测试用例不进入编码；规划阶段建立完整原子化燃尽清单 (`deliverables/acceptance_criteria.md`)，各角色逐项核验。
2. **静态心智推演与差量审查门禁 (Stage 2.5 Reviewer Gate)**：
   - 在编码完成后、测试执行前，调度 Reviewer 基于 Git Diff 审查代码；
   - 心智推演单步执行流程，严查变量暂死区 (TDZ ReferenceError)；
   - 静态核查 Three.js EffectComposer 必须显式配置 `{ samples: 4 }`（WebGL 2 硬件 4x MSAA 抗锯齿）；
   - 严查测试用例断言篡改行为。
3. **通用三维视觉第一性原理**：
   - **反积木/反简单几何体**：严禁仅堆叠光滑立方体/球体；优先调用 `vendor_assets` 工具下载并装配工业级模型资产（如 `helmet` - DamagedHelmet AAA PBR 战损头盔），且必须编写异步容灾降级渲染逻辑；
   - **360° 环境反射**：必须引入 `RoomEnvironment` + `PMREMGenerator` 离屏环境反射贴图，彻底消除金属材质旋转背光死黑；
   - **曲面法线平滑插值**：材质严禁开启面片生硬切角（`flatShading: false`），模型初始化时执行 `geometry.computeVertexNormals()`；
   - **电影级后期辉光与硬件抗锯齿**：发光部件（面罩/全息指示灯）必须接入 `EffectComposer` + `UnrealBloomPass` 产生真实光学光晕；`WebGLRenderTarget` 必须配置 `samples: 4` 硬件 MSAA 抗锯齿，消除像素狗牙。
4. **100% 离线自包含**：所有库与模型通过本地 Vendor 目录管理，杜绝外部 CDN 网络单点故障与 404 阻断。
