# 3D 场景开发工程规范

1. **项目自包含性**：所有源码、资源和产出必须存放在本工程目录（`demo_3d_project`）中。
2. **纯前端免安装**：3D 场景主程序必须为 `index.html`，通过现代 ESM（如 unpkg/cdnjs/skypack 的 Three.js r160+）引入依赖，无需 npm build 即可直接在任何现代浏览器中双击或通过静态服务器即时打开。
3. **模型资产规范（支持高精外部模型或高水准程序化构建）**：
   - **外部高精模型支持**：完全支持并鼓励引用工业级外部 `.gltf` / `.glb` / `.obj` 3D 资产；若使用外部资产，必须通过本地存储或 `vendor_assets` 工具下载缓存到本地，彻底消除由于 CDN 失效或网络断开导致的 404 加载风险。
   - **程序化建模规范（杜绝塑料积木/乐高感）**：若采用纯代码程序化构建，**严禁裸拼基础几何体**！必须遵循行业 AAA 标准：
     - 在内存中通过 HTML5 Canvas 动态绘制程序化科幻装甲法线贴图与粗糙度贴图（**Procedural Greeble Normal Map & Roughness Map**），生成复杂的装甲刻线、接缝、排气格栅与铆钉螺栓阴影，赋予模型万吨级星舰外壳的精密机械质感。
     - 增加次级机械结构：能量导管（`TubeGeometry`）、结构桁架、阵列天线与辐射状散热片，杜绝单一简单立方体堆叠。
4. **高质量光影与电影级后期规范**：
   - **充沛的多重光照体系**：环境光 AmbientLight + 半球天光 HemisphereLight 漫反射 + 主定向光 DirectionalLight 投射阴影 + 逆向边缘轮廓光 Rim Light + 反应堆脉冲霓虹点光，PBR 材质（MeshStandardMaterial）必须具备清透的反光与金属高光，严禁大面积死黑。
   - **电影级后期泛光 (Bloom / UnrealBloomPass)**：必须集成后期处理管线（`EffectComposer` + `RenderPass` + `UnrealBloomPass`），使能量核心、流光能量环、喷射离子流及霓虹线条散发沉浸式光学漫射辉光，告别实心单色线条。
   - **动态交互与遥测**：支持 OrbitControls 阻尼平滑操控、自适应窗口 resize、基于 Raycaster 的部件悬停诊断 HUD 卡片，以及动画帧时钟（`THREE.Clock`）。
   - **多模态自检**：必须主动调用 `browser_test` 进行无头浏览器控制台报错与视口截图审查，确保零报错且视觉震撼。
5. **交付产出**：
   - 场景主页面：`index.html`
   - 交付总结说明：`deliverables/summary.md`
