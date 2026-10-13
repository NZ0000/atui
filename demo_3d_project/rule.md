# 3D 场景开发工程规范

1. **项目自包含性**：所有源码、资源和产出必须存放在本目录（`demo_3d_project`）中。
2. **纯前端免安装**：3D 场景主程序必须为 `index.html`，通过现代 ESM（如 unpkg/cdnjs/skypack 的 Three.js r160+）引入依赖，无需 npm build 即可直接在任何现代浏览器中双击或通过静态服务器打开。
3. **零外部缺失资源风险**：严禁引用未经本地提供或可能 404 的外部 3D 模型资产（.gltf, .obj, .fbx），必须全部使用 Three.js 原生几何体（Box, Cylinder, Torus, Sphere 等）进行程序化建模。
4. **高质量视效与交互规范**：
   - 具备充沛明亮的多重光照体系（环境光 AmbientLight + 半球天光 HemisphereLight 漫反射 + 主定向光 DirectionalLight 投射阴影 + 逆向边缘轮廓光 Rim Light + 彩色发光点光源），PBR 材质（MeshStandardMaterial）必须具备清晰的反射细节与金属高光，**严禁大面积死黑无光**。
   - 支持 OrbitControls 鼠标旋转缩放阻尼以及窗口 resize 响应。
   - 提供基于 Raycaster 的鼠标部件悬停检测与高亮/HUD信息卡片展示。
   - 必须提供动画循环（THREE.Clock 计算 delta）。
   - 必须主动调用 `browser_test` 进行无头浏览器控制台报错捕获与视口截图视觉审查，确保无任何控制台报错且画面通透明亮。
5. **交付产出**：
   - 场景主页面：`index.html`
   - 交付总结说明：`deliverables/summary.md` 或指定输出路径。
