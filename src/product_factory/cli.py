"""Command-line interface."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .providers import ProviderError, create_provider, load_config
from .stages import GATE_LABELS, STAGES
from .workflow import Workflow, WorkflowError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="product-factory",
        description="把已确认 PRD 推进为可在本地和线上验证的产品版本",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    init = subparsers.add_parser("init", help="从 PRD 初始化产品工作区")
    init.add_argument("--prd", required=True, type=Path)
    init.add_argument("--workspace", required=True, type=Path)
    init.add_argument("--name")

    run = subparsers.add_parser("run", help="运行到下一个人工关口或完成")
    run.add_argument("--workspace", type=Path, default=Path.cwd())
    run.add_argument("--provider", choices=("codex", "mock"))
    run.add_argument("--model")
    run.add_argument("--until", choices=tuple(stage.id for stage in STAGES))

    status = subparsers.add_parser("status", help="显示流程状态")
    status.add_argument("--workspace", type=Path, default=Path.cwd())
    status.add_argument("--json", action="store_true")

    for verb in ("approve", "reject"):
        decision = subparsers.add_parser(verb, help=f"{verb} 当前人工关口")
        decision.add_argument("gate", choices=tuple(GATE_LABELS))
        decision.add_argument("--workspace", type=Path, default=Path.cwd())
        decision.add_argument("--by", required=True)
        decision.add_argument("--comment", default="")

    deploy = subparsers.add_parser("deploy", help="执行配置好的部署命令")
    deploy.add_argument("--workspace", type=Path, default=Path.cwd())
    deploy.add_argument("--confirm", required=True)
    return parser


def render_status(snapshot: dict) -> str:
    lines = [
        f"项目：{snapshot['project_name']}",
        f"总状态：{snapshot['status']}",
    ]
    for index, stage in enumerate(STAGES, start=1):
        state = snapshot["stages"][stage.id]
        marker = {
            "pending": "○",
            "running": "◐",
            "completed": "●",
            "failed": "×",
        }.get(state["status"], "?")
        lines.append(f"{index:02d} {marker} {stage.title} [{state['status']}]")
    gate = snapshot.get("pending_gate")
    if gate:
        lines.append(f"等待人工关口：{GATE_LABELS[gate]} ({gate})")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "init":
            workspace = Workflow.initialize(args.workspace, args.prd, args.name)
            print(f"已初始化：{workspace}")
            print("下一步：product-factory run --workspace <目录>")
            return 0

        workspace = args.workspace.resolve()
        if args.command == "run":
            config = load_config(workspace)
            provider_name = args.provider or config.get("default_provider", "codex")
            workflow = Workflow(workspace, create_provider(provider_name, args.model))
            result = workflow.run(args.until)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            if result["blocked_by"]:
                gate = result["blocked_by"]
                print(
                    f"流程已在人工关口暂停：{GATE_LABELS[gate]}。\n"
                    f"检查产物后运行：product-factory approve {gate} "
                    f"--workspace {workspace} --by <姓名>"
                )
            return 0

        workflow = Workflow(workspace, create_provider("mock"))
        if args.command == "status":
            snapshot = workflow.snapshot()
            print(
                json.dumps(snapshot, ensure_ascii=False, indent=2)
                if args.json
                else render_status(snapshot)
            )
            return 0
        if args.command in ("approve", "reject"):
            decision = "approved" if args.command == "approve" else "rejected"
            workflow.decide(args.gate, decision, args.by, args.comment)
            print(f"已记录：{GATE_LABELS[args.gate]} -> {decision}")
            return 0
        if args.command == "deploy":
            workflow.deploy(args.confirm)
            print("部署命令执行成功；请继续运行线上版本验证阶段")
            return 0
    except (ProviderError, WorkflowError, FileNotFoundError, ValueError) as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 2
    return 1
