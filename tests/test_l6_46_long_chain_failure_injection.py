from __future__ import annotations

import pytest

from tiangong_agent_runtime.long_chain_failure_injection_harness import (
    FailureInjectionCase,
    FailureInjectionOutcome,
    L646LongChainFailureReport,
    LongChainFailureInjectionHarness,
    LongChainPressureSnapshot,
    build_pressure_plan,
    default_failure_injections,
)


def test_l6_46_default_failure_matrix_covers_four_path_boundaries() -> None:
    cases = default_failure_injections(stage_count=48)
    kinds = {case.kind for case in cases}

    assert "tool_timeout" in kinds
    assert "planner_schema_mismatch" in kinds
    assert "quality_gate_regression" in kinds
    assert "memory_pollution_write" in kinds
    assert "affective_permission_bypass" in kinds
    assert "free_will_active_task_preemption" in kinds
    assert "lifecycle_auto_apply" in kinds
    assert "credential_leak" in kinds
    assert "rollback_without_checkpoint" in kinds
    assert all(case.should_not_execute is True for case in cases)
    assert all(case.no_tool_dispatch is True for case in cases)
    assert all(case.no_kernel_mutation is True for case in cases)


def test_l6_46_pressure_plan_is_a0_a4_low_friction_candidate_only() -> None:
    plan = build_pressure_plan(32)

    assert len(plan) == 32
    assert all(step.tool_name in {"return_analysis", "return_code"} for step in plan)
    assert all("api_key" not in step.arguments for step in plan)
    assert all(step.step_id.startswith("l646_stage_") for step in plan)


def test_l6_46_harness_runs_four_path_planner_budget_and_rollback_binding() -> None:
    report = LongChainFailureInjectionHarness().run(stage_count=36)

    assert isinstance(report, L646LongChainFailureReport)
    assert report.ok is True
    assert report.four_path_report.preflight.passed is True
    assert report.planner_consumption_report.plan_preflight.passed is True
    assert report.budget_report.decision.passed is True
    assert report.rollback_audit_report.no_direct_execution is True
    assert report.rollback_audit_report.recovery_checkpoint.no_rollback_execution is True
    assert report.pressure_snapshot.recovery_checkpoint_count >= 1
    assert len(report.injection_outcomes) >= 8


def test_l6_46_failure_injection_outcomes_detect_and_block_auto_apply() -> None:
    report = LongChainFailureInjectionHarness().run(stage_count=24)
    routes = {outcome.injection.kind: outcome.route_taken for outcome in report.injection_outcomes}

    assert routes["memory_pollution_write"] == "MemoryWriteFilter/EvidenceGate"
    assert routes["affective_permission_bypass"] == "AffectiveBoundaryGuard"
    assert routes["free_will_active_task_preemption"] == "AutonomyLease/ActiveUserTaskGate"
    assert routes["lifecycle_auto_apply"] == "LifecycleCoordinator/no_auto_apply"
    assert routes["credential_leak"] == "CredentialPrivacyHardBoundary"
    assert all(outcome.detected is True for outcome in report.injection_outcomes)
    assert all(outcome.blocked_auto_apply is True for outcome in report.injection_outcomes)
    assert all(outcome.no_direct_execution is True for outcome in report.injection_outcomes)
    assert all(outcome.no_rollback_execution is True for outcome in report.injection_outcomes)


def test_l6_46_public_report_is_summary_ref_only_and_non_executing() -> None:
    report = LongChainFailureInjectionHarness().run(stage_count=16)
    payload = report.public_dict()
    rendered = str(payload).lower()

    assert payload["ok"] is True
    assert payload["no_second_runtime"] is True
    assert payload["no_direct_execution"] is True
    assert payload["no_tool_dispatch"] is True
    assert payload["no_budget_mutation"] is True
    assert payload["no_memory_write"] is True
    assert payload["no_kernel_mutation"] is True
    assert "sk-" not in rendered
    assert "private_key" not in rendered
    assert "full_evidence_body" not in rendered


def test_l6_46_score_and_bool_guards() -> None:
    with pytest.raises(ValueError):
        FailureInjectionCase(
            injection_id="bad",
            kind="tool_timeout",
            stage_index=1,
            expected_route="RecoveryCheckpoint",
            severity_score=True,  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError):
        LongChainPressureSnapshot(
            snapshot_id="bad",
            stage_count=True,  # type: ignore[arg-type]
            executed_stage_count=0,
            recoverable_failure_count=0,
            hard_boundary_failure_count=0,
            planner_context_pressure_score=0.1,
            budget_pressure_score=0.1,
            failure_pressure_score=0.1,
            recovery_checkpoint_count=0,
            audit_evidence_count=0,
            route_digest="digest",
        )
    case = FailureInjectionCase(
        injection_id="ok",
        kind="tool_timeout",
        stage_index=1,
        expected_route="RecoveryCheckpoint",
    )
    with pytest.raises(ValueError):
        FailureInjectionOutcome(
            outcome_id="bad",
            injection=case,
            detected=False,
            route_taken="RecoveryCheckpoint",
        )
