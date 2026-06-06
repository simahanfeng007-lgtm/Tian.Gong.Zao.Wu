from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from tiangong_agent_runtime.plan_bridge import PlanBridge
from tiangong_agent_runtime.plan_schema import validate_and_build_plan
from tiangong_agent_runtime.project_repair_plan import ProjectRepairPlanBridge, stable_repair_plan_digest
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


def test_l6_25_empty_bridge_is_shell_only() -> None:
    bridge = ProjectRepairPlanBridge()
    snapshot = bridge.public_dict()
    assert snapshot["schema"] == "tiangong.l6_25.project_repair_plan.v1"
    assert snapshot["status"] == "empty"


def test_l6_25_runtime_builds_project_repair_plan_without_applying_patch(tmp_path: Path) -> None:
    _seed_python_project(tmp_path)
    runtime = RuntimeEntry()
    result = runtime.run_project_repair_plan(
        workspace=tmp_path,
        path=".",
        notes="L6.25 工程修复外壳，不污染内核。",
        tool_mode=ToolExecutionMode.RUNTIME_GOVERNED,
        run_compileall=True,
        run_pytest=True,
    )
    assert result.results[-1].tool_name == "build_project_repair_plan"
    assert result.results[-1].status is ToolResultStatus.OK
    report = runtime.project_repair_snapshot()
    assert report["schema"] == "tiangong.l6_25.project_repair_plan.v1"
    assert report["status"] in {"repair_plan_ready", "repair_plan_has_actions", "repair_plan_needs_fix"}
    assert report["execution_first"] is True
    assert report["shell_only"] is True
    assert report["kernel_pollution_guard"] is True
    assert report["applies_patch"] is False
    assert report["writes_file"] is False
    assert report["modifies_kernel"] is False
    assert report["registers_formal_tool"] is False
    assert report["releases_tool_handle"] is False
    assert report["activates_skill"] is False
    assert report["bypasses_governance"] is False
    assert report["project_radar"]["entry_points"] or report["project_radar"]["key_files"]
    assert report["patch_plan"]
    assert any(item["command"] == "compileall" for item in report["regression_hints"])
    assert any(item["command"] == "pytest" for item in report["regression_hints"])
    assert report["rollback_evidence"]["kernel_pollution_guard"] is True
    assert "tiangong_kernel/" in report["rollback_evidence"]["protected_paths"]
    digest = stable_repair_plan_digest(runtime.project_repair.last_report)  # type: ignore[arg-type]
    assert len(digest) == 64


def test_l6_25_missing_tests_generates_smoke_patch_plan(tmp_path: Path) -> None:
    (tmp_path / "pkg").mkdir()
    (tmp_path / "pkg" / "__init__.py").write_text("", encoding="utf-8")
    runtime = RuntimeEntry()
    runtime.run_project_repair_plan(workspace=tmp_path, path=".", tool_mode=ToolExecutionMode.RUNTIME_GOVERNED)
    report = runtime.project_repair_snapshot()
    targets = {step["target_path"] for step in report["patch_plan"]}
    assert "tests/test_smoke.py" in targets
    assert report["diagnosis_status"] == "needs_repair"
    assert report["shell_only"] is True


def test_l6_25_tool_is_a2_and_registered() -> None:
    runtime = RuntimeEntry()
    names = {tool.name: tool.default_risk for tool in runtime.available_tools()}
    assert names["build_project_repair_plan"] == "A2"
    risk, reason = RiskClassifier().classify(ToolInvocation("build_project_repair_plan", {"path": "."}))
    assert risk is RiskLevel.A2
    assert "L6.25" in reason
    assert "不应用补丁" in reason


def test_l6_25_plan_bridge_and_schema_allow_repair_plan() -> None:
    plan = PlanBridge().build_plan("repair-plan . L6.25 工程修复外壳")
    names = [step.tool_name for step in plan]
    assert names == ["scan_project", "run_python_quality_check", "diagnose_project", "build_project_repair_plan"]
    built = validate_and_build_plan(
        {
            "steps": [
                {
                    "tool_name": "build_project_repair_plan",
                    "arguments": {"path": ".", "notes": "只生成 PatchPlan", "max_targets": 8},
                }
            ]
        }
    )
    assert built[0].tool_name == "build_project_repair_plan"
    assert built[0].arguments["max_targets"] == 8


def test_l6_25_cli_repair_plan_build_and_export(tmp_path: Path) -> None:
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
        input="/repair-plan-build . 执行力优先，不污染内核\n/repair-plan\n/repair-plan-save repair_plan.json\n/exit\n",
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=60,
    )
    assert proc.returncode == 0, proc.stderr
    assert "L6.25 工程修复计划" in proc.stdout
    exported = json.loads((tmp_path / "repair_plan.json").read_text(encoding="utf-8"))
    assert exported["schema"] == "tiangong.l6_25.project_repair_plan.v1"
    assert exported["shell_only"] is True
    assert exported["modifies_kernel"] is False
    assert exported["applies_patch"] is False


def test_l6_25_notes_are_redacted(tmp_path: Path) -> None:
    _seed_python_project(tmp_path)
    runtime = RuntimeEntry()
    runtime.run_project_repair_plan(
        workspace=tmp_path,
        notes="api_key=sk-test-secret token=abc password=123",
        tool_mode=ToolExecutionMode.RUNTIME_GOVERNED,
    )
    text = json.dumps(runtime.project_repair_snapshot(), ensure_ascii=False)
    assert "sk-test-secret" not in text
    assert "token=abc" not in text
    assert "password=123" not in text


def test_l6_25_runtime_does_not_pollute_kernel_import_direction() -> None:
    kernel_root = ROOT / "tiangong_kernel"
    forbidden = ["project_repair_plan", "build_project_repair_plan", "ProjectRepairPlanBridge", "/repair-plan"]
    offenders: list[str] = []
    for path in kernel_root.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for token in forbidden:
            if token in text:
                offenders.append(f"{path.relative_to(ROOT)}::{token}")
    assert offenders == []
