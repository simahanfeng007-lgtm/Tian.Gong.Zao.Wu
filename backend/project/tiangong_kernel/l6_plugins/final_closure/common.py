"""L6 phase8 final-closure declarations.

The final-closure package is an inert total收口 layer. It inventories L6 phase1-7,
expresses cross-phase compatibility, planner review readiness, public projection
coverage, evidence coverage, and L7 handoff readiness. It does not add business
plugin capability, execute tests as plugin behavior, call models/tools, write lower
layer state, mutate memory, write audit stores, charge budgets, read credentials,
or claim final freeze before planner review plus total repair.
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

L6_PHASE8 = "L6_PHASE8_FINAL_CLOSURE"
L6_CANDIDATE_FREEZE_ONLY = "candidate_freeze_requires_planner_review_and_total_repair"


class FinalClosurePluginKind(str, Enum):
    STAGE_INVENTORY = "stage_inventory"
    CROSS_PHASE_COMPATIBILITY = "cross_phase_compatibility"
    UNIFIED_QUALITY_GATE = "unified_quality_gate"
    UNIFIED_FORBIDDEN_SCAN = "unified_forbidden_scan"
    UNIFIED_REGRESSION = "unified_regression"
    PUBLIC_PROJECTION_INDEX = "public_projection_index"
    AUDIT_EVIDENCE_CHAIN = "audit_evidence_chain"
    EXECUTION_FIRST_REVIEW = "execution_first_review"
    PLANNER_REVIEW_PACKAGE = "planner_review_package"
    FINAL_HANDOFF = "final_handoff"
    FREEZE_CANDIDATE_PACKAGE = "freeze_candidate_package"
    L7_READINESS = "l7_readiness"


class PlannerRole(str, Enum):
    L3_ORCHESTRATION = "l3_orchestration"
    L5_PLUGIN_GOVERNANCE = "l5_plugin_governance"
    SECURITY_PERMISSION = "security_permission"
    DATA_PRIVACY_CREDENTIAL = "data_privacy_credential"
    AUDIT_EVIDENCE = "audit_evidence"
    BUDGET_RATE_LIMIT = "budget_rate_limit"
    TEST_REGRESSION = "test_regression"
    MATH_MODEL = "math_model"
    CONTEXT_BELIEF_WORLD = "context_belief_world"
    MEMORY_FORGETTING = "memory_forgetting"
    AFFECTIVE_SYSTEM = "affective_system"
    SELF_LEARNING_ITERATION = "self_learning_iteration"
    SELF_HEALING = "self_healing"
    PRODUCT_DELIVERY = "product_delivery"
    PLUGIN_SYSTEM = "plugin_system"
    HANDOFF_MULTI_AGENT = "handoff_multi_agent"
    L4_SANDBOX_ADAPTER = "l4_sandbox_adapter"
    MODEL_ADAPTATION_GOVERNANCE = "model_adaptation_governance"


class FinalClosureRedactionState(str, Enum):
    APPLIED_SUMMARY_ONLY = "applied_summary_only"
    REQUIRED = "required"
    BLOCKED_PUBLIC_DETAIL = "blocked_public_detail"


class FinalClosurePrivacyClass(str, Enum):
    PUBLIC_SUMMARY = "public_summary"
    INTERNAL_REF_ONLY = "internal_ref_only"
    SENSITIVE_SUMMARY_ONLY = "sensitive_summary_only"
    BLOCKED_FROM_PUBLIC = "blocked_from_public"


def ensure_non_negative_int(value: int, field_name: str) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError(f"{field_name} must be non-negative integer")


@dataclass(frozen=True)
class FinalClosureArtifactBase:
    object_ref: str = "l6:phase8_final_closure_artifact"
    phase_refs: tuple[str, ...] = field(default_factory=lambda: tuple(f"l6:phase{i}" for i in range(1, 8)))
    source_refs: tuple[str, ...] = field(default_factory=lambda: ("summary:l6_phase7_candidate_freeze",))
    artifact_refs: tuple[str, ...] = field(default_factory=lambda: ("summary:l6_phase8_artifact_index",))
    plugin_group_refs: tuple[str, ...] = field(default_factory=lambda: (
        "l6:common", "l6:mind", "l6:cognitive_continuity", "l6:governance_control",
        "l6:product_delivery", "l6:adaptive_collaboration", "l6:final_closure",
    ))
    test_refs: tuple[str, ...] = field(default_factory=lambda: ("test:l6_phase8_regression_matrix",))
    report_refs: tuple[str, ...] = field(default_factory=lambda: ("report:l6_phase8_final_validation",))
    quality_gate_refs: tuple[str, ...] = field(default_factory=lambda: ("quality:l6_unified_quality_gate",))
    risk_refs: tuple[str, ...] = field(default_factory=lambda: ("report:l6_phase8_risk_index",))
    evidence_refs: tuple[str, ...] = field(default_factory=lambda: ("evidence:l6_phase8_evidence_index",))
    trace_ref: str = "ref:l6_phase8_trace"
    responsibility_chain_ref: str = "responsibility:l6_phase8_chain"
    tamper_evidence_ref: str = "evidence:l6_phase8_tamper"
    redaction_state: FinalClosureRedactionState | str = FinalClosureRedactionState.APPLIED_SUMMARY_ONLY
    privacy_class: FinalClosurePrivacyClass | str = FinalClosurePrivacyClass.INTERNAL_REF_ONLY
    public_summary: str = "summary:l6_phase8_candidate_freeze_public_summary"
    created_for_phase: str = L6_PHASE8
    freeze_candidate_flag: bool = True
    planner_review_required: bool = True
    total_repair_required_after_planner_review: bool = True
    final_freeze_claimed: bool = False
    business_capability_added: bool = False
    model_called: bool = False
    tool_called: bool = False
    l4_adapter_called: bool = False
    file_written_as_plugin_action: bool = False
    zip_created_as_plugin_action: bool = False
    test_executed_as_plugin_action: bool = False
    l2_written: bool = False
    memory_written: bool = False
    memory_deleted: bool = False
    audit_written: bool = False
    budget_charged: bool = False
    credential_accessed: bool = False
    direct_plugin_link: bool = False
    parallel_runtime_created: bool = False
    old_runtime_backflow: bool = False
    result_faked: bool = False
    blocking_reasons: tuple[str, ...] = field(default_factory=tuple)
    next_action_hint: str = "hint:l6_phase8_enter_planner_review"
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.object_ref, f"{self.__class__.__name__}.object_ref")
        for field_name in (
            "phase_refs", "source_refs", "artifact_refs", "plugin_group_refs", "test_refs", "report_refs",
            "quality_gate_refs", "risk_refs", "evidence_refs", "blocking_reasons",
        ):
            ensure_ref_items(getattr(self, field_name), f"{self.__class__.__name__}.{field_name}", required=field_name not in ("blocking_reasons",))
        for field_name in ("trace_ref", "responsibility_chain_ref", "tamper_evidence_ref", "next_action_hint"):
            ensure_ref_text(getattr(self, field_name), f"{self.__class__.__name__}.{field_name}")
        object.__setattr__(self, "redaction_state", FinalClosureRedactionState(self.redaction_state))
        object.__setattr__(self, "privacy_class", FinalClosurePrivacyClass(self.privacy_class))
        ensure_no_live_or_sensitive_text(self.public_summary, f"{self.__class__.__name__}.public_summary")
        if self.created_for_phase != L6_PHASE8:
            raise ValueError("Final closure objects must be created for L6 phase8")
        for field_name in (
            "freeze_candidate_flag", "planner_review_required", "total_repair_required_after_planner_review",
            "final_freeze_claimed", "business_capability_added", "model_called", "tool_called", "l4_adapter_called",
            "file_written_as_plugin_action", "zip_created_as_plugin_action", "test_executed_as_plugin_action",
            "l2_written", "memory_written", "memory_deleted", "audit_written", "budget_charged",
            "credential_accessed", "direct_plugin_link", "parallel_runtime_created", "old_runtime_backflow", "result_faked",
        ):
            ensure_bool(getattr(self, field_name), f"{self.__class__.__name__}.{field_name}")
        forbidden_flags = (
            self.final_freeze_claimed, self.business_capability_added, self.model_called, self.tool_called,
            self.l4_adapter_called, self.file_written_as_plugin_action, self.zip_created_as_plugin_action,
            self.test_executed_as_plugin_action, self.l2_written, self.memory_written, self.memory_deleted,
            self.audit_written, self.budget_charged, self.credential_accessed, self.direct_plugin_link,
            self.parallel_runtime_created, self.old_runtime_backflow, self.result_faked,
        )
        if any(forbidden_flags):
            raise ValueError("L6 phase8 final closure must remain inert and candidate-freeze only")
        if not (self.freeze_candidate_flag and self.planner_review_required and self.total_repair_required_after_planner_review):
            raise ValueError("L6 phase8 may only create candidate freeze and must require planner review plus total repair")
        ensure_schema_version(self.schema_version)

    @property
    def digest(self) -> str:
        return stable_digest(self)


@dataclass(frozen=True)
class FinalClosurePluginDeclaration:
    plugin_ref: str
    plugin_kind: FinalClosurePluginKind | str
    summary: str
    output_refs: tuple[str, ...] = field(default_factory=lambda: ("report:l6_phase8_summary", "quality:l6_unified_quality_gate"))
    is_executor: bool = False
    adds_business_capability: bool = False
    calls_model: bool = False
    calls_tool: bool = False
    calls_l4_adapter: bool = False
    writes_file_as_plugin_action: bool = False
    creates_zip_as_plugin_action: bool = False
    executes_tests_as_plugin_action: bool = False
    writes_l2: bool = False
    writes_memory: bool = False
    deletes_memory: bool = False
    writes_audit_store: bool = False
    charges_budget: bool = False
    accesses_credentials: bool = False
    direct_plugin_link: bool = False
    creates_parallel_runtime: bool = False
    claims_final_freeze: bool = False
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.plugin_ref, "FinalClosurePluginDeclaration.plugin_ref")
        object.__setattr__(self, "plugin_kind", FinalClosurePluginKind(self.plugin_kind))
        ensure_no_live_or_sensitive_text(self.summary, "FinalClosurePluginDeclaration.summary")
        ensure_ref_items(self.output_refs, "FinalClosurePluginDeclaration.output_refs", required=True)
        for field_name in (
            "is_executor", "adds_business_capability", "calls_model", "calls_tool", "calls_l4_adapter",
            "writes_file_as_plugin_action", "creates_zip_as_plugin_action", "executes_tests_as_plugin_action",
            "writes_l2", "writes_memory", "deletes_memory", "writes_audit_store", "charges_budget",
            "accesses_credentials", "direct_plugin_link", "creates_parallel_runtime", "claims_final_freeze",
        ):
            ensure_bool(getattr(self, field_name), f"FinalClosurePluginDeclaration.{field_name}")
        if any(getattr(self, name) for name in (
            "is_executor", "adds_business_capability", "calls_model", "calls_tool", "calls_l4_adapter",
            "writes_file_as_plugin_action", "creates_zip_as_plugin_action", "executes_tests_as_plugin_action",
            "writes_l2", "writes_memory", "deletes_memory", "writes_audit_store", "charges_budget",
            "accesses_credentials", "direct_plugin_link", "creates_parallel_runtime", "claims_final_freeze",
        )):
            raise ValueError("final_closure plugins are inert reporting/indexing contracts only")
        ensure_schema_version(self.schema_version)

    @property
    def l6_plugin_is_not_executor(self) -> bool:
        return not self.is_executor and not self.adds_business_capability

    @property
    def digest(self) -> str:
        return stable_digest(self)


@dataclass(frozen=True)
class L6ExecutionFirstClosurePolicy:
    policy_ref: str = "policy:l6_phase8_execution_first_closure"
    execution_first_does_not_bypass_hard_boundaries: bool = True
    low_risk_should_continue: bool = True
    reversible_candidate_should_continue: bool = True
    governance_should_summarize_not_interrupt: bool = True
    long_chain_should_degrade_not_abort: bool = True
    confirmation_should_batch_when_safe: bool = True
    product_delivery_should_continue_when_low_risk: bool = True
    adaptive_failure_should_recover_not_abort: bool = True
    summary_ref: str = "summary:l6_phase8_execution_first_review"
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.policy_ref, "L6ExecutionFirstClosurePolicy.policy_ref")
        for field_name in (
            "execution_first_does_not_bypass_hard_boundaries", "low_risk_should_continue",
            "reversible_candidate_should_continue", "governance_should_summarize_not_interrupt",
            "long_chain_should_degrade_not_abort", "confirmation_should_batch_when_safe",
            "product_delivery_should_continue_when_low_risk", "adaptive_failure_should_recover_not_abort",
        ):
            ensure_bool(getattr(self, field_name), f"L6ExecutionFirstClosurePolicy.{field_name}")
        if not all(getattr(self, field_name) for field_name in (
            "execution_first_does_not_bypass_hard_boundaries", "low_risk_should_continue",
            "reversible_candidate_should_continue", "governance_should_summarize_not_interrupt",
            "long_chain_should_degrade_not_abort", "confirmation_should_batch_when_safe",
            "product_delivery_should_continue_when_low_risk", "adaptive_failure_should_recover_not_abort",
        )):
            raise ValueError("ExecutionFirstWithinHardBoundaries must survive L6 closure")
        ensure_ref_text(self.summary_ref, "L6ExecutionFirstClosurePolicy.summary_ref")
        ensure_schema_version(self.schema_version)

    @property
    def digest(self) -> str:
        return stable_digest(self)
