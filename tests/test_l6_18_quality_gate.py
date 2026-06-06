from __future__ import annotations

from pathlib import Path

from tiangong_agent_runtime.quality_gate_bridge import QualityGateBridge
from tiangong_agent_runtime.runtime_entry import RuntimeEntry
from tiangong_agent_runtime.tool_result import ToolResult, ToolResultStatus


def _quality_result(command: str, status: ToolResultStatus) -> ToolResult:
    return ToolResult(
        step_id=f"{command}_step",
        tool_name="run_python_quality_check",
        status=status,
        output_summary=f"{command} summary",
        error_code="" if status is ToolResultStatus.OK else "quality_check_failed",
        data={"argv": ["python", "-m", command], "returncode": 0 if status is ToolResultStatus.OK else 1},
    )


def test_l6_18_quality_gate_passes_when_compileall_and_pytest_ok() -> None:
    bridge = QualityGateBridge()
    verdict = bridge.evaluate(
        quality_results=[_quality_result("compileall", ToolResultStatus.OK), _quality_result("pytest", ToolResultStatus.OK)],
        diagnosis={"issues": []},
        require_pytest=True,
    )
    assert verdict.decision == "pass"
    assert verdict.allow_package is True
    assert verdict.allow_continue is True


def test_l6_18_quality_gate_fails_when_required_pytest_missing() -> None:
    bridge = QualityGateBridge()
    verdict = bridge.evaluate(
        quality_results=[_quality_result("compileall", ToolResultStatus.OK)],
        diagnosis={"issues": []},
        require_pytest=True,
    )
    assert verdict.decision == "fail"
    assert verdict.allow_package is False
    assert any(issue.code == "pytest_missing" for issue in verdict.issues)


def test_l6_18_quality_gate_blocks_on_blocked_quality_check() -> None:
    bridge = QualityGateBridge()
    verdict = bridge.evaluate(
        quality_results=[_quality_result("compileall", ToolResultStatus.BLOCKED)],
        diagnosis={"issues": []},
    )
    assert verdict.decision == "blocked"
    assert verdict.allow_package is False
    assert verdict.allow_continue is False


def test_l6_18_runtime_quality_gate_does_not_package_on_compile_failure(tmp_path: Path) -> None:
    (tmp_path / "bad.py").write_text("def broken(:\n", encoding="utf-8")
    runtime = RuntimeEntry()
    result = runtime.run_quality_gate(
        workspace=tmp_path,
        path=".",
        require_pytest=False,
        package_on_pass=True,
    )
    verdict = runtime.quality_gate_snapshot()
    assert verdict["decision"] == "fail"
    assert verdict["allow_package"] is False
    assert not any(str(item).endswith(".zip") for item in result.projection.artifacts)


def test_l6_18_runtime_quality_gate_packages_when_allowed(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("# demo\n", encoding="utf-8")
    (tmp_path / "demo.py").write_text("def add(a, b):\n    return a + b\n", encoding="utf-8")
    (tmp_path / "test_demo.py").write_text("from demo import add\n\ndef test_add():\n    assert add(1, 2) == 3\n", encoding="utf-8")
    runtime = RuntimeEntry()
    result = runtime.run_quality_gate(
        workspace=tmp_path,
        path=".",
        require_pytest=True,
        package_on_pass=True,
        package_target="dist/quality_gate_ok.zip",
    )
    verdict = runtime.quality_gate_snapshot()
    assert verdict["decision"] in {"pass", "warn"}
    assert verdict["allow_package"] is True
    assert any(str(item).endswith("quality_gate_ok.zip") for item in result.projection.artifacts)
    assert (tmp_path / "dist" / "quality_gate_ok.zip").exists()
