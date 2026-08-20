"""The canonical workflow definition.

Keep orchestration facts in code rather than in model prompts. This makes stage
order, required outputs, and approval boundaries deterministic and testable.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Stage:
    id: str
    title: str
    spec_file: str
    outputs: tuple[str, ...]
    gate_after: str | None = None
    deterministic: bool = False


STAGES: tuple[Stage, ...] = (
    Stage(
        "prd",
        "PRD 归档与需求确认",
        "00-prd.md",
        ("artifacts/00-prd-confirmed.md",),
        gate_after="requirement_confirmation",
        deterministic=True,
    ),
    Stage(
        "tech-selection",
        "技术选型",
        "01-tech-selection.md",
        ("artifacts/01-tech-selection.md",),
    ),
    Stage(
        "development-spec",
        "开发技术文档",
        "02-development-spec.md",
        ("artifacts/02-development-spec.md",),
    ),
    Stage(
        "development-validation-1",
        "首轮开发验证",
        "03-development-validation-1.md",
        ("artifacts/03-development-validation.md",),
        gate_after="functional_acceptance",
    ),
    Stage(
        "frontend-guide",
        "项目级前端手册",
        "04-frontend-guide.md",
        ("artifacts/04-frontend-guide.md",),
    ),
    Stage(
        "visual-style",
        "视觉风格方案",
        "05-visual-style.md",
        ("artifacts/05-visual-style.md",),
        gate_after="visual_acceptance",
    ),
    Stage(
        "integration",
        "前后端开发与联调",
        "06-integration.md",
        ("artifacts/06-integration-report.md", "product/README.md"),
    ),
    Stage(
        "development-validation-2",
        "集成版本开发验证",
        "07-development-validation-2.md",
        ("artifacts/07-acceptance-report.md",),
    ),
    Stage(
        "launch-guide",
        "上线手册",
        "08-launch-guide.md",
        ("artifacts/08-launch-guide.md",),
        gate_after="release_decision",
    ),
    Stage(
        "production-validation",
        "线上版本验证",
        "09-production-validation.md",
        ("artifacts/09-production-validation.md",),
    ),
)

GATE_LABELS = {
    "requirement_confirmation": "需求确认",
    "functional_acceptance": "功能验收",
    "visual_acceptance": "交互/视觉验收",
    "release_decision": "权限与上线决策",
}


def get_stage(stage_id: str) -> Stage:
    for stage in STAGES:
        if stage.id == stage_id:
            return stage
    raise KeyError(f"未知阶段：{stage_id}")
