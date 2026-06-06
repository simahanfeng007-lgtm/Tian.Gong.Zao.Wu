from __future__ import annotations

from pathlib import Path

from tiangong_agent_runtime.rollback_audit_binding import (
    AuditEvidenceEnvelope,
    RecoveryCheckpoint,
    StateDeltaLedger,
    ToolDependencyGraph,
    build_audit_evidence_envelope,
    build_recovery_checkpoint,
    build_rollback_audit_binding_report,
    build_state_delta_ledger,
    build_tool_dependency_graph,
)


def _sample_report() -> dict:
    return {
        "schema": "tiangong.l6_35.planner_execution_controller.v1",
        "task_id": "task_l645",
        "run_id": "run_l645",
        "report_digest": "report_digest_l645",
        "status": "failed_with_resume",
        "total_steps": 3,
        "executed_steps": 2,
        "succeeded_steps": 1,
        "failed_steps": 1,
        "blocked_steps": 0,
        "timeout_steps": 0,
        "resume_envelope": {
            "resume_mode": "resume_from_next_step",
            "can_resume": True,
            "next_step_index": 3,
            "next_step_ids": ["step_validate"],
        },
        "step_records": [
            {
                "step_index": 1,
                "step_id": "step_prepare",
                "tool_name": "file_read_summary",
                "state": "succeeded",
                "audit_ref": "audit_prepare",
                "risk_level": "A1",
                "arguments_digest": "arg_prepare",
                "output_summary": "prepared safe summary; token=secret-value should redact",
                "evidence_refs": ["evidence_prepare"],
            },
            {
                "step_index": 2,
                "step_id": "step_patch",
                "parent_step_id": "step_prepare",
                "tool_name": "workspace_patch_apply",
                "state": "failed",
                "audit_ref": "audit_patch",
                "risk_level": "A3",
                "arguments_digest": "arg_patch",
                "output_summary": "patch failed, need recovery",
                "error_code": "patch_failed",
                "evidence_refs": ["evidence_patch"],
            },
            {
                "step_index": 3,
                "step_id": "step_validate",
                "parent_step_id": "step_patch",
                "tool_name": "pytest_targeted",
                "state": "skipped",
                "audit_ref": "",
                "risk_level": "A1",
                "arguments_digest": "arg_validate",
                "output_summary": "skipped after failure",
                "evidence_refs": [],
            },
        ],
    }


def test_l6_45_state_delta_ledger_is_projection_only_and_append_only(tmp_path: Path) -> None:
    ledger = build_state_delta_ledger(_sample_report())

    assert isinstance(ledger, StateDeltaLedger)
    assert ledger.append_only is True
    assert ledger.no_direct_execution is True
    assert ledger.no_kernel_mutation is True
    assert len(ledger.deltas) == 3
    assert ledger.deltas[0].reversible is True
    assert ledger.deltas[1].reversible is False
    assert "secret-value" not in ledger.deltas[0].public_dict()["changes_summary"]

    exported = ledger.export_jsonl(tmp_path / "ledger.jsonl")
    assert exported.exists()
    assert "delta:l6_45" in exported.read_text(encoding="utf-8")


def test_l6_45_tool_dependency_graph_tracks_edges_and_impacted_steps() -> None:
    graph = build_tool_dependency_graph(_sample_report())

    assert isinstance(graph, ToolDependencyGraph)
    assert graph.no_tool_dispatch is True
    assert graph.no_scheduler_override is True
    assert len(graph.nodes) == 3
    assert len(graph.edges) == 2
    assert graph.failed_step_ids == ("step_patch",)
    assert "step_validate" in graph.impacted_steps_from_failed()


def test_l6_45_dependency_graph_reports_missing_explicit_dependency() -> None:
    graph = build_tool_dependency_graph(_sample_report(), explicit_dependencies={"step_validate": ["step_missing"]})

    assert graph.missing_dependency_refs
    assert graph.no_direct_execution is True


def test_l6_45_recovery_checkpoint_binds_deltas_audits_and_does_not_rollback() -> None:
    report = _sample_report()
    ledger = build_state_delta_ledger(report)
    graph = build_tool_dependency_graph(report)
    checkpoint = build_recovery_checkpoint(report, ledger=ledger, dependency_graph=graph)

    assert isinstance(checkpoint, RecoveryCheckpoint)
    assert checkpoint.can_resume is True
    assert checkpoint.rollback_required is True
    assert checkpoint.next_step_id == "step_validate"
    assert checkpoint.no_rollback_execution is True
    assert checkpoint.no_quality_gate_override is True
    assert "audit_prepare" in checkpoint.audit_refs


def test_l6_45_audit_evidence_envelope_is_ref_only() -> None:
    report = _sample_report()
    ledger = build_state_delta_ledger(report)
    graph = build_tool_dependency_graph(report)
    checkpoint = build_recovery_checkpoint(report, ledger=ledger, dependency_graph=graph)
    envelope = build_audit_evidence_envelope(report, ledger=ledger, dependency_graph=graph, checkpoint=checkpoint)

    assert isinstance(envelope, AuditEvidenceEnvelope)
    assert envelope.evidence_ref_only is True
    assert envelope.no_full_evidence_body is True
    assert envelope.no_plain_secret is True
    payload = envelope.public_dict()
    assert payload["evidence_digest"]
    assert "audit_patch" in payload["audit_refs"]


def test_l6_45_binding_report_is_planner_consumable_without_execution() -> None:
    binding = build_rollback_audit_binding_report(_sample_report())
    payload = binding.public_dict()

    assert binding.planner_consumable is True
    assert binding.no_second_runtime is True
    assert binding.no_direct_execution is True
    assert binding.no_tool_dispatch is True
    assert binding.no_kernel_mutation is True
    assert payload["state_delta_ledger"]["delta_count"] == 3
    assert payload["dependency_graph"]["edge_count"] == 2
    assert payload["recovery_checkpoint"]["rollback_required"] is True
    assert payload["audit_evidence_envelope"]["evidence_ref_only"] is True
