from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from tiangong_agent_runtime.diagnostic_bridge import EngineeringDiagnosticBridge
from tiangong_agent_runtime.plan_schema import validate_and_build_plan
from tiangong_agent_runtime.runtime_entry import RuntimeEntry
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


def test_diagnostic_bridge_flags_missing_tests_and_readme(tmp_path: Path) -> None:
    (tmp_path / "pkg").mkdir()
    (tmp_path / "pkg" / "__init__.py").write_text("", encoding="utf-8")
    runtime = RuntimeEntry()
    runtime.run_text("scan .", workspace=tmp_path, tool_mode=ToolExecutionMode.RUNTIME_GOVERNED)
    result = runtime.run_text("diagnose .", workspace=tmp_path, tool_mode=ToolExecutionMode.RUNTIME_GOVERNED)
    assert result.results[-1].tool_name == "diagnose_project"
    diagnosis = runtime.diagnosis_snapshot()
    codes = {issue["code"] for issue in diagnosis["issues"]}
    assert "missing_tests" in codes
    assert "missing_readme" in codes
    assert diagnosis["status"] == "needs_repair"


def test_runtime_engineering_diagnosis_runs_scan_quality_and_diagnose(tmp_path: Path) -> None:
    _seed_python_project(tmp_path)
    runtime = RuntimeEntry()
    result = runtime.run_engineering_diagnosis(workspace=tmp_path, tool_mode=ToolExecutionMode.RUNTIME_GOVERNED)
    tools = [step.tool_name for step in result.plan]
    assert tools[:2] == ["scan_project", "run_python_quality_check"]
    assert "diagnose_project" in tools
    assert result.results[-1].ok
    assert runtime.diagnosis_snapshot()["schema"] == "tiangong.l6_17.engineering_diagnosis.v1"


def test_runtime_repair_loop_writes_report_and_package(tmp_path: Path) -> None:
    _seed_python_project(tmp_path)
    runtime = RuntimeEntry()
    result = runtime.run_engineering_repair_loop(workspace=tmp_path, tool_mode=ToolExecutionMode.RUNTIME_GOVERNED)
    assert result.results
    assert (tmp_path / "reports" / "l6_17_engineering_diagnosis.md").exists()
    assert (tmp_path / "dist" / "l6_17_repair_loop_delivery.zip").exists()
    assert any(item.endswith("l6_17_repair_loop_delivery.zip") for item in result.projection.artifacts)


def test_plan_validator_accepts_diagnose_project_and_rejects_unsafe_path() -> None:
    plan = validate_and_build_plan({"steps": [{"tool_name": "diagnose_project", "arguments": {"path": "."}}]})
    assert plan[0].tool_name == "diagnose_project"
    bad = None
    try:
        validate_and_build_plan({"steps": [{"tool_name": "diagnose_project", "arguments": {"path": "../secret"}}]})
    except Exception as exc:  # noqa: BLE001
        bad = exc
    assert bad is not None


def test_cli_diagnose_and_repair_loop(tmp_path: Path) -> None:
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
        input="/diagnose .\n/diagnosis\n/repair-loop .\n/diagnosis-save diagnosis.json\n/exit\n",
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=40,
    )
    assert proc.returncode == 0, proc.stderr
    assert "L6.17 工程诊断结果" in proc.stdout
    assert "工程诊断已导出" in proc.stdout
    assert (tmp_path / "diagnosis.json").exists()
    assert (tmp_path / "reports" / "l6_17_engineering_diagnosis.md").exists()


def test_diagnosis_export_does_not_contain_secret_file_content(tmp_path: Path) -> None:
    _seed_python_project(tmp_path)
    (tmp_path / ".env").write_text("SECRET=SHOULD_NOT_APPEAR\n", encoding="utf-8")
    runtime = RuntimeEntry()
    runtime.run_engineering_diagnosis(workspace=tmp_path, tool_mode=ToolExecutionMode.RUNTIME_GOVERNED)
    exported = runtime.export_diagnosis_json(tmp_path / "diag.json")
    text = exported.read_text(encoding="utf-8")
    assert "SHOULD_NOT_APPEAR" not in text
    assert "SECRET=" not in text
