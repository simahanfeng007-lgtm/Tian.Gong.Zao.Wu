"""L6 phase7 adaptive-collaboration common declarations.

This package models self-learning, self-healing, self-iteration and multi-plugin
collaboration *candidates* only. It deliberately remains inert: no skill writes,
knowledge writes, tool production, code patching, file materialization, test
execution, migration, rollback, hot switch, model invocation, tool invocation,
L4 adapter access, lower-layer state mutation, memory mutation, audit write,
budget charge, credential access, plugin dispatch or parallel agent scheduler
happens here.
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

L6_PHASE7 = "L6_PHASE7_ADAPTIVE_COLLABORATION"
ADAPTIVE_EXECUTION_FIRST_POLICY = "AdaptiveExecutionFirstWithinHardBoundaries"


class AdaptivePluginKind(str, Enum):
    LEARNING_NEED_REVIEW = "learning_need_review"
    SKILL_ACQUISITION_CANDIDATE = "skill_acquisition_candidate"
    TOOL_GAP_REQUIREMENT = "tool_gap_requirement"
    SELF_HEALING_DIAGNOSIS = "self_healing_diagnosis"
    REPAIR_PLAN_CANDIDATE = "repair_plan_candidate"
    REGRESSION_VALIDATION_REQUIREMENT = "regression_validation_requirement"
    SELF_ITERATION_PROPOSAL = "self_iteration_proposal"
    CONTRACT_PATCH_CANDIDATE = "contract_patch_candidate"
    EVOLUTION_CANDIDATE_REVIEW = "evolution_candidate_review"
    MULTI_PLUGIN_COLLABORATION_PLAN = "multi_plugin_collaboration_plan"
    HANDOFF_AGGREGATION = "handoff_aggregation"
    CONFLICT_RESOLUTION_SUGGESTION = "conflict_resolution_suggestion"
    LONG_CHAIN_ADAPTIVE_RECOVERY = "long_chain_adaptive_recovery"
    ADAPTIVE_PUBLIC_PROJECTION = "adaptive_public_projection"


class AdaptiveOutputKind(str, Enum):
    CANDIDATE = "candidate"
    REQUIREMENT = "requirement"
    REVIEW_REQUEST = "review_request"
    HINT = "hint"
    SUGGESTION = "suggestion"
    REPORT = "report"
    SUMMARY = "summary"
    HANDOFF = "handoff"


class AdaptiveRedactionState(str, Enum):
    NOT_NEEDED = "not_needed"
    APPLIED_SUMMARY_ONLY = "applied_summary_only"
    REQUIRED = "required"
    BLOCKED_PUBLIC_DETAIL = "blocked_public_detail"


class AdaptivePrivacyClass(str, Enum):
    PUBLIC_SUMMARY = "public_summary"
    INTERNAL_REF_ONLY = "internal_ref_only"
    SENSITIVE_SUMMARY_ONLY = "sensitive_summary_only"
    BLOCKED_FROM_PUBLIC = "blocked_from_public"


def ensure_score(value: float, field_name: str) -> None:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError(f"{field_name} must be numeric score")
    if value < 0.0 or value > 1.0:
        raise ValueError(f"{field_name} must be within [0, 1]")


@dataclass(frozen=True)
class AdaptiveArtifactBase:
    object_ref: str = "ref:l6_phase7_adaptive_artifact"
    source_refs: tuple[str, ...] = field(default_factory=lambda: ("summary:l6_phase7_source",))
    input_summary_refs: tuple[str, ...] = field(default_factory=lambda: ("summary:l6_phase7_input",))
    learning_refs: tuple[str, ...] = field(default_factory=tuple)
    repair_refs: tuple[str, ...] = field(default_factory=tuple)
    collaboration_refs: tuple[str, ...] = field(default_factory=tuple)
    handoff_refs: tuple[str, ...] = field(default_factory=tuple)
    conflict_refs: tuple[str, ...] = field(default_factory=tuple)
    governance_refs: tuple[str, ...] = field(default_factory=lambda: ("review:l6_phase7_governance_required",))
    requirement_refs: tuple[str, ...] = field(default_factory=tuple)
    risk_refs: tuple[str, ...] = field(default_factory=tuple)
    evidence_refs: tuple[str, ...] = field(default_factory=lambda: ("evidence:l6_phase7_evidence",))
    trace_ref: str = "ref:l6_phase7_trace"
    responsibility_chain_ref: str = "responsibility:l6_phase7_chain"
    tamper_evidence_ref: str = "evidence:l6_phase7_tamper"
    redaction_state: AdaptiveRedactionState | str = AdaptiveRedactionState.APPLIED_SUMMARY_ONLY
    privacy_class: AdaptivePrivacyClass | str = AdaptivePrivacyClass.INTERNAL_REF_ONLY
    ttl_ref: str = "ref:l6_phase7_ttl"
    expiry_ref: str = "ref:l6_phase7_expiry"
    confidence_score: float = 0.75
    uncertainty_score: float = 0.25
    reversibility_hint: str = "hint:l6_phase7_reversible_candidate"
    validation_requirement_refs: tuple[str, ...] = field(default_factory=lambda: ("validation:l6_phase7_required",))
    rollback_requirement_refs: tuple[str, ...] = field(default_factory=lambda: ("rollback:l6_phase7_required",))
    public_summary: str = "summary:l6_phase7_minimal_public_summary"
    not_executed: bool = True
    result_verified: bool = False
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.object_ref, f"{self.__class__.__name__}.object_ref")
        tuple_fields = (
            "source_refs", "input_summary_refs", "learning_refs", "repair_refs", "collaboration_refs", "handoff_refs",
            "conflict_refs", "governance_refs", "requirement_refs", "risk_refs", "evidence_refs",
            "validation_requirement_refs", "rollback_requirement_refs",
        )
        for field_name in tuple_fields:
            ensure_ref_items(
                getattr(self, field_name),
                f"{self.__class__.__name__}.{field_name}",
                required=field_name in ("source_refs", "input_summary_refs", "governance_refs", "evidence_refs"),
            )
        for field_name in ("trace_ref", "responsibility_chain_ref", "tamper_evidence_ref", "ttl_ref", "expiry_ref", "reversibility_hint"):
            ensure_ref_text(getattr(self, field_name), f"{self.__class__.__name__}.{field_name}")
        object.__setattr__(self, "redaction_state", AdaptiveRedactionState(self.redaction_state))
        object.__setattr__(self, "privacy_class", AdaptivePrivacyClass(self.privacy_class))
        ensure_score(self.confidence_score, f"{self.__class__.__name__}.confidence_score")
        ensure_score(self.uncertainty_score, f"{self.__class__.__name__}.uncertainty_score")
        ensure_no_live_or_sensitive_text(self.public_summary, f"{self.__class__.__name__}.public_summary")
        ensure_bool(self.not_executed, f"{self.__class__.__name__}.not_executed")
        ensure_bool(self.result_verified, f"{self.__class__.__name__}.result_verified")
        if not self.not_executed:
            raise ValueError("L6 phase7 adaptive artifacts must remain candidate or requirement objects")
        if self.result_verified:
            raise ValueError("L6 phase7 cannot verify or fake adaptive execution results")
        ensure_schema_version(self.schema_version)

    @property
    def digest(self) -> str:
        return stable_digest(self)


@dataclass(frozen=True)
class AdaptivePluginDeclaration:
    plugin_ref: str
    plugin_kind: AdaptivePluginKind | str
    summary: str
    output_kinds: tuple[AdaptiveOutputKind | str, ...] = field(default_factory=lambda: (AdaptiveOutputKind.CANDIDATE, AdaptiveOutputKind.REQUIREMENT, AdaptiveOutputKind.HINT))
    source_refs: tuple[str, ...] = field(default_factory=lambda: ("summary:l6_phase7_plugin_input",))
    evidence_refs: tuple[str, ...] = field(default_factory=lambda: ("evidence:l6_phase7_plugin_declaration",))
    is_executor: bool = False
    writes_skill: bool = False
    writes_knowledge: bool = False
    produces_tool: bool = False
    patches_code: bool = False
    writes_file: bool = False
    runs_tests: bool = False
    performs_migration: bool = False
    performs_rollback: bool = False
    performs_hot_switch: bool = False
    modifies_contract: bool = False
    applies_iteration: bool = False
    dispatches_plugins: bool = False
    creates_agent_scheduler: bool = False
    dispatches_model: bool = False
    dispatches_tool: bool = False
    calls_l4_adapter: bool = False
    reads_credentials: bool = False
    writes_l2_fact: bool = False
    writes_memory: bool = False
    deletes_memory: bool = False
    writes_audit_store: bool = False
    charges_budget: bool = False
    creates_parallel_runtime: bool = False
    direct_plugin_link: bool = False
    learning_continues_when_low_risk: bool = True
    failure_recovers_not_aborts: bool = True
    execution_first_within_hard_boundaries: bool = True
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.plugin_ref, "AdaptivePluginDeclaration.plugin_ref")
        object.__setattr__(self, "plugin_kind", AdaptivePluginKind(self.plugin_kind))
        ensure_no_live_or_sensitive_text(self.summary, "AdaptivePluginDeclaration.summary")
        if not isinstance(self.output_kinds, tuple) or not self.output_kinds:
            raise ValueError("AdaptivePluginDeclaration.output_kinds must be non-empty tuple")
        object.__setattr__(self, "output_kinds", tuple(AdaptiveOutputKind(kind) for kind in self.output_kinds))
        ensure_ref_items(self.source_refs, "AdaptivePluginDeclaration.source_refs", required=True)
        ensure_ref_items(self.evidence_refs, "AdaptivePluginDeclaration.evidence_refs", required=True)
        bool_fields = (
            "is_executor", "writes_skill", "writes_knowledge", "produces_tool", "patches_code", "writes_file", "runs_tests",
            "performs_migration", "performs_rollback", "performs_hot_switch", "modifies_contract", "applies_iteration",
            "dispatches_plugins", "creates_agent_scheduler", "dispatches_model", "dispatches_tool", "calls_l4_adapter",
            "reads_credentials", "writes_l2_fact", "writes_memory", "deletes_memory", "writes_audit_store", "charges_budget",
            "creates_parallel_runtime", "direct_plugin_link", "learning_continues_when_low_risk", "failure_recovers_not_aborts",
            "execution_first_within_hard_boundaries",
        )
        for field_name in bool_fields:
            ensure_bool(getattr(self, field_name), f"AdaptivePluginDeclaration.{field_name}")
        forbidden = (
            self.is_executor, self.writes_skill, self.writes_knowledge, self.produces_tool, self.patches_code,
            self.writes_file, self.runs_tests, self.performs_migration, self.performs_rollback, self.performs_hot_switch,
            self.modifies_contract, self.applies_iteration, self.dispatches_plugins, self.creates_agent_scheduler,
            self.dispatches_model, self.dispatches_tool, self.calls_l4_adapter, self.reads_credentials, self.writes_l2_fact,
            self.writes_memory, self.deletes_memory, self.writes_audit_store, self.charges_budget, self.creates_parallel_runtime,
            self.direct_plugin_link,
        )
        if any(forbidden):
            raise ValueError("L6 phase7 adaptive plugins must stay inert and candidate-only")
        if not (self.learning_continues_when_low_risk and self.failure_recovers_not_aborts and self.execution_first_within_hard_boundaries):
            raise ValueError("Adaptive plugins must preserve execution-first recovery inside hard boundaries")
        ensure_schema_version(self.schema_version)

    @property
    def is_candidate_only(self) -> bool:
        return not any((
            self.is_executor, self.writes_skill, self.writes_knowledge, self.produces_tool, self.patches_code,
            self.writes_file, self.runs_tests, self.dispatches_plugins, self.dispatches_model, self.dispatches_tool,
        ))

    @property
    def digest(self) -> str:
        return stable_digest(self)


@dataclass(frozen=True)
class AdaptiveExecutionFirstPolicy:
    policy_ref: str = "policy:l6_phase7_adaptive_execution_first"
    learning_should_continue_when_low_risk: bool = True
    failure_should_recover_not_abort: bool = True
    repair_candidate_should_not_patch: bool = True
    collaboration_should_not_direct_call: bool = True
    conflict_suggestion_should_not_decide: bool = True
    handoff_aggregation_should_not_merge: bool = True
    iteration_candidate_should_not_apply: bool = True
    evolution_candidate_should_not_execute: bool = True
    hard_boundaries_preserved: bool = True
    summary_ref: str = "summary:l6_phase7_adaptive_execution_first"
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.policy_ref, "AdaptiveExecutionFirstPolicy.policy_ref")
        for field_name in (
            "learning_should_continue_when_low_risk", "failure_should_recover_not_abort", "repair_candidate_should_not_patch",
            "collaboration_should_not_direct_call", "conflict_suggestion_should_not_decide", "handoff_aggregation_should_not_merge",
            "iteration_candidate_should_not_apply", "evolution_candidate_should_not_execute", "hard_boundaries_preserved",
        ):
            ensure_bool(getattr(self, field_name), f"AdaptiveExecutionFirstPolicy.{field_name}")
        if not all(getattr(self, field_name) for field_name in (
            "learning_should_continue_when_low_risk", "failure_should_recover_not_abort", "repair_candidate_should_not_patch",
            "collaboration_should_not_direct_call", "conflict_suggestion_should_not_decide", "handoff_aggregation_should_not_merge",
            "iteration_candidate_should_not_apply", "evolution_candidate_should_not_execute", "hard_boundaries_preserved",
        )):
            raise ValueError("Adaptive execution-first policy cannot weaken phase7 hard-boundary invariants")
        ensure_ref_text(self.summary_ref, "AdaptiveExecutionFirstPolicy.summary_ref")
        ensure_schema_version(self.schema_version)

    @property
    def digest(self) -> str:
        return stable_digest(self)
