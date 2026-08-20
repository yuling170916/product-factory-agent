# StudyTrace 真实案例

这个案例用于演示产品工厂如何从业务问题进入可执行 PRD。

- `BRD.md`：解释为什么做、为谁做、业务价值、验证指标和停止条件。
- `PRD.md`：定义具体功能、数据、交互、非功能需求和验收标准。

两份文档当前都标记为“待需求确认”。这不是缺陷，而是产品工厂的第一个人工关口。任何人都可以提出文档，但只有承担业务责任的人能批准需求进入后续研发。

本地演示：

```bash
product-factory init \
  --prd examples/studytrace/PRD.md \
  --workspace studytrace-workspace \
  --name "StudyTrace 学习证据助手"

product-factory run --workspace studytrace-workspace --provider mock
product-factory status --workspace studytrace-workspace
```

真实生成使用 `--provider codex`。第一次运行仍只会归档 PRD 并停在 `requirement_confirmation`，不能由 Agent 自行批准。
