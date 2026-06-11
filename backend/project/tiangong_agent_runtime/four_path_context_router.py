"""L6.43 FourPathContextRouter：四主路径统一投影。

将执行链状态、记忆召回、情志执行提示、生命周期候选和 P0 支撑系统
压缩为单一 UnifiedPlannerContextPack。它只产出 Planner 可消费上下文，不执行、
不调工具、不写记忆、不改预算、不修改核心组。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from time import time
from typing import Any

from tiangong_kernel.l6_plugins.common._common import ensure_bool

from .four_path_public_projection import (
    FourPathPublicProjection,
    build_redacted_evidence_refs,
    compact_public_payload,
    public_dict_of,
    sanitize_text,
    stable_digest,
)
from .four_path_priority_policy import FourPathPriorityPolicy, FourPathPriorityPolicyReport

L6_43_FOUR_PATH_CONTEXT_SCHEMA = "tiangong.l6_43.four_path_context_router.v1"
SOURCE_VERSION = "L6.43-four-path-context-router"


@dataclass(frozen=True)
class UnifiedPlannerContextPack:
    """Planner 单入口消费包。"""

    pack_id: str
    user_task_summary: str
    execution_contract_ref: str
    top_memory_hints: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    affective_style_hint: str = ""
    affective_candidate_bias: dict[str, Any] = field(default_factory=dict)
    lifecycle_next_action_hints: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    recovery_hints: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    quality_gate_constraints: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    budget_constraints: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    provider_constraints: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    skill_hints: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    handoff_hints: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    hard_boundaries: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    redacted_evidence_refs: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    context_digest: str = ""
    generated_at: float = 0.0
    planner_consumable: bool = True
    unified_projection: bool = True
    execution_first: bool = True
    no_second_runtime: bool = True
    no_direct_execution: bool = True
    no_tool_dispatch: bool = True
    no_model_dispatch: bool = True
    no_budget_mutation: bool = True
    no_memory_write: bool = True
    no_memory_delete: bool = True
    no_registry_mutation: bool = True
    no_kernel_mutation: bool = True
    no_secret_read: bool = True
    summary_only: bool = True
    evidence_ref_only: bool = True
    a0_a4_low_friction: bool = True
    a5_hard_boundary_preserved: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "planner_consumable",
            "unified_projection",
            "execution_first",
            "no_second_runtime",
            "no_direct_execution",
            "no_tool_dispatch",
            "no_model_dispatch",
            "no_budget_mutation",
            "no_memory_write",
            "no_memory_delete",
            "no_registry_mutation",
            "no_kernel_mutation",
            "no_secret_read",
            "summary_only",
            "evidence_ref_only",
            "a0_a4_low_friction",
            "a5_hard_boundary_preserved",
        ):
            ensure_bool(getattr(self, field_name), f"UnifiedPlannerContextPack.{field_name}")
        if not all(
            (
                self.planner_consumable,
                self.unified_projection,
                self.execution_first,
                self.no_second_runtime,
                self.no_direct_execution,
                self.no_tool_dispatch,
                self.no_model_dispatch,
                self.no_budget_mutation,
                self.no_memory_write,
                self.no_memory_delete,
                self.no_registry_mutation,
                self.no_kernel_mutation,
                self.no_secret_read,
                self.summary_only,
                self.evidence_ref_only,
                self.a0_a4_low_friction,
                self.a5_hard_boundary_preserved,
            )
        ):
            raise ValueError("UnifiedPlannerContextPack must remain non-executing projection")
        if len(self.top_memory_hints) > 5:
            raise ValueError("UnifiedPlannerContextPack allows at most 5 memory hints")
        if len(self.lifecycle_next_action_hints) > 3:
            raise ValueError("UnifiedPlannerContextPack allows at most 3 lifecycle hints")
        if not sanitize_text(self.execution_contract_ref, limit=240):
            raise ValueError("execution_contract_ref must be non-empty")

    def public_dict(self) -> dict[str, Any]:
        return {
            "schema": L6_43_FOUR_PATH_CONTEXT_SCHEMA,
            "source_version": SOURCE_VERSION,
            "pack_id": sanitize_text(self.pack_id, limit=240),
            "user_task_summary": sanitize_text(self.user_task_summary, limit=700),
            "execution_contract_ref": sanitize_text(self.execution_contract_ref, limit=240),
            "top_memory_hints": list(self.top_memory_hints),
            "affective_style_hint": sanitize_text(self.affective_style_hint, limit=500),
            "affective_candidate_bias": dict(self.affective_candidate_bias),
            "lifecycle_next_action_hints": list(self.lifecycle_next_action_hints),
            "recovery_hints": list(self.recovery_hints),
            "quality_gate_constraints": list(self.quality_gate_constraints),
            "budget_constraints": list(self.budget_constraints),
            "provider_constraints": list(self.provider_constraints),
            "skill_hints": list(self.skill_hints),
            "handoff_hints": list(self.handoff_hints),
            "hard_boundaries": list(self.hard_boundaries),
            "redacted_evidence_refs": list(self.redacted_evidence_refs),
            "context_digest": sanitize_text(self.context_digest, limit=80),
            "generated_at": self.generated_at,
            "memory_hint_count": len(self.top_memory_hints),
            "lifecycle_hint_count": len(self.lifecycle_next_action_hints),
            "evidence_ref_count": len(self.redacted_evidence_refs),
            "planner_consumable": self.planner_consumable,
            "unified_projection": self.unified_projection,
            "execution_first": self.execution_first,
            "no_second_runtime": self.no_second_runtime,
            "no_direct_execution": self.no_direct_execution,
            "no_tool_dispatch": self.no_tool_dispatch,
            "no_model_dispatch": self.no_model_dispatch,
            "no_budget_mutation": self.no_budget_mutation,
            "no_memory_write": self.no_memory_write,
            "no_memory_delete": self.no_memory_delete,
            "no_registry_mutation": self.no_registry_mutation,
            "no_kernel_mutation": self.no_kernel_mutation,
            "no_secret_read": self.no_secret_read,
            "summary_only": self.summary_only,
            "evidence_ref_only": self.evidence_ref_only,
            "a0_a4_low_friction": self.a0_a4_low_friction,
            "a5_hard_boundary_preserved": self.a5_hard_boundary_preserved,
        }


@dataclass(frozen=True)
class PlanPreflightCheck:
    """Planner 消费前预检。只检查上下文包边界，不执行计划。"""

    check_id: str
    passed: bool
    issues: tuple[str, ...] = field(default_factory=tuple)
    planner_consumable: bool = True
    no_direct_execution: bool = True

    def __post_init__(self) -> None:
        for field_name in ("passed", "planner_consumable", "no_direct_execution"):
            ensure_bool(getattr(self, field_name), f"PlanPreflightCheck.{field_name}")
        if not self.planner_consumable or not self.no_direct_execution:
            raise ValueError("PlanPreflightCheck must remain non-executing")

    def public_dict(self) -> dict[str, Any]:
        return {
            "check_id": sanitize_text(self.check_id, limit=180),
            "passed": self.passed,
            "issues": [sanitize_text(item, limit=240) for item in self.issues],
            "planner_consumable": self.planner_consumable,
            "no_direct_execution": self.no_direct_execution,
        }


@dataclass(frozen=True)
class FourPathContextReport:
    report_id: str
    generated_at: float
    status: str
    context_pack: UnifiedPlannerContextPack
    priority_policy: FourPathPriorityPolicyReport
    public_projection: FourPathPublicProjection
    preflight: PlanPreflightCheck
    summary: str = ""
    planner_consumable: bool = True
    no_second_runtime: bool = True
    no_direct_execution: bool = True
    no_tool_invocation: bool = True
    no_budget_mutation: bool = True
    no_memory_write: bool = True
    no_kernel_mutation: bool = True
    report_digest: str = ""

    def __post_init__(self) -> None:
        for field_name in (
            "planner_consumable",
            "no_second_runtime",
            "no_direct_execution",
            "no_tool_invocation",
            "no_budget_mutation",
            "no_memory_write",
            "no_kernel_mutation",
        ):
            ensure_bool(getattr(self, field_name), f"FourPathContextReport.{field_name}")
        if not (
            self.planner_consumable
            and self.no_second_runtime
            and self.no_direct_execution
            and self.no_tool_invocation
            and self.no_budget_mutation
            and self.no_memory_write
            and self.no_kernel_mutation
        ):
            raise ValueError("FourPathContextReport must remain non-executing")

    def public_dict(self) -> dict[str, Any]:
        return {
            "schema": L6_43_FOUR_PATH_CONTEXT_SCHEMA,
            "report_id": sanitize_text(self.report_id, limit=200),
            "generated_at": self.generated_at,
            "status": sanitize_text(self.status, limit=120),
            "summary": sanitize_text(self.summary, limit=900),
            "context_pack": self.context_pack.public_dict(),
            "priority_policy": self.priority_policy.public_dict(),
            "public_projection": self.public_projection.public_dict(),
            "preflight": self.preflight.public_dict(),
            "planner_consumable": self.planner_consumable,
            "no_second_runtime": self.no_second_runtime,
            "no_direct_execution": self.no_direct_execution,
            "no_tool_invocation": self.no_tool_invocation,
            "no_budget_mutation": self.no_budget_mutation,
            "no_memory_write": self.no_memory_write,
            "no_kernel_mutation": self.no_kernel_mutation,
            "report_digest": sanitize_text(self.report_digest, limit=80),
        }

    def summary_text(self) -> str:
        pack = self.context_pack
        return (
            "L6.43 FourPathContextRouter："
            f"status={self.status}; memory={len(pack.top_memory_hints)}; lifecycle={len(pack.lifecycle_next_action_hints)}; "
            f"evidence={len(pack.redacted_evidence_refs)}; preflight={self.preflight.passed}; "
            "execution_first=True; no_second_runtime=True; no_core_pollution=True。"
        )


class FourPathContextRouter:
    """四主路径统一投影路由器。"""

    def __init__(self) -> None:
        self._last_report: FourPathContextReport | None = None
        self._policy = FourPathPriorityPolicy()

    @property
    def last_report(self) -> FourPathContextReport | None:
        return self._last_report

    def build(
        self,
        *,
        user_task: Any,
        execution_contract_ref: str = "execution_contract:L6.37_frozen_execution_chain",
        memory_route: Any | None = None,
        affective_route: Any | None = None,
        lifecycle_bundle: Any | None = None,
        provider_envelope: Any | None = None,
        budget_snapshot: Any | None = None,
        skill_envelope: Any | None = None,
        handoff_envelope: Any | None = None,
        audit_evidence: Any | None = None,
        recovery_ticket: Any | None = None,
        quality_gate: Any | None = None,
        notes: str = "",
    ) -> FourPathContextReport:
        memory_hints = _memory_hints(memory_route)
        affective_style, affective_bias = _affective_projection(affective_route)
        lifecycle_hints = _lifecycle_hints(lifecycle_bundle)
        recovery_hints = _recovery_hints(recovery_ticket, lifecycle_bundle)
        quality_constraints = _quality_constraints(quality_gate)
        budget_constraints = _budget_constraints(budget_snapshot)
        provider_constraints = _provider_constraints(provider_envelope)
        skill_hints = _skill_hints(skill_envelope)
        handoff_hints = _handoff_hints(handoff_envelope)
        priority = self._policy.build_report(include_quality_gate=bool(quality_gate), notes=notes)
        public_projection = build_redacted_evidence_refs(
            {
                "memory": memory_route,
                "affective": affective_route,
                "lifecycle": lifecycle_bundle,
                "provider": provider_envelope,
                "budget": budget_snapshot,
                "skill": skill_envelope,
                "handoff": handoff_envelope,
                "audit": audit_evidence,
                "recovery": recovery_ticket,
                "quality_gate": quality_gate,
            }
        )
        hard_boundaries = tuple(priority.hard_boundaries)
        pack_payload = {
            "user_task_summary": sanitize_text(user_task, limit=700),
            "execution_contract_ref": sanitize_text(execution_contract_ref, limit=240),
            "top_memory_hints": memory_hints,
            "affective_style_hint": affective_style,
            "affective_candidate_bias": affective_bias,
            "lifecycle_next_action_hints": lifecycle_hints,
            "recovery_hints": recovery_hints,
            "quality_gate_constraints": quality_constraints,
            "budget_constraints": budget_constraints,
            "provider_constraints": provider_constraints,
            "skill_hints": skill_hints,
            "handoff_hints": handoff_hints,
            "hard_boundaries": hard_boundaries,
            "redacted_evidence_refs": tuple(item.public_dict() for item in public_projection.evidence_refs),
        }
        context_digest = stable_digest(pack_payload, length=24)
        pack = UnifiedPlannerContextPack(
            pack_id=f"unified_planner_context_pack:l6_43_{context_digest}",
            user_task_summary=pack_payload["user_task_summary"],
            execution_contract_ref=pack_payload["execution_contract_ref"],
            top_memory_hints=tuple(memory_hints),
            affective_style_hint=affective_style,
            affective_candidate_bias=affective_bias,
            lifecycle_next_action_hints=tuple(lifecycle_hints),
            recovery_hints=tuple(recovery_hints),
            quality_gate_constraints=tuple(quality_constraints),
            budget_constraints=tuple(budget_constraints),
            provider_constraints=tuple(provider_constraints),
            skill_hints=tuple(skill_hints),
            handoff_hints=tuple(handoff_hints),
            hard_boundaries=hard_boundaries,
            redacted_evidence_refs=tuple(item.public_dict() for item in public_projection.evidence_refs),
            context_digest=context_digest,
            generated_at=time(),
        )
        preflight = _preflight(pack)
        status = "four_path_context_ready" if preflight.passed else "four_path_context_blocked"
        summary = _summary(pack, notes=notes)
        report = FourPathContextReport(
            report_id=f"four_path_context_report:{stable_digest([pack.public_dict(), priority.public_dict(), preflight.public_dict()], length=16)}",
            generated_at=time(),
            status=status,
            context_pack=pack,
            priority_policy=priority,
            public_projection=public_projection,
            preflight=preflight,
            summary=summary,
        )
        digest = stable_digest({k: v for k, v in report.public_dict().items() if k != "report_digest"}, length=24)
        report = FourPathContextReport(**{**report.__dict__, "report_digest": digest})
        self._last_report = report
        return report

    def build_planner_hint(self) -> str:
        if self._last_report is None:
            return ""
        return self._last_report.summary_text()[:1800]

    def public_dict(self) -> dict[str, Any]:
        if self._last_report is None:
            return {"schema": L6_43_FOUR_PATH_CONTEXT_SCHEMA, "status": "empty"}
        return self._last_report.public_dict()


def _memory_hints(memory_route: Any | None) -> list[dict[str, Any]]:
    payload = public_dict_of(memory_route)
    raw_hints = payload.get("hints") or []
    hints: list[dict[str, Any]] = []
    for item in raw_hints[:5]:
        if not isinstance(item, dict):
            item = compact_public_payload(item)
        hints.append(
            {
                "memory_id": sanitize_text(item.get("memory_id"), limit=120),
                "sanitized_summary": sanitize_text(item.get("sanitized_summary"), limit=360),
                "recall_score": item.get("recall_score", 0.0),
                "evidence_refs": [sanitize_text(ref, limit=160) for ref in item.get("evidence_refs", [])[:4]],
                "summary_only": True,
                "no_raw_memory_body": True,
            }
        )
    return hints[:5]


def _affective_projection(affective_route: Any | None) -> tuple[str, dict[str, Any]]:
    payload = public_dict_of(affective_route)
    planner_hint = payload.get("planner_hint") if isinstance(payload.get("planner_hint"), dict) else {}
    style = planner_hint.get("style_hint") or payload.get("style_hint") or "情志未提供：使用默认克制、结构化、执行优先语言状态。"
    bias = {
        "candidate_priority_hint": sanitize_text(planner_hint.get("candidate_priority_hint"), limit=420),
        "risk_attention_hint": planner_hint.get("risk_attention_hint", 0.0),
        "recovery_patience_hint": planner_hint.get("recovery_patience_hint", 0.0),
        "long_chain_pacing_hint": planner_hint.get("long_chain_pacing_hint", 0.0),
        "same_risk_ranking_only": True,
        "not_authorization": True,
        "not_refusal": True,
        "no_tool_dispatch": True,
    }
    return sanitize_text(style, limit=520), bias


def _lifecycle_hints(lifecycle_bundle: Any | None) -> list[dict[str, Any]]:
    payload = public_dict_of(lifecycle_bundle)
    raw_hints = payload.get("planner_hints") or []
    hints: list[dict[str, Any]] = []
    for item in raw_hints:
        if not isinstance(item, dict):
            item = compact_public_payload(item)
        if item.get("blocked"):
            continue
        hints.append(
            {
                "hint_id": sanitize_text(item.get("hint_id"), limit=160),
                "priority": sanitize_text(item.get("priority"), limit=120),
                "hint_text": sanitize_text(item.get("hint_text"), limit=520),
                "requires_ticket": bool(item.get("requires_ticket", False)),
                "no_direct_execution": True,
            }
        )
        if len(hints) >= 3:
            break
    return hints


def _recovery_hints(recovery_ticket: Any | None, lifecycle_bundle: Any | None) -> list[dict[str, Any]]:
    hints: list[dict[str, Any]] = []
    for name, source in (("recovery_ticket", recovery_ticket), ("lifecycle", lifecycle_bundle)):
        payload = public_dict_of(source)
        if not payload:
            continue
        text = payload.get("planner_hint") or payload.get("status_summary") or payload.get("summary") or payload.get("status")
        if text:
            hints.append({"source": name, "hint": sanitize_text(text, limit=420), "no_direct_execution": True})
        if len(hints) >= 3:
            break
    return hints


def _quality_constraints(quality_gate: Any | None) -> list[dict[str, Any]]:
    payload = public_dict_of(quality_gate)
    if not payload:
        return [
            {
                "constraint_ref": "quality:l6_43_default_activation_gate",
                "constraint": "发布、打包、Skill 激活、Tool 注册、版本合入、热切换必须经过质量门和回滚证据。",
                "blocks_publication_activation_merge": True,
            }
        ]
    return [
        {
            "constraint_ref": sanitize_text(payload.get("evidence_id") or payload.get("report_digest") or payload.get("schema") or "quality:l6_43", limit=160),
            "constraint": sanitize_text(payload.get("planner_hint") or payload.get("summary") or payload.get("status") or "质量门约束", limit=420),
            "blocks_publication_activation_merge": True,
        }
    ]


def _budget_constraints(budget_snapshot: Any | None) -> list[dict[str, Any]]:
    payload = public_dict_of(budget_snapshot)
    if not payload:
        return [{"constraint_ref": "budget:l6_43_default_low_friction", "constraint": "A0-A4 不因投影层默认阻断；预算只提供低摩擦提示。", "mutates_budget": False}]
    return [
        {
            "constraint_ref": sanitize_text(payload.get("snapshot_id") or payload.get("ledger_id") or "budget:l6_43", limit=160),
            "planner_budget_hint": sanitize_text(payload.get("planner_budget_hint") or payload.get("hard_block_reason") or "预算约束摘要", limit=420),
            "resource_exhausted": bool(payload.get("resource_exhausted", False)),
            "mutates_budget": False,
        }
    ]


def _provider_constraints(provider_envelope: Any | None) -> list[dict[str, Any]]:
    payload = public_dict_of(provider_envelope)
    if not payload:
        return [{"constraint_ref": "provider:l6_43_no_naked_sdk", "constraint": "Provider 实调必须走 Runtime 治理，不允许裸 SDK/明文凭证。", "no_plain_secret": True}]
    return [
        {
            "constraint_ref": sanitize_text(payload.get("envelope_id") or payload.get("schema") or "provider:l6_43", limit=160),
            "constraint": sanitize_text(payload.get("fallback_reason") or payload.get("summary") or "Provider 声明式约束", limit=420),
            "no_plain_secret": True,
            "no_direct_network_call": True,
        }
    ]


def _skill_hints(skill_envelope: Any | None) -> list[dict[str, Any]]:
    payload = public_dict_of(skill_envelope)
    raw = payload.get("execution_hints") or payload.get("candidate_routes") or []
    hints: list[dict[str, Any]] = []
    for item in raw[:3]:
        if not isinstance(item, dict):
            item = compact_public_payload(item)
        hints.append({"skill_name": sanitize_text(item.get("skill_name"), limit=120), "hint": sanitize_text(item.get("hint_text") or item.get("planner_hint"), limit=360), "no_activation": True})
    return hints


def _handoff_hints(handoff_envelope: Any | None) -> list[dict[str, Any]]:
    payload = public_dict_of(handoff_envelope)
    if not payload:
        return []
    report = payload.get("parent_collect_report") if isinstance(payload.get("parent_collect_report"), dict) else {}
    hints = report.get("suggested_parent_steps") or []
    return [{"hint": sanitize_text(item, limit=320), "no_auto_recursive_spawn": True} for item in hints[:3]]


def _preflight(pack: UnifiedPlannerContextPack) -> PlanPreflightCheck:
    issues: list[str] = []
    if len(pack.top_memory_hints) > 5:
        issues.append("memory hints exceed top-5 limit")
    if len(pack.lifecycle_next_action_hints) > 3:
        issues.append("lifecycle hints exceed top-3 limit")
    if not pack.no_direct_execution or not pack.no_tool_dispatch:
        issues.append("context pack attempts direct execution/tool dispatch")
    if not pack.no_kernel_mutation:
        issues.append("context pack may mutate kernel")
    if not pack.redacted_evidence_refs:
        issues.append("context pack lacks evidence refs")
    return PlanPreflightCheck(
        check_id=f"plan_preflight:l6_43_{stable_digest(pack.public_dict(), length=16)}",
        passed=not issues,
        issues=tuple(issues),
    )


def _summary(pack: UnifiedPlannerContextPack, *, notes: str = "") -> str:
    text = (
        "四主路径已统一投影为 Planner 单入口上下文：执行链 contract 优先；Memory 只给摘要；"
        "Affective 只给语言/同风险排序提示；Lifecycle 只给候选；P0 支撑系统只给约束 ref。"
    )
    if notes:
        text += " 备注：" + sanitize_text(notes, limit=220)
    return text
