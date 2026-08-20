# 阶段 Spec：前后端开发与联调

在 `product/` 下从干净目录实现可运行产品，先遵守已批准的需求、技术选型与视觉结论，再补齐接口契约、真实错误处理、权限校验和环境配置。运行合理的安装、测试和构建命令。把命令、结果、未实现项和联调证据写入报告；禁止部署或操作线上数据。

技术栈是阶段契约，不得因为存在网站脚手架、宿主技能或托管模板而替换：

- 必须使用 React + TypeScript + Vite、React Router、Dexie/IndexedDB 和 Zod。
- 必须创建 `product/index.html`、`product/src/main.tsx`、`package.json` 和 lockfile。
- 禁止 Next.js、vinext、Drizzle、Cloudflare Worker、应用后端、ChatGPT auth、云数据库和 `.openai/hosting.json`。
- 禁止复制静态演示页代替 FR-01 至 FR-08；目标、任务、证据、复盘、导入导出必须由真实状态和持久化驱动。
- 禁止在 `product/` 内初始化嵌套 Git 仓库。
- `package.json` 必须提供 `lint`、`typecheck`、`test` 和 `build` 脚本，并用真实退出码验证。
