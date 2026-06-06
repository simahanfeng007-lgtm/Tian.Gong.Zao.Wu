from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from tiangong_agent_runtime.delivery_standardization import DeliveryStandardizationBridge, stable_delivery_standard_digest
from tiangong_agent_runtime.plan_bridge import PlanBridge
from tiangong_agent_runtime.plan_schema import validate_and_build_plan
from tiangong_agent_runtime.risk_classifier import RiskClassifier
from tiangong_agent_runtime.runtime_entry import RuntimeEntry
from tiangong_agent_runtime.tool_invocation import ToolInvocation
from tiangong_agent_runtime.tool_result import ToolResultStatus
from tiangong_agent_runtime.execution_policy import RiskLevel
from tiangong_agent_shell.tool_bridge import ToolExecutionMode

ROOT = Path(__file__).resolve().parents[1]


def _seed_python_project(root: Path) -> None:
    (root / "README.md").write_text("# Demo\n", encoding="utf-8")
    (root / "pyproject.toml").write_text("[project]\nname='demo'\n", encoding="utf-8")
    (root / "pkg").mkdir()
    (root / "pkg" / "__init__.py").write_text("", encoding="utf-8")
    (root / "pkg" / "demo.py").write_text("def add(a, b):\n    return a + b\n", encoding="utf-8")
    (root / "tests").mkdir()
    (root / "tests" / "test_demo.py").write_text("from pkg.demo import add\n\ndef test_add():\n    assert add(1, 2) == 3\n", encoding="utf-8")


def test_l6_26_empty_bridge_is_shell_only() -> None:
    bridge = DeliveryStandardizationBridge()
    snapshot = bridge.public_dict()
    assert snapshot["schema"] == "tiangong.l6_26.delivery_standardization.v1"
    assert snapshot["status"] == "empty"


def test_l6_26_runtime_builds_standardized_delivery_evidence_without_bundle_or_patch(tmp_path: Path) -> None:
    _seed_python_project(tmp_path)
    runtime = RuntimeEntry()
    result = runtime.run_delivery_standardization(
        workspace=tmp_path,
        path=".",
        notes="L6.26 交付链标准化，不污染内核。",
        tool_mode=ToolExecutionMode.RUNTIME_GOVERNED,
        run_compileall=True,
        run_pytest=True,
    )
    assert result.results[-1].tool_name == "build_delivery_standardization"
    assert result.results[-1].status is ToolResultStatus.OK
    report = runtime.delivery_standardization_snapshot()
    assert report["schema"] == "tiangong.l6_26.delivery_standardization.v1"
    assert report["status"] in {"delivery_standard_ready", "delivery_standard_has_open_items", "delivery_standard_needs_fix"}
    assert report["execution_first"] is True
    assert report["shell_only"] is True
    assert report["kernel_pollution_guard"] is True
    assert report["creates_release_bundle"] is False
    assert report["writes_file"] is False
    assert report["applies_patch"] is False
    assert report["modifies_kernel"] is False
    assert report["registers_formal_tool"] is False
    assert report["releases_tool_handle"] is False
    assert report["activates_skill"] is False
    assert report["bypasses_governance"] is False
    assert report["change_set"]
    assert report["test_evidence"]
    assert any(item["command"] == "compileall" for item in report["test_evidence"])
    assert any(item["command"] == "pytest" for item in report["test_evidence"])
    assert report["integrity_evidence"]["report_digest"]
    assert "tiangong_kernel/" in report["integrity_evidence"]["protected_paths"]
    assert any(item["item_id"] == "todo_release_manifest" for item in report["todo_report"])
    digest = stable_delivery_standard_digest(runtime.delivery_standardization.last_report)  # type: ignore[arg-type]
    assert len(digest) == 64
    assert not (tmp_path / "dist" / "l6_26_delivery_standardization.zip").exists()


def test_l6_26_can_consume_existing_release_manifest(tmp_path: Path) -> None:
    _seed_python_project(tmp_path)
    runtime = RuntimeEntry()
    runtime.run_release(
        workspace=tmp_path,
        path=".",
        target="dist/release.zip",
        tool_mode=ToolExecutionMode.RUNTIME_GOVERNED,
        require_pytest=True,
    )
    runtime.run_delivery_standardization(
        workspace=tmp_path,
        path=".",
        notes="汇总已有 Release Manifest。",
        tool_mode=ToolExecutionMode.RUNTIME_GOVERNED,
        run_compileall=True,
        run_pytest=True,
    )
    report = runtime.delivery_standardization_snapshot()
    assert report["manifest_evidence"]["manifest_available"] is True
    assert report["manifest_evidence"]["allow_release"] is True
    assert report["manifest_evidence"]["bundle_sha256"]
    assert report["integrity_evidence"]["sha256_sidecar_present"] is True


def test_l6_26_tool_is_a2_and_registered() -> None:
    runtime = RuntimeEntry()
    names = {tool.name: tool.default_risk for tool in runtime.available_tools()}
    assert names["build_delivery_standardization"] == "A2"
    risk, reason = RiskClassifier().classify(ToolInvocation("build_delivery_standardization", {"path": "."}))
    assert risk is RiskLevel.A2
    assert "L6.26" in reason
    assert "不打包" in reason
    assert "不改内核" in reason


def test_l6_26_plan_bridge_and_schema_allow_delivery_standardization() -> None:
    plan = PlanBridge().build_plan("delivery-standard . L6.26 交付链标准化")
    assert [step.tool_name for step in plan] == ["build_delivery_standardization"]
    built = validate_and_build_plan(
        {
            "steps": [
                {
                    "tool_name": "build_delivery_standardization",
                    "arguments": {"path": ".", "notes": "只生成交付证据"},
                }
            ]
        }
    )
    assert built[0].tool_name == "build_delivery_standardization"
    assert built[0].arguments["path"] == "."


def test_l6_26_cli_delivery_standardization_build_and_export(tmp_path: Path) -> None:
    _seed_python_project(tmp_path)
    proc = subprocess.run(
        [
            sys.executable,
            "run_agent.py",
            "--mock",
            "--tool-mode",
            "runtime_governed",
            "--workspace",
            str(tmp_path),
        ],
        cwd=ROOT,
        input="/delivery-standard-build . 交付链标准化\n/delivery-standard\n/delivery-standard-save delivery_standard.json\n/exit\n",
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=60,
    )
    assert proc.returncode == 0, proc.stderr
    assert "L6.26 标准化交付证据" in proc.stdout
    exported = json.loads((tmp_path / "delivery_standard.json").read_text(encoding="utf-8"))
    assert exported["schema"] == "tiangong.l6_26.delivery_standardization.v1"
    assert exported["shell_only"] is True
    assert exported["creates_release_bundle"] is False
    assert exported["modifies_kernel"] is False


def test_l6_26_notes_are_redacted(tmp_path: Path) -> None:
    _seed_python_project(tmp_path)
    runtime = RuntimeEntry()
    runtime.run_delivery_standardization(
        workspace=tmp_path,
        notes="api_key=sk-test-secret token=abc password=123",
        tool_mode=ToolExecutionMode.RUNTIME_GOVERNED,
    )
    text = json.dumps(runtime.delivery_standardization_snapshot(), ensure_ascii=False)
    assert "sk-test-secret" not in text
    assert "token=abc" not in text
    assert "password=123" not in text


def test_l6_26_runtime_does_not_pollute_kernel_import_direction() -> None:
    kernel_root = ROOT / "tiangong_kernel"
    forbidden = ["delivery_standardization", "build_delivery_standardization", "DeliveryStandardizationBridge", "/delivery-standard"]
    offenders: list[str] = []
    for path in kernel_root.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for token in forbidden:
            if token in text:
                offenders.append(f"{path.relative_to(ROOT)}::{token}")
    assert offenders == []
