from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from product_factory.providers import CodexProvider, MockProvider, Provider
from product_factory.stages import STAGES
from product_factory.workflow import Workflow, WorkflowError


SAMPLE_PRD = """# 习惯打卡器

## 用户
希望每天记录一项习惯的个人用户。

## MVP
- 创建习惯
- 每日打卡
- 查看连续天数

## 验收标准
创建习惯后可以在当天打卡，刷新后记录仍存在。
"""


class InvalidIntegrationProvider(Provider):
    name = "invalid-integration"

    def execute(self, workspace: Path, stage, prompt: str) -> str:
        for relative in stage.outputs:
            target = workspace / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("这是一个长度足够但技术栈错误的测试产物。" * 3, encoding="utf-8")
        if stage.id == "integration":
            (workspace / "product" / "package.json").write_text(
                json.dumps(
                    {
                        "dependencies": {"react": "1", "next": "1"},
                        "scripts": {"build": "next build"},
                    }
                ),
                encoding="utf-8",
            )
        return "invalid"


class WorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        root = Path(self.temporary.name)
        self.prd = root / "prd-source.md"
        self.prd.write_text(SAMPLE_PRD, encoding="utf-8")
        self.workspace = root / "workspace"
        Workflow.initialize(self.workspace, self.prd, "测试产品")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def workflow(self) -> Workflow:
        return Workflow(self.workspace, MockProvider())

    def test_has_exactly_ten_stages_and_four_gates(self) -> None:
        self.assertEqual(10, len(STAGES))
        gates = [stage.gate_after for stage in STAGES if stage.gate_after]
        self.assertEqual(
            [
                "requirement_confirmation",
                "functional_acceptance",
                "visual_acceptance",
                "release_decision",
            ],
            gates,
        )

    def test_full_mock_run_stops_at_every_human_gate(self) -> None:
        workflow = self.workflow()
        first = workflow.run()
        self.assertEqual("requirement_confirmation", first["blocked_by"])
        workflow.decide("requirement_confirmation", "approved", "owner")

        second = workflow.run()
        self.assertEqual("functional_acceptance", second["blocked_by"])
        workflow.decide("functional_acceptance", "approved", "qa")

        third = workflow.run()
        self.assertEqual("visual_acceptance", third["blocked_by"])
        workflow.decide("visual_acceptance", "approved", "designer")

        fourth = workflow.run()
        self.assertEqual("release_decision", fourth["blocked_by"])
        workflow.decide("release_decision", "approved", "release-owner")

        final = workflow.run()
        self.assertTrue(final["completed"])
        self.assertEqual("completed", workflow.snapshot()["status"])
        for stage in STAGES:
            for relative in stage.outputs:
                self.assertTrue((self.workspace / relative).is_file(), relative)

    def test_rejected_gate_cannot_be_skipped(self) -> None:
        workflow = self.workflow()
        workflow.run()
        workflow.decide(
            "requirement_confirmation", "rejected", "owner", "验收标准不清楚"
        )
        blocked = workflow.run()
        self.assertEqual("requirement_confirmation", blocked["blocked_by"])
        workflow.decide("requirement_confirmation", "approved", "owner", "已补充")
        resumed = workflow.run()
        self.assertIn("tech-selection", resumed["executed"])

    def test_deploy_is_denied_without_release_approval(self) -> None:
        workflow = self.workflow()
        with self.assertRaisesRegex(WorkflowError, "上线决策尚未批准"):
            workflow.deploy("release_decision")

    def test_codex_provider_uses_compatible_approval_arguments(self) -> None:
        stage = STAGES[1]

        def fake_run(command, **kwargs):
            output_index = command.index("--output-last-message") + 1
            Path(command[output_index]).write_text("完成", encoding="utf-8")
            return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

        with patch("product_factory.providers.subprocess.run", side_effect=fake_run) as run:
            result = CodexProvider(executable="codex").execute(
                self.workspace, stage, "测试提示"
            )
        command = run.call_args.args[0]
        self.assertIn("--approve-for-me", command)
        self.assertNotIn("--sandbox", command)
        self.assertEqual("完成", result)

    def test_real_integration_rejects_wrong_stack(self) -> None:
        workflow = Workflow(self.workspace, InvalidIntegrationProvider())
        workflow.state["cursor"] = 6
        for stage in STAGES[:6]:
            workflow.state["stages"][stage.id]["status"] = "completed"
        with self.assertRaisesRegex(WorkflowError, "缺少 product/index.html"):
            workflow.run()


if __name__ == "__main__":
    unittest.main()
