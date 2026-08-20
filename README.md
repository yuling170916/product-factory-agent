# 产品工厂 Agent

把一份已经确定的 PRD，按固定研发流程推进为“可在本地和线上验证”的产品版本。AI 负责推导文档、生成代码和执行部分验证；确定性的流程引擎负责阶段顺序、必需产物、审批关口和审计记录。

> 当前状态：可运行的 v0.1 原型。仓库尚未发布到 GitHub，也不会自动创建远程仓库或部署产品。

## 先用一句话理解

它不是一个万能聊天机器人，而是一条带 AI 工人的软件生产线：PRD 是原料，技术/前端/上线手册是工艺标准，各阶段 Spec 是工位说明，人工审批是质检门，代码、文档和验证报告是产品。

## 能不能做？

可以，但需要把“自动化”和“责任”分开：

- 适合自动化：从 PRD 推导技术文档、创建代码、运行本地测试、生成检查报告、准备部署命令。
- 必须由人判断：需求是否正确、功能是否符合业务、视觉是否可接受、是否拥有生产权限、是否真的上线。
- 不应承诺全自动：复杂需求澄清、支付/隐私/合规决策、生产事故处理、所有视觉判断和所有线上验收。

因此，这个项目的目标不是“一键无脑上线”，而是“一键推进到下一个需要人负责的关口”。

## 工作流

| # | 阶段 | 自动执行 | 必需产物 | 阶段后的人工关口 |
|---:|---|---|---|---|
| 1 | PRD 归档 | 原样归档输入 | `00-prd-confirmed.md` | 需求确认 |
| 2 | 技术选型 | 推导架构与选型 | `01-tech-selection.md` | — |
| 3 | 开发技术文档 | API、数据、权限、任务拆分 | `02-development-spec.md` | — |
| 4 | 首轮开发验证 | 可行性、测试或契约验证 | `03-development-validation.md` | 功能验收 |
| 5 | 项目级前端手册 | 页面、组件、状态、可访问性 | `04-frontend-guide.md` | — |
| 6 | 视觉风格方案 | 生成 2–3 个方向和推荐项 | `05-visual-style.md` | 交互/视觉验收 |
| 7 | 前后端开发与联调 | 在 `product/` 生成真实项目 | `06-integration-report.md` | — |
| 8 | 集成版本开发验证 | 回归、契约、构建和关键旅程 | `07-acceptance-report.md` | — |
| 9 | 上线手册 | 环境、部署、监控、回滚 | `08-launch-guide.md` | 权限与上线决策 |
| 10 | 线上版本验证 | 验证目标 URL 和线上旅程 | `09-production-validation.md` | — |

`run` 会自动连续执行，但每到人工关口立即暂停。审批人的姓名、意见、时间和结论会追加到 `.product-factory/state.json`，不会被 AI 自行修改。

## 原理

产品工厂由四层组成：

1. **状态机**：`src/product_factory/stages.py` 固定顺序、产物和人工关口；模型无权跳步。
2. **上下文装配器**：每个阶段只加载 PRD、三份固定手册、当前 Spec 和已完成的上游产物。
3. **AI 执行器**：默认通过本机 `codex exec` 在工作区沙箱内完成当前阶段。`mock` 执行器不调用模型，只生成带标记的契约产物，适合教学和测试。
4. **验证与审计**：阶段结束后独立检查必需文件；状态以原子写入保存；部署需要已批准的上线决策和再次显式确认。

这是一种“确定性骨架 + 概率性执行”的 Agent 架构。状态机处理必须 100% 稳定的事情，模型处理需要理解和创造的事情。

## 目录

```text
product-factory-agent/
├── src/product_factory/        # 流程引擎、CLI、执行器
│   └── templates/
│       ├── manuals/            # 技术栈、前端、上线固定手册
│       └── specs/              # 10 个阶段 Spec
├── .codex/skills/product-factory/ # 可复用 Codex Skill
├── examples/sample-prd.md
├── tests/
└── docs/architecture.md
```

一个初始化后的产品工作区会包含：

```text
my-product/
├── prd.md
├── factory.config.json
├── manuals/
├── specs/
├── artifacts/                 # 每阶段报告
├── product/                   # 实际前后端产品
└── .product-factory/state.json
```

## 5 分钟本地演示（不调用 AI）

需要 Python 3.9+，核心运行时没有第三方依赖。

```bash
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

第一次 `run` 会停在需求确认。检查 `demo-workspace/artifacts/00-prd-confirmed.md` 后：

```bash
product-factory approve requirement_confirmation \
  --workspace demo-workspace --by "产品负责人" --comment "范围确认"

product-factory run --workspace demo-workspace --provider mock
```

之后用同样方式处理 `functional_acceptance`、`visual_acceptance` 和 `release_decision`。mock 产物都明确标有 `MOCK`，只能证明流程能跑通，不能证明产品已开发完成。

## 完整业务案例

仓库包含一个可进入真实开发的学习产品案例：

- [`examples/studytrace/BRD.md`](examples/studytrace/BRD.md)：业务问题、目标用户、价值、验证指标、商业假设和停止条件。
- [`examples/studytrace/PRD.md`](examples/studytrace/PRD.md)：功能、数据模型、交互、非功能需求和可执行验收标准。
- [`docs/execution-and-problem-map.md`](docs/execution-and-problem-map.md)：完整执行流程、人工关口和问题思维导图。

案例有意保持“待需求确认”，用于真实演示第一个人工关口，不代表 Agent 可以替业务负责人批准自己的文档。

## 用 Codex 生成真实产品

先安装并登录 Codex CLI，确认 `codex exec --help` 可用。初始化工作区后运行：

```bash
product-factory run --workspace demo-workspace --provider codex
```

每次运行只会推进到下一个人工关口。也可以通过 `--model YOUR_CODEX_MODEL` 指定模型，或设置 `PRODUCT_FACTORY_MODEL` 环境变量。项目不保存登录凭据或 API key。

### 配置实际项目命令

初始化后编辑 `factory.config.json`。命令必须写成参数数组，不经过 shell 展开：

```json
{
  "project_name": "食材保质期助手",
  "default_provider": "codex",
  "target_url": "https://example.com",
  "commands": {
    "install": ["npm", "ci"],
    "test": ["npm", "test"],
    "build": ["npm", "run", "build"],
    "deploy": ["your-deploy-cli", "deploy", "--prod"]
  }
}
```

当前版本会把安装、测试和构建命令作为上下文交给 Codex 执行。部署命令只有在 `release_decision` 已被批准后，且人再次显式输入确认，才会执行：

```bash
product-factory deploy \
  --workspace demo-workspace \
  --confirm release_decision
```

上线属于真实外部副作用。执行前必须检查命令、账号、目标环境、费用、迁移和回滚方案。

## 请求修改与继续

人工检查不通过时记录拒绝：

```bash
product-factory reject visual_acceptance \
  --workspace demo-workspace \
  --by "设计负责人" \
  --comment "对比度不足，需要重做方案 B"
```

当前 v0.1 会保持在该关口。修改对应产物或由开发者重新处理后，再执行 `approve`。后续版本计划增加受控的 `rerun` 命令，自动失效下游产物。

## 测试

```bash
python3 -m unittest discover -s tests -v
```

测试覆盖 10 阶段顺序、4 个人工关口、拒绝后不可跳过、完整 mock 流程和未批准时禁止部署。

## 当前边界与下一步

- v0.1 的产物验证是“文件契约 + 阶段报告”，不是对每种技术栈的深度质量判断。
- 线上验证需要真实 URL、测试账号和可观测性入口；缺少时必须报告阻塞。
- 一份 PRD 可能仍包含矛盾。需求审批人要对输入负责，AI 不能替代业务决策。
- 后续可加入阶段重跑/下游失效、GitHub Check、Web 审批台、按技术栈加载专用 Spec，以及结构化 eval。

OpenAI 官方模型指南也建议明确自治与审批边界：安全的本地读取、编辑和测试可以自动进行，外部写入、破坏性操作、付费行为或实质扩展范围需要确认。本项目把这条原则固化在流程和部署命令中，而不只依赖提示词。

## GitHub 发布前检查

本仓库已经具备 README、MIT License、测试和 CI 文件，但本轮没有执行 `git push`、没有创建远程仓库。发布前建议：

1. 用一份真实且脱敏的 PRD 跑完 Codex 模式。
2. 检查生成项目是否误含密钥、客户数据或内部地址。
3. 确认仓库名称、作者、License 和公开范围。
4. 再创建 GitHub 仓库并推送。
