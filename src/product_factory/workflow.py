"""Deterministic workflow orchestration."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

from .providers import Provider, load_config
from .stages import GATE_LABELS, STAGES, Stage, get_stage
from .storage import load_state, now_iso, save_state


class WorkflowError(RuntimeError):
    pass


class Workflow:
    def __init__(self, workspace: Path, provider: Provider):
        self.workspace = workspace.resolve()
        self.provider = provider
        self.state = load_state(self.workspace)

    @classmethod
    def initialize(cls, workspace: Path, prd: Path, name: str | None = None) -> Path:
        workspace = workspace.resolve()
        prd = prd.resolve()
        if not prd.is_file():
            raise WorkflowError(f"找不到 PRD：{prd}")
        if (workspace / ".product-factory" / "state.json").exists():
            raise WorkflowError(f"工作区已经初始化：{workspace}")

        workspace.mkdir(parents=True, exist_ok=True)
        (workspace / "artifacts").mkdir(exist_ok=True)
        (workspace / "product").mkdir(exist_ok=True)
        templates = Path(__file__).with_name("templates")
        shutil.copytree(templates / "manuals", workspace / "manuals", dirs_exist_ok=True)
        shutil.copytree(templates / "specs", workspace / "specs", dirs_exist_ok=True)
        shutil.copy2(prd, workspace / "prd.md")

        project_name = name or prd.stem
        config = {
            "project_name": project_name,
            "default_provider": "codex",
            "target_url": "",
            "commands": {
                "install": [],
                "test": [],
                "build": [],
                "deploy": [],
            },
        }
        (workspace / "factory.config.json").write_text(
            json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        created = now_iso()
        state: dict[str, Any] = {
            "schema_version": 1,
            "project_name": project_name,
            "created_at": created,
            "updated_at": created,
            "cursor": 0,
            "status": "running",
            "stages": {
                stage.id: {
                    "status": "pending",
                    "attempts": 0,
                    "summary": "",
                    "started_at": None,
                    "completed_at": None,
                }
                for stage in STAGES
            },
            "decisions": [],
            "deployments": [],
        }
        save_state(workspace, state)
        return workspace

    def latest_gate_decision(self, gate: str) -> dict[str, Any] | None:
        for decision in reversed(self.state["decisions"]):
            if decision["gate"] == gate:
                return decision
        return None

    def pending_gate(self) -> str | None:
        cursor = self.state["cursor"]
        if cursor >= len(STAGES):
            return None
        stage = STAGES[cursor]
        stage_state = self.state["stages"][stage.id]
        if stage_state["status"] != "completed" or not stage.gate_after:
            return None
        decision = self.latest_gate_decision(stage.gate_after)
        if not decision or decision["decision"] != "approved":
            return stage.gate_after
        return None

    def run(self, until: str | None = None) -> dict[str, Any]:
        if until is not None:
            get_stage(until)
        executed: list[str] = []
        while self.state["cursor"] < len(STAGES):
            cursor = self.state["cursor"]
            stage = STAGES[cursor]
            stage_state = self.state["stages"][stage.id]

            if stage_state["status"] == "completed":
                gate = stage.gate_after
                if gate:
                    decision = self.latest_gate_decision(gate)
                    if not decision or decision["decision"] != "approved":
                        self.state["status"] = "waiting_for_approval"
                        save_state(self.workspace, self.state)
                        return {"executed": executed, "blocked_by": gate, "completed": False}
                self.state["cursor"] += 1
                save_state(self.workspace, self.state)
                continue

            self._execute_stage(stage)
            executed.append(stage.id)
            if stage.gate_after:
                self.state["status"] = "waiting_for_approval"
                save_state(self.workspace, self.state)
                return {
                    "executed": executed,
                    "blocked_by": stage.gate_after,
                    "completed": False,
                }
            self.state["cursor"] += 1
            save_state(self.workspace, self.state)
            if until == stage.id:
                return {"executed": executed, "blocked_by": None, "completed": False}

        self.state["status"] = "completed"
        save_state(self.workspace, self.state)
        return {"executed": executed, "blocked_by": None, "completed": True}

    def _execute_stage(self, stage: Stage) -> None:
        stage_state = self.state["stages"][stage.id]
        stage_state["status"] = "running"
        stage_state["attempts"] += 1
        stage_state["started_at"] = now_iso()
        save_state(self.workspace, self.state)
        try:
            if stage.deterministic:
                source = (self.workspace / "prd.md").read_text(encoding="utf-8")
                target = self.workspace / stage.outputs[0]
                target.write_text(
                    "# 待确认 PRD\n\n"
                    "> 本文件由产品工厂归档。审批 `requirement_confirmation` "
                    "代表需求范围、验收标准与非目标已由负责人确认。\n\n"
                    + source,
                    encoding="utf-8",
                )
                summary = "已归档 PRD，等待需求负责人确认"
            else:
                prompt = self._build_prompt(stage)
                summary = self.provider.execute(self.workspace, stage, prompt)
            self._validate_outputs(stage)
        except Exception as exc:
            stage_state["status"] = "failed"
            stage_state["summary"] = str(exc)
            save_state(self.workspace, self.state)
            raise
        stage_state["status"] = "completed"
        stage_state["summary"] = summary
        stage_state["completed_at"] = now_iso()
        save_state(self.workspace, self.state)

    def _build_prompt(self, stage: Stage) -> str:
        spec = (self.workspace / "specs" / stage.spec_file).read_text(encoding="utf-8")
        manuals = []
        for path in sorted((self.workspace / "manuals").glob("*.md")):
            manuals.append(f"## 固定手册：{path.name}\n\n{path.read_text(encoding='utf-8')}")
        previous = []
        for other in STAGES:
            if other.id == stage.id:
                break
            for relative in other.outputs:
                path = self.workspace / relative
                if path.is_file():
                    previous.append(
                        f"## 已有产物：{relative}\n\n{path.read_text(encoding='utf-8')}"
                    )
        config = (self.workspace / "factory.config.json").read_text(encoding="utf-8")
        expected = "\n".join(f"- `{path}`" for path in stage.outputs)
        return f"""你正在执行“产品工厂”的单一阶段：{stage.title}（{stage.id}）。

工作区就是当前目录。请严格执行本阶段，不要跳到后续阶段。

安全边界：
- 允许读取和修改当前工作区中的项目文件。
- 禁止修改 `.product-factory/` 内的状态文件。
- 禁止发布代码、创建远程仓库、部署、发送消息、购买资源或修改线上数据。
- 如输入不足，在阶段报告中列出阻塞项；不要虚构已验证结果。

必须创建并填写以下产物：
{expected}

最终回复只简述完成内容、验证证据和未解决风险。流程引擎会独立检查产物是否存在。

# 项目配置

```json
{config}
```

# 已确认 PRD

{(self.workspace / 'prd.md').read_text(encoding='utf-8')}

# 本阶段 Spec

{spec}

# 固定资产

{chr(10).join(manuals)}

# 上游产物

{chr(10).join(previous) or '无'}
"""

    def _validate_outputs(self, stage: Stage) -> None:
        failures = []
        for relative in stage.outputs:
            path = self.workspace / relative
            if not path.is_file():
                failures.append(f"缺少 {relative}")
            elif path.stat().st_size < 40:
                failures.append(f"{relative} 内容过短")
        if stage.id == "integration" and self.provider.name != "mock":
            failures.extend(self._validate_integration_stack())
        if failures:
            raise WorkflowError("阶段产物契约未通过：" + "；".join(failures))

    def _validate_integration_stack(self) -> list[str]:
        product = self.workspace / "product"
        required_files = (
            "package.json",
            "package-lock.json",
            "index.html",
            "src/main.tsx",
        )
        failures = [
            f"集成实现缺少 product/{relative}"
            for relative in required_files
            if not (product / relative).is_file()
        ]
        forbidden_files = (
            ".openai/hosting.json",
            "next.config.js",
            "next.config.mjs",
            "next.config.ts",
            "drizzle.config.ts",
            "worker/index.ts",
            ".git/HEAD",
        )
        failures.extend(
            f"集成实现包含被禁止的技术栈文件 product/{relative}"
            for relative in forbidden_files
            if (product / relative).exists()
        )
        package_path = product / "package.json"
        if not package_path.is_file():
            return failures
        try:
            package = json.loads(package_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            failures.append(f"product/package.json 无效：{exc}")
            return failures
        dependencies = {
            **package.get("dependencies", {}),
            **package.get("devDependencies", {}),
        }
        for dependency in ("react", "react-router-dom", "dexie", "zod"):
            if dependency not in dependencies:
                failures.append(f"集成实现缺少依赖 {dependency}")
        for dependency in ("next", "vinext", "drizzle-orm", "@openai/sites-vite-plugin"):
            if dependency in dependencies:
                failures.append(f"集成实现包含被禁止的依赖 {dependency}")
        scripts = package.get("scripts", {})
        for script in ("lint", "typecheck", "test", "build"):
            if not scripts.get(script):
                failures.append(f"product/package.json 缺少 {script} 脚本")
        return failures

    def decide(self, gate: str, decision: str, by: str, comment: str = "") -> None:
        if gate not in GATE_LABELS:
            raise WorkflowError(f"未知人工关口：{gate}")
        pending = self.pending_gate()
        if pending != gate:
            if pending:
                raise WorkflowError(f"当前等待的是 {pending}，不是 {gate}")
            raise WorkflowError("当前没有待处理的人工关口")
        self.state["decisions"].append(
            {
                "gate": gate,
                "decision": decision,
                "by": by,
                "comment": comment,
                "at": now_iso(),
                "stage": STAGES[self.state["cursor"]].id,
            }
        )
        self.state["status"] = "running" if decision == "approved" else "changes_requested"
        save_state(self.workspace, self.state)

    def deploy(self, confirmation: str) -> None:
        release = self.latest_gate_decision("release_decision")
        if not release or release["decision"] != "approved":
            raise WorkflowError("上线决策尚未批准，禁止部署")
        if confirmation != "release_decision":
            raise WorkflowError("部署必须显式传入 --confirm release_decision")
        config = load_config(self.workspace)
        command = config.get("commands", {}).get("deploy", [])
        if not isinstance(command, list) or not command:
            raise WorkflowError("factory.config.json 中尚未配置 commands.deploy 参数数组")
        completed = subprocess.run(command, cwd=self.workspace / "product", check=False)
        record = {
            "command": command,
            "returncode": completed.returncode,
            "at": now_iso(),
        }
        self.state["deployments"].append(record)
        save_state(self.workspace, self.state)
        if completed.returncode != 0:
            raise WorkflowError(f"部署命令失败，退出码 {completed.returncode}")

    def snapshot(self) -> dict[str, Any]:
        data = dict(self.state)
        data["pending_gate"] = self.pending_gate()
        data["stage_order"] = [stage.id for stage in STAGES]
        return data
