from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from tiangong_agent_runtime.execution_policy import RiskLevel
from tiangong_agent_runtime.p0_system_integration_two import (
    L6_39_SCHEMA,
    AuditEvidenceEnvelope,
    L639P0SystemIntegrationBridge,
    MemoryRecallRoute,
    QualityGateEvidence,
    RecoveryResumeTicket,
)
from tiangong_agent_runtime.plan_bridge import PlanBridge
from tiangong_agent_runtime.plan_schema import validate_and_build_plan
from tiangong_agent_runtime.risk_classifier import RiskClassifier
from tiangong_agent_runtime.runtime_entry import RuntimeEntry
from tiangong_agent_runtime.tool_invocation import ToolInvocation
from tiangong_agent_runtime.tool_result import ToolResultStatus
from tiangong_agent_shell.tool_bridge import ToolExecutionMode

ROOT = Path(__file__).resolve().parents[1]


def _workspace(tmp_path: Path) -> Path:
    (tmp_path / "README.md").write_text("# demo\n", encoding="utf-8")
    return tmp_path


def test_l6_39_bridge_builds_memory_audit_recovery_quality_report_without_side_effects() -> None:
    bridge = L639P0SystemIntegrationBridge()
    bridge.build_memory(
        context_snapshot={
            "session_records": 1,
            "recent": [{"status": "ok", "intent": "demo", "summary": "api_key=sk-test token=abc secret=hidden"}],
            "planner_hint": "safe hint",
        },
        notes="memory smoke",
    )
    bridge.build_audit(
        audit_events=[
            {
                "audit_id": "audit_demo",
                "tool_name": "read_file",
                "risk_level": "A1",
                "permit_status": "allowed",
                "output_status": "ok",
                "input_summary": {"api_key": "sk-test"},
                "output_summary": "token=abc secret=hidden",
            }
        ],
        notes="audit smoke",
    )
    bridge.build_recovery(
        recovery_report={
            "report_digest": "recovery_digest",
            "failure_signal_count": 1,
            "resume_plan_count": 1,
            "failure_signals": [{"severity": "P2", "requires_human_confirmation": False}],
            "resume_plans": [{"next_action": "诊断→修复→复测→父链回流"}],
        },
        notes="recovery smoke",
    )
    bridge.build_quality_gate(
        quality_gate_report={"status": "ready", "decision": "warn", "allow_continue": True, "allow_package": True, "severity_counts": {"P2": 1}, "issues": [{}]},
        notes="quality smoke",
    )
    report = bridge.build_report().public_dict()

    assert report["schema"] == L6_39_SCHEMA
    assert report["status"] == "p0_systems_two_ready"
    assert report["planner_consumable"] is True
    assert report["runtime_governed"] is True
    assert report["uses_planner_execution_controller"] is True
    assert report["no_second_runtime"] is True
    assert report["no_kernel_mutation"] is True
    assert report["no_memory_write"] is True
    assert report["no_audit_mutation"] is True
    assert report["no_recovery_execution"] is True
    assert report["no_quality_gate_override"] is True
    assert report["memory"]["writes_l2_fact"] is False
    assert report["memory"]["mutates_memory_store"] is False
    assert report["audit"]["mutates_audit_log"] is False
    assert report["recovery"]["applies_patch"] is False
    assert report["recovery"]["spawns_agent"] is False
    assert report["quality_gate"]["overrides_quality_gate"] is False
    assert report["quality_gate"]["auto_approves_release"] is False

    rendered = json.dumps(report, ensure_ascii=False).lower()
    assert "sk-test" not in rendered
    assert "token=abc" not in rendered
    assert "secret=hidden" not in rendered


def test_l6_39_boundary_dataclasses_reject_bypass_flags() -> None:
    with pytest.raises(ValueError):
        MemoryRecallRoute(route_id="bad", snapshot_ref="s", session_records=1, writes_l2_fact=True)
    with pytest.raises(ValueError):
        AuditEvidenceEnvelope(envelope_id="bad", event_count=1, mutates_audit_log=True)
    with pytest.raises(ValueError):
        RecoveryResumeTicket(ticket_id="bad", source_report_ref="r", failure_count=0, resume_plan_count=0, applies_patch=True)
    with pytest.raises(ValueError):
        RecoveryResumeTicket(ticket_id="bad", source_report_ref="r", failure_count=0, resume_plan_count=0, spawns_agent=True)
    with pytest.raises(ValueError):
        QualityGateEvidence(evidence_id="bad", gate_status="ready", decision="pass", allow_continue=True, allow_package=True, overrides_quality_gate=True)
    with pytest.raises(ValueError):
        QualityGateEvidence(evidence_id="bad", gate_status="ready", decision="pass", allow_continue=True, allow_package=True, auto_approves_release=True)


def test_l6_39_runtime_registers_tools_and_executes_through_l6_37_chain(tmp_path: Path) -> None:
    runtime = RuntimeEntry()
    tools = {tool.name: tool.default_risk for tool in runtime.available_tools()}
    expected = {
        "build_l6_39_memory_integration",
        "build_l6_39_audit_integration",
        "build_l6_39_recovery_integration",
        "build_l6_39_quality_gate_integration",
        "build_l6_39_p0_integration",
    }
    assert expected.issubset(set(tools))
    assert all(tools[name] == "A2" for name in expected)

    result = runtime.run_l6_39_p0_system_integration_two(
        workspace=_workspace(tmp_path),
        notes="L6.39 Memory / Audit / Recovery / QualityGate",
        tool_mode=ToolExecutionMode.RUNTIME_GOVERNED,
        max_steps=10,
        max_items=4,
    )
    assert result.results[-1].tool_name == "build_l6_39_p0_integration"
    assert result.results[-1].status is ToolResultStatus.OK
    report = runtime.p0_system_integration_two_snapshot()
    assert report["schema"] == L6_39_SCHEMA
    assert report["status"] == "p0_systems_two_ready"
    assert report["uses_planner_execution_controller"] is True

    planner = runtime.planner_execution_snapshot()
    assert planner["status"] == "completed"
    assert planner["uses_long_chain_runner"] is True
    assert planner["uses_execution_spine"] is True
    assert planner["no_parallel_runtime"] is True
    assert planner["no_direct_adapter_call"] is True
    assert planner["no_kernel_mutation"] is True
    executed_tools = {step["tool_name"] for step in planner["step_records"]}
    assert expected.issubset(executed_tools)


def test_l6_39_plan_bridge_schema_and_risk_classifier_accept_p0_tools() -> None:
    plan = PlanBridge().build_plan("L6.39 Memory / Audit / Recovery / QualityGate 系统接入")
    tool_names = [step.tool_name for step in plan]
    assert "build_l6_39_memory_integration" in tool_names
    assert "build_l6_39_audit_integration" in tool_names
    assert "build_l6_39_recovery_integration" in tool_names
    assert "build_l6_39_quality_gate_integration" in tool_names
    assert "build_l6_39_p0_integration" in tool_names

    validated = validate_and_build_plan(
        {
            "steps": [
                {"tool_name": "l6_39_memory", "arguments": {"max_items": 2}},
                {"tool_name": "l6_39_audit", "arguments": {"max_events": 4}},
                {"tool_name": "l6_39_recovery", "arguments": {"max_items": 2}},
                {"tool_name": "l6_39_quality_gate", "arguments": {}},
                {"tool_name": "l6_39_p0", "arguments": {}},
            ]
        }
    )
    assert [step.tool_name for step in validated] == [
        "build_l6_39_memory_integration",
        "build_l6_39_audit_integration",
        "build_l6_39_recovery_integration",
        "build_l6_39_quality_gate_integration",
        "build_l6_39_p0_integration",
    ]

    classifier = RiskClassifier()
    for name in [step.tool_name for step in validated]:
        risk, reason = classifier.classify(ToolInvocation(name, {}))
        assert risk is RiskLevel.A2
        assert "L6.39" in reason


def test_l6_39_cli_build_show_export_and_reset(tmp_path: Path) -> None:
    _workspace(tmp_path)
    proc = subprocess.run(
        [sys.executable, "run_agent.py", "--mock", "--tool-mode", "runtime_governed", "--workspace", str(tmp_path)],
        cwd=ROOT,
        input="/p0-system2-build L6.39 Memory Audit Recovery QualityGate\n/p0-system2\n/p0-system2-save p0_system2.json\n/p0-system2-reset\n/p0-system2\n/exit\n",
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=60,
    )
    assert proc.returncode == 0, proc.stderr
    assert "L6.39 P0 系统接入二报告" in proc.stdout
    assert "L6.39 P0 系统接入二报告已导出" in proc.stdout
    assert "L6.39 P0 系统接入二报告已清空" in proc.stdout
    payload = json.loads((tmp_path / "p0_system2.json").read_text(encoding="utf-8"))
    assert payload["schema"] == L6_39_SCHEMA
    assert payload["status"] == "p0_systems_two_ready"


def test_l6_39_does_not_pollute_kernel_layer() -> None:
    forbidden = {
        "p0_system_integration_two",
        "build_l6_39_memory_integration",
        "build_l6_39_audit_integration",
        "build_l6_39_recovery_integration",
        "build_l6_39_quality_gate_integration",
        "build_l6_39_p0_integration",
        "/p0-system2",
    }
    offenders: list[str] = []
    for path in (ROOT / "tiangong_kernel").rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for token in forbidden:
            if token in text:
                offenders.append(f"{path.relative_to(ROOT)}:{token}")
    assert offenders == []
