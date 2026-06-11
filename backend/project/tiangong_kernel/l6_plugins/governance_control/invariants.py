"""L6 phase5 governance-control invariant declarations."""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l6_plugins.common._common import L6_COMMON_SCHEMA_VERSION, ensure_bool, ensure_ref_items, ensure_ref_text, ensure_schema_version, stable_digest


L6_PHASE5_INVARIANTS: tuple[str, ...] = (
    "governance_plugin_is_not_l5",
    "governance_requirement_is_not_permit",
    "risk_projection_is_not_decision",
    "permission_requirement_is_not_authorization",
    "budget_requirement_is_not_allocation",
    "audit_requirement_is_not_audit_write",
    "credential_requirement_ref_is_not_secret_access",
    "privacy_requirement_is_not_data_access",
    "human_gate_requirement_is_not_confirmation_ticket",
    "degradation_suggestion_is_not_command",
    "public_projection_safety_hint_is_not_redaction_execution",
    "long_chain_checkpoint_hint_is_not_scheduler_state",
    "execution_first_does_not_bypass_hard_boundaries",
    "risk_score_does_not_block_by_default",
    "low_risk_should_continue",
    "reversible_candidate_should_continue",
    "governance_should_summarize_not_interrupt",
    "long_chain_should_degrade_not_abort",
    "confirmation_should_batch_when_safe",
    "no_live_model_call",
    "no_raw_tool_call",
    "no_direct_l4_adapter_call",
    "no_direct_l2_write",
    "no_direct_memory_write",
    "no_direct_memory_delete",
    "no_direct_audit_write",
    "no_direct_budget_charge",
    "no_raw_secret",
    "no_provider_base_url_or_api_key",
    "no_plugin_direct_import_call_state_write",
    "no_parallel_runtime",
    "no_old_runtime_or_abilitypackage_backflow",
    "public_projection_minimal_disclosure",
)


@dataclass(frozen=True)
class L6Phase5InvariantSuite:
    suite_ref: str = "invariant:l6_phase5_suite"
    invariant_refs: tuple[str, ...] = field(default_factory=lambda: tuple(f"invariant:{name}" for name in L6_PHASE5_INVARIANTS))
    all_required: bool = True
    execution_first_within_hard_boundaries: bool = True
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.suite_ref, "L6Phase5InvariantSuite.suite_ref")
        ensure_ref_items(self.invariant_refs, "L6Phase5InvariantSuite.invariant_refs", required=True)
        ensure_bool(self.all_required, "L6Phase5InvariantSuite.all_required")
        ensure_bool(self.execution_first_within_hard_boundaries, "L6Phase5InvariantSuite.execution_first_within_hard_boundaries")
        if not self.all_required or not self.execution_first_within_hard_boundaries:
            raise ValueError("L6 phase5 invariant suite is mandatory and execution-first")
        ensure_schema_version(self.schema_version)

    @property
    def digest(self) -> str:
        return stable_digest(self)
