# demo_3d_project 局部工程运行约定

1. **项目自包含性**：本工程所有源码、静态资源与成果文件存放在 `demo_3d_project/` 目录下。
2. **纯前端免安装入口**：工程主程序为 `index.html`，通过现代 ESM 引用所需组件，可直接在静态 HTTP 服务器（如 `python3 -m http.server 8080`）或现代浏览器中运行。
3. **遵循系统全局规范**：通用 3D 渲染法则、PBR 材质规范、后期泛光与工程质量门禁，严格遵循系统根目录 `rule/rule.md`。
4. **交付产出**：
   - 场景主页面：`index.html`
   - 交付说明：`deliverables/summary.md`
