# 天魁 (atui) — 自主进化终端智能体 Harness 系统

<p align="center">
  <b>天魁 (atui)</b> —— 命名取自三十六天罡之首“天魁星”，意为领袖群伦、统筹全局。<br>
  英文名 <b>atui</b> (Autonomous Terminal User & Agent Harness)，是一个以<b>测试驱动开发 (TDD)</b> 为核心、深度依托<b>强大的 Python 生态</b>、具备<b>真实自我进化能力</b>的多角色自主终端智能体框架。
</p>

---

## 🌟 核心特色与架构优势

### 1. 深度依托强大的 Python 生态 (Powered by Python Ecosystem)
Python 是全球 AI、数据科学、自动化与工程运维领域无可争议的通用语言，天魁 (atui) 充分汲取了 Python 生态的工程威力：
- **动态内省与元编程能力 (Dynamic Metaprogramming & Introspection)**：
  - 借助 Python 的 `ast` 抽象语法树分析、`importlib` 动态模块加载机制、`py_compile` 静态编译检查与运行时反射，天魁能够**在毫秒级动态加载、发现并热替换任何工具插件与代码模块**，为 Agent 自身的代码编写、自我修复与热重载提供了天然的运行环境。
- **零外部强依赖的高便携底座 (Zero-Dependency Portability)**：
  - 核心底层通信、进程调度、差异对比与测试驱动完全基于 Python 3 原生标准库（`urllib.request`, `subprocess`, `difflib`, `argparse`, `json`, `tempfile`），无任何冗余臃肿第三方依赖，跨平台（Linux、macOS、Windows）极速启动。
- **无缝调度世界级工程工具链与科学计算库**：
  - 测试驱动层直连 Python 顶级测试套件 `pytest` 与 `unittest`，支持异常捕获、Traceback 堆栈精准溯源与测试快照。
  - Agent 具备无限拓展能力，可直接借助 `pip`/`venv` 无缝调用数据分析（NumPy、Pandas）、人工智能（PyTorch、HuggingFace、LangChain）、自动化采集（Playwright、Scrapy）等全球数以百万计的开源库。
- **作为 Python 库被深度集成**：
  - 支持 `from atui import run_agent, run_pipeline, switch_project`，可作为轻量级模块直接嵌入到现有 Python 后端、FastAPI 接口、桌面客户端或自动化 CI/CD 流水线中。

---

### 2. 独创的自进化闭环架构 (The Self-Evolution Architecture)

> **“万物皆文本、皆文件、皆配置、皆命令行”** —— 这是天魁实现自主进化的哲学基石。
> 智能体的提示词是 Markdown，工具是独立 Python 脚本，配置是 JSON/YAML，经验记忆是 Deliverables 文档。一切皆对智能体透明、可读、可审、可改！

```
┌────────────────────────────────────────────────────────────────────────┐
│                   天魁 (atui) 五维闭环自进化机制 (Self-Evolution)          │
└────────────────────────────────────────────────────────────────────────┘
                                     │
           1. 需求感知与架构规划 (Perception & Plan)
           智能体感知缺失能力，检索模式，先期编写 TDD 测试契约 (RED)
                                     ▼
           2. 工具与代码自生成 (Tool Synthesis & Coding)
           自主编写独立插件 tools/<new_tool>.py，实现功能逻辑
                                     ▼
           3. 自动化质量自验证 (Self-Verification Loop)
           调用 test_runner 执行 AST 解析 + 全量 Pytest，5 轮内自修复
                                     ▼
           4. 能力版本自固化 (Self-Persistence & Git Commit)
           测试全绿通过 TDD 门禁后，Git Agent 自动提交合并至版本库
                                     ▼
           5. 经验沉淀与规则反哺 (Precipitation & Rule Evolution)
           Delivery 智能体梳理踩坑点与最佳实践，反哺优化后续 Agent 提示词与规则
```

#### 实机验证的自进化闭环案例：
在实机运行中，系统接收到“扩展计算与统计分析能力”任务时：
1. **Planner 智能体**自主分析工具注册表，在 [deliverables/plan.md](file:///home/xxx/atui_harness/deliverables/plan.md) 规划新工具设计，并**先期编写了覆盖 9 个用例的单元测试 [tests/test_calc.py](file:///home/xxx/atui_harness/tests/test_calc.py)**（处于 TDD 红灯态）；
2. **Coder 智能体**根据测试要求，自主开发了符合插件标准的 [tools/calc.py](file:///home/xxx/atui_harness/tools/calc.py)；
3. **Tester 智能体**启动全量回归测试，全部 28 个测试用例 100% 绿色通过；
4. **Git Agent 智能体**通过 TDD 门禁，将新工具与测试用例自动执行 Git 提交（Commit: `84484e7`），将其永久固化为系统原生能力；
5. **动态热插拔生效**：工具注册中心 [tools/\_\_init\_\_.py](file:///home/xxx/atui_harness/tools/__init__.py) 瞬间自动识别出新工具 `calc`，使得后续任何 Agent 均可直接调用此工具！

---

### 3. 类似 Claude Code 的极致交互式终端体验 (TUI)
- **告别臃肿的原始 JSON 堆砌**：摒弃机器调试式的全量报文输出，提供清晰优雅的人性化终端视觉流。
- **轻量化动作渲染**：以精简图标（`● ⚙️ [read]`、`✔ 执行成功`、`🧪 门禁通过`）实时追踪智能体思考、工具调用与测试进展。
- **类 Claude Code REPL 交互**：自带彩色状态横幅、上下文提示符（`atui [master] ~/my-project ❯`），支持结构化 Markdown 输出渲染。
- **原生 Slash 斜杠指令体系**：集成 `/cd`、`/project`、`/rules`、`/role`、`/model`、`/pipeline`、`/git`、`/test`、`/tools`、`/clear` 等高频快捷命令。

---

### 4. 统一项目目录穿透与规则热注入 (Project Context & Rules Injection)
- **跨项目无缝工作**：无论 `atui` 部署在何处，均可通过统一接口 `/cd <项目路径>` 或 `switch_project(path)` 将当前工作区锁定在目标代码仓库。
- **自动规则发现与注入**：自动检索目标项目根目录下的 `rule/rule.md`、`rule.md`、`AGENTS.md`、`CLAUDE.md` 等规则守则，将其动态注入到智能体 System Prompt，确保智能体严格遵循目标项目的工程规范与契约。
- **会话持久化**：自动持久化当前激活项目路径至 `~/.atui_project_state.json`，随时打开即进入上次的工作上下文。

---

### 5. 全生命周期多智能体流水线 (Multi-Agent Lifecycle Pipeline)
系统内置完备的八大角色智能体，协同完成复杂软件工程闭环：
- 🌐 **部署运维与环境工程师 (DevOps)**：负责环境基线探针、依赖包自动化安装、网络通信底座（HTTP 静态伺服、WebSocket、MQTT）搭建与端口守护，彻底消除本地 `file:///` CORS 跨域痛点。
- 🧭 **规划与架构师 (Planner)**：头脑风暴、分析参考代码模式、先期设计编写 TDD 测试用例，并**强制分解原子化燃尽验收清单 (`acceptance_criteria.md`)**。
- 💻 **全栈编码与重构工程师 (Coder)**：遵循测试用例与项目规则，执行最小化高内聚编码，消除红灯。
- 🧪 **全栈质量测试专家 (Tester)**：执行 Python AST / `py_compile` / `pytest` / `unittest`、Web 语法校验 (`web_validator`)、无头 Chromium 控制台报错拦截与测试诊断。
- 🎨 **视觉设计与审美总监 (Designer)**：负责设计规范定义、文生图素材策划、调用无头浏览器截屏并依托多模态视觉感知进行审美审查打勾，坚决杜绝死黑与辣眼睛界面。
- 🌿 **版本控制与安全审计 (Git Agent)**：审计代码 Diff，通过 TDD 门禁后执行原子化 Commit；若出现破坏性变更或测试未过，果断触发 **Git Rollback 自动回退**。
- 📦 **收尾交付与知识沉淀 (Delivery)**：复盘全流程，梳理核心经验、踩坑要点（Gotchas）、使用指南并沉淀归档交付资产。
- 🧠 **主调度大脑 (Orchestrator)**：统筹上述各子角色流转、自修复循环与燃尽门禁协调。

---

### 6. 严苛的 TDD 质量门禁与燃尽验收闭环 (Burn-Down Acceptance & Self-Repair)
- **无测试，不编码**：强制实行 TDD 先行，未编写对应测试用例禁止合并。
- **原子化燃尽验收清单 (Acceptance Burn-down Checklist)**：Planner 分解出的功能、环境与审美清单必须逐项核验；未满足项拒绝退出，自动携带剩余清单打回 Coder 继续修复，直至 100% 燃尽！
- **双向自修复循环**：当 Tester 或 Designer 发现功能缺陷或视觉软缺陷时，将详细诊断反馈给 Coder，智能体在两者之间循环修复（默认上限 5 轮），直至测试全绿且视觉达标。
- **后置回归与 Git 自动回退保护**：合并代码后重新执行全局回归测试；若有任何用例失败，立即调用 `git restore` / 回退操作，保护代码仓库绝对安全。

---

### 7. 万物皆插件，万物皆接口 (Everything is a Plugin)
- 所有 Function Calling 工具均置于 `tools/` 目录，符合独立脚本规范：
  - `read` / `write` / `run`：文件与终端命令基础三件套（`write` 原生支持自动递归创建父目录）。
  - `batch_run`：支持单轮次批量提交执行多个工具调用，大幅缩减交互轮次与延迟。
  - `web_validator`：HTML5 标签树闭合、CSS 语法与 Node.js V8 级 JavaScript 语法深度检测。
  - `browser_test`：无头 Chromium 运行、WebGL 软光栅化渲染、控制台报错实时捕获与视口截图。
  - `env_manager`：环境系统探针、本地 HTTP / WebSocket / MQTT 背景服务编排与守护。
  - `vendor_assets`：离线前端依赖本地落地与管理，杜绝外部 CDN 单点断流。
- **双模调用**：每个工具既可以被 Python 作为函数导入调用 (`execute(params)`)，也可以直接在终端通过 CLI 命令参数调用。
- **即插即用**：放入新的 Python 脚本即可被注册中心自动发现与热加载。

---

### 8. 严格遵循全局规则守则 ([rule/rule.md](file:///home/xxx/atui_harness/rule/rule.md))
- 1. 万物皆插件，万物皆接口，可调用
- 2. 模块化，可复用，功能解耦
- 3. 配置驱动，使用 md、json、yaml
- 5. 既可以通过函数调用，也可以命令行参数调用
- 6. 为后续前端（H5、App、桌面端、TUI）预留标准化调用接口与 EventBus
- 8. 所有 Agent 角色或任务必须有产出（md 或 diff），门禁失败自动进入 Harness 循环

---

## 📂 项目结构

```text
atui_harness/
├── atui.py                    # 主入口：交互式 TUI、CLI 调度与 Python API
├── conftest.py                # Pytest 自动路径解析配置
├── pytest.ini                 # Pytest 自动化测试隔离配置
├── rule/
│   └── rule.md                # 项目规则守则（门禁遵循）
├── config/
│   └── config.json            # 多大模型接口、API Key、Base URL 及 Harness 策略配置
├── agents/                    # 角色驱动配置（Markdown 格式，定义工具、权限、门禁、提示词）
│   ├── planner.md             # 规划与架构师智能体
│   ├── coder.md               # 编码实现智能体
│   ├── tester.md              # 质量测试智能体
│   ├── orchestrator.md        # 主调度循环智能体
│   ├── git_agent.md           # Git版本控制智能体
│   └── delivery.md            # 收尾交付智能体
├── tools/                     # 工具插件集（支持命令行与函数双调用）
│   ├── __init__.py            # 插件动态发现与注册中心
│   ├── base.py                # 统一工具基类与 CLI 自动解析器
│   ├── read.py                # 读文件（支持分行分片）或列举目录
│   ├── write.py               # 创建、覆盖、追加或分块替换文件
│   ├── run.py                 # 运行终端命令（安全拦截与超时保护）
│   ├── test_runner.py         # 质量检测：AST语法解析、py_compile、全量测试运行
│   ├── git_tool.py            # 版本控制：status、diff、commit、log、rollback
│   ├── inspect_ref.py         # 参考检索：深入搜索 ref/ 模式与架构
│   └── calc.py                # 自进化产物：四则运算与统计分析新工具
├── core/                      # Harness 核心引擎与门禁层
│   ├── project.py             # 统一项目目录管理、工作区切换与规则自动注入
│   ├── llm.py                 # 零额外依赖 OpenAI 兼容 LLM 客户端
│   ├── role.py                # Markdown 角色解析器
│   ├── harness.py             # 单智能体执行循环与产出门禁（Rule 8）
│   ├── tdd_gate.py            # TDD 质量门禁与 Git 自动合并/回退控制器
│   ├── pipeline.py            # 全流程多智能体流水线编排器
│   └── event_bus.py           # 结构化事件总线（供 CLI 与多端 UI 订阅）
├── ui/                        # 交互终端 UI 层
│   ├── __init__.py
│   └── terminal.py            # Claude Code 风格交互式终端 REPL
├── api/                       # 开放服务层（Rule 6 预留多端调用接口）
│   ├── __init__.py
│   └── service.py             # 高层 Python API（run_single_agent, run_pipeline 等）
├── tests/                     # 自动化测试套件（31 个单元测试全部通过）
│   ├── test_tools.py          # 工具测试（命令行调用与函数调用验证）
│   ├── test_role.py           # 角色解析与权限控制测试
│   ├── test_tdd_gate.py       # TDD 门禁及回退机制测试
│   ├── test_project.py        # 项目管理与规则热注入测试
│   ├── test_api.py            # API 服务及事件总线测试
│   ├── test_self_check.py     # 架构自检清单自动化测试
│   └── test_calc.py           # 进化生成工具单元测试
└── deliverables/              # 交付资产归档目录
    ├── plan.md                # 架构设计方案
    ├── code_changes.md        # 编码变更报告
    ├── test_report.md         # 质量测试报告
    ├── git_report.md          # Git 审计与提交报告
    └── final_delivery_summary.md  # 终极交付沉淀文档
```

---

## 🚀 快速上手

### 1. 启动 Claude Code 交互式终端 (推荐)
直接运行：
```bash
python atui.py
```
进入带有当前项目路径、Git 分支和规则状态的彩色横幅界面：
```text
╭──────────────────────────────────────────────────────────────────────────────╮
│ ▲ ATUI Harness — Autonomous Terminal Agent (Claude Code Mode)                │
│ 项目目录 : /home/xxx/atui_harness (master)                                   │
│ 规则注入 : rule/rule.md (已自动注入提示词)                                   │
│ 当前角色 : orchestrator  │  模型 : gemini-2.5-flash-lite                     │
╰──────────────────────────────────────────────────────────────────────────────╯
输入提示词即可对话；输入 /help 查看命令，输入 /cd <目录> 切换项目

atui [master] atui_harness (orchestrator) ❯ 你好，请做个自我介绍
```

**交互式终端常用斜杠命令：**
| 命令 | 说明 |
| :--- | :--- |
| `/cd <路径>` 或 `/project <路径>` | 切换工作目录至指定项目，**自动检测并热注入该项目的规则守则** |
| `/pwd` | 查看当前工作项目路径与 Git 分支 |
| `/rules` | 查看当前项目已注入给智能体的完整规则全文 |
| `/role <角色名>` | 快速切换当前角色（如 `coder`、`planner`、`tester`、`delivery` 等） |
| `/model <模型名>` | 快速切换大模型接口 |
| `/pipeline <任务>` | 在当前项目上直接启动全套 5 阶段 TDD 智能体流水线 |
| `/git [status/diff]` | 审查当前项目的 Git 状态或代码差异 |
| `/test` | 在当前项目执行全量自动化测试 |
| `/tools` | 查看已注册的所有 Function Call 插件列表 |
| `/clear` | 清理终端屏幕 |
| `/help` | 查看帮助菜单 |
| `/exit` 或 `/quit` | 退出终端 |

---

### 2. 命令行脚本参数调用 (CLI)

- **调度单智能体执行任务（指定产出文件与模型）**：
  ```bash
  python atui.py agents/orchestrator.md "分析系统架构并输出总结" deliverables/summary.md gemini-2.5-flash-lite
  ```

- **使用命名参数在指定项目上执行**：
  ```bash
  python atui.py --project /path/to/target_repo --agent agents/coder.md --task "修复测试用例" --output deliverables/fix.md
  ```

- **一键启动全生命周期多智能体流水线**：
  ```bash
  python atui.py pipeline "为当前项目添加统计分析模块并遵循TDD提交" deliverables/summary.md gemini-2.5-flash-lite
  ```

- **直接使用底层工具插件**：
  ```bash
  python tools/read.py --path rule/rule.md
  python tools/run.py --command "pytest -v"
  python tools/git_tool.py --action status
  python tools/test_runner.py --target tests/
  ```

---

### 3. Python 模块代码直接调用 (API)

```python
from atui import (
    run_agent,
    run_pipeline,
    run_tool,
    switch_project,
    get_current_project,
    manage_project
)

# 1. 切换目标项目（自动注入该项目的 rule/rule.md 等规则）
proj = switch_project("/home/xxx/my_web_app")
print(f"当前项目: {proj.path}, 规则文件: {proj.rules_file}")

# 2. 调度指定角色执行子任务
res = run_agent(
    agent_file_or_name="agents/coder.md",
    task="为当前项目编写数据清洗工具函数",
    output_file="deliverables/cleaner_summary.md",
    model="gemini-2.5-flash-lite"
)
print("执行结果:", res["last_message"])

# 3. 调度全套 TDD 多智能体流水线 (Plan -> Code -> Test -> Git -> Delivery)
pipeline_res = run_pipeline(
    task="为当前项目实现新功能模块并完成测试提交",
    output_file="deliverables/final_summary.md"
)
print("流水线执行状态:", pipeline_res["success"])

# 4. 直接调用插件工具
read_data = run_tool("read", {"path": "README.md"})
```

---

## ⚙️ 模型配置与多接口支持

在 `config/config.json` 中配置大模型提供商（兼容 OpenAI 规范，支持本地部署大模型、Tokenfy、OpenAI、DeepSeek、Claude 等）：

```json
{
  "default_provider": "tokenfy",
  "default_model": "gemini-2.5-flash-lite",
  "providers": {
    "tokenfy": {
      "base_url": "https://tokenfy.net/v1",
      "api_key": "sk-your-key-here",
      "models": [
        "gemini-2.5-flash-lite",
        "gpt-4o-mini",
        "claude-3-5-sonnet-20241022",
        "deepseek-chat"
      ],
      "timeout": 60
    }
  },
  "harness": {
    "max_turns": 25,
    "max_retry_on_gate_failure": 3,
    "tdd_max_repair_loops": 5,
    "temperature": 0.2
  }
}
```

---

## 🧪 单元测试

本项目包含 31 个单元测试，全面覆盖工具、角色、TDD 门禁、项目目录管理与多智能体流转：
```bash
pytest -v
```
测试全部通过（`31 passed in 0.88s`）。

---

## 📄 License
MIT License.
