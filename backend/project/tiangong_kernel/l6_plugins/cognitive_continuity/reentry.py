"""L6 phase4 cognitive reentry envelopes.

Reentry envelopes are routing candidates. They are not dispatchers and cannot
write facts, write memory, remove memory, or approve execution.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l6_plugins.common._common import (
    L6_COMMON_SCHEMA_VERSION,
    ensure_bool,
    ensure_no_live_or_sensitive_text,
    ensure_ref_items,
    ensure_ref_text,
    ensure_schema_version,
    stable_digest,
)
from .common import CognitiveReentryTarget, L6_PHASE4


@dataclass(frozen=True)
class CognitiveReentryEnvelope:
    envelope_ref: str = "l6:l6_phase4_cognitive_reentry_envelope"
    phase: str = L6_PHASE4
    source_projection_refs: tuple[str, ...] = field(default_factory=lambda: ("projection:l6_phase4_source",))
    target_refs: tuple[CognitiveReentryTarget | str, ...] = field(default_factory=lambda: (
        CognitiveReentryTarget.L3_ORCHESTRATION_REVIEW,
        CognitiveReentryTarget.L5_GOVERNANCE_REVIEW,
    ))
    conflict_refs: tuple[str, ...] = field(default_factory=tuple)
    evidence_refs: tuple[str, ...] = field(default_factory=lambda: ("evidence:l6_phase4_reentry",))
    trace_ref: str = "ref:l6_phase4_reentry_trace"
    audit_ref: str = "audit:l6_phase4_reentry"
    responsibility_chain_ref: str = "responsibility:l6_phase4_reentry"
    summary: str = "summary:l6_phase4_reentry"
    l3_review_required: bool = True
    l5_review_required: bool = True
    l2_direct_write: bool = False
    memory_direct_write: bool = False
    memory_direct_removal: bool = False
    audit_direct_write: bool = False
    budget_direct_charge: bool = False
    model_direct_dispatch: bool = False
    tool_direct_dispatch: bool = False
    permission_granted: bool = False
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.envelope_ref, "CognitiveReentryEnvelope.envelope_ref")
        if self.phase != L6_PHASE4:
            raise ValueError("CognitiveReentryEnvelope.phase must be L6 phase4")
        ensure_ref_items(self.source_projection_refs, "CognitiveReentryEnvelope.source_projection_refs", required=True)
        object.__setattr__(self, "target_refs", tuple(CognitiveReentryTarget(target) for target in self.target_refs))
        ensure_ref_items(self.conflict_refs, "CognitiveReentryEnvelope.conflict_refs")
        ensure_ref_items(self.evidence_refs, "CognitiveReentryEnvelope.evidence_refs", required=True)
        for field_name in ("trace_ref", "audit_ref", "responsibility_chain_ref"):
            ensure_ref_text(getattr(self, field_name), f"CognitiveReentryEnvelope.{field_name}")
        ensure_no_live_or_sensitive_text(self.summary, "CognitiveReentryEnvelope.summary")
        for field_name in (
            "l3_review_required", "l5_review_required", "l2_direct_write", "memory_direct_write", "memory_direct_removal",
            "audit_direct_write", "budget_direct_charge", "model_direct_dispatch", "tool_direct_dispatch", "permission_granted",
        ):
            ensure_bool(getattr(self, field_name), f"CognitiveReentryEnvelope.{field_name}")
        if not self.l3_review_required or not self.l5_review_required:
            raise ValueError("cognitive reentry requires L3 and L5 review")
        if any(
            (
                self.l2_direct_write,
                self.memory_direct_write,
                self.memory_direct_removal,
                self.audit_direct_write,
                self.budget_direct_charge,
                self.model_direct_dispatch,
                self.tool_direct_dispatch,
                self.permission_granted,
            )
        ):
            raise ValueError("cognitive reentry envelope cannot perform privileged actions")
        ensure_schema_version(self.schema_version)

    @property
    def digest(self) -> str:
        return stable_digest(self)

@dataclass(frozen=True)
class ContextReentryEnvelope(CognitiveReentryEnvelope):
    envelope_ref: str = "l6:l6_phase4_context_reentry_envelope"
    source_projection_refs: tuple[str, ...] = field(default_factory=lambda: ("projection:l6_phase4_context_continuity",))
    target_refs: tuple[CognitiveReentryTarget | str, ...] = field(default_factory=lambda: (
        CognitiveReentryTarget.CONTEXT_SAFETY_REVIEW,
        CognitiveReentryTarget.L3_ORCHESTRATION_REVIEW,
        CognitiveReentryTarget.L5_GOVERNANCE_REVIEW,
    ))
    direct_prompt_injection_allowed: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_bool(self.direct_prompt_injection_allowed, "ContextReentryEnvelope.direct_prompt_injection_allowed")
        if self.direct_prompt_injection_allowed:
            raise ValueError("context reentry envelope cannot inject prompt directly")


@dataclass(frozen=True)
class CognitiveReentryMatrixRule:
    rule_ref: str
    source_plugin_ref: str
    target_review: CognitiveReentryTarget | str
    allowed_output_refs: tuple[str, ...]
    host_mediated_only: bool = True
    direct_plugin_call_allowed: bool = False
    direct_state_change_allowed: bool = False
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.rule_ref, "CognitiveReentryMatrixRule.rule_ref")
        ensure_ref_text(self.source_plugin_ref, "CognitiveReentryMatrixRule.source_plugin_ref")
        object.__setattr__(self, "target_review", CognitiveReentryTarget(self.target_review))
        ensure_ref_items(self.allowed_output_refs, "CognitiveReentryMatrixRule.allowed_output_refs", required=True)
        ensure_bool(self.host_mediated_only, "CognitiveReentryMatrixRule.host_mediated_only")
        ensure_bool(self.direct_plugin_call_allowed, "CognitiveReentryMatrixRule.direct_plugin_call_allowed")
        ensure_bool(self.direct_state_change_allowed, "CognitiveReentryMatrixRule.direct_state_change_allowed")
        if not self.host_mediated_only or self.direct_plugin_call_allowed or self.direct_state_change_allowed:
            raise ValueError("phase4 reentry matrix must remain host-mediated")
        ensure_schema_version(self.schema_version)


def default_cognitive_reentry_matrix() -> tuple[CognitiveReentryMatrixRule, ...]:
    return (
        CognitiveReentryMatrixRule("l6:phase4_context_to_context_safety", "l6_phase4:context_continuity", CognitiveReentryTarget.CONTEXT_SAFETY_REVIEW, ("projection:l6_phase4_context_continuity",)),
        CognitiveReentryMatrixRule("l6:phase4_memory_to_memory_review", "l6_phase4:memory_candidate", CognitiveReentryTarget.MEMORY_PROPOSAL_REVIEW, ("projection:l6_phase4_memory_promotion_review_candidate",)),
        CognitiveReentryMatrixRule("l6:phase4_forgetting_to_forgetting_review", "l6_phase4:forgetting_candidate", CognitiveReentryTarget.FORGETTING_PROPOSAL_REVIEW, ("projection:l6_phase4_forgetting_review_candidate", "projection:l6_phase4_tombstone_proposal")),
        CognitiveReentryMatrixRule("l6:phase4_belief_world_to_l2_review", "l6_phase4:belief_world_review", CognitiveReentryTarget.L2_CANDIDATE_REVIEW, ("projection:l6_phase4_belief_world_review", "projection:l6_phase4_candidate_fact_review_request")),
        CognitiveReentryMatrixRule("l6:phase4_affective_to_l3_l5", "l6_phase4:affective_reentry", CognitiveReentryTarget.L3_ORCHESTRATION_REVIEW, ("projection:l6_phase4_affective_projection", "projection:l6_phase4_affective_pollution_risk")),
    )
