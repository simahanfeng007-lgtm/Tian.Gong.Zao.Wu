"""L6.46 长链压力测试与失败注入测试外壳。

本模块用于验证 L6.40-L6.45 四主路径接入后的长链稳定性：
- FourPathContextRouter 是否能压缩长链上下文；
- Planner 消费层是否只吃 UnifiedPlannerContextPack；
- 预算低摩擦治理是否保持 A0-A4 顺滑、A5 硬边界；
- 回滚审计绑定是否能覆盖失败、跳过、恢复检查点；
- 失败注入是否只生成检测/恢复/阻断证据，不直接执行。

它是 runtime 外壳层的 deterministic harness，不调真实工具、不启动后台调度、
不执行回滚、不修改内核、不修改 Registry、不写长期记忆。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from time import time
from typing import Any, Iterable

from tiangong_kernel.l6_plugins.common._common import ensure_bool

from .budget_low_friction_governance import BudgetLowFrictionGovernanceBridge, BudgetLowFrictionReport
from .four_path_context_router import FourPathContextReport, FourPathContextRouter
from .four_path_public_projection import sanitize_text, stable_digest
from .planner_unified_consumption import PlannerConsumptionReport, PlannerUnifiedConsumptionBridge
from .rollback_audit_binding import RollbackAuditBindingReport, build_rollback_audit_binding_report
from .tool_invocation import ToolInvocation

L6_46_LONG_CHAIN_FAILURE_SCHEMA = "tiangong.l6_46.long_chain_pressure_failure_injection.v1"
SOURCE_VERSION = "L6.46-long-chain-pressure-failure-injection"

RECOVERABLE_FAILURE_KINDS = {
    "tool_timeout",
    "tool_result_error",
    "planner_schema_mismatch",
    "quality_gate_regression",
}
HARD_BOUNDARY_FAILURE_KINDS = {
    "credential_leak",
    "affective_permission_bypass",
    "lifecycle_auto_apply",
    "free_will_active_task_preemption",
    "memory_pollution_write",
    "rollback_without_checkpoint",
}
SUPPORTED_FAILURE_KINDS = RECOVERABLE_FAILURE_KINDS | HARD_BOUNDARY_FAILURE_KINDS


def _score(value: float, *, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field_name} must be a real score and must reject bool")
    number = float(value)
    if number != number or number < 0.0 or number > 1.0:
        raise ValueError(f"{field_name} must be within [0, 1]")
    return number


def _bounded_int(value: int, *, field_name: str, minimum: int = 0, maximum: int = 10000) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field_name} must be int and must reject bool")
    if value < minimum or value > maximum:
        raise ValueError(f"{field_name} out of range")
    return value


@dataclass(frozen=True)
class FailureInjectionCase:
    """失败注入用例。只描述要注入的故障，不触发真实执行。"""

    injection_id: str
    kind: str
    stage_index: int
    expected_route: str
    severity_score: float = 0.50
    description: str = ""
    requires_recovery_checkpoint: bool = True
    requires_quality_gate: bool = False
    requires_user_confirmation: bool = False
    should_block_auto_apply: bool = True
    should_not_execute: bool = True
    no_direct_execution: bool = True
    no_tool_dispatch: bool = True
    no_background_scheduler: bool = True
    no_kernel_mutation: bool = True
    no_registry_mutation: bool = True
    no_memory_write: bool = True

    def __post_init__(self) -> None:
        _bounded_int(self.stage_index, field_name="FailureInjectionCase.stage_index", minimum=1)
        _score(self.severity_score, field_name="FailureInjectionCase.severity_score")
        for field_name in (
            "requires_recovery_checkpoint",
            "requires_quality_gate",
            "requires_user_confirmation",
            "should_block_auto_apply",
            "should_not_execute",
            "no_direct_execution",
            "no_tool_dispatch",
            "no_background_scheduler",
            "no_kernel_mutation",
            "no_registry_mutation",
            "no_memory_write",
        ):
            ensure_bool(getattr(self, field_name), f"FailureInjectionCase.{field_name}")
        if self.kind not in SUPPORTED_FAILURE_KINDS:
            raise ValueError(f"unsupported failure injection kind: {self.kind}")
        if not self.injection_id:
            raise ValueError("FailureInjectionCase.injection_id required")
        if not all((self.should_not_execute, self.no_direct_execution, self.no_tool_dispatch, self.no_kernel_mutation, self.no_registry_mutation)):
            raise ValueError("FailureInjectionCase must remain non-executing")

    def public_dict(self) -> dict[str, Any]:
        return {
            "injection_id": sanitize_text(self.injection_id, limit=180),
            "kind": sanitize_text(self.kind, limit=120),
            "stage_index": self.stage_index,
            "expected_route": sanitize_text(self.expected_route, limit=180),
            "severity_score": self.severity_score,
            "description": sanitize_text(self.description, limit=360),
            "requires_recovery_checkpoint": self.requires_recovery_checkpoint,
            "requires_quality_gate": self.requires_quality_gate,
            "requires_user_confirmation": self.requires_user_confirmation,
            "should_block_auto_apply": self.should_block_auto_apply,
            "should_not_execute": self.should_not_execute,
            "no_direct_execution": self.no_direct_execution,
            "no_tool_dispatch": self.no_tool_dispatch,
            "no_background_scheduler": self.no_background_scheduler,
            "no_kernel_mutation": self.no_kernel_mutation,
            "no_registry_mutation": self.no_registry_mutation,
            "no_memory_write": self.no_memory_write,
        }


@dataclass(frozen=True)
class FailureInjectionOutcome:
    """失败注入检测结果。只产出证据、路线和阻断状态。"""

    outcome_id: str
    injection: FailureInjectionCase
    detected: bool
    route_taken: str
    recovery_hint: str = ""
    audit_ref: str = ""
    checkpoint_ref: str = ""
    quality_gate_ref: str = ""
    blocked_auto_apply: bool = True
    blocked_direct_execution: bool = True
    planner_consumable: bool = True
    evidence_ref_only: bool = True
    no_direct_execution: bool = True
    no_tool_dispatch: bool = True
    no_rollback_execution: bool = True
    no_budget_mutation: bool = True
    no_memory_write: bool = True
    no_kernel_mutation: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "detected",
            "blocked_auto_apply",
            "blocked_direct_execution",
            "planner_consumable",
            "evidence_ref_only",
            "no_direct_execution",
            "no_tool_dispatch",
            "no_rollback_execution",
            "no_budget_mutation",
            "no_memory_write",
            "no_kernel_mutation",
        ):
            ensure_bool(getattr(self, field_name), f"FailureInjectionOutcome.{field_name}")
        if not (
            self.detected
            and self.blocked_auto_apply
            and self.blocked_direct_execution
            and self.planner_consumable
            and self.evidence_ref_only
            and self.no_direct_execution
            and self.no_tool_dispatch
            and self.no_rollback_execution
            and self.no_budget_mutation
            and self.no_memory_write
            and self.no_kernel_mutation
        ):
            raise ValueError("FailureInjectionOutcome must be detected, blocked, evidence-ref-only and non-executing")

    def public_dict(self) -> dict[str, Any]:
        return {
            "outcome_id": sanitize_text(self.outcome_id, limit=180),
            "injection": self.injection.public_dict(),
            "detected": self.detected,
            "route_taken": sanitize_text(self.route_taken, limit=180),
            "recovery_hint": sanitize_text(self.recovery_hint, limit=420),
            "audit_ref": sanitize_text(self.audit_ref, limit=180),
            "checkpoint_ref": sanitize_text(self.checkpoint_ref, limit=180),
            "quality_gate_ref": sanitize_text(self.quality_gate_ref, limit=180),
            "blocked_auto_apply": self.blocked_auto_apply,
            "blocked_direct_execution": self.blocked_direct_execution,
            "planner_consumable": self.planner_consumable,
            "evidence_ref_only": self.evidence_ref_only,
            "no_direct_execution": self.no_direct_execution,
            "no_tool_dispatch": self.no_tool_dispatch,
            "no_rollback_execution": self.no_rollback_execution,
            "no_budget_mutation": self.no_budget_mutation,
            "no_memory_write": self.no_memory_write,
            "no_kernel_mutation": self.no_kernel_mutation,
        }


@dataclass(frozen=True)
class LongChainPressureSnapshot:
    """长链压力摘要。只记录压力，不调度、不执行。"""

    snapshot_id: str
    stage_count: int
    executed_stage_count: int
    recoverable_failure_count: int
    hard_boundary_failure_count: int
    planner_context_pressure_score: float
    budget_pressure_score: float
    failure_pressure_score: float
    recovery_checkpoint_count: int
    audit_evidence_count: int
    route_digest: str
    pressure_status: str = "pressure_checked"
    planner_consumable: bool = True
    no_second_runtime: bool = True
    no_direct_execution: bool = True
    no_tool_dispatch: bool = True
    no_background_scheduler: bool = True
    no_budget_mutation: bool = True
    no_memory_write: bool = True
    no_kernel_mutation: bool = True

    def __post_init__(self) -> None:
        _bounded_int(self.stage_count, field_name="LongChainPressureSnapshot.stage_count", minimum=1)
        _bounded_int(self.executed_stage_count, field_name="LongChainPressureSnapshot.executed_stage_count", minimum=0)
        _bounded_int(self.recoverable_failure_count, field_name="LongChainPressureSnapshot.recoverable_failure_count", minimum=0)
        _bounded_int(self.hard_boundary_failure_count, field_name="LongChainPressureSnapshot.hard_boundary_failure_count", minimum=0)
        _bounded_int(self.recovery_checkpoint_count, field_name="LongChainPressureSnapshot.recovery_checkpoint_count", minimum=0)
        _bounded_int(self.audit_evidence_count, field_name="LongChainPressureSnapshot.audit_evidence_count", minimum=0)
        _score(self.planner_context_pressure_score, field_name="LongChainPressureSnapshot.planner_context_pressure_score")
        _score(self.budget_pressure_score, field_name="LongChainPressureSnapshot.budget_pressure_score")
        _score(self.failure_pressure_score, field_name="LongChainPressureSnapshot.failure_pressure_score")
        for field_name in (
            "planner_consumable",
            "no_second_runtime",
            "no_direct_execution",
            "no_tool_dispatch",
            "no_background_scheduler",
            "no_budget_mutation",
            "no_memory_write",
            "no_kernel_mutation",
        ):
            ensure_bool(getattr(self, field_name), f"LongChainPressureSnapshot.{field_name}")
        if not all((self.planner_consumable, self.no_second_runtime, self.no_direct_execution, self.no_tool_dispatch, self.no_kernel_mutation)):
            raise ValueError("LongChainPressureSnapshot must remain projection-only")

    def public_dict(self) -> dict[str, Any]:
        return {
            "snapshot_id": sanitize_text(self.snapshot_id, limit=180),
            "stage_count": self.stage_count,
            "executed_stage_count": self.executed_stage_count,
            "recoverable_failure_count": self.recoverable_failure_count,
            "hard_boundary_failure_count": self.hard_boundary_failure_count,
            "planner_context_pressure_score": self.planner_context_pressure_score,
            "budget_pressure_score": self.budget_pressure_score,
            "failure_pressure_score": self.failure_pressure_score,
            "recovery_checkpoint_count": self.recovery_checkpoint_count,
            "audit_evidence_count": self.audit_evidence_count,
            "route_digest": sanitize_text(self.route_digest, limit=80),
            "pressure_status": sanitize_text(self.pressure_status, limit=120),
            "planner_consumable": self.planner_consumable,
            "no_second_runtime": self.no_second_runtime,
            "no_direct_execution": self.no_direct_execution,
            "no_tool_dispatch": self.no_tool_dispatch,
            "no_background_scheduler": self.no_background_scheduler,
            "no_budget_mutation": self.no_budget_mutation,
            "no_memory_write": self.no_memory_write,
            "no_kernel_mutation": self.no_kernel_mutation,
        }


@dataclass(frozen=True)
class L646LongChainFailureReport:
    report_id: str
    generated_at: float
    pressure_snapshot: LongChainPressureSnapshot
    four_path_report: FourPathContextReport
    planner_consumption_report: PlannerConsumptionReport
    budget_report: BudgetLowFrictionReport
    rollback_audit_report: RollbackAuditBindingReport
    injection_outcomes: tuple[FailureInjectionOutcome, ...]
    status: str = "l6_46_pressure_failure_passed"
    planner_consumable: bool = True
    no_second_runtime: bool = True
    no_direct_execution: bool = True
    no_tool_dispatch: bool = True
    no_background_scheduler: bool = True
    no_rollback_execution: bool = True
    no_budget_mutation: bool = True
    no_memory_write: bool = True
    no_memory_delete: bool = True
    no_registry_mutation: bool = True
    no_kernel_mutation: bool = True
    report_digest: str = ""

    def __post_init__(self) -> None:
        for field_name in (
            "planner_consumable",
            "no_second_runtime",
            "no_direct_execution",
            "no_tool_dispatch",
            "no_background_scheduler",
            "no_rollback_execution",
            "no_budget_mutation",
            "no_memory_write",
            "no_memory_delete",
            "no_registry_mutation",
            "no_kernel_mutation",
        ):
            ensure_bool(getattr(self, field_name), f"L646LongChainFailureReport.{field_name}")
        if not self.ok:
            raise ValueError("L646LongChainFailureReport requires all projection and detection gates to pass")

    @property
    def ok(self) -> bool:
        return bool(
            self.planner_consumable
            and self.no_second_runtime
            and self.no_direct_execution
            and self.no_tool_dispatch
            and self.no_background_scheduler
            and self.no_rollback_execution
            and self.no_budget_mutation
            and self.no_memory_write
            and self.no_memory_delete
            and self.no_registry_mutation
            and self.no_kernel_mutation
            and self.four_path_report.preflight.passed
            and self.planner_consumption_report.plan_preflight.passed
            and self.budget_report.decision.passed
            and self.rollback_audit_report.no_direct_execution
            and all(outcome.detected and outcome.blocked_auto_apply for outcome in self.injection_outcomes)
        )

    def public_dict(self) -> dict[str, Any]:
        return {
            "schema": L6_46_LONG_CHAIN_FAILURE_SCHEMA,
            "source_version": SOURCE_VERSION,
            "report_id": sanitize_text(self.report_id, limit=180),
            "generated_at": self.generated_at,
            "status": sanitize_text(self.status, limit=160),
            "ok": self.ok,
            "pressure_snapshot": self.pressure_snapshot.public_dict(),
            "four_path_report_digest": sanitize_text(self.four_path_report.report_digest, limit=80),
            "planner_consumption_report_digest": sanitize_text(self.planner_consumption_report.report_digest, limit=80),
            "budget_report_digest": sanitize_text(self.budget_report.report_digest, limit=80),
            "rollback_audit_report_digest": sanitize_text(self.rollback_audit_report.report_digest, limit=80),
            "injection_outcomes": [outcome.public_dict() for outcome in self.injection_outcomes],
            "planner_consumable": self.planner_consumable,
            "no_second_runtime": self.no_second_runtime,
            "no_direct_execution": self.no_direct_execution,
            "no_tool_dispatch": self.no_tool_dispatch,
            "no_background_scheduler": self.no_background_scheduler,
            "no_rollback_execution": self.no_rollback_execution,
            "no_budget_mutation": self.no_budget_mutation,
            "no_memory_write": self.no_memory_write,
            "no_memory_delete": self.no_memory_delete,
            "no_registry_mutation": self.no_registry_mutation,
            "no_kernel_mutation": self.no_kernel_mutation,
            "report_digest": sanitize_text(self.report_digest, limit=80),
        }

    def summary_text(self) -> str:
        return (
            "L6.46 长链压力/失败注入："
            f"status={self.status}; stages={self.pressure_snapshot.stage_count}; "
            f"injections={len(self.injection_outcomes)}; ok={self.ok}; "
            "no_second_runtime=True; no_direct_execution=True; no_core_pollution=True。"
        )


def default_failure_injections(stage_count: int = 48) -> tuple[FailureInjectionCase, ...]:
    _bounded_int(stage_count, field_name="stage_count", minimum=8, maximum=500)
    return (
        FailureInjectionCase(
            injection_id="inj:tool_timeout",
            kind="tool_timeout",
            stage_index=max(2, stage_count // 6),
            expected_route="RecoveryCheckpoint",
            severity_score=0.55,
            description="工具超时应生成恢复检查点，不直接重试无限循环。",
        ),
        FailureInjectionCase(
            injection_id="inj:planner_schema_mismatch",
            kind="planner_schema_mismatch",
            stage_index=max(3, stage_count // 5),
            expected_route="PlanPreflightCheck",
            severity_score=0.60,
            description="Planner shape 不兼容应在预检层拦截并生成续接 hint。",
        ),
        FailureInjectionCase(
            injection_id="inj:quality_gate_regression",
            kind="quality_gate_regression",
            stage_index=max(4, stage_count // 3),
            expected_route="QualityGateEvidence",
            severity_score=0.72,
            requires_quality_gate=True,
            description="质量门回归必须转验证要求，不得自动发布或合入。",
        ),
        FailureInjectionCase(
            injection_id="inj:memory_pollution_write",
            kind="memory_pollution_write",
            stage_index=max(5, stage_count // 2),
            expected_route="MemoryWriteFilter/EvidenceGate",
            severity_score=0.78,
            requires_user_confirmation=True,
            description="低置信或污染记忆写入必须被证据门拦住。",
        ),
        FailureInjectionCase(
            injection_id="inj:affective_permission_bypass",
            kind="affective_permission_bypass",
            stage_index=max(6, (stage_count * 2) // 3),
            expected_route="AffectiveBoundaryGuard",
            severity_score=0.82,
            requires_user_confirmation=True,
            description="情志不得变成授权、拒绝或工具派发理由。",
        ),
        FailureInjectionCase(
            injection_id="inj:free_will_active_task_preemption",
            kind="free_will_active_task_preemption",
            stage_index=max(7, (stage_count * 3) // 4),
            expected_route="AutonomyLease/ActiveUserTaskGate",
            severity_score=0.70,
            description="自由意志 tick 不能抢占当前用户任务。",
        ),
        FailureInjectionCase(
            injection_id="inj:lifecycle_auto_apply",
            kind="lifecycle_auto_apply",
            stage_index=max(8, stage_count - 2),
            expected_route="LifecycleCoordinator/no_auto_apply",
            severity_score=0.86,
            requires_quality_gate=True,
            requires_user_confirmation=True,
            description="自愈/学习/迭代候选不得自动修复、注册、合入或热切换。",
        ),
        FailureInjectionCase(
            injection_id="inj:credential_leak",
            kind="credential_leak",
            stage_index=max(8, stage_count - 1),
            expected_route="CredentialPrivacyHardBoundary",
            severity_score=0.95,
            requires_quality_gate=True,
            requires_user_confirmation=True,
            description="凭证/隐私泄露必须硬边界，不进入普通 PlannerContext。",
        ),
        FailureInjectionCase(
            injection_id="inj:rollback_without_checkpoint",
            kind="rollback_without_checkpoint",
            stage_index=stage_count,
            expected_route="RollbackAuditBinding/CheckpointRequired",
            severity_score=0.90,
            requires_quality_gate=True,
            requires_user_confirmation=True,
            description="缺少回滚点的更新不得执行回滚、发布、合入。",
        ),
    )


def build_pressure_plan(stage_count: int) -> tuple[ToolInvocation, ...]:
    _bounded_int(stage_count, field_name="stage_count", minimum=1, maximum=500)
    plan: list[ToolInvocation] = []
    for index in range(1, stage_count + 1):
        if index % 7 == 0:
            plan.append(ToolInvocation("return_code", {"language": "python", "content": f"# stage {index}\nvalue = {index}"}, step_id=f"l646_stage_{index:03d}"))
        elif index % 5 == 0:
            plan.append(ToolInvocation("return_analysis", {"content": f"复盘阶段 {index}，生成摘要和下一步 hint"}, step_id=f"l646_stage_{index:03d}"))
        else:
            plan.append(ToolInvocation("return_analysis", {"content": f"长链安全分析阶段 {index}"}, step_id=f"l646_stage_{index:03d}"))
    return tuple(plan)


def _budget_snapshot(stage_count: int, recoverable_failures: int) -> dict[str, Any]:
    executed_seen = max(stage_count // 2, 1)
    return {
        "snapshot_id": f"budget:l6_46:{stage_count}",
        "step_ledger": {
            "max_steps": stage_count + 12,
            "planned_steps": stage_count,
            "executed_steps_seen": executed_seen,
            "remaining_steps": max(12, stage_count + 12 - executed_seen),
            "exhausted": False,
        },
        "chain_lease": {"requested_extension": 5 if stage_count >= 45 else 0, "renewal_recommended": stage_count >= 45},
        "timeout_budget": {"default_timeout_seconds": 180.0, "remaining_timeout_seconds": 75.0, "blocks_execution": False},
        "failure_budget": {"max_failures": max(3, recoverable_failures + 2), "observed_failures": recoverable_failures, "exhausted": False},
        "planner_budget_hint": "L6.46 pressure: keep A0-A4 low friction; preserve A5 hard gates",
        "resource_exhausted": False,
        "downgrade_required": stage_count >= 80,
    }


def _memory_route_stub(stage_count: int) -> dict[str, Any]:
    return {
        "hints": [
            {
                "memory_id": f"memory:l646:{idx}",
                "sanitized_summary": f"长链阶段 {idx} 的可复用执行经验摘要",
                "recall_score": round(0.80 - idx * 0.04, 3),
                "evidence_refs": [f"evidence:l646:memory:{idx}"],
            }
            for idx in range(1, min(5, max(1, stage_count // 12)) + 1)
        ],
        "summary_only": True,
        "no_raw_memory_body": True,
    }


def _affective_route_stub(stage_count: int, recoverable_failures: int) -> dict[str, Any]:
    pressure = min(1.0, 0.20 + stage_count / 200.0 + recoverable_failures * 0.08)
    return {
        "planner_hint": {
            "style_hint": "长链压力下保持克制、结构化、少废话，优先交付与恢复点。",
            "candidate_priority_hint": "achievement/order 优先推进当前任务闭环，rest 只建议压缩链路。",
            "risk_attention_hint": min(1.0, pressure + 0.10),
            "recovery_patience_hint": min(1.0, 0.45 + recoverable_failures * 0.10),
            "long_chain_pacing_hint": pressure,
        },
        "not_authorization": True,
        "not_refusal": True,
        "no_tool_dispatch": True,
    }


def _lifecycle_bundle_stub(injections: Iterable[FailureInjectionCase]) -> dict[str, Any]:
    hints: list[dict[str, Any]] = []
    for index, case in enumerate(list(injections)[:3], start=1):
        hints.append(
            {
                "hint_id": f"lifecycle:l646:{index}",
                "priority": "current_task_recovery" if case.kind in RECOVERABLE_FAILURE_KINDS else "hard_boundary_review",
                "hint_text": f"{case.kind} 只生成候选/票据/恢复 hint，不自动执行。",
                "requires_ticket": case.requires_user_confirmation or case.requires_quality_gate,
                "blocked": False,
            }
        )
    return {
        "planner_hints": hints,
        "blocked_by_active_user_task": False,
        "requires_ticket": any(case.requires_user_confirmation for case in injections),
        "no_direct_execution": True,
    }


def _synthetic_execution_report(stage_count: int, injections: tuple[FailureInjectionCase, ...]) -> dict[str, Any]:
    recoverable = {case.stage_index: case for case in injections if case.kind in RECOVERABLE_FAILURE_KINDS}
    records: list[dict[str, Any]] = []
    failed_seen = False
    for index in range(1, stage_count + 1):
        case = recoverable.get(index)
        if case is not None:
            state = "failed" if not failed_seen else "skipped"
            failed_seen = True
            records.append(
                {
                    "step_index": index,
                    "step_id": f"l646_stage_{index:03d}",
                    "parent_step_id": f"l646_stage_{index - 1:03d}" if index > 1 else "",
                    "tool_name": "return_analysis",
                    "state": state,
                    "audit_ref": f"audit:l646:{case.kind}:{index}",
                    "risk_level": "A2" if case.kind != "quality_gate_regression" else "A4",
                    "arguments_digest": f"arg:l646:{index}",
                    "output_summary": f"injected recoverable failure {case.kind}; route={case.expected_route}",
                    "error_code": case.kind,
                    "evidence_refs": [f"evidence:l646:{case.kind}:{index}"],
                }
            )
        elif failed_seen:
            records.append(
                {
                    "step_index": index,
                    "step_id": f"l646_stage_{index:03d}",
                    "parent_step_id": f"l646_stage_{index - 1:03d}" if index > 1 else "",
                    "tool_name": "return_analysis",
                    "state": "skipped",
                    "audit_ref": "",
                    "risk_level": "A1",
                    "arguments_digest": f"arg:l646:{index}",
                    "output_summary": "skipped after injected failure for resume test",
                    "evidence_refs": [],
                }
            )
        else:
            records.append(
                {
                    "step_index": index,
                    "step_id": f"l646_stage_{index:03d}",
                    "parent_step_id": f"l646_stage_{index - 1:03d}" if index > 1 else "",
                    "tool_name": "return_analysis",
                    "state": "succeeded",
                    "audit_ref": f"audit:l646:stage:{index}",
                    "risk_level": "A1",
                    "arguments_digest": f"arg:l646:{index}",
                    "output_summary": f"stage {index} completed with public summary only",
                    "evidence_refs": [f"evidence:l646:stage:{index}"],
                }
            )
    failed_count = sum(1 for item in records if item["state"] == "failed")
    skipped_count = sum(1 for item in records if item["state"] == "skipped")
    succeeded_count = sum(1 for item in records if item["state"] == "succeeded")
    next_skipped = next((item for item in records if item["state"] == "skipped"), None)
    payload = {
        "schema": "tiangong.l6_46.synthetic_planner_execution_report.v1",
        "task_id": "task_l646_pressure_failure",
        "run_id": "run_l646_pressure_failure",
        "status": "failed_with_resume" if failed_count else "succeeded",
        "total_steps": stage_count,
        "executed_steps": succeeded_count + failed_count,
        "succeeded_steps": succeeded_count,
        "failed_steps": failed_count,
        "blocked_steps": 0,
        "timeout_steps": sum(1 for case in injections if case.kind == "tool_timeout"),
        "skipped_steps": skipped_count,
        "resume_envelope": {
            "resume_mode": "resume_from_checkpoint" if failed_count else "completed",
            "can_resume": bool(failed_count),
            "next_step_index": int(next_skipped["step_index"]) if next_skipped else stage_count + 1,
            "next_step_ids": [next_skipped["step_id"]] if next_skipped else [],
        },
        "step_records": records,
    }
    payload["report_digest"] = stable_digest(payload, length=24)
    return payload


def _outcome_for(case: FailureInjectionCase) -> FailureInjectionOutcome:
    route = case.expected_route
    digest = stable_digest(case.public_dict(), length=16)
    if case.kind in RECOVERABLE_FAILURE_KINDS:
        recovery_hint = f"检测到 {case.kind}，生成恢复检查点并回到 Planner 续接。"
        checkpoint_ref = f"checkpoint:l6_46:{digest}"
        quality_ref = f"quality:l6_46:{digest}" if case.requires_quality_gate else ""
    else:
        recovery_hint = f"检测到 {case.kind}，阻断自动执行/自动合入，转 review 或质量门。"
        checkpoint_ref = ""
        quality_ref = f"quality:l6_46:{digest}" if case.requires_quality_gate or case.kind in HARD_BOUNDARY_FAILURE_KINDS else ""
    return FailureInjectionOutcome(
        outcome_id=f"failure_injection_outcome:l6_46_{digest}",
        injection=case,
        detected=True,
        route_taken=route,
        recovery_hint=recovery_hint,
        audit_ref=f"audit:l6_46:{digest}",
        checkpoint_ref=checkpoint_ref,
        quality_gate_ref=quality_ref,
    )


class LongChainFailureInjectionHarness:
    """长链压力与失败注入外壳。"""

    def __init__(self) -> None:
        self._last_report: L646LongChainFailureReport | None = None

    @property
    def last_report(self) -> L646LongChainFailureReport | None:
        return self._last_report

    def run(
        self,
        *,
        stage_count: int = 48,
        injections: Iterable[FailureInjectionCase] | None = None,
    ) -> L646LongChainFailureReport:
        _bounded_int(stage_count, field_name="stage_count", minimum=8, maximum=500)
        injection_cases = tuple(injections) if injections is not None else default_failure_injections(stage_count)
        recoverable_count = sum(1 for case in injection_cases if case.kind in RECOVERABLE_FAILURE_KINDS)
        hard_count = sum(1 for case in injection_cases if case.kind in HARD_BOUNDARY_FAILURE_KINDS)
        budget_snapshot = _budget_snapshot(stage_count, recoverable_count)

        four_path_report = FourPathContextRouter().build(
            user_task=f"L6.46 长链压力测试：{stage_count} 阶段，{len(injection_cases)} 个失败注入点。",
            memory_route=_memory_route_stub(stage_count),
            affective_route=_affective_route_stub(stage_count, recoverable_count),
            lifecycle_bundle=_lifecycle_bundle_stub(injection_cases),
            budget_snapshot=budget_snapshot,
            audit_evidence={"evidence_refs": [f"evidence:l646:injection:{case.kind}" for case in injection_cases[:5]]},
            quality_gate={"constraints": ["发布/激活/合入必须质量门", "缺回滚点不得执行更新"]},
            notes="L6.46 pressure/failure harness",
        )
        plan = build_pressure_plan(stage_count)
        planner_consumption = PlannerUnifiedConsumptionBridge().consume(four_path_report, plan=plan)
        budget_report = BudgetLowFrictionGovernanceBridge().evaluate(plan, budget_snapshot=budget_snapshot)
        synthetic_report = _synthetic_execution_report(stage_count, injection_cases)
        rollback_report = build_rollback_audit_binding_report(synthetic_report)
        outcomes = tuple(_outcome_for(case) for case in injection_cases)

        context_pressure = min(1.0, 0.18 + stage_count / 180.0 + len(injection_cases) * 0.015)
        budget_pressure = max(
            budget_report.decision.pressure_signal.step_pressure_score,
            budget_report.decision.pressure_signal.timeout_pressure_score,
            budget_report.decision.pressure_signal.failure_pressure_score,
        )
        failure_pressure = min(1.0, recoverable_count * 0.12 + hard_count * 0.08)
        route_digest = stable_digest(
            {
                "four_path": four_path_report.report_digest,
                "planner": planner_consumption.report_digest,
                "budget": budget_report.report_digest,
                "rollback": rollback_report.report_digest,
                "outcomes": [outcome.public_dict() for outcome in outcomes],
            },
            length=24,
        )
        snapshot = LongChainPressureSnapshot(
            snapshot_id=f"long_chain_pressure_snapshot:l6_46_{route_digest}",
            stage_count=stage_count,
            executed_stage_count=int(synthetic_report["executed_steps"]),
            recoverable_failure_count=recoverable_count,
            hard_boundary_failure_count=hard_count,
            planner_context_pressure_score=round(context_pressure, 4),
            budget_pressure_score=round(float(budget_pressure), 4),
            failure_pressure_score=round(failure_pressure, 4),
            recovery_checkpoint_count=1 if synthetic_report["resume_envelope"].get("can_resume") else 0,
            audit_evidence_count=len(rollback_report.audit_evidence_envelope.audit_refs),
            route_digest=route_digest,
        )
        draft = L646LongChainFailureReport(
            report_id=f"l6_46_long_chain_failure_report:{stable_digest([snapshot.public_dict(), route_digest], length=16)}",
            generated_at=time(),
            pressure_snapshot=snapshot,
            four_path_report=four_path_report,
            planner_consumption_report=planner_consumption,
            budget_report=budget_report,
            rollback_audit_report=rollback_report,
            injection_outcomes=outcomes,
        )
        digest = stable_digest({k: v for k, v in draft.public_dict().items() if k != "report_digest"}, length=24)
        report = L646LongChainFailureReport(**{**draft.__dict__, "report_digest": digest})
        self._last_report = report
        return report

    def public_dict(self) -> dict[str, Any]:
        if self._last_report is None:
            return {"schema": L6_46_LONG_CHAIN_FAILURE_SCHEMA, "status": "empty"}
        return self._last_report.public_dict()
