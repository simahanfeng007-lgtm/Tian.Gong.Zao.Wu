"""L6 capability and governance requirement declarations.

Requirement objects are not permits, grants, allocations, credentials, context
leases, audit records, model selections, tool handles, or lower-layer actions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from ._common import (
    ALLOWED_PROVIDER_NEUTRAL_HINTS,
    L6_COMMON_SCHEMA_VERSION,
    ensure_bool,
    ensure_no_live_or_sensitive_text,
    ensure_ref_items,
    ensure_ref_text,
    ensure_schema_version,
    ensure_short_text,
    validate_provider_neutral_hints,
)


class L6CapabilityRequirementKind(str, Enum):
    GENERIC = "generic"
    MODEL = "model"
    TOOL = "tool"
    PERMISSION = "permission"
    BUDGET = "budget"
    AUDIT = "audit"
    CREDENTIAL = "credential"
    CONTEXT = "context"
    STATE_PROJECTION = "state_projection"


class L6ToolSideEffectGrade(str, Enum):
    NONE = "none"
    READ_ONLY = "read_only"
    PROPOSED_WRITE = "proposed_write"
    HUMAN_CONFIRMED_ACTION_REQUIRED = "human_confirmed_action_required"


@dataclass(frozen=True, slots=True)
class L6CapabilityRequirement:
    requirement_ref: str = "l6:capability_requirement"
    requirement_kind: L6CapabilityRequirementKind | str = L6CapabilityRequirementKind.GENERIC
    summary: str = "requirement_only"
    policy_refs: tuple[str, ...] = field(default_factory=lambda: ("policy:l6_requirement_only",))
    evidence_refs: tuple[str, ...] = field(default_factory=tuple)
    requirement_only: bool = True
    is_permit: bool = False
    is_authorization: bool = False
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.requirement_ref, "L6CapabilityRequirement.requirement_ref")
        object.__setattr__(self, "requirement_kind", L6CapabilityRequirementKind(self.requirement_kind))
        ensure_no_live_or_sensitive_text(self.summary, "L6CapabilityRequirement.summary")
        ensure_ref_items(self.policy_refs, "L6CapabilityRequirement.policy_refs", required=True)
        ensure_ref_items(self.evidence_refs, "L6CapabilityRequirement.evidence_refs")
        if not self.requirement_only or self.is_permit or self.is_authorization:
            raise ValueError("L6 capability requirement cannot become permit or authorization")
        ensure_schema_version(self.schema_version)


@dataclass(frozen=True, slots=True)
class L6ModelCapabilityRequirement:
    requirement_ref: str = "model-cap:l6_model_requirement"
    reasoning: bool = False
    structured_output: bool = False
    tool_calling: bool = False
    streaming: bool = False
    multimodal: bool = False
    long_context: bool = False
    code_ability: bool = False
    function_call: bool = False
    json_schema: bool = False
    safety_refusal_envelope: bool = True
    provider_neutral_hints: tuple[str, ...] = field(default_factory=tuple)
    budget_refs: tuple[str, ...] = field(default_factory=lambda: ("budget:l6_model_requirement_budget_ref",))
    credential_policy_refs: tuple[str, ...] = field(default_factory=lambda: ("credential-policy:l6_model_requirement_policy_ref",))
    audit_envelope_required: bool = True
    provider_selection_allowed: bool = False
    contains_live_provider_locator: bool = False
    contains_sdk_import: bool = False
    direct_l4_adapter_access: bool = False
    raw_http_allowed: bool = False
    requirement_only: bool = True
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.requirement_ref, "L6ModelCapabilityRequirement.requirement_ref")
        for name in (
            "reasoning", "structured_output", "tool_calling", "streaming", "multimodal", "long_context",
            "code_ability", "function_call", "json_schema", "safety_refusal_envelope", "audit_envelope_required",
            "provider_selection_allowed", "contains_live_provider_locator", "contains_sdk_import", "direct_l4_adapter_access",
            "raw_http_allowed", "requirement_only",
        ):
            ensure_bool(getattr(self, name), f"L6ModelCapabilityRequirement.{name}")
        validate_provider_neutral_hints(self.provider_neutral_hints)
        ensure_ref_items(self.budget_refs, "L6ModelCapabilityRequirement.budget_refs", required=True)
        ensure_ref_items(self.credential_policy_refs, "L6ModelCapabilityRequirement.credential_policy_refs", required=True)
        if not self.audit_envelope_required:
            raise ValueError("L6 model capability requirement must require audit envelope")
        if self.provider_selection_allowed or self.contains_live_provider_locator or self.contains_sdk_import or self.direct_l4_adapter_access or self.raw_http_allowed:
            raise ValueError("L6 model capability requirement cannot select provider, import SDK, store locator, use raw HTTP, or touch L4 adapter")
        if not self.requirement_only:
            raise ValueError("L6 model capability requirement must remain requirement-only")
        ensure_schema_version(self.schema_version)


@dataclass(frozen=True, slots=True)
class L6ToolCapabilityRequirement:
    requirement_ref: str = "tool-cap:l6_tool_requirement"
    tool_intent_ref: str = "tool-cap:intent_ref_only"
    tool_category_ref: str = "tool-cap:category_ref_only"
    input_contract_ref: str = "decl:l6_tool_input_contract"
    output_contract_ref: str = "decl:l6_tool_output_contract"
    side_effect_grade: L6ToolSideEffectGrade | str = L6ToolSideEffectGrade.NONE
    permission_requirement_refs: tuple[str, ...] = field(default_factory=lambda: ("permission:l6_tool_permission_requirement",))
    budget_requirement_refs: tuple[str, ...] = field(default_factory=lambda: ("budget:l6_tool_budget_requirement",))
    audit_requirement_refs: tuple[str, ...] = field(default_factory=lambda: ("audit:l6_tool_audit_requirement",))
    credential_requirement_refs: tuple[str, ...] = field(default_factory=tuple)
    sandbox_requirement_refs: tuple[str, ...] = field(default_factory=lambda: ("policy:l6_tool_sandbox_requirement",))
    rollback_requirement_refs: tuple[str, ...] = field(default_factory=tuple)
    human_confirmation_refs: tuple[str, ...] = field(default_factory=tuple)
    stores_tool_handle: bool = False
    releases_raw_tool_schema: bool = False
    invokes_tool: bool = False
    direct_shell_allowed: bool = False
    direct_file_access_allowed: bool = False
    direct_network_access_allowed: bool = False
    direct_database_access_allowed: bool = False
    requirement_only: bool = True
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.requirement_ref, "L6ToolCapabilityRequirement.requirement_ref")
        ensure_ref_text(self.tool_intent_ref, "L6ToolCapabilityRequirement.tool_intent_ref")
        ensure_ref_text(self.tool_category_ref, "L6ToolCapabilityRequirement.tool_category_ref")
        ensure_ref_text(self.input_contract_ref, "L6ToolCapabilityRequirement.input_contract_ref")
        ensure_ref_text(self.output_contract_ref, "L6ToolCapabilityRequirement.output_contract_ref")
        object.__setattr__(self, "side_effect_grade", L6ToolSideEffectGrade(self.side_effect_grade))
        for field_name in (
            "permission_requirement_refs", "budget_requirement_refs", "audit_requirement_refs", "credential_requirement_refs",
            "sandbox_requirement_refs", "rollback_requirement_refs", "human_confirmation_refs",
        ):
            ensure_ref_items(getattr(self, field_name), f"L6ToolCapabilityRequirement.{field_name}")
        if not self.permission_requirement_refs or not self.budget_requirement_refs or not self.audit_requirement_refs or not self.sandbox_requirement_refs:
            raise ValueError("L6 tool capability requirement must declare permission, budget, audit, and sandbox requirement refs")
        if any((self.stores_tool_handle, self.releases_raw_tool_schema, self.invokes_tool, self.direct_shell_allowed, self.direct_file_access_allowed, self.direct_network_access_allowed, self.direct_database_access_allowed)):
            raise ValueError("L6 tool capability requirement cannot hold handles, release raw schemas, or perform direct actions")
        if not self.requirement_only:
            raise ValueError("L6 tool capability requirement must remain requirement-only")
        ensure_schema_version(self.schema_version)


@dataclass(frozen=True, slots=True)
class L6PermissionRequirement:
    requirement_ref: str = "permission:l6_permission_requirement"
    permission_scope_refs: tuple[str, ...] = field(default_factory=lambda: ("policy:l6_permission_scope",))
    human_gate_refs: tuple[str, ...] = field(default_factory=tuple)
    policy_refs: tuple[str, ...] = field(default_factory=lambda: ("policy:l6_permission_not_grant",))
    requirement_only: bool = True
    grants_permission: bool = False
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.requirement_ref, "L6PermissionRequirement.requirement_ref")
        ensure_ref_items(self.permission_scope_refs, "L6PermissionRequirement.permission_scope_refs", required=True)
        ensure_ref_items(self.human_gate_refs, "L6PermissionRequirement.human_gate_refs")
        ensure_ref_items(self.policy_refs, "L6PermissionRequirement.policy_refs", required=True)
        if not self.requirement_only or self.grants_permission:
            raise ValueError("L6 permission requirement cannot grant permission")
        ensure_schema_version(self.schema_version)


@dataclass(frozen=True, slots=True)
class L6BudgetRequirement:
    requirement_ref: str = "budget:l6_budget_requirement"
    budget_scope_refs: tuple[str, ...] = field(default_factory=lambda: ("budget:l6_scope_ref",))
    quota_policy_refs: tuple[str, ...] = field(default_factory=lambda: ("policy:l6_quota_policy_ref",))
    cost_summary_refs: tuple[str, ...] = field(default_factory=tuple)
    requirement_only: bool = True
    allocates_budget: bool = False
    decrements_budget: bool = False
    bypasses_budget: bool = False
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.requirement_ref, "L6BudgetRequirement.requirement_ref")
        ensure_ref_items(self.budget_scope_refs, "L6BudgetRequirement.budget_scope_refs", required=True)
        ensure_ref_items(self.quota_policy_refs, "L6BudgetRequirement.quota_policy_refs", required=True)
        ensure_ref_items(self.cost_summary_refs, "L6BudgetRequirement.cost_summary_refs")
        if not self.requirement_only or self.allocates_budget or self.decrements_budget or self.bypasses_budget:
            raise ValueError("L6 budget requirement cannot allocate, decrement, or bypass budget")
        ensure_schema_version(self.schema_version)


@dataclass(frozen=True, slots=True)
class L6AuditRequirement:
    requirement_ref: str = "audit:l6_audit_requirement"
    audit_envelope_ref: str = "audit:l6_audit_envelope_required"
    evidence_required_refs: tuple[str, ...] = field(default_factory=lambda: ("evidence:l6_required_evidence_ref",))
    responsibility_chain_ref: str = "responsibility:l6_responsibility_chain_required"
    requirement_only: bool = True
    writes_audit_record: bool = False
    stores_evidence_blob: bool = False
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.requirement_ref, "L6AuditRequirement.requirement_ref")
        ensure_ref_text(self.audit_envelope_ref, "L6AuditRequirement.audit_envelope_ref")
        ensure_ref_items(self.evidence_required_refs, "L6AuditRequirement.evidence_required_refs", required=True)
        ensure_ref_text(self.responsibility_chain_ref, "L6AuditRequirement.responsibility_chain_ref")
        if not self.requirement_only or self.writes_audit_record or self.stores_evidence_blob:
            raise ValueError("L6 audit requirement cannot write audit record or store evidence blob")
        ensure_schema_version(self.schema_version)


@dataclass(frozen=True, slots=True)
class L6CredentialRequirement:
    requirement_ref: str = "credential-policy:l6_credential_requirement"
    credential_policy_refs: tuple[str, ...] = field(default_factory=lambda: ("credential-policy:l6_policy_ref_only",))
    redaction_policy_refs: tuple[str, ...] = field(default_factory=lambda: ("policy:l6_credential_redaction_required",))
    requirement_only: bool = True
    reads_credential: bool = False
    stores_credential: bool = False
    refreshes_credential: bool = False
    decrypts_credential: bool = False
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.requirement_ref, "L6CredentialRequirement.requirement_ref")
        ensure_ref_items(self.credential_policy_refs, "L6CredentialRequirement.credential_policy_refs", required=True)
        ensure_ref_items(self.redaction_policy_refs, "L6CredentialRequirement.redaction_policy_refs", required=True)
        if not self.requirement_only or self.reads_credential or self.stores_credential or self.refreshes_credential or self.decrypts_credential:
            raise ValueError("L6 credential requirement cannot read, store, refresh, or decrypt credentials")
        ensure_schema_version(self.schema_version)


@dataclass(frozen=True, slots=True)
class L6ContextRequirement:
    requirement_ref: str = "context:l6_context_requirement"
    context_projection_refs: tuple[str, ...] = field(default_factory=lambda: ("context:l6_minimized_projection_ref",))
    minimization_policy_refs: tuple[str, ...] = field(default_factory=lambda: ("policy:l6_context_minimization",))
    retention_policy_refs: tuple[str, ...] = field(default_factory=lambda: ("policy:l6_context_no_raw_retention",))
    requirement_only: bool = True
    reads_full_context: bool = False
    stores_raw_context: bool = False
    treats_context_as_instruction: bool = False
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.requirement_ref, "L6ContextRequirement.requirement_ref")
        ensure_ref_items(self.context_projection_refs, "L6ContextRequirement.context_projection_refs", required=True)
        ensure_ref_items(self.minimization_policy_refs, "L6ContextRequirement.minimization_policy_refs", required=True)
        ensure_ref_items(self.retention_policy_refs, "L6ContextRequirement.retention_policy_refs", required=True)
        if not self.requirement_only or self.reads_full_context or self.stores_raw_context or self.treats_context_as_instruction:
            raise ValueError("L6 context requirement cannot read full context, store raw context, or treat context as instruction")
        ensure_schema_version(self.schema_version)


__all__ = (
    "ALLOWED_PROVIDER_NEUTRAL_HINTS",
    "L6CapabilityRequirementKind",
    "L6ToolSideEffectGrade",
    "L6CapabilityRequirement",
    "L6ModelCapabilityRequirement",
    "L6ToolCapabilityRequirement",
    "L6PermissionRequirement",
    "L6BudgetRequirement",
    "L6AuditRequirement",
    "L6CredentialRequirement",
    "L6ContextRequirement",
)
