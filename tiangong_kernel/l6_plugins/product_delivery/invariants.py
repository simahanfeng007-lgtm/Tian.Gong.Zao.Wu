"""Invariant declarations for L6 phase6 product delivery."""

from __future__ import annotations

from dataclasses import dataclass, field

from .common import ProductArtifactBase, ensure_bool, ensure_ref_items

PHASE6_INVARIANTS: tuple[str, ...] = (
    "product_delivery_plugin_is_not_executor",
    "product_seed_is_not_product_spec",
    "product_plan_candidate_is_not_execution_plan",
    "artifact_structure_candidate_is_not_file_tree",
    "delivery_package_candidate_is_not_zip",
    "product_quality_gate_candidate_is_not_passed_result",
    "product_dispatch_intent_is_not_execution",
    "file_write_requirement_is_not_file_write",
    "package_build_requirement_is_not_zip_creation",
    "test_run_requirement_is_not_test_execution",
    "tool_capability_requirement_is_not_tool_call",
    "model_capability_requirement_is_not_model_call",
    "governance_review_required_before_dispatch",
    "no_live_model_call",
    "no_raw_tool_call",
    "no_direct_l4_adapter_call",
    "no_direct_file_write",
    "no_direct_zip_creation",
    "no_direct_test_execution",
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
    "product_delivery_should_continue_when_low_risk",
    "product_generation_should_minimize_clarification",
    "product_long_chain_should_checkpoint",
    "product_failure_should_recover_not_abort",
    "product_result_must_not_be_faked",
)


@dataclass(frozen=True)
class L6Phase6InvariantSuite(ProductArtifactBase):
    object_ref: str = "invariant:l6_phase6_product_delivery_suite"
    invariant_refs: tuple[str, ...] = field(default_factory=lambda: tuple(f"invariant:l6_phase6_{name}" for name in PHASE6_INVARIANTS))
    all_required: bool = True
    schema_checked: bool = True

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_items(self.invariant_refs, "L6Phase6InvariantSuite.invariant_refs", required=True)
        ensure_bool(self.all_required, "L6Phase6InvariantSuite.all_required")
        ensure_bool(self.schema_checked, "L6Phase6InvariantSuite.schema_checked")
        if not self.all_required or not self.schema_checked:
            raise ValueError("All phase6 invariants must be required and schema checked")
