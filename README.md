# 天魁 (atui) — 自主进化终端智能体 Harness 系统

<p align="center">
  <b>天魁 (atui)</b> —— 命名取自三十六天罡之首“天魁星”，意为领袖群伦、统筹全局。<br>
  英文名 <b>atui</b> (Autonomous Terminal User & Agent Harness)，是一个以<b>测试驱动开发 (TDD)</b> 为核心、具备<b>自我进化能力</b>的多角色自主终端智能体框架。
</p>

---

## 🌟 核心特色

### 1. 类似 Claude Code 的极致终端交互体验 (TUI)
- **告别臃肿的原始 JSON 堆砌**：摒弃机器调试式的全量报文输出，提供清晰优雅的终端视觉流。
- **轻量化动作渲染**：以精简图标（`● ⚙️ [read]`、`✔ 执行成功`、`🧪 门禁通过`）实时追踪智能体思考、工具调用与测试进展。
- **类 Claude Code REPL 交互**：自带彩色状态横幅、上下文提示符（`atui [master] ~/my-project ❯`），支持结构化 Markdown 输出渲染。
- **原生 Slash 斜杠指令体系**：集成 `/cd`、`/project`、`/rules`、`/role`、`/model`、`/pipeline`、`/git`、`/test`、`/tools`、`/clear` 等高频快捷命令。

### 2. 统一项目目录穿透与规则热注入 (Project Context & Rules Injection)
- **跨项目无缝工作**：无论 `atui` 部署在何处，均可通过统一接口 `/cd <项目路径>` 或 `switch_project(path)` 将当前工作区锁定在目标代码仓库。
- **自动规则发现与注入**：自动检索目标项目根目录下的 `rule/rule.md`、`rule.md`、`AGENTS.md`、`CLAUDE.md` 等规则守则，将其动态注入到智能体 System Prompt，确保智能体严格遵循目标项目的工程规范与契约。
- **会话持久化**：自动持久化当前激活项目路径至 `~/.atui_project_state.json`，随时打开即进入上次的工作上下文。

### 3. 全生命周期多智能体流水线 (Multi-Agent Lifecycle Pipeline)
系统内置完备的五大角色智能体，协同完成复杂软件工程闭环：
- 🧭 **规划与架构师 (Planner)**：头脑风暴、分析参考代码模式、提出功能方案，并**先期设计并编写 TDD 测试用例**。
- 💻 **编码与重构工程师 (Coder)**：遵循测试用例与项目规则，执行最小化高内聚编码，消除红灯。
- 🧪 **质量测试专家 (Tester)**：执行 Python AST 语法解析、`py_compile` 静态编译检查及 `pytest`/`unittest` 完整用例，输出详细错误诊断。
- 🌿 **版本控制与安全审计 (Git Agent)**：审计代码 Diff，通过 TDD 门禁后执行原子化 Commit；若出现破坏性变更或测试未过，果断触发 **Git Rollback 自动回退**。
- 📦 **收尾交付与知识沉淀 (Delivery)**：复盘全流程，梳理核心经验、踩坑要点（Gotchas）、使用指南并沉淀归档交付资产。
- 🧠 **主调度大脑 (Orchestrator)**：统筹上述各子角色流转与状态协调。

### 4. 严苛的 TDD 质量门禁与自修复闭环 (TDD Gate & Self-Repair)
- **无测试，不编码**：强制实行 TDD 先行，未编写对应测试用例禁止合并。
- **双向自修复循环**：当 Tester 发现测试失败时，将失败堆栈与诊断信息精准反馈给 Coder，智能体在两者之间循环修复（默认上限 5 轮），直至测试全绿。
- **后置回归与 Git 自动回退保护**：合并代码后重新执行全局回归测试；若有任何用例失败，立即调用 `git restore` / 回退操作，保护代码仓库绝对安全。

### 5. 万物皆插件，万物皆接口 (Everything is a Plugin)
- 所有 Function Calling 工具均置于 `tools/` 目录，符合独立脚本规范。
- **双模调用**：每个工具既可以被 Python 作为函数导入调用 (`execute(params)`)，也可以直接在终端通过 CLI 命令参数调用 (`python tools/read.py --path ...`)。
- **即插即用**：放入新的 Python 脚本即可被注册中心自动发现与热加载。

### 6. 自主进化能力 (Self-Evolution)
- **万物皆文本、皆文件、皆配置、皆命令行**。
- 提示词定义在 Markdown 文件中，工具是独立的 Python 脚本，配置在 JSON 中。
- 智能体能够自主分析现有代码、编写自身的新工具插件（如实机自进化生成的 `tools/calc.py`）、为其编写测试、自测通过并提交 Git，实现工程能力的自迭代。

---

### 7. 严格遵循全局规则守则 ([rule/rule.md](file:///home/xxx/atui_harness/rule/rule.md))
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
│   └── calc.py                # 自进化产出：四则运算与统计分析新工具
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
