# 全局工程与智能体协作规范 (Global Harness Rules)

## 一、系统架构与设计准则
1. **万物皆插件，万物皆接口**：所有新增功能、工具和模块必须遵循独立插件规范，既支持 Python 函数模块级导入，也支持命令行参数直接运行。
2. **强解耦与高复用**：各组件与模块职责单一，杜绝巨型单文件，为后续前端（H5、App、桌面端、WebUI）预留标准化调用接口。
3. **配置与文档驱动**：统一采用 Markdown、JSON、YAML 驱动配置与状态流转。
4. **硬性成果门禁（Output Gate）**：所有 Agent 角色或执行流水线必须产生确凿成果（Markdown 文档、代码变更 Diff 或测试报告），否则判定未达标并触发自修复回路。

## 二、测试驱动开发 (TDD) 与燃尽验收准则
1. **测试先行 (TDD RED)**：在实现业务代码前，必须先编写可执行的测试用例（`tests/`），严禁无测试直接编码。
2. **全需求原子化燃尽清单 (Acceptance Burn-Down Checklist)**：
   - 规划阶段必须将任务的所有显式与隐式需求拆解为 `deliverables/acceptance_criteria.md` 中的原子化清单；
   - 涵盖环境与部署（Environment）、功能与逻辑（Functional）、视觉与审美（Aesthetic）、交付规范（General）；
   - 后续阶段各 Agent 逐项核验，全部达成勾选后方可通过门禁，杜绝模型偷懒早退。
3. **闭环自修复与安全回退**：发现测试失败、运行报错或审美驳回时，调度 Coder 进行自修复循环（至多 5 轮）；若合并造成基线破坏，调度 Git Agent 立即回退至干净提交。
4. **静态心智推演与差量审查门禁 (Static Mental Simulation & Git Diff Review Gate)**：
   - 编码完成后、进入编译与测试套件执行前，必须调度 Reviewer 进行 Git Diff 差量审查与静态心智推演；
   - **单步推演运行时状态机**：严查变量暂时死区 (TDZ ReferenceError)、空指针解引用、并发数据竞争、以及 Three.js EffectComposer 后期抗锯齿配置缺失；
   - **严格防作弊门禁**：严禁私自篡改既有测试用例断言或跳过测试；一旦发现作弊或致命逻辑死穴，立即短路驳回重写！

## 三、通用三维 (3D) 与视觉工程第一性原理（通用无题材偏见）
无论何种题材（交通工具、建筑空间、智慧城市、生物解剖、科幻概念、日用工业品或交互游戏），均必须遵循以下图形学与工程法则：
1. **反乐高积木/反简单几何体原则 (Anti-Primitive Principle)**：
   - 严禁裸拼光滑立方体、球体、圆柱体等初级几何体堆叠。
   - 必须使用复合几何体造型：旋转体 (`LatheGeometry`)、路径放样管道 (`TubeGeometry`)、挤出成型 (`ExtrudeGeometry`)、倒角削边以及多层级装配体（Group Hierarchy），构建符合题材物理规律的结构丰富度。
2. **通用内存程序化贴图工程 (Procedural Canvas Textures)**：
   - 在免构建/无外部素材网络环境下，必须利用 HTML5 2D Canvas 在内存中动态绘制**切线空间法线贴图 (Normal Map)** 与 **粗糙度贴图 (Roughness Map)**：
     - 切线空间基准为 `rgb(128,128,255)`（法向量垂直表面朝外）；
     - 结合具体题材绘制微观起伏坡度向量、接缝划线、微小凸起/凹槽、材质粗糙度色阶；
     - 赋予 PBR 物理材质 (`MeshStandardMaterial` / `MeshPhysicalMaterial`) 真实的微观光照起伏，彻底消除塑料玩具感。
3. **多层次充沛光影与电影级色调映射 (Multi-Light Hierarchy & Tonemapping)**：
   - 严禁单一白光导致的平庸死白或大面积“黑黢麻黑”死黑面。
   - 标配多重视效布光：半球环境漫反射光 (HemisphereLight) 提亮暗部冷暖质感 + 主平行光 (DirectionalLight) 投射锐利阴影 + 侧逆边缘轮廓光 (Rim Light) 勾勒主体分离背景 + 局部点聚光。
   - 开启电影级色调映射 (`ACESFilmicToneMapping`) 与合理的曝光度，确保暗部有层次、高光不过曝。
4. **光学后期泛光与硬件多重采样抗锯齿 (Optical Post-Processing & Hardware MSAA)**：
   - 现实中任何发光物体（车灯、指示灯、霓虹、射线、全息屏、能量流），若无后期处理均为实心死板色块。
   - 必须接入后期合成管线 (`EffectComposer` + `RenderPass` + `UnrealBloomPass`)，配合材质自发光 (`emissive` + `emissiveIntensity > 1.0`)，呈现电影级真实光学辉光漫射。
   - **抗锯齿防狗牙铁律**：Three.js 中一旦挂载 `EffectComposer`，硬件自带的 `antialias: true` 会被彻底绕过失效！**必须显式为 `WebGLRenderTarget` 配置 `{ samples: 4 }`（WebGL 2 硬件 4x MSAA 抗锯齿）**，彻底消除发光圈、地台边缘与几何轮廓的像素锯齿。
5. **曲面法线平滑插值 (Smooth Normal Shading)**：
   - 严禁曲面呈现生硬的低模多边形切面折痕；加载或构建模型必须确保材质开启平滑着色（`flatShading: false`），并调用 `geometry.computeVertexNormals()` 插值平滑法线。
6. **外部模型高精资产容灾标准 (Resilient External Assets)**：
   - 允许且鼓励使用工业级 `.gltf` / `.glb` / `.obj` 外部模型；
   - 必须通过本地资源管理或 `vendor_assets` 工具下载缓存到本地，严禁依赖不稳定的公网 CDN URL 导致 404 崩溃；
   - 必须编写异步加载容灾逻辑（Fallback），在外部资产缺失或加载超时时自动降级到程序化精细模型，确保 100% 正常运行。

## 四、执行能效与零冗余原则
1. **原生路径自动创建**：系统 `write` 工具原生支持递归创建任何深度的父目录。严禁在写文件前冗余调用 `mkdir -p`，严禁无目的调用 `ls -la` 浪费轮次。
2. **批量调用优先**：关联的多个工具调用优先使用 `batch_run` 一并提交，最大限度压缩 Token 消耗与往返延迟。

