"""L5 phase 1 invariant data shells."""

from __future__ import annotations

from dataclasses import dataclass, field

from ._common import L5_PLUGIN_HOST_SCHEMA_VERSION, ensure_ref_items, ensure_ref_text, ensure_schema_version, ensure_short_text, ensure_text_items


@dataclass(frozen=True, slots=True)
class L5Phase1InvariantSuite:
    suite_ref: str
    required_invariants: tuple[str, ...] = field(default_factory=lambda: (
        "manifest_view_is_data_only",
        "registry_snapshot_is_immutable",
        "handoff_index_refs_only",
        "no_dynamic_code_loading",
        "no_live_external_action",
        "no_lower_layer_mutation",
        "no_l6_business_logic",
        "no_legacy_main_chain",
        "audit_evidence_refs_only",
    ))
    evidence_refs: tuple[str, ...] = field(default_factory=tuple)
    summary: str = ""
    schema_version: str = L5_PLUGIN_HOST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.suite_ref, "L5Phase1InvariantSuite.suite_ref")
        ensure_text_items(self.required_invariants, "L5Phase1InvariantSuite.required_invariants", limit=128)
        ensure_ref_items(self.evidence_refs, "L5Phase1InvariantSuite.evidence_refs")
        ensure_short_text(self.summary, "L5Phase1InvariantSuite.summary")
        ensure_schema_version(self.schema_version, "L5Phase1InvariantSuite.schema_version")


@dataclass(frozen=True, slots=True)
class L5Phase2InvariantSuite:
    suite_ref: str
    required_invariants: tuple[str, ...] = field(default_factory=lambda: (
        "manifest_schema_required_fields_complete",
        "manifest_hash_is_canonical_and_self_excluding",
        "entry_reference_is_non_executable",
        "package_descriptor_is_non_file_scanning",
        "permission_resource_credential_data_audit_version_rollback_compatibility_are_declarative",
        "capability_token_is_declarative",
        "trust_boundary_is_declarative",
        "no_dynamic_code_loading",
        "no_live_external_action",
        "no_l6_business_logic",
        "no_legacy_main_chain",
    ))
    evidence_refs: tuple[str, ...] = field(default_factory=tuple)
    summary: str = ""
    schema_version: str = L5_PLUGIN_HOST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.suite_ref, "L5Phase2InvariantSuite.suite_ref")
        ensure_text_items(self.required_invariants, "L5Phase2InvariantSuite.required_invariants", limit=128)
        ensure_ref_items(self.evidence_refs, "L5Phase2InvariantSuite.evidence_refs")
        ensure_short_text(self.summary, "L5Phase2InvariantSuite.summary")
        ensure_schema_version(self.schema_version, "L5Phase2InvariantSuite.schema_version")


@dataclass(frozen=True, slots=True)
class L5Phase3InvariantSuite:
    suite_ref: str
    required_invariants: tuple[str, ...] = field(default_factory=lambda: (
        "registry_is_declaration_view_only",
        "registry_validator_is_pure_reporter",
        "snapshot_digest_is_canonical",
        "delta_is_difference_only_not_patch",
        "audit_index_refs_only",
        "public_projection_minimal_disclosure",
        "inert_forbidden_patterns_do_not_execute",
        "migration_hot_switch_replay_breaking_change_are_refs_only",
        "no_dynamic_code_loading",
        "no_live_external_action",
        "no_l6_business_logic",
        "no_legacy_main_chain",
    ))
    evidence_refs: tuple[str, ...] = field(default_factory=tuple)
    summary: str = ""
    schema_version: str = L5_PLUGIN_HOST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.suite_ref, "L5Phase3InvariantSuite.suite_ref")
        ensure_text_items(self.required_invariants, "L5Phase3InvariantSuite.required_invariants", limit=128)
        ensure_ref_items(self.evidence_refs, "L5Phase3InvariantSuite.evidence_refs")
        ensure_short_text(self.summary, "L5Phase3InvariantSuite.summary")
        ensure_schema_version(self.schema_version, "L5Phase3InvariantSuite.schema_version")


@dataclass(frozen=True, slots=True)
class L5Phase4InvariantSuite:
    suite_ref: str
    required_invariants: tuple[str, ...] = field(default_factory=lambda: (
        "lifecycle_state_machine_is_declaration_only",
        "lifecycle_transition_rules_have_no_execution_methods",
        "mount_declarations_have_no_live_entry",
        "validators_are_pure_reporters",
        "public_projection_minimal_disclosure",
        "audit_chain_refs_are_structured",
        "switch_migration_replay_refs_are_declarative",
        "self_healing_chain_is_declarative",
        "no_dynamic_code_loading",
        "no_live_external_action",
        "no_l6_business_logic",
        "no_legacy_main_chain",
    ))
    evidence_refs: tuple[str, ...] = field(default_factory=tuple)
    summary: str = ""
    schema_version: str = L5_PLUGIN_HOST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.suite_ref, "L5Phase4InvariantSuite.suite_ref")
        ensure_text_items(self.required_invariants, "L5Phase4InvariantSuite.required_invariants", limit=128)
        ensure_ref_items(self.evidence_refs, "L5Phase4InvariantSuite.evidence_refs")
        ensure_short_text(self.summary, "L5Phase4InvariantSuite.summary")
        ensure_schema_version(self.schema_version, "L5Phase4InvariantSuite.schema_version")


@dataclass(frozen=True, slots=True)
class L5Phase6InvariantSuite:
    suite_ref: str
    required_invariants: tuple[str, ...] = field(default_factory=lambda: (
        "health_signals_are_declarative_no_live_probe",
        "health_checks_do_not_collect_metrics_or_logs",
        "isolation_disposition_is_declarative_no_state_mutation",
        "permission_preconditions_are_not_permits_leases_or_tickets",
        "public_projection_minimal_disclosure",
        "audit_event_refs_are_structured",
        "quality_gate_allow_enter_phase7_is_hard_derived",
        "no_dynamic_code_loading",
        "no_live_external_action",
        "no_l6_business_logic",
        "no_legacy_main_chain",
    ))
    evidence_refs: tuple[str, ...] = field(default_factory=tuple)
    summary: str = ""
    schema_version: str = L5_PLUGIN_HOST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.suite_ref, "L5Phase6InvariantSuite.suite_ref")
        ensure_text_items(self.required_invariants, "L5Phase6InvariantSuite.required_invariants", limit=128)
        ensure_ref_items(self.evidence_refs, "L5Phase6InvariantSuite.evidence_refs")
        ensure_short_text(self.summary, "L5Phase6InvariantSuite.summary")
        ensure_schema_version(self.schema_version, "L5Phase6InvariantSuite.schema_version")
