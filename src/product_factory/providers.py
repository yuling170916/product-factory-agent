"""AI execution providers.

The mock provider is deterministic and is used for onboarding and tests. The
Codex provider delegates an individual stage to a sandboxed `codex exec` run.
"""

from __future__ import annotations

import json
import os
import subprocess
from abc import ABC, abstractmethod
from pathlib import Path

from .stages import Stage


class ProviderError(RuntimeError):
    pass


class Provider(ABC):
    name = "abstract"

    @abstractmethod
    def execute(self, workspace: Path, stage: Stage, prompt: str) -> str:
        """Execute one stage and return a short run summary."""


class MockProvider(Provider):
    name = "mock"

    def execute(self, workspace: Path, stage: Stage, prompt: str) -> str:
        for relative in stage.outputs:
            target = workspace / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            if relative == "product/README.md":
                body = (
                    "# Mock product\n\n"
                    "这是由 mock provider 创建的产品目录占位文件。使用 Codex provider "
                    "时，这里会变成依据 PRD 实现的真实应用。\n"
                )
            else:
                body = (
                    f"# {stage.title}\n\n"
                    "> MOCK 产物：仅用于验证流程引擎、审批关口和文件契约。\n\n"
                    f"- 阶段 ID：`{stage.id}`\n"
                    f"- 输入提示长度：{len(prompt)} 字符\n"
                    "- 结果：流程契约验证通过\n\n"
                    "## 待真实执行\n\n"
                    "请使用 `--provider codex` 让 AI 根据 PRD 和固定资产生成真实内容。\n"
                )
            target.write_text(body, encoding="utf-8")
        return f"mock provider 已生成 {len(stage.outputs)} 个契约产物"


class CodexProvider(Provider):
    name = "codex"

    def __init__(self, executable: str | None = None, model: str | None = None):
        self.executable = executable or os.environ.get("CODEX_BIN", "codex")
        self.model = model or os.environ.get("PRODUCT_FACTORY_MODEL")

    def execute(self, workspace: Path, stage: Stage, prompt: str) -> str:
        result_file = workspace / ".product-factory" / f"{stage.id}-last-message.md"
        command = [
            self.executable,
            "exec",
            "--skip-git-repo-check",
            "--ephemeral",
            "--color",
            "never",
            "--approve-for-me",
            "--cd",
            str(workspace),
            "--output-last-message",
            str(result_file),
        ]
        if self.model:
            command.extend(["--model", self.model])
        command.append("-")
        completed = subprocess.run(
            command,
            input=prompt,
            text=True,
            capture_output=True,
            check=False,
        )
        if completed.returncode != 0:
            tail = (completed.stderr or completed.stdout)[-2000:]
            raise ProviderError(
                f"Codex 执行阶段 {stage.id} 失败（退出码 {completed.returncode}）：\n{tail}"
            )
        if result_file.exists():
            summary = result_file.read_text(encoding="utf-8").strip()
        else:
            summary = completed.stdout.strip()
        return summary[-2000:] or "Codex 阶段执行完成"


def create_provider(name: str, model: str | None = None) -> Provider:
    if name == "mock":
        return MockProvider()
    if name == "codex":
        return CodexProvider(model=model)
    raise ValueError(f"不支持的 provider：{name}")


def load_config(workspace: Path) -> dict:
    path = workspace / "factory.config.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ProviderError(f"配置文件不是有效 JSON：{path}: {exc}") from exc
