"""L6 phase5 governance-control common declarations.

This package is an execution-first governance assistance layer for L6. It
creates risk, permission, budget, audit, privacy, credential and long-chain
review candidates only. It is not L5, never signs a real permit, never charges a
real budget, never writes audit/state/memory, never reads credentials, and never
calls models, tools, adapters or external systems.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l6_plugins.common._common import (
    L6_COMMON_SCHEMA_VERSION,
    ensure_bool,
    ensure_score,
    ensure_no_live_or_sensitive_text,
    ensure_ref_items,
    ensure_ref_text,
    ensure_schema_version,
    stable_digest,
)

L6_PHASE5 = "L6_PHASE5_GOVERNANCE_CONTROL"
EXECUTION_FIRST_WITHIN_HARD_BOUNDARIES = "ExecutionFirstWithinHardBoundaries"


class GovernancePluginKind(str, Enum):
    RISK_ASSESSMENT = "risk_assessment"
    PERMISSION_REQUIREMENT = "permission_requirement"
    BUDGET_PRESSURE = "budget_pressure"
    AUDIT_EVIDENCE = "audit_evidence"
    CREDENTIAL_BOUNDARY = "credential_boundary"
    PRIVACY_REDACTION = "privacy_redaction"
    GOVERNANCE_REVIEW = "governance_review"
    HUMAN_GATE = "human_gate"
    DEGRADATION_POLICY = "degradation_policy"
    PUBLIC_PROJECTION_SAFETY = "public_projection_safety"
    LONG_CHAIN_GOVERNANCE = "long_chain_governance"


class GovernanceOutputKind(str, Enum):
    PROJECTION = "projection"
    REQUIREMENT = "requirement"
    REVIEW_REQUEST = "review_request"
    HINT = "hint"
    SUGGESTION = "suggestion"
    REPORT = "report"
    SUMMARY = "summary"
    PLACEHOLDER = "placeholder"


class GovernanceReviewTarget(str, Enum):
    L3_CONTINUATION = "l3_continuation"
    L5_REVIEW = "l5_review"
    L2_STATE_ADMISSION_REVIEW = "l2_state_admission_review"
    MEMORY_PROPOSAL_GOVERNANCE = "memory_proposal_governance"
    FORGETTING_PROPOSAL_GOVERNANCE = "forgetting_proposal_governance"
    PRODUCT_BRIDGE_GOVERNANCE = "product_bridge_governance"
    LEARNING_HEALING_GOVERNANCE = "learning_healing_governance"


class GovernanceReasonKind(str, Enum):
    HARD_BOUNDARY_A5 = "hard_boundary_a5"
    CREDENTIAL_BOUNDARY = "credential_boundary"
    PRIVACY_BOUNDARY = "privacy_boundary"
    IRREVERSIBLE_SIDE_EFFECT = "irreversible_side_effect"
    REAL_EXTERNAL_ACTION = "real_external_action"
    STATE_OR_MEMORY_MUTATION = "state_or_memory_mutation"
    REAL_MODEL_OR_TOOL_CALL = "real_model_or_tool_call"
    REAL_BUDGET_CHARGE = "real_budget_charge"
    SYSTEM_BOUNDARY = "system_boundary"
    CONTEXT_INSUFFICIENT = "context_insufficient"
    BUDGET_EXHAUSTED = "budget_exhausted"


class RiskTier(str, Enum):
    A0 = "a0"
    A1 = "a1"
    A2 = "a2"
    A3 = "a3"
    A4 = "a4"
    A5 = "a5"


class RedactionState(str, Enum):
    NOT_NEEDED = "not_needed"
    REQUIRED = "required"
    APPLIED_SUMMARY_ONLY = "applied_summary_only"
    BLOCKED_PUBLIC_DETAIL = "blocked_public_detail"


class PrivacyClass(str, Enum):
    PUBLIC_SUMMARY = "public_summary"
    INTERNAL_REF_ONLY = "internal_ref_only"
    SENSITIVE_SUMMARY_ONLY = "sensitive_summary_only"
    BLOCKED_FROM_PUBLIC = "blocked_from_public"


def ensure_score(value: float, field_name: str) -> None:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError(f"{field_name} must be numeric score")
    if value < 0.0 or value > 1.0:
        raise ValueError(f"{field_name} must be within [0, 1]")


def ensure_non_negative_int(value: int, field_name: str) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError(f"{field_name} must be non-negative integer")


def ensure_digest_summary(value: str, field_name: str) -> None:
    ensure_no_live_or_sensitive_text(value, field_name)


@dataclass(frozen=True)
class GovernanceArtifactBase:
    object_ref: str
    source_refs: tuple[str, ...] = field(default_factory=lambda: ("summary:l6_phase5_source",))
    input_summary_refs: tuple[str, ...] = field(default_factory=lambda: ("summary:l6_phase5_input",))
    evidence_refs: tuple[str, ...] = field(default_factory=lambda: ("evidence:l6_phase5_evidence",))
    risk_refs: tuple[str, ...] = field(default_factory=tuple)
    requirement_refs: tuple[str, ...] = field(default_factory=tuple)
    trace_ref: str = "ref:l6_phase5_trace"
    responsibility_chain_ref: str = "responsibility:l6_phase5_chain"
    tamper_evidence_ref: str = "evidence:l6_phase5_tamper"
    redaction_state: RedactionState | str = RedactionState.APPLIED_SUMMARY_ONLY
    privacy_class: PrivacyClass | str = PrivacyClass.INTERNAL_REF_ONLY
    ttl_ref: str = "ref:l6_phase5_ttl"
    expiry_ref: str = "ref:l6_phase5_expiry"
    confidence_score: float = 0.75
    uncertainty_score: float = 0.25
    reversibility_hint: str = "summary:reversible_or_reviewable_candidate"
    degradation_hint: str = "summary:degrade_before_abort_when_safe"
    public_summary: str = "summary:l6_phase5_minimal_public_summary"
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.object_ref, f"{self.__class__.__name__}.object_ref")
        for field_name in ("source_refs", "input_summary_refs", "evidence_refs"):
            ensure_ref_items(getattr(self, field_name), f"{self.__class__.__name__}.{field_name}", required=True)
        ensure_ref_items(self.risk_refs, f"{self.__class__.__name__}.risk_refs")
        ensure_ref_items(self.requirement_refs, f"{self.__class__.__name__}.requirement_refs")
        for field_name in ("trace_ref", "responsibility_chain_ref", "tamper_evidence_ref", "ttl_ref", "expiry_ref"):
            ensure_ref_text(getattr(self, field_name), f"{self.__class__.__name__}.{field_name}")
        object.__setattr__(self, "redaction_state", RedactionState(self.redaction_state))
        object.__setattr__(self, "privacy_class", PrivacyClass(self.privacy_class))
        ensure_score(self.confidence_score, f"{self.__class__.__name__}.confidence_score")
        ensure_score(self.uncertainty_score, f"{self.__class__.__name__}.uncertainty_score")
        ensure_digest_summary(self.reversibility_hint, f"{self.__class__.__name__}.reversibility_hint")
        ensure_digest_summary(self.degradation_hint, f"{self.__class__.__name__}.degradation_hint")
        ensure_digest_summary(self.public_summary, f"{self.__class__.__name__}.public_summary")
        ensure_schema_version(self.schema_version)

    @property
    def digest(self) -> str:
        return stable_digest(self)


@dataclass(frozen=True)
class GovernanceControlPluginDeclaration:
    plugin_ref: str
    plugin_kind: GovernancePluginKind | str
    summary: str
    output_kinds: tuple[GovernanceOutputKind | str, ...] = field(default_factory=lambda: (GovernanceOutputKind.REQUIREMENT, GovernanceOutputKind.REVIEW_REQUEST, GovernanceOutputKind.HINT))
    source_refs: tuple[str, ...] = field(default_factory=lambda: ("summary:l6_phase5_input",))
    evidence_refs: tuple[str, ...] = field(default_factory=lambda: ("evidence:l6_phase5_plugin_declaration",))
    is_l5: bool = False
    issues_permit: bool = False
    emits_final_governance_result: bool = False
    allocates_budget: bool = False
    writes_audit_store: bool = False
    reads_credentials: bool = False
    dispatches_model: bool = False
    dispatches_tool: bool = False
    calls_l4_adapter: bool = False
    writes_l2_fact: bool = False
    writes_memory: bool = False
    deletes_memory: bool = False
    creates_parallel_runtime: bool = False
    direct_plugin_link: bool = False
    interrupts_low_risk_by_default: bool = False
    execution_first_within_hard_boundaries: bool = True
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.plugin_ref, "GovernanceControlPluginDeclaration.plugin_ref")
        object.__setattr__(self, "plugin_kind", GovernancePluginKind(self.plugin_kind))
        ensure_no_live_or_sensitive_text(self.summary, "GovernanceControlPluginDeclaration.summary")
        if not isinstance(self.output_kinds, tuple) or not self.output_kinds:
            raise ValueError("GovernanceControlPluginDeclaration.output_kinds must be non-empty tuple")
        object.__setattr__(self, "output_kinds", tuple(GovernanceOutputKind(kind) for kind in self.output_kinds))
        ensure_ref_items(self.source_refs, "GovernanceControlPluginDeclaration.source_refs", required=True)
        ensure_ref_items(self.evidence_refs, "GovernanceControlPluginDeclaration.evidence_refs", required=True)
        bool_fields = (
            "is_l5", "issues_permit", "emits_final_governance_result", "allocates_budget", "writes_audit_store", "reads_credentials",
            "dispatches_model", "dispatches_tool", "calls_l4_adapter", "writes_l2_fact", "writes_memory", "deletes_memory",
            "creates_parallel_runtime", "direct_plugin_link", "interrupts_low_risk_by_default", "execution_first_within_hard_boundaries",
        )
        for field_name in bool_fields:
            ensure_bool(getattr(self, field_name), f"GovernanceControlPluginDeclaration.{field_name}")
        forbidden_flags = (
            self.is_l5,
            self.issues_permit,
            self.emits_final_governance_result,
            self.allocates_budget,
            self.writes_audit_store,
            self.reads_credentials,
            self.dispatches_model,
            self.dispatches_tool,
            self.calls_l4_adapter,
            self.writes_l2_fact,
            self.writes_memory,
            self.deletes_memory,
            self.creates_parallel_runtime,
            self.direct_plugin_link,
            self.interrupts_low_risk_by_default,
        )
        if any(forbidden_flags):
            raise ValueError("L6 phase5 governance declarations must stay advisory, inert, and execution-first")
        if not self.execution_first_within_hard_boundaries:
            raise ValueError("ExecutionFirstWithinHardBoundaries must be preserved")
        ensure_schema_version(self.schema_version)

    @property
    def digest(self) -> str:
        return stable_digest(self)


@dataclass(frozen=True)
class GovernanceControlGroupArchitecture:
    group_ref: str = "l6:phase5_governance_control_group"
    phase: str = L6_PHASE5
    policy_ref: str = "policy:execution_first_within_hard_boundaries"
    plugin_refs: tuple[str, ...] = field(default_factory=lambda: tuple(f"l6_phase5:{kind.value}" for kind in GovernancePluginKind))
    l5_final_governance_required: bool = True
    l3_continuation_required: bool = True
    issues_permit: bool = False
    charges_budget: bool = False
    reads_credentials: bool = False
    writes_audit_store: bool = False
    blocks_low_risk_by_default: bool = False
    supports_long_chain_continuation: bool = True
    preserves_hard_boundaries: bool = True
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.group_ref, "GovernanceControlGroupArchitecture.group_ref")
        if self.phase != L6_PHASE5:
            raise ValueError("GovernanceControlGroupArchitecture.phase must be L6 phase5")
        ensure_ref_text(self.policy_ref, "GovernanceControlGroupArchitecture.policy_ref")
        ensure_ref_items(self.plugin_refs, "GovernanceControlGroupArchitecture.plugin_refs", required=True)
        for field_name in (
            "l5_final_governance_required", "l3_continuation_required", "issues_permit", "charges_budget", "reads_credentials",
            "writes_audit_store", "blocks_low_risk_by_default", "supports_long_chain_continuation", "preserves_hard_boundaries",
        ):
            ensure_bool(getattr(self, field_name), f"GovernanceControlGroupArchitecture.{field_name}")
        if not self.l5_final_governance_required or not self.l3_continuation_required:
            raise ValueError("Phase5 governance assistance must return to L3/L5 legal chain")
        if any((self.issues_permit, self.charges_budget, self.reads_credentials, self.writes_audit_store, self.blocks_low_risk_by_default)):
            raise ValueError("Phase5 group cannot make final governance decisions or over-block low-risk work")
        if not self.supports_long_chain_continuation or not self.preserves_hard_boundaries:
            raise ValueError("Phase5 must support long-chain continuity within hard boundaries")
        ensure_schema_version(self.schema_version)

    @property
    def governance_plugin_is_not_l5(self) -> bool:
        return self.issues_permit is False and self.l5_final_governance_required is True


def default_governance_control_plugin_declarations() -> tuple[GovernanceControlPluginDeclaration, ...]:
    summaries = {
        GovernancePluginKind.RISK_ASSESSMENT: "风险识别、分级、投影和长链风险累积摘要；不生成最终拒绝。",
        GovernancePluginKind.PERMISSION_REQUIREMENT: "权限需求、人类确认需求与最小确认策略；不签发许可。",
        GovernancePluginKind.BUDGET_PRESSURE: "预算、资源、成本、上下文窗口和长链分段压力提示；不扣预算。",
        GovernancePluginKind.AUDIT_EVIDENCE: "证据索引、审计需求、责任链、防篡改摘要与长链审计连续性；不写审计库。",
        GovernancePluginKind.CREDENTIAL_BOUNDARY: "凭证需求引用、边界和泄露风险投影；不读取或保存凭证。",
        GovernancePluginKind.PRIVACY_REDACTION: "隐私风险、脱敏需求、最小公开披露和敏感字段阻断提示。",
        GovernancePluginKind.GOVERNANCE_REVIEW: "统一治理审查请求与 L3/L5 回流摘要；不替代 L5。",
        GovernancePluginKind.HUMAN_GATE: "人工确认需求、批量确认和延后确认建议；不伪造确认票据。",
        GovernancePluginKind.DEGRADATION_POLICY: "分段、低能耗、缩小范围和可恢复续接建议；不直接终止。",
        GovernancePluginKind.PUBLIC_PROJECTION_SAFETY: "公开投影最小披露和泄露风险检查；不公开完整敏感材料。",
        GovernancePluginKind.LONG_CHAIN_GOVERNANCE: "超长链 checkpoint、恢复、最小确认和降级继续执行提示；不自建调度器。",
    }
    return tuple(
        GovernanceControlPluginDeclaration(
            plugin_ref=f"l6_phase5:{kind.value}",
            plugin_kind=kind,
            summary=summaries[kind],
        )
        for kind in GovernancePluginKind
    )
