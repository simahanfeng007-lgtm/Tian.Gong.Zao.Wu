"""L5 affective plugin host declarations.

This module is intentionally inert. It only models declaration references for
future L6 affective plugins. It does not implement emotion models, compute
seven-emotion/six-desire logic, execute tools, mutate memory, bypass policy,
call L4 adapters, or submit side effects.
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields
from re import compile as _compile
from typing import Any

from ._common import ensure_bool, ensure_ref_items, ensure_ref_text, stable_digest, stable_primitive

AFFECTIVE_PLUGIN_KIND_REF = "plugin_kind:AffectivePlugin"
AFFECTIVE_MOUNT_KIND_REF = "mount_kind:affective"
AFFECTIVE_CAPABILITY_KIND_REFS = (
    "AffectiveModulationCapability",
    "AffectiveExpressionStyleCapability",
    "AffectiveAttentionBiasCapability",
    "AffectiveMemoryWeightCapability",
    "AffectiveRiskSensitivityCapability",
    "AffectiveLearningMotivationCapability",
)
AFFECTIVE_ALLOWED_MODULATION_REFS = (
    "affective_modulation:expression_style",
    "affective_modulation:attention_bias",
    "affective_modulation:priority_bias",
    "affective_modulation:memory_weight_bias",
    "affective_modulation:risk_sensitivity_bias",
    "affective_modulation:learning_motivation_bias",
)
AFFECTIVE_FORBIDDEN_MISUSE_REFS = (
    "forbid:affective_state_as_authorization",
    "forbid:affective_state_as_permit",
    "forbid:affective_state_as_lease",
    "forbid:affective_state_as_confirmation_ticket",
    "forbid:affective_permission_bypass",
    "forbid:affective_policy_bypass",
    "forbid:affective_human_gate_bypass",
    "forbid:affective_contract_bypass",
    "forbid:affective_audit_bypass",
    "forbid:affective_direct_tool_call",
    "forbid:affective_direct_l4_adapter_call",
    "forbid:affective_direct_memory_write_delete_promote",
    "forbid:affective_core_mutation",
    "forbid:affective_side_effect",
    "forbid:affective_self_healing_trigger",
    "forbid:affective_self_evolution_trigger",
    "forbid:affective_product_factory_trigger",
)

_AFFECTIVE_LIVE_FIELD_NAMES = frozenset(
    (
        "handler",
        "endpoint",
        "callable_ref",
        "module_path",
        "import_path",
        "entry_point",
        "tool_schema",
        "function_schema",
        "raw_credential",
        "secret_handle",
        "plaintext_identity",
        "raw_emotion_state",
        "raw_psychological_profile",
        "user_sensitive_profile",
    )
)
_AFFECTIVE_LIVE_TEXT_FRAGMENTS = (
    "://",
    "http://",
    "https://",
    "file://",
    "postgres://",
    "mysql://",
    "mongodb://",
    "redis://",
    "BEGIN " "PRIVATE " "KEY",
    "BEGIN CERTIFICATE",
    "mockkey_",
    "Bearer ",
    "/mnt/",
    "/home/",
    "/var/",
    "/etc/",
)
_AFFECTIVE_PATH_RE = _compile(r"(^|[\s'\"=])([A-Za-z]:\\|\\\\[^\\]+\\[^\\]+|/(?:mnt|home|var|etc|tmp)/)")


def affective_declaration_digest(value: Any, excluded: tuple[str, ...] = ()) -> str:
    payload = stable_primitive(value)
    if isinstance(payload, dict):
        payload = {key: item for key, item in payload.items() if key not in excluded}
    return stable_digest(payload)


def _iter_values(value: Any) -> tuple[Any, ...]:
    if hasattr(value, "__dataclass_fields__") and not isinstance(value, type):
        items: list[Any] = []
        for item in fields(value):
            items.extend(_iter_values(getattr(value, item.name)))
        return tuple(items)
    if isinstance(value, dict):
        items = []
        for key, item in value.items():
            items.extend(_iter_values(key))
            items.extend(_iter_values(item))
        return tuple(items)
    if isinstance(value, (tuple, list, set, frozenset)):
        items = []
        for item in value:
            items.extend(_iter_values(item))
        return tuple(items)
    return (value,)


def has_affective_live_locator(value: Any) -> bool:
    for item in _iter_values(value):
        if isinstance(item, str):
            if _AFFECTIVE_PATH_RE.search(item):
                return True
            if any(fragment in item for fragment in _AFFECTIVE_LIVE_TEXT_FRAGMENTS):
                return True
    return False


def has_forbidden_affective_field_name(value: Any) -> bool:
    names = tuple(field.name for field in fields(value)) if hasattr(value, "__dataclass_fields__") and not isinstance(value, type) else ()
    return any(name in _AFFECTIVE_LIVE_FIELD_NAMES for name in names)


def _check_affective_base(obj: Any) -> None:
    for item in fields(obj):
        value = getattr(obj, item.name)
        if item.name.endswith("_ref") and item.name != "declaration_digest":
            ensure_ref_text(value, f"{type(obj).__name__}.{item.name}", required=False)
        elif item.name.endswith("_refs"):
            ensure_ref_items(value, f"{type(obj).__name__}.{item.name}")
        elif isinstance(value, bool):
            ensure_bool(value, f"{type(obj).__name__}.{item.name}")
    if has_forbidden_affective_field_name(obj) or has_affective_live_locator(obj):
        raise ValueError(f"{type(obj).__name__} must not expose live locator, credential, executable handle, or sensitive raw affective state")


@dataclass(frozen=True, slots=True)
class _AffectiveDeclarationBase:
    actor_ref: str = "actor:l5_affective_plugin"
    scope_ref: str = "scope:l5_affective_plugin"
    trace_ref: str = "trace:l5_affective_plugin"
    policy_refs: tuple[str, ...] = ("policy:l5_affective_plugin",)
    approval_ref: str = "approval:l5_affective_plugin_declaration"
    evidence_refs: tuple[str, ...] = ("evidence:redacted:l5_affective_plugin",)
    provenance_refs: tuple[str, ...] = ("provenance:l5_affective_plugin",)
    responsibility_chain_ref: str = "responsibility:l5_affective_plugin"
    accountability_ref: str = "accountability:l5_affective_plugin"
    tamper_evidence_ref: str = "tamper:l5_affective_plugin"
    source_layer: str = "L5_AFFECTIVE_PLUGIN_DECLARATION"
    risk_tags: tuple[str, ...] = ("declaration_only", "l6_planning_only", "no_live_execution", "no_authorization")

    def __post_init__(self) -> None:
        _check_affective_base(self)


@dataclass(frozen=True, slots=True)
class AffectiveCapabilityDeclaration(_AffectiveDeclarationBase):
    capability_declaration_ref: str = "capability:affective_plugin"
    plugin_kind_ref: str = AFFECTIVE_PLUGIN_KIND_REF
    capability_kind_refs: tuple[str, ...] = AFFECTIVE_CAPABILITY_KIND_REFS
    capability_metadata_ref: str = "metadata:affective_capability:redacted"
    capability_contract_ref: str = "contract:affective_modulation"
    allowed_modulation_refs: tuple[str, ...] = AFFECTIVE_ALLOWED_MODULATION_REFS
    forbidden_misuse_refs: tuple[str, ...] = AFFECTIVE_FORBIDDEN_MISUSE_REFS
    no_authorization_ref: str = "no_authorization:affective_plugin"
    no_direct_tool_call_ref: str = "no_direct_tool_call:affective_plugin"
    no_direct_l4_adapter_ref: str = "no_direct_l4_adapter:affective_plugin"
    no_core_mutation_ref: str = "no_core_mutation:affective_plugin"
    no_side_effect_ref: str = "no_side_effect:affective_plugin"
    declaration_digest: str = ""

    def __post_init__(self) -> None:
        _AffectiveDeclarationBase.__post_init__(self)
        if set(AFFECTIVE_CAPABILITY_KIND_REFS) - set(self.capability_kind_refs):
            raise ValueError("AffectiveCapabilityDeclaration must cover all required affective capability kinds")
        if set(AFFECTIVE_ALLOWED_MODULATION_REFS) - set(self.allowed_modulation_refs):
            raise ValueError("AffectiveCapabilityDeclaration must cover all allowed affective modulation refs")
        if set(AFFECTIVE_FORBIDDEN_MISUSE_REFS) - set(self.forbidden_misuse_refs):
            raise ValueError("AffectiveCapabilityDeclaration must include all affective forbidden misuse refs")
        if not self.declaration_digest:
            object.__setattr__(self, "declaration_digest", affective_declaration_digest(self, ("declaration_digest",)))


@dataclass(frozen=True, slots=True)
class AffectivePluginMountDeclaration(_AffectiveDeclarationBase):
    affective_mount_ref: str = "affective_mount:declaration_only"
    plugin_kind_ref: str = AFFECTIVE_PLUGIN_KIND_REF
    mount_kind_ref: str = AFFECTIVE_MOUNT_KIND_REF
    capability_kind_refs: tuple[str, ...] = AFFECTIVE_CAPABILITY_KIND_REFS
    modulation_contract_binding_ref: str = "contract_binding:affective_modulation"
    safety_boundary_ref: str = "safety_boundary:affective_plugin"
    audit_binding_ref: str = "audit_binding:affective_plugin"
    public_projection_summary_ref: str = "projection_summary:affective_plugin:redacted"
    l6_handoff_ref: str = "handoff:l5_l6_affective_plugin"
    allowed_modulation_refs: tuple[str, ...] = AFFECTIVE_ALLOWED_MODULATION_REFS
    forbidden_misuse_refs: tuple[str, ...] = AFFECTIVE_FORBIDDEN_MISUSE_REFS
    declaration_not_authorization_ref: str = "declaration_not_authorization:affective_plugin"
    l6_planning_only_ref: str = "l6_planning_only:affective_plugin"
    no_live_execution_ref: str = "no_live_execution:affective_plugin"
    no_direct_tool_call_ref: str = "no_direct_tool_call:affective_plugin"
    no_direct_l4_adapter_ref: str = "no_direct_l4_adapter:affective_plugin"
    no_core_mutation_ref: str = "no_core_mutation:affective_plugin"
    no_side_effect_ref: str = "no_side_effect:affective_plugin"
    no_permission_bypass_ref: str = "no_permission_bypass:affective_plugin"
    no_confirmation_bypass_ref: str = "no_confirmation_bypass:affective_plugin"
    no_memory_mutation_ref: str = "no_memory_mutation:affective_plugin"
    declaration_digest: str = ""

    def __post_init__(self) -> None:
        _AffectiveDeclarationBase.__post_init__(self)
        if self.plugin_kind_ref != AFFECTIVE_PLUGIN_KIND_REF:
            raise ValueError("AffectivePluginMountDeclaration must declare AffectivePlugin kind")
        if self.mount_kind_ref != AFFECTIVE_MOUNT_KIND_REF:
            raise ValueError("AffectivePluginMountDeclaration must declare affective mount kind")
        if not self.declaration_digest:
            object.__setattr__(self, "declaration_digest", affective_declaration_digest(self, ("declaration_digest",)))


@dataclass(frozen=True, slots=True)
class AffectiveModulationContractBinding(_AffectiveDeclarationBase):
    contract_binding_ref: str = "contract_binding:affective_modulation"
    allowed_modulation_refs: tuple[str, ...] = AFFECTIVE_ALLOWED_MODULATION_REFS
    forbidden_misuse_refs: tuple[str, ...] = AFFECTIVE_FORBIDDEN_MISUSE_REFS
    advisory_only_ref: str = "advisory_only:affective_modulation"
    no_execution_order_ref: str = "no_execution_order:affective_modulation"
    declaration_digest: str = ""

    def __post_init__(self) -> None:
        _AffectiveDeclarationBase.__post_init__(self)
        if set(AFFECTIVE_ALLOWED_MODULATION_REFS) - set(self.allowed_modulation_refs):
            raise ValueError("AffectiveModulationContractBinding must cover all allowed modulation refs")
        if not self.declaration_digest:
            object.__setattr__(self, "declaration_digest", affective_declaration_digest(self, ("declaration_digest",)))


@dataclass(frozen=True, slots=True)
class AffectiveSafetyBoundaryRef(_AffectiveDeclarationBase):
    safety_boundary_ref: str = "safety_boundary:affective_plugin"
    allowed_modulation_refs: tuple[str, ...] = AFFECTIVE_ALLOWED_MODULATION_REFS
    forbidden_misuse_refs: tuple[str, ...] = AFFECTIVE_FORBIDDEN_MISUSE_REFS
    no_sensitive_profile_plaintext_ref: str = "no_plaintext_sensitive_affective_profile:l5"
    no_risk_decision_override_ref: str = "no_risk_decision_override:affective_plugin"
    no_budget_override_ref: str = "no_budget_override:affective_plugin"
    no_memory_write_delete_promote_ref: str = "no_memory_write_delete_promote:affective_plugin"
    declaration_digest: str = ""

    def __post_init__(self) -> None:
        _AffectiveDeclarationBase.__post_init__(self)
        if set(AFFECTIVE_FORBIDDEN_MISUSE_REFS) - set(self.forbidden_misuse_refs):
            raise ValueError("AffectiveSafetyBoundaryRef must include all affective forbidden misuse refs")
        if not self.declaration_digest:
            object.__setattr__(self, "declaration_digest", affective_declaration_digest(self, ("declaration_digest",)))


@dataclass(frozen=True, slots=True)
class AffectiveAuditBinding(_AffectiveDeclarationBase):
    audit_binding_ref: str = "audit_binding:affective_plugin"
    safety_boundary_ref: str = "safety_boundary:affective_plugin"
    l6_handoff_ref: str = "handoff:l5_l6_affective_plugin"
    public_projection_summary_ref: str = "projection_summary:affective_plugin:redacted"
    event_refs: tuple[str, ...] = ("event:l5_affective_plugin_mount_declared", "event:l5_affective_boundary_checked")
    evidence_refs: tuple[str, ...] = ("evidence:redacted:l5_affective_audit",)
    declaration_digest: str = ""

    def __post_init__(self) -> None:
        _AffectiveDeclarationBase.__post_init__(self)
        if not self.event_refs:
            raise ValueError("AffectiveAuditBinding requires event refs")
        if not self.declaration_digest:
            object.__setattr__(self, "declaration_digest", affective_declaration_digest(self, ("declaration_digest",)))


@dataclass(frozen=True, slots=True)
class AffectivePublicProjectionSummary(_AffectiveDeclarationBase):
    projection_summary_ref: str = "projection_summary:affective_plugin:redacted"
    status_ref: str = "status:affective_plugin:l6_planning_only"
    allowed_modulation_summary_refs: tuple[str, ...] = AFFECTIVE_ALLOWED_MODULATION_REFS
    forbidden_misuse_summary_refs: tuple[str, ...] = AFFECTIVE_FORBIDDEN_MISUSE_REFS
    redacted_evidence_refs: tuple[str, ...] = ("evidence:redacted:l5_affective_projection",)
    redaction_state_ref: str = "redaction:affective_projection"
    no_sensitive_profile_plaintext_ref: str = "no_plaintext_sensitive_affective_profile:l5"
    declaration_digest: str = ""

    def __post_init__(self) -> None:
        _AffectiveDeclarationBase.__post_init__(self)
        if not all(ref.startswith(("evidence:redacted:", "redacted:")) for ref in self.redacted_evidence_refs):
            raise ValueError("AffectivePublicProjectionSummary requires redacted evidence refs")
        if not self.declaration_digest:
            object.__setattr__(self, "declaration_digest", affective_declaration_digest(self, ("declaration_digest",)))


@dataclass(frozen=True, slots=True)
class AffectiveL6HandoffRef(_AffectiveDeclarationBase):
    l6_handoff_ref: str = "handoff:l5_l6_affective_plugin"
    allowed_consume_refs: tuple[str, ...] = (
        "consume:affective_plugin_mount_declaration",
        "consume:affective_modulation_contract_binding",
        "consume:affective_safety_boundary",
        "consume:affective_audit_binding",
        "consume:affective_public_projection_summary",
    )
    forbidden_misuse_refs: tuple[str, ...] = AFFECTIVE_FORBIDDEN_MISUSE_REFS
    l6_planning_only_ref: str = "l6_planning_only:affective_plugin"
    no_live_execution_ref: str = "no_live_execution:affective_plugin"
    no_tool_call_ref: str = "no_tool_call:affective_plugin"
    no_adapter_call_ref: str = "no_adapter_call:affective_plugin"
    no_authorization_ref: str = "no_authorization:affective_plugin"
    declaration_digest: str = ""

    def __post_init__(self) -> None:
        _AffectiveDeclarationBase.__post_init__(self)
        if set(AFFECTIVE_FORBIDDEN_MISUSE_REFS) - set(self.forbidden_misuse_refs):
            raise ValueError("AffectiveL6HandoffRef must include all affective forbidden misuse refs")
        if not self.declaration_digest:
            object.__setattr__(self, "declaration_digest", affective_declaration_digest(self, ("declaration_digest",)))


__all__ = (
    "AFFECTIVE_PLUGIN_KIND_REF",
    "AFFECTIVE_MOUNT_KIND_REF",
    "AFFECTIVE_CAPABILITY_KIND_REFS",
    "AFFECTIVE_ALLOWED_MODULATION_REFS",
    "AFFECTIVE_FORBIDDEN_MISUSE_REFS",
    "AffectiveCapabilityDeclaration",
    "AffectivePluginMountDeclaration",
    "AffectiveModulationContractBinding",
    "AffectiveSafetyBoundaryRef",
    "AffectiveAuditBinding",
    "AffectivePublicProjectionSummary",
    "AffectiveL6HandoffRef",
    "affective_declaration_digest",
    "has_affective_live_locator",
    "has_forbidden_affective_field_name",
)
