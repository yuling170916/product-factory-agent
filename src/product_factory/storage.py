"""State persistence with atomic writes."""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


STATE_DIRECTORY = ".product-factory"
STATE_FILE = "state.json"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def state_path(workspace: Path) -> Path:
    return workspace / STATE_DIRECTORY / STATE_FILE


def load_state(workspace: Path) -> dict[str, Any]:
    path = state_path(workspace)
    if not path.exists():
        raise FileNotFoundError(
            f"{workspace} 不是产品工厂工作区；请先运行 product-factory init"
        )
    return json.loads(path.read_text(encoding="utf-8"))


def save_state(workspace: Path, state: dict[str, Any]) -> None:
    target = state_path(workspace)
    target.parent.mkdir(parents=True, exist_ok=True)
    state["updated_at"] = now_iso()
    payload = json.dumps(state, ensure_ascii=False, indent=2) + "\n"
    descriptor, temporary_name = tempfile.mkstemp(
        prefix="state-", suffix=".json", dir=target.parent
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, target)
    finally:
        if os.path.exists(temporary_name):
            os.unlink(temporary_name)
