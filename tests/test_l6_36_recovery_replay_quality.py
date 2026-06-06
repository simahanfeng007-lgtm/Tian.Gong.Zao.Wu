from __future__ import annotations

from pathlib import Path

from tiangong_agent_runtime.recovery_replay_quality import L6_36_CORPUS_SCHEMA, L6_36_SCHEMA, run_l6_36_replay_corpus
from tiangong_agent_runtime.runtime_entry import RuntimeEntry
from tiangong_agent_runtime.tool_invocation import ToolInvocation
from tiangong_agent_runtime.tool_result import ToolResult, ToolResultStatus
from tiangong_agent_shell.tool_bridge import ToolExecutionMode
from tiangong_agent_runtime.runtime_tool_registry import ToolDescriptor


def _workspace(tmp_path: Path) -> Path:
    (tmp_path / "README.md").write_text("# demo\n", encoding="utf-8")
    (tmp_path / "demo.py").write_text("print('ok')\n", encoding="utf-8")
    return tmp_path


def test_l6_36_completed_report_has_replay_recovery_and_quality_gate(tmp_path: Path) -> None:
    runtime = RuntimeEntry()
    runtime.execute_plan(
        [ToolInvocation("return_code", {"content": "print('ok')"}), ToolInvocation("return_analysis", {"content": "ok"})],
        workspace=_workspace(tmp_path),
        tool_mode=ToolExecutionMode.RUNTIME_GOVERNED,
        max_steps=4,
    )
    report = runtime.planner_execution_snapshot()
    l6_36 = report["l6_36"]
    assert l6_36["schema"] == L6_36_SCHEMA
    assert l6_36["failure_classifications"] == []
    assert l6_36["recovery_plan"]["mode"] == "completed"
    assert l6_36["quality_gate_result"]["decision"] == "pass"
    assert l6_36["replay_report"]["reconstructable"] is True
    assert l6_36["execution_chain_ready"] is True
    assert l6_36["no_direct_execution"] is True
    assert l6_36["no_kernel_mutation"] is True


def test_l6_36_failed_step_maps_to_recovery_plan_and_quality_fail(tmp_path: Path) -> None:
    runtime = RuntimeEntry()
    runtime.execute_plan(
        [ToolInvocation("read_file", {"path": "missing.txt"}), ToolInvocation("return_analysis", {"content": "after"})],
        workspace=_workspace(tmp_path),
        tool_mode=ToolExecutionMode.RUNTIME_GOVERNED,
        max_steps=4,
    )
    report = runtime.planner_execution_snapshot()
    l6_36 = report["l6_36"]
    failure_types = {item["failure_type"] for item in l6_36["failure_classifications"]}
    assert "tool_failed" in failure_types
    assert "budget_exhausted" in failure_types
    assert l6_36["recovery_plan"]["mode"] in {"recover_failed_step", "resume_from_next_step"}
    assert l6_36["recovery_plan"]["can_resume"] is True
    assert l6_36["quality_gate_result"]["decision"] == "fail"
    assert l6_36["quality_gate_result"]["allow_continue"] is True
    assert l6_36["replay_report"]["reconstructable"] is True


def test_l6_36_blocked_step_is_safety_stop_not_resume(tmp_path: Path) -> None:
    runtime = RuntimeEntry()
    runtime.execute_plan(
        [ToolInvocation("read_file", {"path": ".env"}), ToolInvocation("return_analysis", {"content": "after"})],
        workspace=_workspace(tmp_path),
        tool_mode=ToolExecutionMode.RUNTIME_GOVERNED,
        max_steps=4,
    )
    report = runtime.planner_execution_snapshot()
    l6_36 = report["l6_36"]
    assert l6_36["failure_type_counts"]["risk_blocked"] == 1
    assert l6_36["recovery_plan"]["mode"] == "blocked_replan"
    assert l6_36["recovery_plan"]["can_resume"] is False
    assert l6_36["quality_gate_result"]["decision"] == "blocked"
    assert "stop_for_safety" in l6_36["failure_classifications"][0]["next_action"]


def test_l6_36_confirmation_waits_for_ticket_and_quality_warn(tmp_path: Path) -> None:
    runtime = RuntimeEntry()
    runtime.execute_plan(
        [ToolInvocation("write_workspace_file", {"path": str(tmp_path / "absolute.txt"), "content": "x"})],
        workspace=_workspace(tmp_path),
        tool_mode=ToolExecutionMode.RUNTIME_GOVERNED,
        max_steps=2,
    )
    report = runtime.planner_execution_snapshot()
    l6_36 = report["l6_36"]
    assert l6_36["failure_type_counts"]["confirmation_required"] == 1
    assert l6_36["recovery_plan"]["mode"] == "await_confirmation"
    assert l6_36["quality_gate_result"]["decision"] == "warn"
    assert l6_36["recovery_plan"]["confirmation_ticket_ids"]


def test_l6_36_timeout_has_separate_failure_type_and_resume(tmp_path: Path) -> None:
    runtime = RuntimeEntry()

    def timeout_adapter(invocation: ToolInvocation, context) -> ToolResult:  # noqa: ANN001
        return ToolResult(invocation.step_id, invocation.tool_name, ToolResultStatus.TIMEOUT, "timeout", error_code="timeout")

    runtime.registry.register(ToolDescriptor("diagnose_timeout", "测试超时。", "A1"), timeout_adapter)
    runtime.execute_plan(
        [ToolInvocation("diagnose_timeout", {"path": "."}), ToolInvocation("return_analysis", {"content": "after"})],
        workspace=_workspace(tmp_path),
        tool_mode=ToolExecutionMode.RUNTIME_GOVERNED,
        max_steps=4,
    )
    report = runtime.planner_execution_snapshot()
    l6_36 = report["l6_36"]
    assert l6_36["failure_type_counts"]["timeout"] == 1
    assert l6_36["recovery_plan"]["mode"] == "recover_timeout_step"
    assert l6_36["recovery_plan"]["can_resume"] is True
    assert l6_36["quality_gate_result"]["decision"] == "fail"


def test_l6_36_replay_corpus_covers_core_failure_and_delivery_cases(tmp_path: Path) -> None:
    report = run_l6_36_replay_corpus(tmp_path, export_dir=tmp_path / "reports")
    payload = report.public_dict()
    assert payload["schema"] == L6_36_CORPUS_SCHEMA
    assert payload["ok"] is True
    cases = {case["case_name"]: case for case in payload["cases"]}
    assert set(cases) >= {
        "code_generation",
        "code_analysis",
        "file_read",
        "project_diagnosis",
        "recoverable_failure",
        "safety_blocked",
        "confirmation_required",
        "delivery_package",
        "quality_compileall",
    }
    assert cases["recoverable_failure"]["quality_decision"] == "fail"
    assert cases["safety_blocked"]["quality_decision"] == "blocked"
    assert cases["confirmation_required"]["quality_decision"] == "warn"
    assert (tmp_path / "reports" / "replay_corpus_result.json").exists()
    assert "L6.36 Replay Corpus" in (tmp_path / "reports" / "replay_corpus_report.txt").read_text(encoding="utf-8")
