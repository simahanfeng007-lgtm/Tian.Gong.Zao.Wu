"""L6 phase3 mind state envelopes.

Mind state is a revocable, expiring, auditable candidate domain. It is never a
canonical L2 fact, never a permission grant, and never an execution plan.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l6_plugins.common._common import (
    ensure_score,
    L6_COMMON_SCHEMA_VERSION,
    ensure_bool, ensure_score,
    ensure_no_live_or_sensitive_text,
    ensure_ref_items,
    ensure_ref_text,
    ensure_schema_version,
    stable_digest,
)


class MindStateDomain(str, Enum):
    CONTEXT = "context"
    BELIEF = "belief"
    WORLD = "world"
    GOAL = "goal"
    INTENTION = "intention"
    ATTENTION = "attention"
    PREFERENCE = "preference"
    AFFECTIVE = "affective"
    MEMORY_CANDIDATE = "memory_candidate"
    FORGETTING_CANDIDATE = "forgetting_candidate"
    SELF_REFLECTION = "self_reflection"
    LEARNING_EVOLUTION = "learning_evolution"
    FUSION = "fusion"
    POLLUTION_DEFENSE = "pollution_defense"


def _score(value: float, field_name: str) -> None:
    ensure_score(value, field_name)


@dataclass(frozen=True)
class MindStateEnvelope:
    state_ref: str = "state:l6_mind_state"
    state_domain: MindStateDomain | str = MindStateDomain.CONTEXT
    plugin_ref: str = "mind:context_mind"
    source_refs: tuple[str, ...] = field(default_factory=lambda: ("ref:l6_mind_source",))
    input_summary_refs: tuple[str, ...] = field(default_factory=lambda: ("summary:l6_mind_input",))
    evidence_refs: tuple[str, ...] = field(default_factory=lambda: ("evidence:l6_mind_state",))
    confidence_score: float = 0.5
    uncertainty_score: float = 0.5
    risk_score: float = 0.0
    freshness_score: float = 0.5
    ttl_ref: str = "ref:l6_mind_state_ttl"
    expiry_ref: str = "ref:l6_mind_state_expiry"
    conflict_refs: tuple[str, ...] = field(default_factory=tuple)
    revocation_policy_ref: str = "policy:l6_mind_state_revocation"
    rollback_policy_ref: str = "rollback:l6_mind_state_rollback"
    redaction_profile_ref: str = "policy:l6_mind_state_redaction"
    public_projection_policy_ref: str = "policy:l6_mind_state_public_minimal"
    audit_trace_ref: str = "audit:l6_mind_state_trace"
    responsibility_chain_ref: str = "responsibility:l6_mind_state_chain"
    digest_summary: str = "summary:l6_mind_state"
    is_l2_fact: bool = False
    is_authorization: bool = False
    is_execution_plan: bool = False
    contains_raw_credential: bool = False
    contains_provider_locator: bool = False
    contains_tool_or_model_handle: bool = False
    contains_callable: bool = False
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.state_ref, "MindStateEnvelope.state_ref")
        object.__setattr__(self, "state_domain", MindStateDomain(self.state_domain))
        for field_name in (
            "plugin_ref", "ttl_ref", "expiry_ref", "revocation_policy_ref", "rollback_policy_ref",
            "redaction_profile_ref", "public_projection_policy_ref", "audit_trace_ref", "responsibility_chain_ref",
        ):
            ensure_ref_text(getattr(self, field_name), f"MindStateEnvelope.{field_name}")
        for field_name in ("source_refs", "input_summary_refs", "evidence_refs", "conflict_refs"):
            ensure_ref_items(getattr(self, field_name), f"MindStateEnvelope.{field_name}")
        for field_name in ("confidence_score", "uncertainty_score", "risk_score", "freshness_score"):
            _score(getattr(self, field_name), f"MindStateEnvelope.{field_name}")
        ensure_no_live_or_sensitive_text(self.digest_summary, "MindStateEnvelope.digest_summary")
        for field_name in (
            "is_l2_fact", "is_authorization", "is_execution_plan", "contains_raw_credential",
            "contains_provider_locator", "contains_tool_or_model_handle", "contains_callable",
        ):
            ensure_bool(getattr(self, field_name), f"MindStateEnvelope.{field_name}")
        if any(
            (
                self.is_l2_fact,
                self.is_authorization,
                self.is_execution_plan,
                self.contains_raw_credential,
                self.contains_provider_locator,
                self.contains_tool_or_model_handle,
                self.contains_callable,
            )
        ):
            raise ValueError("Mind state must remain candidate, inert, and safe for projection")
        ensure_schema_version(self.schema_version)

    @property
    def digest(self) -> str:
        return stable_digest(self)


@dataclass(frozen=True)
class ContextMindState(MindStateEnvelope):
    state_ref: str = "state:l6_context_mind"
    state_domain: MindStateDomain | str = MindStateDomain.CONTEXT
    plugin_ref: str = "mind:context_mind"
    context_is_prompt_injection: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.context_is_prompt_injection:
            raise ValueError("Context mind state cannot become prompt injection")


@dataclass(frozen=True)
class BeliefMindState(MindStateEnvelope):
    state_ref: str = "state:l6_belief_mind"
    state_domain: MindStateDomain | str = MindStateDomain.BELIEF
    plugin_ref: str = "mind:belief_mind"
    belief_is_fact: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.belief_is_fact:
            raise ValueError("Belief mind state cannot become fact")


@dataclass(frozen=True)
class WorldMindState(MindStateEnvelope):
    state_ref: str = "state:l6_world_mind"
    state_domain: MindStateDomain | str = MindStateDomain.WORLD
    plugin_ref: str = "mind:world_constraint_mind"
    canonical_world_state: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.canonical_world_state:
            raise ValueError("World mind state cannot become canonical state")


@dataclass(frozen=True)
class GoalMindState(MindStateEnvelope):
    state_ref: str = "state:l6_goal_mind"
    state_domain: MindStateDomain | str = MindStateDomain.GOAL
    plugin_ref: str = "mind:goal_mind"
    goal_is_execution_plan: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.goal_is_execution_plan:
            raise ValueError("Goal mind state cannot become execution plan")


@dataclass(frozen=True)
class IntentionMindState(MindStateEnvelope):
    state_ref: str = "state:l6_intention_mind"
    state_domain: MindStateDomain | str = MindStateDomain.INTENTION
    plugin_ref: str = "mind:intention_mind"


@dataclass(frozen=True)
class AttentionMindState(MindStateEnvelope):
    state_ref: str = "state:l6_attention_mind"
    state_domain: MindStateDomain | str = MindStateDomain.ATTENTION
    plugin_ref: str = "mind:attention_mind"
    attention_is_interrupt: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.attention_is_interrupt:
            raise ValueError("Attention mind state cannot become interrupt command")


@dataclass(frozen=True)
class PreferenceMindState(MindStateEnvelope):
    state_ref: str = "state:l6_preference_mind"
    state_domain: MindStateDomain | str = MindStateDomain.PREFERENCE
    plugin_ref: str = "mind:preference_mind"


@dataclass(frozen=True)
class AffectiveMindState(MindStateEnvelope):
    state_ref: str = "state:l6_affective_mind"
    state_domain: MindStateDomain | str = MindStateDomain.AFFECTIVE
    plugin_ref: str = "mind:affective_mind"
    affective_state_is_permission: bool = False
    complete_profile_public: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.affective_state_is_permission or self.complete_profile_public:
            raise ValueError("Affective mind state cannot grant permission or disclose complete profile")


@dataclass(frozen=True)
class MemoryCandidateMindState(MindStateEnvelope):
    state_ref: str = "state:l6_memory_candidate_mind"
    state_domain: MindStateDomain | str = MindStateDomain.MEMORY_CANDIDATE
    plugin_ref: str = "mind:memory_candidate_mind"
    writes_memory: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.writes_memory:
            raise ValueError("Memory candidate mind state cannot write memory")


@dataclass(frozen=True)
class ForgettingCandidateMindState(MindStateEnvelope):
    state_ref: str = "state:l6_forgetting_candidate_mind"
    state_domain: MindStateDomain | str = MindStateDomain.FORGETTING_CANDIDATE
    plugin_ref: str = "mind:forgetting_candidate_mind"
    deletes_memory: bool = False
    protected_l5_memory_retained: bool = True

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.deletes_memory or not self.protected_l5_memory_retained:
            raise ValueError("Forgetting candidate cannot delete memory or bypass L5 retention protection")


@dataclass(frozen=True)
class SelfReflectionMindState(MindStateEnvelope):
    state_ref: str = "state:l6_self_reflection_mind"
    state_domain: MindStateDomain | str = MindStateDomain.SELF_REFLECTION
    plugin_ref: str = "mind:self_reflection_mind"
    applies_repair: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.applies_repair:
            raise ValueError("Self reflection mind state cannot apply repair")


@dataclass(frozen=True)
class LearningEvolutionMindState(MindStateEnvelope):
    state_ref: str = "state:l6_learning_evolution_mind"
    state_domain: MindStateDomain | str = MindStateDomain.LEARNING_EVOLUTION
    plugin_ref: str = "mind:learning_evolution_mind"
    applies_migration: bool = False
    applies_rollback: bool = False
    performs_switch: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.applies_migration or self.applies_rollback or self.performs_switch:
            raise ValueError("Learning evolution mind state cannot migrate, rollback, or switch")


@dataclass(frozen=True)
class MindFusionState(MindStateEnvelope):
    state_ref: str = "state:l6_mind_fusion"
    state_domain: MindStateDomain | str = MindStateDomain.FUSION
    plugin_ref: str = "mind:mind_fusion_scoring"
    fusion_is_decision: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.fusion_is_decision:
            raise ValueError("Mind fusion state cannot become decision")


@dataclass(frozen=True)
class MindPollutionDefenseState(MindStateEnvelope):
    state_ref: str = "state:l6_mind_pollution_defense"
    state_domain: MindStateDomain | str = MindStateDomain.POLLUTION_DEFENSE
    plugin_ref: str = "mind:pollution_defense"
    value_dictatorship: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.value_dictatorship:
            raise ValueError("Pollution defense cannot become value dictatorship")
