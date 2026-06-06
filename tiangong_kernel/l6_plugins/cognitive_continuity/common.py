"""L6 phase4 cognitive continuity common declarations.

This package is a cognitive continuity, memory/forgetting candidate, and state
reentry design layer. It declares summary/ref/digest-only objects for L3/L5/L2
review. It never calls models, tools, adapters, state stores, memory stores,
auditors, budget systems, credentials, or any parallel runtime.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l6_plugins.common._common import (
    L6_COMMON_SCHEMA_VERSION,
    ensure_bool,
    ensure_no_live_or_sensitive_text,
    ensure_ref_items,
    ensure_ref_text,
    ensure_schema_version,
    stable_digest,
)

L6_PHASE4 = "L6_PHASE4_COGNITIVE_CONTINUITY_MEMORY_FORGETTING_REENTRY"


class CognitiveContinuityPluginKind(str, Enum):
    CONTEXT_CONTINUITY = "context_continuity"
    MEMORY_CANDIDATE = "memory_candidate"
    FORGETTING_CANDIDATE = "forgetting_candidate"
    BELIEF_WORLD_REVIEW = "belief_world_review"
    AFFECTIVE_REENTRY = "affective_reentry"
    SELF_REFLECTION_LEARNING = "self_reflection_learning"
    COGNITIVE_REENTRY_FUSION = "cognitive_reentry_fusion"
    PRODUCT_BRIDGE_SEED = "product_bridge_seed"


class CognitiveOutputKind(str, Enum):
    PROJECTION = "projection"
    CANDIDATE = "candidate"
    REVIEW_REQUEST = "review_request"
    REENTRY_ENVELOPE = "reentry_envelope"
    HINT = "hint"
    SUGGESTION = "suggestion"
    REPORT = "report"
    SCORE = "score"


class CognitiveReentryTarget(str, Enum):
    L3_ORCHESTRATION_REVIEW = "l3_orchestration_review"
    L5_GOVERNANCE_REVIEW = "l5_governance_review"
    L2_CANDIDATE_REVIEW = "l2_candidate_review"
    MEMORY_PROPOSAL_REVIEW = "memory_proposal_review"
    FORGETTING_PROPOSAL_REVIEW = "forgetting_proposal_review"
    CONTEXT_SAFETY_REVIEW = "context_safety_review"


class GovernanceReasonKind(str, Enum):
    SAFETY_POLICY = "safety_policy"
    PERMISSION_GOVERNANCE = "permission_governance"
    BUDGET_EXHAUSTED = "budget_exhausted"
    TOOL_UNAVAILABLE = "tool_unavailable"
    CONTEXT_INSUFFICIENT = "context_insufficient"
    USER_REQUIREMENT_UNCLEAR = "user_requirement_unclear"
    SYSTEM_BOUNDARY_BLOCKED = "system_boundary_blocked"


@dataclass(frozen=True)
class CognitiveContinuityPluginDeclaration:
    plugin_ref: str
    plugin_kind: CognitiveContinuityPluginKind | str
    summary: str
    output_kinds: tuple[CognitiveOutputKind | str, ...] = field(default_factory=lambda: (CognitiveOutputKind.PROJECTION, CognitiveOutputKind.HINT))
    source_refs: tuple[str, ...] = field(default_factory=lambda: ("summary:l6_phase4_input",))
    evidence_refs: tuple[str, ...] = field(default_factory=lambda: ("evidence:l6_phase4_plugin_declaration",))
    is_runtime: bool = False
    grants_permission: bool = False
    dispatches_model: bool = False
    dispatches_tool: bool = False
    writes_l2_fact: bool = False
    writes_memory: bool = False
    removes_memory: bool = False
    writes_audit: bool = False
    charges_budget: bool = False
    reads_live_credentials: bool = False
    direct_plugin_link: bool = False
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.plugin_ref, "CognitiveContinuityPluginDeclaration.plugin_ref")
        object.__setattr__(self, "plugin_kind", CognitiveContinuityPluginKind(self.plugin_kind))
        ensure_no_live_or_sensitive_text(self.summary, "CognitiveContinuityPluginDeclaration.summary")
        if not isinstance(self.output_kinds, tuple) or not self.output_kinds:
            raise ValueError("CognitiveContinuityPluginDeclaration.output_kinds must be non-empty tuple")
        object.__setattr__(self, "output_kinds", tuple(CognitiveOutputKind(kind) for kind in self.output_kinds))
        ensure_ref_items(self.source_refs, "CognitiveContinuityPluginDeclaration.source_refs", required=True)
        ensure_ref_items(self.evidence_refs, "CognitiveContinuityPluginDeclaration.evidence_refs", required=True)
        for field_name in (
            "is_runtime", "grants_permission", "dispatches_model", "dispatches_tool", "writes_l2_fact",
            "writes_memory", "removes_memory", "writes_audit", "charges_budget", "reads_live_credentials",
            "direct_plugin_link",
        ):
            ensure_bool(getattr(self, field_name), f"CognitiveContinuityPluginDeclaration.{field_name}")
        if any(
            (
                self.is_runtime,
                self.grants_permission,
                self.dispatches_model,
                self.dispatches_tool,
                self.writes_l2_fact,
                self.writes_memory,
                self.removes_memory,
                self.writes_audit,
                self.charges_budget,
                self.reads_live_credentials,
                self.direct_plugin_link,
            )
        ):
            raise ValueError("L6 phase4 cognitive continuity declarations must stay inert and review-mediated")
        ensure_schema_version(self.schema_version)

    @property
    def digest(self) -> str:
        return stable_digest(self)


@dataclass(frozen=True)
class CognitiveContinuityGroupArchitecture:
    group_ref: str = "l6:phase4_cognitive_continuity_group"
    phase: str = L6_PHASE4
    plugin_refs: tuple[str, ...] = field(default_factory=lambda: tuple(f"l6_phase4:{kind.value}" for kind in CognitiveContinuityPluginKind))
    l3_reentry_required: bool = True
    l5_review_required: bool = True
    l2_write_directly_allowed: bool = False
    memory_write_directly_allowed: bool = False
    memory_removal_directly_allowed: bool = False
    affective_as_modulation_only: bool = True
    product_bridge_inert_only: bool = True
    creates_parallel_runtime: bool = False
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.group_ref, "CognitiveContinuityGroupArchitecture.group_ref")
        if self.phase != L6_PHASE4:
            raise ValueError("CognitiveContinuityGroupArchitecture.phase must be L6 phase4")
        ensure_ref_items(self.plugin_refs, "CognitiveContinuityGroupArchitecture.plugin_refs", required=True)
        for field_name in (
            "l3_reentry_required", "l5_review_required", "l2_write_directly_allowed", "memory_write_directly_allowed",
            "memory_removal_directly_allowed", "affective_as_modulation_only", "product_bridge_inert_only", "creates_parallel_runtime",
        ):
            ensure_bool(getattr(self, field_name), f"CognitiveContinuityGroupArchitecture.{field_name}")
        if not self.l3_reentry_required or not self.l5_review_required:
            raise ValueError("Phase4 outputs must reenter through L3 and L5")
        if any((self.l2_write_directly_allowed, self.memory_write_directly_allowed, self.memory_removal_directly_allowed, self.creates_parallel_runtime)):
            raise ValueError("Phase4 group cannot write state, change memory, or create runtime")
        if not self.affective_as_modulation_only or not self.product_bridge_inert_only:
            raise ValueError("Phase4 affective/product branches must stay non-executing")
        ensure_schema_version(self.schema_version)

    @property
    def cognitive_group_is_not_runtime(self) -> bool:
        return self.creates_parallel_runtime is False


def default_cognitive_continuity_plugin_declarations() -> tuple[CognitiveContinuityPluginDeclaration, ...]:
    summaries = {
        CognitiveContinuityPluginKind.CONTEXT_CONTINUITY: "上下文连续性、断裂检测、重入摘要和安全审查候选。",
        CognitiveContinuityPluginKind.MEMORY_CANDIDATE: "记忆召回、晋升、关联、压缩和安全过滤候选。",
        CognitiveContinuityPluginKind.FORGETTING_CANDIDATE: "遗忘、衰减、墓碑、主动召回抑制和污染隔离候选。",
        CognitiveContinuityPluginKind.BELIEF_WORLD_REVIEW: "信念与世界状态候选审查、置信调节和事实候选复核。",
        CognitiveContinuityPluginKind.AFFECTIVE_REENTRY: "情志调制、污染监测、疲劳压力投影和治理原因绑定表达。",
        CognitiveContinuityPluginKind.SELF_REFLECTION_LEARNING: "自省、失败归因、学习需求和自愈候选，不自动修复。",
        CognitiveContinuityPluginKind.COGNITIVE_REENTRY_FUSION: "认知回流信封、冲突合并和 L3/L5 合法回流。",
        CognitiveContinuityPluginKind.PRODUCT_BRIDGE_SEED: "成品生产未来桥接候选，只保留 inert seed，不构建。",
    }
    return tuple(
        CognitiveContinuityPluginDeclaration(
            plugin_ref=f"l6_phase4:{kind.value}",
            plugin_kind=kind,
            summary=summaries[kind],
        )
        for kind in CognitiveContinuityPluginKind
    )
