# 产品工厂 Agent

把一份已经确认的 PRD，稳稳地推进成一个可以在本地运行、测试，并为上线做好准备的真实产品。

这里的“产品工厂”不是让 AI 随意发挥，而是给 AI 一条有顺序、有标准、有人把关的软件生产线：AI 负责整理文档、生成代码和执行验证；人负责需求、功能、视觉和上线等关键决定。

> 当前版本：`v0.1` 教学原型。流程引擎、示例、测试和 GitHub Actions 均可运行；它不会绕过人工审批自动部署产品。

## 目录

- [先用一分钟了解它](#先用一分钟了解它)
- [它能解决什么问题](#它能解决什么问题)
- [适合谁使用](#适合谁使用)
- [完整工作流](#完整工作流)
- [它是怎么工作的](#它是怎么工作的)
- [仓库目录怎么读](#仓库目录怎么读)
- [5 分钟体验流程](#5-分钟体验流程)
- [用 Codex 生成真实产品](#用-codex-生成真实产品)
- [真实案例：StudyTrace](#真实案例studytrace)
- [人工审批与修改](#人工审批与修改)
- [测试](#测试)
- [当前边界](#当前边界)

## 先用一分钟了解它

可以把它想象成一条软件生产线：

```text
已确认的 PRD
  ↓
技术方案 → 开发文档 → 前端规范 → 视觉方案
  ↓                         ↓
自动生成和验证          人工选择与验收
  ↓
真实产品代码 → 集成测试 → 上线手册
  ↓
人工决定是否上线 → 线上验证
```

其中：

- **PRD 是原料**：告诉 Agent 要做什么产品。
- **手册和 Spec 是工艺标准**：告诉 Agent 每一步应该怎么做、交付什么。
- **AI 是执行工人**：整理文档、写代码、运行部分检查。
- **人工关口是质检门**：需求、功能、视觉和上线都必须由人决定。
- **文档、代码和报告是成品与质检记录**。

它追求的不是“一句话无脑上线”，而是“自动推进到下一个需要人负责的决定”。

## 它能解决什么问题

一个 PRD 交给不同的人，常会出现技术方案缺失、文档和代码不一致、测试做没做说不清、上线风险无人确认等问题。产品工厂把这些容易遗漏的步骤固定下来：

- 把 PRD 逐步推导为技术选型、开发规格、前端规范和上线手册。
- 让每个阶段都有明确输入、输出和完成标准。
- 自动生成前后端代码并执行一部分测试、构建和本地验证。
- 在关键位置暂停，让真正负责的人确认，而不是让 AI 替人做决定。
- 保存每个阶段的结果、审批意见和验证证据，方便复盘与追踪。
- 当部署信息、权限或验证证据不足时明确报告阻塞，不假装已经上线成功。

## 适合谁使用

- 正在学习 Agent、产品开发或软件工程流程的人。
- 手里已经有 PRD，希望把研发步骤标准化的小团队。
- 想研究“状态机 + AI 执行器 + 人工审批”架构的开发者。
- 想建立内部产品模板、技术规范和质量关口的团队。

如果需求还很模糊，建议先完成业务调研和 PRD；产品工厂的起点是一份**已经确定并愿意负责的 PRD**。

## 完整工作流

| # | 阶段 | Agent 做什么 | 主要产物 | 人工关口 |
|---:|---|---|---|---|
| 1 | PRD 归档 | 保存输入，建立执行基线 | `00-prd-confirmed.md` | 需求确认 |
| 2 | 技术选型 | 推导架构、技术栈和风险 | `01-tech-selection.md` | — |
| 3 | 开发技术文档 | 定义数据、接口、权限和任务 | `02-development-spec.md` | — |
| 4 | 首轮开发验证 | 检查可行性、契约和需求覆盖 | `03-development-validation.md` | 功能验收 |
| 5 | 前端手册 | 定义页面、组件、状态和可访问性 | `04-frontend-guide.md` | — |
| 6 | 视觉风格 | 生成多个方向并说明取舍 | `05-visual-style.md` | 交互/视觉验收 |
| 7 | 开发与联调 | 在 `product/` 中生成真实项目 | `06-integration-report.md` | — |
| 8 | 集成验证 | 运行回归、测试、构建和关键旅程 | `07-acceptance-report.md` | — |
| 9 | 上线手册 | 准备环境、监控、冒烟和回滚方案 | `08-launch-guide.md` | 权限与上线决策 |
| 10 | 线上验证 | 检查真实 URL 和生产版本 | `09-production-validation.md` | — |

`run` 会连续推进流程，但遇到人工关口就立即暂停。审批人、意见、时间和结论会写入工作区状态文件，AI 无权自行跳过。

## 它是怎么工作的

产品工厂包含四个核心部分：

1. **状态机**：固定 10 个阶段、执行顺序、必需产物和 4 个人工关口。
2. **上下文装配器**：每个阶段只提供所需的 PRD、手册、Spec 和上游结果，减少混乱。
3. **AI 执行器**：默认调用本机 `codex exec` 完成当前阶段；`mock` 模式只生成教学用契约产物。
4. **验证与审计**：检查文件和技术栈，记录状态；部署还需要上线审批和第二次显式确认。

这是一种“**确定性的流程骨架 + 概率性的 AI 执行**”架构：必须稳定的事情交给程序控制，需要理解和创造的事情交给模型处理。

更详细的图解请看：[执行流程与问题地图](docs/execution-and-problem-map.md)。

## 仓库目录怎么读

如果你第一次打开仓库，建议先看 `README.md`，再看 `examples/studytrace/`，最后进入 `src/` 阅读实现。

```text
product-factory-agent/
├── README.md                         # 你正在看的项目入口
├── src/product_factory/              # 产品工厂的 Python 流程引擎
│   ├── stages.py                     # 10 个阶段和 4 个人工关口
│   ├── workflow.py                   # 执行、暂停、审批和部署保护
│   ├── providers.py                  # Codex 与 mock 执行器
│   └── templates/
│       ├── manuals/                  # 固定的技术、前端和上线手册
│       └── specs/                    # 每个阶段的工作说明书
├── .codex/skills/product-factory/    # 可复用的 Codex Skill
├── examples/
│   ├── sample-prd.md                 # 最小演示 PRD
│   └── studytrace/                   # 完整 BRD/PRD 业务案例
├── docs/                             # 架构、流程图和问题地图
├── tests/                            # 流程和安全关口测试
└── .github/workflows/test.yml        # GitHub 自动测试
```

产品工厂运行后会另外创建一个“产品工作区”：

```text
my-product/
├── prd.md                            # 本次产品的需求基线
├── factory.config.json               # 测试、构建和部署命令配置
├── manuals/                          # 本次使用的固定手册
├── specs/                            # 10 个阶段的执行要求
├── artifacts/                        # 每个阶段生成的文档和报告
├── product/                          # 真正可以运行的产品源码
└── .product-factory/state.json       # 本地流程状态和审批记录
```

最容易混淆的是：**本仓库负责“生产产品”，工作区里的 `product/` 才是被生产出来的应用。**

## 5 分钟体验流程

下面使用 `mock` 模式体验流程，不调用 AI，也不会部署任何东西。

要求：Python 3.9 或更高版本。

```bash
git clone https://github.com/yuling170916/product-factory-agent.git
cd product-factory-agent

python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e .

product-factory init \
  --prd examples/sample-prd.md \
  --workspace demo-workspace \
  --name "食材保质期助手"

product-factory run --workspace demo-workspace --provider mock
product-factory status --workspace demo-workspace
```

第一次运行会停在“需求确认”。检查生成的 `demo-workspace/artifacts/00-prd-confirmed.md` 后，可以记录审批：

```bash
product-factory approve requirement_confirmation \
  --workspace demo-workspace \
  --by "产品负责人" \
  --comment "范围确认，可以继续"

product-factory run --workspace demo-workspace --provider mock
```

后续三个关口分别是 `functional_acceptance`、`visual_acceptance` 和 `release_decision`。mock 文件会明确标注 `MOCK`，只能证明流程可运行，不代表真实产品已经开发完成。

## 用 Codex 生成真实产品

先安装并登录 Codex CLI，确认 `codex exec --help` 可以运行，然后执行：

```bash
product-factory run --workspace demo-workspace --provider codex
```

每次运行只会推进到下一个人工关口。也可以使用 `--model YOUR_CODEX_MODEL` 指定模型，或设置 `PRODUCT_FACTORY_MODEL` 环境变量。项目不会保存登录凭据或 API key。

初始化后，请在 `factory.config.json` 中填写真实项目命令。每条命令必须是参数数组，不经过 shell 展开：

```json
{
  "project_name": "食材保质期助手",
  "default_provider": "codex",
  "target_url": "",
  "commands": {
    "install": ["npm", "ci"],
    "test": ["npm", "test"],
    "build": ["npm", "run", "build"],
    "deploy": []
  }
}
```

建议在准备上线前才填写 `target_url` 和 `deploy`。部署只有在 `release_decision` 已批准，而且操作人再次显式确认后才会执行：

```bash
product-factory deploy \
  --workspace demo-workspace \
  --confirm release_decision
```

## 真实案例：StudyTrace

仓库自带一个完整学习产品案例：

- [StudyTrace BRD](examples/studytrace/BRD.md)：为什么做、为谁做、价值和验证指标。
- [StudyTrace PRD](examples/studytrace/PRD.md)：功能、数据、交互、非功能需求和验收标准。
- [StudyTrace 成品仓库](https://github.com/yuling170916/studytrace-product)：由这套流程真正生成的产品、阶段文档和测试报告。
- [执行流程与思维导图](docs/execution-and-problem-map.md)：Agent 如何一步步工作，以及它解决哪些问题。

如果你想理解整个项目，推荐按“BRD → PRD → 成品仓库中的 `artifacts/` → `product/` 源码”这个顺序阅读。

## 人工审批与修改

如果某个关口没有通过，可以记录拒绝原因：

```bash
product-factory reject visual_acceptance \
  --workspace demo-workspace \
  --by "设计负责人" \
  --comment "对比度不足，请重新调整"
```

当前 `v0.1` 会停在该关口，不能绕过。修改对应产物后再重新审批。后续版本计划增加受控的阶段重跑和下游产物失效机制。

## 测试

```bash
python3 -m unittest discover -s tests -v
```

当前测试覆盖：

- 10 个阶段的固定顺序。
- 4 个人工关口均会暂停。
- 拒绝后不能跳过审批。
- 完整 mock 流程。
- 技术栈不符合要求时拒绝集成产物。
- 未批准上线时禁止执行部署。

GitHub Actions 会在推送和 Pull Request 时自动运行这些测试。

## 当前边界

- `v0.1` 主要验证流程、产物契约和人工关口，不代表能深度判断所有技术栈的质量。
- PRD 中的矛盾仍需要真实负责人解决，AI 不能替业务承担决策责任。
- 涉及支付、医疗、隐私、合规或生产数据时，需要增加对应领域审查和测试。
- 线上验证需要真实 URL、权限、监控和回滚方案；缺少任一关键条件都应明确停止。
- 外部写入、付费操作和生产部署不会仅凭模型判断自动执行。

欢迎把它当作一个可拆解、可修改的 Agent 学习样本。你可以先跑 mock 流程，理解人工关口，再逐步替换自己的 PRD、手册和阶段 Spec。
