"""L6 plugin manifest declaration.

The manifest is a data-only contract surface. It has no executable entry point,
no module locator, no shell command, no provider locator, no credentials, no
file path, no database address, and no direct lower-layer handles.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ._common import (
    L6_COMMON_SCHEMA_VERSION,
    L6_SOURCE_LAYER,
    ensure_field_names_are_safe,
    ensure_no_live_or_sensitive_text,
    ensure_ref_items,
    ensure_ref_or_summary_items,
    ensure_ref_text,
    ensure_schema_version,
    stable_digest,
    stable_primitive,
)
from .event_contract import L6EventContract
from .failure import L6DegradationContract, L6FailureContract, L6HotSwitchReadinessContract, L6MigrationContract, L6RollbackContract
from .handoff import L6HandoffContract
from .invariants import L6InvariantRule, default_l6_invariant_rules
from .lifecycle import L6PluginLifecycleDeclaration, L6PluginLifecycleState, normalize_lifecycle_state
from .public_projection import L6PublicProjection
from .requirement import (
    L6AuditRequirement,
    L6BudgetRequirement,
    L6CapabilityRequirement,
    L6ContextRequirement,
    L6CredentialRequirement,
    L6ModelCapabilityRequirement,
    L6PermissionRequirement,
    L6ToolCapabilityRequirement,
)
from .state_projection import L6StateProjectionContract


def _ensure_tuple_of_type(items: tuple[Any, ...], expected_type: type[Any], field_name: str) -> None:
    if not isinstance(items, tuple):
        raise ValueError(f"{field_name} must be a tuple")
    for item in items:
        if not isinstance(item, expected_type):
            raise ValueError(f"{field_name} must contain {expected_type.__name__}")


@dataclass(frozen=True, slots=True)
class L6PluginManifest:
    plugin_id: str
    plugin_name: str
    plugin_version: str
    plugin_type: str = "common_foundation"
    plugin_group: str = "l6_public_plugin_foundation"
    source_layer: str = L6_SOURCE_LAYER
    lifecycle_state: L6PluginLifecycleState | str = L6PluginLifecycleState.DECLARED
    lifecycle_declaration: L6PluginLifecycleDeclaration = field(default_factory=L6PluginLifecycleDeclaration)
    l5_registry_ref: str = "l5:registry_ref_required"
    l5_host_binding_ref: str = "l5:host_binding_ref_required"
    l5_governance_binding_ref: str = "l5:governance_binding_ref_required"
    capability_declarations: tuple[L6CapabilityRequirement, ...] = field(default_factory=tuple)
    model_capability_requirements: tuple[L6ModelCapabilityRequirement, ...] = field(default_factory=tuple)
    tool_capability_requirements: tuple[L6ToolCapabilityRequirement, ...] = field(default_factory=tuple)
    permission_requirements: tuple[L6PermissionRequirement, ...] = field(default_factory=lambda: (L6PermissionRequirement(),))
    budget_requirements: tuple[L6BudgetRequirement, ...] = field(default_factory=lambda: (L6BudgetRequirement(),))
    audit_requirements: tuple[L6AuditRequirement, ...] = field(default_factory=lambda: (L6AuditRequirement(),))
    credential_requirements: tuple[L6CredentialRequirement, ...] = field(default_factory=tuple)
    context_requirements: tuple[L6ContextRequirement, ...] = field(default_factory=lambda: (L6ContextRequirement(),))
    state_projection_requirements: tuple[L6StateProjectionContract, ...] = field(default_factory=lambda: (L6StateProjectionContract(),))
    event_subscriptions: tuple[L6EventContract, ...] = field(default_factory=tuple)
    event_publications: tuple[L6EventContract, ...] = field(default_factory=tuple)
    input_contract_ref: str = "decl:l6_input_contract_ref"
    output_contract_ref: str = "decl:l6_output_contract_ref"
    public_projection_policy_ref: str = "policy:l6_public_projection_policy"
    handoff_contract_refs: tuple[str, ...] = field(default_factory=lambda: ("handoff:l6_default_handoff_contract",))
    handoff_contracts: tuple[L6HandoffContract, ...] = field(default_factory=tuple)
    failure_modes: tuple[L6FailureContract, ...] = field(default_factory=lambda: (L6FailureContract(),))
    degradation_policy: L6DegradationContract = field(default_factory=L6DegradationContract)
    rollback_policy: L6RollbackContract = field(default_factory=L6RollbackContract)
    migration_policy: L6MigrationContract = field(default_factory=L6MigrationContract)
    hotswitch_policy: L6HotSwitchReadinessContract = field(default_factory=L6HotSwitchReadinessContract)
    invariants: tuple[L6InvariantRule, ...] = field(default_factory=default_l6_invariant_rules)
    forbidden_imports: tuple[str, ...] = field(default_factory=lambda: ("forbid:provider_sdk_import", "forbid:dynamic_import", "forbid:parallel_runtime"))
    forbidden_network_targets: tuple[str, ...] = field(default_factory=lambda: ("forbid:raw_http", "forbid:provider_base_url", "forbid:external_endpoint"))
    tests_required: tuple[str, ...] = field(default_factory=lambda: ("test:l6_common_contract_tests", "test:l6_forbidden_scan", "test:l6_public_projection_leak_test"))
    evidence_refs: tuple[str, ...] = field(default_factory=tuple)
    responsibility_chain_ref: str = "responsibility:l6_manifest_responsibility_chain"
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.plugin_id, "L6PluginManifest.plugin_id")
        ensure_no_live_or_sensitive_text(self.plugin_name, "L6PluginManifest.plugin_name")
        ensure_ref_text(self.plugin_version, "L6PluginManifest.plugin_version")
        ensure_ref_text(self.plugin_type, "L6PluginManifest.plugin_type")
        ensure_ref_text(self.plugin_group, "L6PluginManifest.plugin_group")
        if self.source_layer != L6_SOURCE_LAYER:
            raise ValueError("L6PluginManifest.source_layer must be L6")
        object.__setattr__(self, "lifecycle_state", normalize_lifecycle_state(self.lifecycle_state))
        if not isinstance(self.lifecycle_declaration, L6PluginLifecycleDeclaration):
            raise ValueError("L6PluginManifest.lifecycle_declaration must be L6PluginLifecycleDeclaration")
        ensure_ref_text(self.l5_registry_ref, "L6PluginManifest.l5_registry_ref")
        ensure_ref_text(self.l5_host_binding_ref, "L6PluginManifest.l5_host_binding_ref")
        ensure_ref_text(self.l5_governance_binding_ref, "L6PluginManifest.l5_governance_binding_ref")
        _ensure_tuple_of_type(self.capability_declarations, L6CapabilityRequirement, "L6PluginManifest.capability_declarations")
        _ensure_tuple_of_type(self.model_capability_requirements, L6ModelCapabilityRequirement, "L6PluginManifest.model_capability_requirements")
        _ensure_tuple_of_type(self.tool_capability_requirements, L6ToolCapabilityRequirement, "L6PluginManifest.tool_capability_requirements")
        _ensure_tuple_of_type(self.permission_requirements, L6PermissionRequirement, "L6PluginManifest.permission_requirements")
        _ensure_tuple_of_type(self.budget_requirements, L6BudgetRequirement, "L6PluginManifest.budget_requirements")
        _ensure_tuple_of_type(self.audit_requirements, L6AuditRequirement, "L6PluginManifest.audit_requirements")
        _ensure_tuple_of_type(self.credential_requirements, L6CredentialRequirement, "L6PluginManifest.credential_requirements")
        _ensure_tuple_of_type(self.context_requirements, L6ContextRequirement, "L6PluginManifest.context_requirements")
        _ensure_tuple_of_type(self.state_projection_requirements, L6StateProjectionContract, "L6PluginManifest.state_projection_requirements")
        _ensure_tuple_of_type(self.event_subscriptions, L6EventContract, "L6PluginManifest.event_subscriptions")
        _ensure_tuple_of_type(self.event_publications, L6EventContract, "L6PluginManifest.event_publications")
        ensure_ref_text(self.input_contract_ref, "L6PluginManifest.input_contract_ref")
        ensure_ref_text(self.output_contract_ref, "L6PluginManifest.output_contract_ref")
        ensure_ref_text(self.public_projection_policy_ref, "L6PluginManifest.public_projection_policy_ref")
        ensure_ref_items(self.handoff_contract_refs, "L6PluginManifest.handoff_contract_refs", required=True)
        _ensure_tuple_of_type(self.handoff_contracts, L6HandoffContract, "L6PluginManifest.handoff_contracts")
        _ensure_tuple_of_type(self.failure_modes, L6FailureContract, "L6PluginManifest.failure_modes")
        if not isinstance(self.degradation_policy, L6DegradationContract):
            raise ValueError("L6PluginManifest.degradation_policy must be L6DegradationContract")
        if not isinstance(self.rollback_policy, L6RollbackContract):
            raise ValueError("L6PluginManifest.rollback_policy must be L6RollbackContract")
        if not isinstance(self.migration_policy, L6MigrationContract):
            raise ValueError("L6PluginManifest.migration_policy must be L6MigrationContract")
        if not isinstance(self.hotswitch_policy, L6HotSwitchReadinessContract):
            raise ValueError("L6PluginManifest.hotswitch_policy must be L6HotSwitchReadinessContract")
        _ensure_tuple_of_type(self.invariants, L6InvariantRule, "L6PluginManifest.invariants")
        ensure_ref_items(self.forbidden_imports, "L6PluginManifest.forbidden_imports", required=True)
        ensure_ref_items(self.forbidden_network_targets, "L6PluginManifest.forbidden_network_targets", required=True)
        ensure_ref_items(self.tests_required, "L6PluginManifest.tests_required", required=True)
        ensure_ref_items(self.evidence_refs, "L6PluginManifest.evidence_refs")
        ensure_ref_text(self.responsibility_chain_ref, "L6PluginManifest.responsibility_chain_ref")
        ensure_schema_version(self.schema_version)
        ensure_field_names_are_safe(self, "L6PluginManifest")

    @property
    def manifest_digest(self) -> str:
        return stable_digest(stable_primitive(self))


def public_projection_from_manifest(manifest: L6PluginManifest) -> L6PublicProjection:
    if not isinstance(manifest, L6PluginManifest):
        raise ValueError("public_projection_from_manifest requires L6PluginManifest")
    return L6PublicProjection(
        projection_ref=f"public:{manifest.plugin_id}_projection",
        plugin_ref=manifest.plugin_id,
        status_summary=f"{manifest.plugin_name}:{manifest.lifecycle_state.value}:requirement_only",
        risk_summary_refs=("summary:l6_manifest_risk_summary",),
        audit_summary_refs=("audit:l6_manifest_audit_summary",),
        readiness_summary_refs=("summary:l6_manifest_readiness_summary",),
        redacted_evidence_refs=manifest.evidence_refs,
        disclosure_policy_refs=(manifest.public_projection_policy_ref,),
    )
