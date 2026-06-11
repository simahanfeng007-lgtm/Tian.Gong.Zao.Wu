"""L5 phase 7 generic host boundary gate and cross-layer handoff declarations.

This module is intentionally inert. It models generic plugin-host precheck,
host governance gates, L3/L4/L6 handoff boundaries, route/hook/event
subscription declarations, contract/service/capability mount bindings, and the
conditional artifact-production mount binding as immutable declaration data.

It does not load plugins, call L3, call L4 adapters, create hooks, subscribe to
live events, release tool schemas, generate artifacts, write files, build
packages, deliver artifacts, issue permits, create leases, create tickets, mint
or validate tokens, start background tasks, or implement L6 plugins.
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields, is_dataclass
from enum import Enum
from typing import Any

from ._common import ensure_bool, ensure_ref_items, ensure_ref_text, ensure_short_text, stable_digest, stable_primitive
from .affective_plugin_declaration import (
    AFFECTIVE_ALLOWED_MODULATION_REFS,
    AFFECTIVE_CAPABILITY_KIND_REFS,
    AFFECTIVE_FORBIDDEN_MISUSE_REFS,
    AFFECTIVE_MOUNT_KIND_REF,
    AFFECTIVE_PLUGIN_KIND_REF,
)

PHASE7_PHASE = "L5_PHASE7"

GENERIC_HOST_PASS = "PASS_GENERIC_HOST"
GENERIC_HOST_PASS_WITH_COMPATIBLE_EXTENSION = "PASS_WITH_COMPATIBLE_EXTENSION"
GENERIC_HOST_BLOCK_TOOL_ONLY = "BLOCK_TOOL_ONLY_HOST"

_PLUGIN_KIND_BASE = (
    "ToolPlugin",
    "SkillPlugin",
    "MemoryPlugin",
    "PolicyPlugin",
    "AdapterPlugin",
    "GovernancePlugin",
    "ObservationPlugin",
)
_PLUGIN_KIND_PRODUCTION = (
    "ProductionPlugin",
    "ArtifactFactoryPlugin",
    "ProductBuilderPlugin",
    "DeliveryPlugin",
    "ValidationPlugin",
)
_PLUGIN_KIND_AFFECTIVE = ("AffectivePlugin",)
_CAPABILITY_KIND_BASE = (
    "ToolCapability",
    "SkillCapability",
    "MemoryCapability",
    "PolicyCapability",
    "AdapterCapability",
)
_CAPABILITY_KIND_PRODUCTION = (
    "ArtifactFactoryCapability",
    "ProductBuilderCapability",
    "ProductSpecCapability",
    "BuildPlanCapability",
    "ArtifactBuildCapability",
    "ArtifactValidationCapability",
    "ArtifactDeliveryCapability",
    "RepairAndRebuildCapability",
    "ProductQualityCapability",
    "ProductTemplateCapability",
    "ProductPackagingCapability",
    "ProductExportCapability",
)
_CAPABILITY_KIND_AFFECTIVE = AFFECTIVE_CAPABILITY_KIND_REFS

_EXECUTION_METHOD_NAMES = frozenset(
    (
        "apply",
        "execute",
        "run",
        "start",
        "stop",
        "mount",
        "unmount",
        "enable",
        "disable",
        "isolate",
        "quarantine",
        "recover",
        "rollback",
        "hot_switch",
        "replay",
        "migrate",
        "checkpoint",
        "observe",
        "probe",
        "ping",
        "connect",
        "collect",
        "read_log",
        "read_metric",
        "issue_permit",
        "issue_lease",
        "issue_ticket",
        "mint_token",
        "validate_token",
        "route_live",
        "dispatch",
        "call_adapter",
        "call_tool",
        "load_plugin",
        "build_artifact",
        "generate_artifact",
        "deliver_artifact",
        "package_artifact",
        "export_artifact",
        "commit",
        "mutate",
        "transition_to",
        "validate_and_apply",
        "auto_fix",
        "repair",
    )
)

_LIVE_FIELD_NAMES = frozenset(
    (
        "tool_schema",
        "function_schema",
        "model_visible_name",
        "execution_endpoint",
        "handler",
        "handler_ref",
        "handler_name",
        "callback",
        "callable_ref",
        "endpoint",
        "url",
        "socket",
        "port",
        "server",
        "service_instance",
        "adapter_instance",
        "client",
        "session",
        "terminal_handle",
        "sandbox_instance",
        "credential_handle",
        "storage_client",
        "plugin_instance",
        "module_path",
        "import_path",
        "entry_point",
        "class_name",
        "function_name",
        "artifact_output_path",
        "package_path",
        "repository_path",
        "deploy_target",
        "build_command",
        "validation_command",
        "delivery_command",
        "permit_object",
        "lease_object",
        "confirmation_ticket_object",
        "token_object",
        "raw_value",
        "token_value",
        "secret_value",
        "api_key_value",
        "password_value",
    )
)

_LIVE_LOCATOR_FRAGMENTS = (
    "://",
    "file://",
    "http://",
    "https://",
    "ws://",
    "wss://",
    "postgres://",
    "mysql://",
    "mongodb://",
    "redis://",
    "module:function",
    "importlib.import_module",
    "importlib.util.spec_from_file_location",
    "__import__",
    "runpy",
    "pkgutil",
    "entry_points",
    "subprocess",
    "os.system",
    "Path.write_text",
    "Path.unlink",
    "shutil.rmtree",
    "BEGIN " "PRIVATE " "KEY",
    "BEGIN CERTIFICATE",
    "call_tool",
    "call_adapter",
    "load_plugin",
    "AbilityPackage",
    "CapabilityPort",
    "AbilityPackagePort",
)

_PRODUCT_LIVE_VERBS = (
    " build ",
    "build_artifact",
    "generate_artifact",
    "render_artifact",
    "export_artifact",
    "package_artifact",
    "deliver_artifact",
    " generate ",
    " render ",
    " export ",
    " package ",
    " deliver ",
    " deploy ",
    " write_file",
    "create_pdf",
    "create_docx",
    "create_ppt",
    "create_image",
    "create_app",
    "create_installer",
)


class PluginPhase7ConflictSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    P3 = "p3"
    P2 = "p2"
    P1 = "p1"
    P0 = "p0"


class PluginPhase7ConflictKind(str, Enum):
    GENERIC_HOST_TOOL_ONLY_CONFLICT = "generic_host_tool_only_conflict"
    CAPABILITY_KIND_TOOL_ONLY_CONFLICT = "capability_kind_tool_only_conflict"
    MOUNT_KIND_TOOL_ONLY_CONFLICT = "mount_kind_tool_only_conflict"
    PRODUCTION_PRECHECK_NOT_PASSED_CONFLICT = "production_precheck_not_passed_conflict"
    PRODUCTION_MOUNT_ADDED_WITHOUT_GENERIC_HOST_SUPPORT_CONFLICT = "production_mount_added_without_generic_host_support_conflict"
    PRODUCTION_MOUNT_MISSING_PRODUCT_SPEC_CONTRACT_CONFLICT = "production_mount_missing_product_spec_contract_conflict"
    PRODUCTION_MOUNT_MISSING_BUILD_PLAN_CONTRACT_CONFLICT = "production_mount_missing_build_plan_contract_conflict"
    PRODUCTION_MOUNT_MISSING_ARTIFACT_BUILD_CONTRACT_CONFLICT = "production_mount_missing_artifact_build_contract_conflict"
    PRODUCTION_MOUNT_MISSING_VALIDATION_CONTRACT_CONFLICT = "production_mount_missing_validation_contract_conflict"
    PRODUCTION_MOUNT_MISSING_DELIVERY_CONTRACT_CONFLICT = "production_mount_missing_delivery_contract_conflict"
    PRODUCTION_MOUNT_MISSING_ARTIFACT_INTEGRITY_CONFLICT = "production_mount_missing_artifact_integrity_conflict"
    PRODUCTION_MOUNT_MISSING_ARTIFACT_PROVENANCE_CONFLICT = "production_mount_missing_artifact_provenance_conflict"
    PRODUCTION_MOUNT_MISSING_TRANSACTION_COMPENSATION_CONFLICT = "production_mount_missing_transaction_compensation_conflict"
    PRODUCTION_MOUNT_LIVE_BUILD_CONFLICT = "production_mount_live_build_conflict"
    PRODUCTION_MOUNT_DIRECT_TOOL_CALL_CONFLICT = "production_mount_direct_tool_call_conflict"
    PRODUCTION_MOUNT_DIRECT_L4_ADAPTER_CONFLICT = "production_mount_direct_l4_adapter_conflict"
    AFFECTIVE_MOUNT_MISSING_CONTRACT_CONFLICT = "affective_mount_missing_contract_conflict"
    AFFECTIVE_MOUNT_MISSING_SAFETY_BOUNDARY_CONFLICT = "affective_mount_missing_safety_boundary_conflict"
    AFFECTIVE_MOUNT_MISSING_AUDIT_BINDING_CONFLICT = "affective_mount_missing_audit_binding_conflict"
    AFFECTIVE_MOUNT_LIVE_ACTION_CONFLICT = "affective_mount_live_action_conflict"
    L3_HANDOFF_MISSING_ORCHESTRATION_BOUNDARY_CONFLICT = "l3_handoff_missing_orchestration_boundary_conflict"
    L3_HANDOFF_DIRECT_EXECUTION_PLAN_CONFLICT = "l3_handoff_direct_execution_plan_conflict"
    L3_HANDOFF_RUNTIME_STATE_MUTATION_CONFLICT = "l3_handoff_runtime_state_mutation_conflict"
    L4_HANDOFF_MISSING_ADAPTER_BOUNDARY_CONFLICT = "l4_handoff_missing_adapter_boundary_conflict"
    L4_HANDOFF_DIRECT_ADAPTER_CALL_CONFLICT = "l4_handoff_direct_adapter_call_conflict"
    L4_HANDOFF_LIVE_EXTERNAL_ACTION_CONFLICT = "l4_handoff_live_external_action_conflict"
    L6_ENTRY_MISSING_CONTRACT_CONFLICT = "l6_entry_missing_contract_conflict"
    L6_ENTRY_DYNAMIC_LOAD_CONFLICT = "l6_entry_dynamic_load_conflict"
    L6_ENTRY_LIVE_INVOCATION_CONFLICT = "l6_entry_live_invocation_conflict"
    L6_IMPLEMENTATION_IN_L5_CONFLICT = "l6_implementation_in_l5_conflict"
    ROUTE_LIVE_DISPATCH_CONFLICT = "route_live_dispatch_conflict"
    ROUTE_MISSING_CONTRACT_CONFLICT = "route_missing_contract_conflict"
    ROUTE_EXPOSES_EXECUTABLE_ENDPOINT_CONFLICT = "route_exposes_executable_endpoint_conflict"
    HOOK_LIVE_HANDLER_CONFLICT = "hook_live_handler_conflict"
    HOOK_BACKGROUND_TASK_CONFLICT = "hook_background_task_conflict"
    EVENT_SUBSCRIPTION_LIVE_BUS_CONFLICT = "event_subscription_live_bus_conflict"
    EVENT_SUBSCRIPTION_EMIT_CONFLICT = "event_subscription_emit_conflict"
    EVENT_SUBSCRIPTION_MISSING_BOUNDARY_CONFLICT = "event_subscription_missing_boundary_conflict"
    CONTRACT_BINDING_MISSING_CONTRACT_REF_CONFLICT = "contract_binding_missing_contract_ref_conflict"
    CONTRACT_BINDING_MISSING_VALIDATION_REF_CONFLICT = "contract_binding_missing_validation_ref_conflict"
    SERVICE_MOUNT_LIVE_SERVICE_CONFLICT = "service_mount_live_service_conflict"
    SERVICE_MOUNT_EXPOSES_ENDPOINT_CONFLICT = "service_mount_exposes_endpoint_conflict"
    CAPABILITY_MOUNT_RELEASES_TOOL_SCHEMA_CONFLICT = "capability_mount_releases_tool_schema_conflict"
    CAPABILITY_MOUNT_MODEL_VISIBLE_EXECUTION_CONFLICT = "capability_mount_model_visible_execution_conflict"
    CAPABILITY_MOUNT_MISSING_BOUNDARY_GATE_CONFLICT = "capability_mount_missing_boundary_gate_conflict"
    GOVERNANCE_MISSING_GATE_CONFLICT = "governance_missing_gate_conflict"
    GOVERNANCE_BYPASS_LIVE_TOOL_CONFLICT = "governance_bypass_live_tool_conflict"
    GOVERNANCE_BYPASS_L4_ADAPTER_CONFLICT = "governance_bypass_l4_adapter_conflict"
    GOVERNANCE_BYPASS_AUDIT_CONFLICT = "governance_bypass_audit_conflict"
    GOVERNANCE_BYPASS_BUDGET_CONFLICT = "governance_bypass_budget_conflict"
    GOVERNANCE_BYPASS_PRIVACY_SECRET_CONFLICT = "governance_bypass_privacy_secret_conflict"
    PUBLIC_PROJECTION_LEAK_CONFLICT = "public_projection_leak_conflict"
    AUDIT_EVIDENCE_CHAIN_MISSING_CONFLICT = "audit_evidence_chain_missing_conflict"
    LEGACY_RUNTIME_CONFLICT = "legacy_runtime_conflict"
    LIVE_ACTION_CONFLICT = "live_action_conflict"


@dataclass(frozen=True, slots=True)
class PluginPhase7Conflict:
    conflict_ref: str
    conflict_kind: str
    severity: str
    field_path: str
    message: str
    blocking: bool = True
    evidence_refs: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        ensure_ref_text(self.conflict_ref, "PluginPhase7Conflict.conflict_ref")
        ensure_ref_text(self.conflict_kind, "PluginPhase7Conflict.conflict_kind")
        ensure_ref_text(self.severity, "PluginPhase7Conflict.severity")
        ensure_ref_text(self.field_path, "PluginPhase7Conflict.field_path", required=False)
        ensure_short_text(self.message, "PluginPhase7Conflict.message")
        ensure_bool(self.blocking, "PluginPhase7Conflict.blocking")
        ensure_ref_items(self.evidence_refs, "PluginPhase7Conflict.evidence_refs")


def phase7_declaration_digest(value: Any, exclude_fields: tuple[str, ...] = ()) -> str:
    primitive = stable_primitive(value)
    excluded = set(exclude_fields)
    if isinstance(primitive, dict):
        primitive = {key: item for key, item in primitive.items() if key not in excluded and not key.endswith("_digest")}
    return stable_digest(primitive)


def _iter_values(value: Any) -> tuple[Any, ...]:
    if is_dataclass(value) and not isinstance(value, type):
        result: list[Any] = []
        for item in fields(value):
            result.extend(_iter_values(getattr(value, item.name)))
        return tuple(result)
    if isinstance(value, dict):
        result: list[Any] = []
        for key, item in value.items():
            result.extend(_iter_values(key))
            result.extend(_iter_values(item))
        return tuple(result)
    if isinstance(value, (tuple, list, set, frozenset)):
        result = []
        for item in value:
            result.extend(_iter_values(item))
        return tuple(result)
    return (value,)


def has_live_phase7_locator(value: Any) -> bool:
    for item in _iter_values(value):
        if not isinstance(item, str):
            continue
        lowered = item.lower()
        if any(fragment.lower() in lowered for fragment in _LIVE_LOCATOR_FRAGMENTS):
            return True
        if "mockkey_" in item or "bearer " in lowered or "akia" in item:
            return True
        if any(pattern in lowered for pattern in ("password=", "api_key=", "token=", "secret=")):
            return True
        padded = f" {lowered} "
        if any(verb in padded for verb in _PRODUCT_LIVE_VERBS):
            return True
    return False


def has_forbidden_phase7_field_name(value: Any) -> bool:
    if not (is_dataclass(value) and not isinstance(value, type)):
        return False
    return any(item.name in _LIVE_FIELD_NAMES for item in fields(value))


def has_forbidden_phase7_method(value: Any) -> bool:
    names = set(dir(value))
    return any(name in names and callable(getattr(value, name, None)) for name in _EXECUTION_METHOD_NAMES)


def phase7_public_text_is_safe(value: Any) -> bool:
    return not has_live_phase7_locator(value)


def _has_ref(value: str) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _has_refs(value: tuple[str, ...]) -> bool:
    return isinstance(value, tuple) and any(_has_ref(item) for item in value)


def _require_ref(obj: Any, field_name: str, conflicts: list[PluginPhase7Conflict], kind: PluginPhase7ConflictKind, severity: PluginPhase7ConflictSeverity = PluginPhase7ConflictSeverity.P1) -> None:
    value = getattr(obj, field_name, "")
    ok = _has_refs(value) if isinstance(value, tuple) else _has_ref(value)
    if not ok:
        conflicts.append(_conflict(kind, severity, field_name, f"{field_name} is required", getattr(obj, "evidence_refs", ())))


def _base_missing(obj: Any) -> tuple[str, ...]:
    missing: list[str] = []
    for name in (
        "actor_ref",
        "scope_ref",
        "trace_ref",
        "evidence_refs",
        "provenance_refs",
        "responsibility_chain_ref",
        "accountability_ref",
        "tamper_evidence_ref",
        "source_layer",
    ):
        if not hasattr(obj, name):
            missing.append(name)
            continue
        value = getattr(obj, name)
        if isinstance(value, tuple):
            if not _has_refs(value):
                missing.append(name)
        elif not _has_ref(value):
            missing.append(name)
    if hasattr(obj, "policy_refs") and not _has_refs(getattr(obj, "policy_refs")):
        missing.append("policy_refs")
    return tuple(missing)


def _conflict(kind: PluginPhase7ConflictKind, severity: PluginPhase7ConflictSeverity, field_path: str, message: str, evidence_refs: tuple[str, ...] = ()) -> PluginPhase7Conflict:
    return PluginPhase7Conflict(
        conflict_ref=f"conflict:l5_phase7:{kind.value}:{field_path}",
        conflict_kind=kind.value,
        severity=severity.value,
        field_path=field_path,
        message=message,
        blocking=severity in (PluginPhase7ConflictSeverity.P0, PluginPhase7ConflictSeverity.P1),
        evidence_refs=tuple(evidence_refs),
    )


def _count_conflicts(conflicts: tuple[PluginPhase7Conflict, ...]) -> tuple[int, int, int, int]:
    return (
        sum(1 for item in conflicts if item.severity == PluginPhase7ConflictSeverity.P0.value),
        sum(1 for item in conflicts if item.severity == PluginPhase7ConflictSeverity.P1.value),
        sum(1 for item in conflicts if item.severity == PluginPhase7ConflictSeverity.P2.value),
        sum(1 for item in conflicts if item.severity == PluginPhase7ConflictSeverity.P3.value),
    )


def _conflict_refs(conflicts: tuple[PluginPhase7Conflict, ...]) -> tuple[str, ...]:
    return tuple(item.conflict_ref for item in conflicts)


@dataclass(frozen=True, slots=True)
class _Phase7Base:
    actor_ref: str = "actor:l5_phase7"
    scope_ref: str = "scope:l5_phase7"
    trace_ref: str = "trace:l5_phase7"
    policy_refs: tuple[str, ...] = ("policy:l5_phase7",)
    approval_ref: str = "approval:declared"
    evidence_refs: tuple[str, ...] = ("evidence:l5_phase7",)
    provenance_refs: tuple[str, ...] = ("provenance:l5_phase7",)
    responsibility_chain_ref: str = "responsibility:l5_phase7"
    accountability_ref: str = "accountability:l5_phase7"
    tamper_evidence_ref: str = "tamper:l5_phase7"
    source_layer: str = PHASE7_PHASE
    severity: str = PluginPhase7ConflictSeverity.P2.value
    risk_tags: tuple[str, ...] = ("declaration_only", "no_live_action")

    def __post_init__(self) -> None:
        for name in ("actor_ref", "scope_ref", "trace_ref", "approval_ref", "responsibility_chain_ref", "accountability_ref", "tamper_evidence_ref", "source_layer", "severity"):
            ensure_ref_text(getattr(self, name), f"{self.__class__.__name__}.{name}", required=False)
        for name in ("policy_refs", "evidence_refs", "provenance_refs", "risk_tags"):
            ensure_ref_items(getattr(self, name), f"{self.__class__.__name__}.{name}")


@dataclass(frozen=True, slots=True)
class PluginGenericHostPrecheckReport(_Phase7Base):
    precheck_ref: str = "precheck:l5_phase7:generic_host"
    result: str = GENERIC_HOST_PASS_WITH_COMPATIBLE_EXTENSION
    plugin_kind_support_refs: tuple[str, ...] = _PLUGIN_KIND_BASE + _PLUGIN_KIND_AFFECTIVE
    capability_kind_support_refs: tuple[str, ...] = _CAPABILITY_KIND_BASE + _CAPABILITY_KIND_AFFECTIVE
    mount_kind_support_refs: tuple[str, ...] = ("mount_kind:generic", "mount_kind:capability", "mount_kind:service", AFFECTIVE_MOUNT_KIND_REF)
    contract_binding_support_ref: str = "contract_binding:generic"
    tool_only_findings: tuple[str, ...] = field(default_factory=tuple)
    compatible_extension_refs: tuple[str, ...] = ("extension:production_kind_declaration", "extension:artifact_capability_kind_declaration", "extension:affective_kind_declaration", "extension:affective_capability_kind_declaration")
    precheck_digest: str = ""

    def __post_init__(self) -> None:
        _Phase7Base.__post_init__(self)
        ensure_ref_text(self.precheck_ref, "PluginGenericHostPrecheckReport.precheck_ref")
        if self.result not in (GENERIC_HOST_PASS, GENERIC_HOST_PASS_WITH_COMPATIBLE_EXTENSION, GENERIC_HOST_BLOCK_TOOL_ONLY):
            raise ValueError("PluginGenericHostPrecheckReport.result must be a known precheck result")
        for name in ("plugin_kind_support_refs", "capability_kind_support_refs", "mount_kind_support_refs", "tool_only_findings", "compatible_extension_refs"):
            ensure_ref_items(getattr(self, name), f"PluginGenericHostPrecheckReport.{name}")
        ensure_ref_text(self.contract_binding_support_ref, "PluginGenericHostPrecheckReport.contract_binding_support_ref", required=False)
        if not self.precheck_digest:
            object.__setattr__(self, "precheck_digest", phase7_declaration_digest(self, ("precheck_digest",)))


class PluginGenericHostPrecheckValidator:
    def check(self, *, supports_plugin_kind: bool, supports_capability_kind: bool, supports_mount_kind: bool, supports_contract_ref: bool, tool_schema_only: bool = False, forced_tool_plugin: bool = False, evidence_refs: tuple[str, ...] = ("evidence:generic_precheck",)) -> PluginGenericHostPrecheckReport:
        tool_only = tool_schema_only or forced_tool_plugin or not (supports_plugin_kind and supports_capability_kind and supports_mount_kind and supports_contract_ref)
        if tool_only and (tool_schema_only or forced_tool_plugin):
            return PluginGenericHostPrecheckReport(
                result=GENERIC_HOST_BLOCK_TOOL_ONLY,
                plugin_kind_support_refs=(),
                capability_kind_support_refs=(),
                mount_kind_support_refs=(),
                contract_binding_support_ref="",
                tool_only_findings=("tool_schema_only",) if tool_schema_only else ("forced_tool_plugin",),
                evidence_refs=evidence_refs,
                severity=PluginPhase7ConflictSeverity.P1.value,
            )
        if tool_only:
            return PluginGenericHostPrecheckReport(
                result=GENERIC_HOST_PASS_WITH_COMPATIBLE_EXTENSION,
                compatible_extension_refs=("extension:plugin_kind", "extension:capability_kind", "extension:mount_kind", "extension:contract_ref"),
                evidence_refs=evidence_refs,
                severity=PluginPhase7ConflictSeverity.P2.value,
            )
        return PluginGenericHostPrecheckReport(result=GENERIC_HOST_PASS, compatible_extension_refs=(), evidence_refs=evidence_refs, severity=PluginPhase7ConflictSeverity.INFO.value)


@dataclass(frozen=True, slots=True)
class PluginHostBoundaryGateDeclaration(_Phase7Base):
    host_boundary_gate_ref: str = "host_boundary_gate:l5_phase7"
    registry_key_ref: str = "registry_key:declared"
    plugin_kind_ref: str = "PluginKind:generic"
    capability_kind_refs: tuple[str, ...] = _CAPABILITY_KIND_BASE + _CAPABILITY_KIND_AFFECTIVE
    lifecycle_ref: str = "lifecycle:declared"
    mount_decl_ref: str = "mount:declared"
    health_gate_ref: str = "health_gate:declared"
    isolation_gate_ref: str = "isolation_gate:declared"
    permission_gate_ref: str = "permission_gate:declared"
    resource_gate_ref: str = "resource_gate:declared"
    privacy_gate_ref: str = "privacy_gate:declared"
    audit_gate_ref: str = "audit_gate:declared"
    contract_gate_ref: str = "contract_gate:declared"
    version_gate_ref: str = "version_gate:declared"
    validation_gate_ref: str = "validation_gate:declared"
    artifact_integrity_gate_ref: str = "artifact_integrity_gate:declared"
    l3_handoff_ref: str = "l3_handoff:declared"
    l4_handoff_ref: str = "l4_handoff:declared"
    l6_entry_ref: str = "l6_entry:declared"
    deny_by_default_declared: bool = True
    least_privilege_declared: bool = True
    declaration_not_authorization_ref: str = "declaration_not_authorization:l5_phase7"
    no_direct_tool_call_ref: str = "no_direct_tool_call:l5_phase7"
    no_direct_l4_adapter_ref: str = "no_direct_l4_adapter:l5_phase7"
    no_l6_implementation_ref: str = "no_l6_implementation:l5_phase7"
    required_policy_refs: tuple[str, ...] = ("policy:host_boundary",)
    required_approval_ref: str = "approval:host_boundary"
    required_evidence_refs: tuple[str, ...] = ("evidence:host_boundary",)
    gate_digest: str = ""

    def __post_init__(self) -> None:
        _Phase7Base.__post_init__(self)
        for name in ("host_boundary_gate_ref", "registry_key_ref", "plugin_kind_ref", "lifecycle_ref", "mount_decl_ref", "health_gate_ref", "isolation_gate_ref", "permission_gate_ref", "resource_gate_ref", "privacy_gate_ref", "audit_gate_ref", "contract_gate_ref", "version_gate_ref", "validation_gate_ref", "artifact_integrity_gate_ref", "l3_handoff_ref", "l4_handoff_ref", "l6_entry_ref", "declaration_not_authorization_ref", "no_direct_tool_call_ref", "no_direct_l4_adapter_ref", "no_l6_implementation_ref", "required_approval_ref"):
            ensure_ref_text(getattr(self, name), f"PluginHostBoundaryGateDeclaration.{name}", required=False)
        for name in ("capability_kind_refs", "required_policy_refs", "required_evidence_refs"):
            ensure_ref_items(getattr(self, name), f"PluginHostBoundaryGateDeclaration.{name}")
        ensure_bool(self.deny_by_default_declared, "PluginHostBoundaryGateDeclaration.deny_by_default_declared")
        ensure_bool(self.least_privilege_declared, "PluginHostBoundaryGateDeclaration.least_privilege_declared")
        if not self.gate_digest:
            object.__setattr__(self, "gate_digest", phase7_declaration_digest(self, ("gate_digest",)))


@dataclass(frozen=True, slots=True)
class PluginL3HandoffDeclaration(_Phase7Base):
    l3_handoff_ref: str = "l3_handoff:l5_phase7"
    registry_key_ref: str = "registry_key:declared"
    flow_ref: str = "flow:declared"
    run_scope_ref: str = "run_scope:declared"
    task_scope_ref: str = "task_scope:declared"
    turn_scope_ref: str = "turn_scope:declared"
    step_scope_ref: str = "step_scope:declared"
    decision_ref: str = "decision:declared"
    effect_ref: str = "effect:declared"
    transaction_ref: str = "transaction:declared"
    compensation_ref: str = "compensation:declared"
    validation_ref: str = "validation:declared"
    regression_ref: str = "regression:declared"
    orchestration_boundary_ref: str = "orchestration_boundary:declared"
    no_direct_execution_plan_ref: str = "no_direct_execution_plan:l5_phase7"
    no_runtime_state_mutation_ref: str = "no_runtime_state_mutation:l5_phase7"
    event_kind_refs: tuple[str, ...] = ("event_kind:l3_handoff_declared",)
    handoff_event_ref: str = "event:l3_handoff"
    required_policy_refs: tuple[str, ...] = ("policy:l3_handoff",)
    required_evidence_refs: tuple[str, ...] = ("evidence:l3_handoff",)
    handoff_digest: str = ""

    def __post_init__(self) -> None:
        _Phase7Base.__post_init__(self)
        for item in fields(self):
            if item.name.endswith("_ref") and item.name != "handoff_digest":
                ensure_ref_text(getattr(self, item.name), f"PluginL3HandoffDeclaration.{item.name}", required=False)
        for name in ("event_kind_refs", "required_policy_refs", "required_evidence_refs"):
            ensure_ref_items(getattr(self, name), f"PluginL3HandoffDeclaration.{name}")
        if not self.handoff_digest:
            object.__setattr__(self, "handoff_digest", phase7_declaration_digest(self, ("handoff_digest",)))


@dataclass(frozen=True, slots=True)
class PluginL4AdapterHandoffDeclaration(_Phase7Base):
    l4_handoff_ref: str = "l4_handoff:l5_phase7"
    registry_key_ref: str = "registry_key:declared"
    adapter_kind_refs: tuple[str, ...] = ("adapter_kind:file_decl", "adapter_kind:network_decl")
    adapter_boundary_refs: tuple[str, ...] = ("adapter_boundary:declared",)
    tool_boundary_refs: tuple[str, ...] = ("tool_boundary:declared",)
    file_boundary_refs: tuple[str, ...] = ("file_boundary:declared",)
    network_boundary_refs: tuple[str, ...] = ("network_boundary:declared",)
    terminal_boundary_refs: tuple[str, ...] = ("terminal_boundary:declared",)
    browser_boundary_refs: tuple[str, ...] = ("browser_boundary:declared",)
    model_client_boundary_refs: tuple[str, ...] = ("model_client_boundary:declared",)
    sandbox_boundary_refs: tuple[str, ...] = ("sandbox_boundary:declared",)
    credential_boundary_refs: tuple[str, ...] = ("credential_boundary:declared",)
    storage_boundary_refs: tuple[str, ...] = ("storage_boundary:declared",)
    no_direct_adapter_call_ref: str = "no_direct_adapter_call:l5_phase7"
    no_live_external_action_ref: str = "no_live_external_action:l5_phase7"
    handoff_event_ref: str = "event:l4_handoff"
    required_policy_refs: tuple[str, ...] = ("policy:l4_handoff",)
    required_approval_ref: str = "approval:l4_handoff"
    required_evidence_refs: tuple[str, ...] = ("evidence:l4_handoff",)
    handoff_digest: str = ""

    def __post_init__(self) -> None:
        _Phase7Base.__post_init__(self)
        for item in fields(self):
            value = getattr(self, item.name)
            if item.name.endswith("_ref") and item.name != "handoff_digest":
                ensure_ref_text(value, f"PluginL4AdapterHandoffDeclaration.{item.name}", required=False)
            elif item.name.endswith("_refs"):
                ensure_ref_items(value, f"PluginL4AdapterHandoffDeclaration.{item.name}")
        if has_live_phase7_locator(self) or has_forbidden_phase7_field_name(self):
            raise ValueError("PluginL4AdapterHandoffDeclaration must not contain live L4 adapter material")
        if not self.handoff_digest:
            object.__setattr__(self, "handoff_digest", phase7_declaration_digest(self, ("handoff_digest",)))


@dataclass(frozen=True, slots=True)
class PluginL6EntryDeclaration(_Phase7Base):
    l6_entry_ref: str = "l6_entry:l5_phase7"
    registry_key_ref: str = "registry_key:declared"
    plugin_kind_ref: str = "PluginKind:generic"
    capability_kind_refs: tuple[str, ...] = _CAPABILITY_KIND_BASE
    entry_contract_ref: str = "contract:l6_entry"
    implementation_absent_required: bool = True
    no_dynamic_load_ref: str = "no_dynamic_load:l5_phase7"
    no_live_invocation_ref: str = "no_live_invocation:l5_phase7"
    lifecycle_gate_ref: str = "lifecycle_gate:declared"
    health_gate_ref: str = "health_gate:declared"
    isolation_gate_ref: str = "isolation_gate:declared"
    permission_gate_ref: str = "permission_gate:declared"
    resource_gate_ref: str = "resource_gate:declared"
    privacy_gate_ref: str = "privacy_gate:declared"
    audit_gate_ref: str = "audit_gate:declared"
    contract_gate_ref: str = "contract_gate:declared"
    validation_gate_ref: str = "validation_gate:declared"
    production_boundary_ref: str = "production_boundary:optional_declared"
    artifact_integrity_gate_ref: str = "artifact_integrity_gate:optional_declared"
    required_policy_refs: tuple[str, ...] = ("policy:l6_entry",)
    required_approval_ref: str = "approval:l6_entry"
    required_evidence_refs: tuple[str, ...] = ("evidence:l6_entry",)
    entry_digest: str = ""

    def __post_init__(self) -> None:
        _Phase7Base.__post_init__(self)
        ensure_bool(self.implementation_absent_required, "PluginL6EntryDeclaration.implementation_absent_required")
        for item in fields(self):
            value = getattr(self, item.name)
            if item.name.endswith("_ref") and item.name != "entry_digest":
                ensure_ref_text(value, f"PluginL6EntryDeclaration.{item.name}", required=False)
            elif item.name.endswith("_refs"):
                ensure_ref_items(value, f"PluginL6EntryDeclaration.{item.name}")
        if has_live_phase7_locator(self) or has_forbidden_phase7_field_name(self):
            raise ValueError("PluginL6EntryDeclaration must not expose module path, import path, entry point, callable, or plugin instance")
        if not self.entry_digest:
            object.__setattr__(self, "entry_digest", phase7_declaration_digest(self, ("entry_digest",)))


@dataclass(frozen=True, slots=True)
class PluginRouteDeclaration(_Phase7Base):
    route_decl_ref: str = "route:l5_phase7"
    registry_key_ref: str = "registry_key:declared"
    route_kind_ref: str = "route_kind:declaration"
    intent_kind_refs: tuple[str, ...] = ("intent:declared",)
    capability_kind_refs: tuple[str, ...] = _CAPABILITY_KIND_BASE
    contract_ref: str = "contract:route"
    route_boundary_ref: str = "route_boundary:declared"
    no_live_dispatch_ref: str = "no_live_dispatch:l5_phase7"
    no_direct_tool_call_ref: str = "no_direct_tool_call:l5_phase7"
    required_policy_refs: tuple[str, ...] = ("policy:route",)
    event_kind_refs: tuple[str, ...] = ("event_kind:route_declared",)
    route_digest: str = ""

    def __post_init__(self) -> None:
        _Phase7Base.__post_init__(self)
        for item in fields(self):
            value = getattr(self, item.name)
            if item.name.endswith("_ref") and item.name != "route_digest":
                ensure_ref_text(value, f"PluginRouteDeclaration.{item.name}", required=False)
            elif item.name.endswith("_refs"):
                ensure_ref_items(value, f"PluginRouteDeclaration.{item.name}")
        if has_live_phase7_locator(self) or has_forbidden_phase7_field_name(self):
            raise ValueError("PluginRouteDeclaration must not expose live dispatch endpoint")
        if not self.route_digest:
            object.__setattr__(self, "route_digest", phase7_declaration_digest(self, ("route_digest",)))


@dataclass(frozen=True, slots=True)
class PluginHookDeclaration(_Phase7Base):
    hook_decl_ref: str = "hook:l5_phase7"
    registry_key_ref: str = "registry_key:declared"
    hook_kind_refs: tuple[str, ...] = ("hook_kind:declaration",)
    hook_boundary_ref: str = "hook_boundary:declared"
    event_kind_refs: tuple[str, ...] = ("event_kind:hook_declared",)
    subscription_policy_ref: str = "subscription_policy:declared"
    no_live_handler_ref: str = "no_live_handler:l5_phase7"
    no_background_task_ref: str = "no_background_task:l5_phase7"
    required_policy_refs: tuple[str, ...] = ("policy:hook",)
    hook_digest: str = ""

    def __post_init__(self) -> None:
        _Phase7Base.__post_init__(self)
        for item in fields(self):
            value = getattr(self, item.name)
            if item.name.endswith("_ref") and item.name != "hook_digest":
                ensure_ref_text(value, f"PluginHookDeclaration.{item.name}", required=False)
            elif item.name.endswith("_refs"):
                ensure_ref_items(value, f"PluginHookDeclaration.{item.name}")
        if has_live_phase7_locator(self) or has_forbidden_phase7_field_name(self):
            raise ValueError("PluginHookDeclaration must not expose live handler or background task")
        if not self.hook_digest:
            object.__setattr__(self, "hook_digest", phase7_declaration_digest(self, ("hook_digest",)))


@dataclass(frozen=True, slots=True)
class PluginEventSubscriptionDeclaration(_Phase7Base):
    subscription_decl_ref: str = "subscription:l5_phase7"
    registry_key_ref: str = "registry_key:declared"
    event_kind_refs: tuple[str, ...] = ("event_kind:declared",)
    event_boundary_ref: str = "event_boundary:declared"
    event_filter_decl_refs: tuple[str, ...] = ("event_filter:declared",)
    event_projection_ref: str = "event_projection:declared"
    no_live_subscription_ref: str = "no_live_subscription:l5_phase7"
    no_event_emit_ref: str = "no_event_emit:l5_phase7"
    required_policy_refs: tuple[str, ...] = ("policy:event_subscription",)
    subscription_digest: str = ""

    def __post_init__(self) -> None:
        _Phase7Base.__post_init__(self)
        for item in fields(self):
            value = getattr(self, item.name)
            if item.name.endswith("_ref") and item.name != "subscription_digest":
                ensure_ref_text(value, f"PluginEventSubscriptionDeclaration.{item.name}", required=False)
            elif item.name.endswith("_refs"):
                ensure_ref_items(value, f"PluginEventSubscriptionDeclaration.{item.name}")
        if has_live_phase7_locator(self) or has_forbidden_phase7_field_name(self):
            raise ValueError("PluginEventSubscriptionDeclaration must not expose live event bus")
        if not self.subscription_digest:
            object.__setattr__(self, "subscription_digest", phase7_declaration_digest(self, ("subscription_digest",)))


@dataclass(frozen=True, slots=True)
class PluginContractBindingDeclaration(_Phase7Base):
    contract_binding_ref: str = "contract_binding:l5_phase7"
    contract_ref: str = "contract:generic"
    capability_kind_refs: tuple[str, ...] = _CAPABILITY_KIND_BASE
    plugin_kind_ref: str = "PluginKind:generic"
    l3_handoff_ref: str = "l3_handoff:declared"
    l4_handoff_ref: str = "l4_handoff:declared"
    l6_entry_ref: str = "l6_entry:declared"
    boundary_gate_ref: str = "boundary_gate:declared"
    version_ref: str = "version:declared"
    migration_ref: str = "migration:declared"
    compatibility_ref: str = "compatibility:declared"
    validation_ref: str = "validation:declared"
    regression_ref: str = "regression:declared"
    audit_decl_ref: str = "audit:declared"
    contract_binding_digest: str = ""

    def __post_init__(self) -> None:
        _Phase7Base.__post_init__(self)
        for item in fields(self):
            value = getattr(self, item.name)
            if item.name.endswith("_ref") and item.name != "contract_binding_digest":
                ensure_ref_text(value, f"PluginContractBindingDeclaration.{item.name}", required=False)
            elif item.name.endswith("_refs"):
                ensure_ref_items(value, f"PluginContractBindingDeclaration.{item.name}")
        if not self.contract_binding_digest:
            object.__setattr__(self, "contract_binding_digest", phase7_declaration_digest(self, ("contract_binding_digest",)))


@dataclass(frozen=True, slots=True)
class PluginServiceMountBindingDeclaration(_Phase7Base):
    service_mount_binding_ref: str = "service_mount:l5_phase7"
    service_surface_ref: str = "service_surface:declared"
    mount_decl_ref: str = "mount:declared"
    lifecycle_ref: str = "lifecycle:declared"
    health_gate_ref: str = "health_gate:declared"
    isolation_gate_ref: str = "isolation_gate:declared"
    permission_gate_ref: str = "permission_gate:declared"
    resource_gate_ref: str = "resource_gate:declared"
    privacy_gate_ref: str = "privacy_gate:declared"
    audit_gate_ref: str = "audit_gate:declared"
    no_live_service_ref: str = "no_live_service:l5_phase7"
    no_endpoint_ref: str = "no_endpoint:l5_phase7"
    service_mount_digest: str = ""

    def __post_init__(self) -> None:
        _Phase7Base.__post_init__(self)
        for item in fields(self):
            if item.name.endswith("_ref") and item.name != "service_mount_digest":
                ensure_ref_text(getattr(self, item.name), f"PluginServiceMountBindingDeclaration.{item.name}", required=False)
        if has_live_phase7_locator(self) or has_forbidden_phase7_field_name(self):
            raise ValueError("PluginServiceMountBindingDeclaration must not expose service endpoint")
        if not self.service_mount_digest:
            object.__setattr__(self, "service_mount_digest", phase7_declaration_digest(self, ("service_mount_digest",)))


@dataclass(frozen=True, slots=True)
class PluginCapabilityMountBindingDeclaration(_Phase7Base):
    capability_mount_binding_ref: str = "capability_mount:l5_phase7"
    capability_kind_refs: tuple[str, ...] = _CAPABILITY_KIND_BASE
    capability_metadata_ref: str = "capability_metadata:declared"
    capability_contract_ref: str = "capability_contract:declared"
    boundary_gate_ref: str = "boundary_gate:declared"
    l3_handoff_ref: str = "l3_handoff:declared"
    l4_handoff_ref: str = "l4_handoff:declared"
    l6_entry_ref: str = "l6_entry:declared"
    no_tool_schema_release_ref: str = "no_tool_schema_release:l5_phase7"
    no_model_visible_execution_ref: str = "no_model_visible_execution:l5_phase7"
    capability_mount_digest: str = ""

    def __post_init__(self) -> None:
        _Phase7Base.__post_init__(self)
        ensure_ref_items(self.capability_kind_refs, "PluginCapabilityMountBindingDeclaration.capability_kind_refs")
        for item in fields(self):
            if item.name.endswith("_ref") and item.name != "capability_mount_digest":
                ensure_ref_text(getattr(self, item.name), f"PluginCapabilityMountBindingDeclaration.{item.name}", required=False)
        if has_live_phase7_locator(self) or has_forbidden_phase7_field_name(self):
            raise ValueError("PluginCapabilityMountBindingDeclaration must not release tool_schema/function_schema or model-visible execution")
        if not self.capability_mount_digest:
            object.__setattr__(self, "capability_mount_digest", phase7_declaration_digest(self, ("capability_mount_digest",)))


@dataclass(frozen=True, slots=True)
class PluginArtifactProductionMountBindingDeclaration(_Phase7Base):
    production_mount_binding_ref: str = "production_mount:l5_phase7"
    registry_key_ref: str = "registry_key:declared"
    production_plugin_kind_ref: str = "ProductionPlugin"
    artifact_capability_kind_refs: tuple[str, ...] = _CAPABILITY_KIND_PRODUCTION
    product_spec_contract_ref: str = "contract:product_spec"
    build_plan_contract_ref: str = "contract:build_plan"
    artifact_build_contract_ref: str = "contract:artifact_build"
    artifact_validation_contract_ref: str = "contract:artifact_validation"
    artifact_delivery_contract_ref: str = "contract:artifact_delivery"
    repair_rebuild_contract_ref: str = "contract:repair_rebuild"
    artifact_integrity_ref: str = "artifact_integrity:declared"
    artifact_provenance_ref: str = "artifact_provenance:declared"
    artifact_validation_ref: str = "artifact_validation:declared"
    artifact_delivery_boundary_ref: str = "artifact_delivery_boundary:declared"
    l3_handoff_ref: str = "l3_handoff:declared"
    l4_handoff_ref: str = "l4_handoff:declared"
    l6_entry_ref: str = "l6_entry:declared"
    boundary_gate_ref: str = "boundary_gate:declared"
    resource_gate_ref: str = "resource_gate:declared"
    privacy_gate_ref: str = "privacy_gate:declared"
    audit_gate_ref: str = "audit_gate:declared"
    version_gate_ref: str = "version_gate:declared"
    transaction_compensation_ref: str = "transaction_compensation:declared"
    no_live_build_ref: str = "no_live_build:l5_phase7"
    no_live_file_generation_ref: str = "no_live_file_generation:l5_phase7"
    no_live_package_ref: str = "no_live_package:l5_phase7"
    no_live_delivery_ref: str = "no_live_delivery:l5_phase7"
    no_direct_tool_call_ref: str = "no_direct_tool_call:l5_phase7"
    no_direct_l4_adapter_ref: str = "no_direct_l4_adapter:l5_phase7"
    required_policy_refs: tuple[str, ...] = ("policy:production_mount",)
    required_approval_ref: str = "approval:production_mount"
    required_evidence_refs: tuple[str, ...] = ("evidence:production_mount",)
    production_mount_digest: str = ""

    def __post_init__(self) -> None:
        _Phase7Base.__post_init__(self)
        for item in fields(self):
            value = getattr(self, item.name)
            if item.name.endswith("_ref") and item.name != "production_mount_digest":
                ensure_ref_text(value, f"PluginArtifactProductionMountBindingDeclaration.{item.name}", required=False)
            elif item.name.endswith("_refs"):
                ensure_ref_items(value, f"PluginArtifactProductionMountBindingDeclaration.{item.name}")
        if has_live_phase7_locator(self) or has_forbidden_phase7_field_name(self):
            raise ValueError("PluginArtifactProductionMountBindingDeclaration must not expose live production, build, delivery, tool, or L4 action material")
        if not self.production_mount_digest:
            object.__setattr__(self, "production_mount_digest", phase7_declaration_digest(self, ("production_mount_digest",)))


@dataclass(frozen=True, slots=True)
class AffectivePluginMountDeclaration(_Phase7Base):
    affective_mount_ref: str = "affective_mount:declaration_only"
    plugin_kind_ref: str = AFFECTIVE_PLUGIN_KIND_REF
    mount_kind_ref: str = AFFECTIVE_MOUNT_KIND_REF
    capability_kind_refs: tuple[str, ...] = _CAPABILITY_KIND_AFFECTIVE
    modulation_contract_binding_ref: str = "contract_binding:affective_modulation"
    safety_boundary_ref: str = "safety_boundary:affective_plugin"
    audit_binding_ref: str = "audit_binding:affective_plugin"
    public_projection_summary_ref: str = "projection_summary:affective_plugin:redacted"
    l6_handoff_ref: str = "handoff:l5_l6_affective_plugin"
    allowed_modulation_refs: tuple[str, ...] = AFFECTIVE_ALLOWED_MODULATION_REFS
    forbidden_misuse_refs: tuple[str, ...] = AFFECTIVE_FORBIDDEN_MISUSE_REFS
    declaration_not_authorization_ref: str = "declaration_not_authorization:affective_plugin"
    no_direct_tool_call_ref: str = "no_direct_tool_call:affective_plugin"
    no_direct_l4_adapter_ref: str = "no_direct_l4_adapter:affective_plugin"
    no_permission_bypass_ref: str = "no_permission_bypass:affective_plugin"
    no_confirmation_bypass_ref: str = "no_confirmation_bypass:affective_plugin"
    no_core_mutation_ref: str = "no_core_mutation:affective_plugin"
    no_side_effect_ref: str = "no_side_effect:affective_plugin"
    no_memory_mutation_ref: str = "no_memory_mutation:affective_plugin"
    l6_planning_only_ref: str = "l6_planning_only:affective_plugin"
    affective_mount_digest: str = ""

    def __post_init__(self) -> None:
        _Phase7Base.__post_init__(self)
        for item in fields(self):
            value = getattr(self, item.name)
            if item.name.endswith("_ref") and item.name != "affective_mount_digest":
                ensure_ref_text(value, f"AffectivePluginMountDeclaration.{item.name}", required=False)
            elif item.name.endswith("_refs"):
                ensure_ref_items(value, f"AffectivePluginMountDeclaration.{item.name}")
        if self.plugin_kind_ref != AFFECTIVE_PLUGIN_KIND_REF:
            raise ValueError("AffectivePluginMountDeclaration must declare AffectivePlugin kind")
        if self.mount_kind_ref != AFFECTIVE_MOUNT_KIND_REF:
            raise ValueError("AffectivePluginMountDeclaration must declare affective mount kind")
        if set(AFFECTIVE_CAPABILITY_KIND_REFS) - set(self.capability_kind_refs):
            raise ValueError("AffectivePluginMountDeclaration must cover affective capability kinds")
        if set(AFFECTIVE_FORBIDDEN_MISUSE_REFS) - set(self.forbidden_misuse_refs):
            raise ValueError("AffectivePluginMountDeclaration must include affective forbidden misuse refs")
        if has_live_phase7_locator(self) or has_forbidden_phase7_field_name(self):
            raise ValueError("AffectivePluginMountDeclaration must not expose live action material")
        if not self.affective_mount_digest:
            object.__setattr__(self, "affective_mount_digest", phase7_declaration_digest(self, ("affective_mount_digest",)))


@dataclass(frozen=True, slots=True)
class PluginHostGovernanceGateDeclaration(_Phase7Base):
    governance_gate_ref: str = "governance_gate:l5_phase7"
    registry_key_ref: str = "registry_key:declared"
    event_gate_ref: str = "event_gate:declared"
    effect_gate_ref: str = "effect_gate:declared"
    lease_gate_ref: str = "lease_gate:declared"
    policy_gate_ref: str = "policy_gate:declared"
    contract_gate_ref: str = "contract_gate:declared"
    risk_decision_gate_ref: str = "risk_decision_gate:declared"
    human_gate_ref: str = "human_gate:declared"
    audit_evidence_gate_ref: str = "audit_evidence_gate:declared"
    resource_budget_gate_ref: str = "resource_budget_gate:declared"
    privacy_secret_gate_ref: str = "privacy_secret_gate:declared"
    version_migration_gate_ref: str = "version_migration_gate:declared"
    test_validation_regression_gate_ref: str = "test_validation_regression_gate:declared"
    transaction_compensation_gate_ref: str = "transaction_compensation_gate:declared"
    artifact_provenance_integrity_gate_ref: str = "artifact_provenance_integrity_gate:declared"
    deny_by_default_declared: bool = True
    least_privilege_declared: bool = True
    no_bypass_declared: bool = True
    required_policy_refs: tuple[str, ...] = ("policy:governance_gate",)
    required_approval_ref: str = "approval:governance_gate"
    required_evidence_refs: tuple[str, ...] = ("evidence:governance_gate",)
    governance_gate_digest: str = ""

    def __post_init__(self) -> None:
        _Phase7Base.__post_init__(self)
        for item in fields(self):
            value = getattr(self, item.name)
            if item.name.endswith("_ref") and item.name != "governance_gate_digest":
                ensure_ref_text(value, f"PluginHostGovernanceGateDeclaration.{item.name}", required=False)
            elif item.name.endswith("_refs"):
                ensure_ref_items(value, f"PluginHostGovernanceGateDeclaration.{item.name}")
        for name in ("deny_by_default_declared", "least_privilege_declared", "no_bypass_declared"):
            ensure_bool(getattr(self, name), f"PluginHostGovernanceGateDeclaration.{name}")
        if not self.governance_gate_digest:
            object.__setattr__(self, "governance_gate_digest", phase7_declaration_digest(self, ("governance_gate_digest",)))


@dataclass(frozen=True, slots=True)
class PluginPhase7ValidationReport(_Phase7Base):
    report_ref: str = "report:l5_phase7:validation"
    conflict_refs: tuple[str, ...] = field(default_factory=tuple)
    p0_count: int = 0
    p1_count: int = 0
    p2_count: int = 0
    p3_count: int = 0
    passed: bool = True
    blocking_reasons: tuple[str, ...] = field(default_factory=tuple)
    rule_source_ref: str = "rule:l5_phase7"
    detected_by_ref: str = "detector:l5_phase7"
    report_digest: str = ""

    def __post_init__(self) -> None:
        _Phase7Base.__post_init__(self)
        ensure_ref_text(self.report_ref, "PluginPhase7ValidationReport.report_ref")
        ensure_ref_items(self.conflict_refs, "PluginPhase7ValidationReport.conflict_refs")
        ensure_ref_items(self.blocking_reasons, "PluginPhase7ValidationReport.blocking_reasons")
        for name in ("p0_count", "p1_count", "p2_count", "p3_count"):
            if not isinstance(getattr(self, name), int) or getattr(self, name) < 0:
                raise ValueError(f"PluginPhase7ValidationReport.{name} must be non-negative int")
        ensure_bool(self.passed, "PluginPhase7ValidationReport.passed")
        ensure_ref_text(self.rule_source_ref, "PluginPhase7ValidationReport.rule_source_ref")
        ensure_ref_text(self.detected_by_ref, "PluginPhase7ValidationReport.detected_by_ref")
        if not self.report_digest:
            object.__setattr__(self, "report_digest", phase7_declaration_digest(self, ("report_digest",)))


class PluginHostBoundaryGateValidator:
    def check(self, *objects: Any, precheck: PluginGenericHostPrecheckReport | None = None, production_mount_enabled: bool = False) -> PluginPhase7ValidationReport:
        conflicts: list[PluginPhase7Conflict] = []
        if precheck is not None and precheck.result == GENERIC_HOST_BLOCK_TOOL_ONLY:
            conflicts.append(_conflict(PluginPhase7ConflictKind.GENERIC_HOST_TOOL_ONLY_CONFLICT, PluginPhase7ConflictSeverity.P1, "generic_plugin_host_precheck", "generic plugin host precheck is BLOCK_TOOL_ONLY_HOST", precheck.evidence_refs))
        for obj in objects:
            for field_name in _base_missing(obj):
                conflicts.append(_conflict(PluginPhase7ConflictKind.AUDIT_EVIDENCE_CHAIN_MISSING_CONFLICT, PluginPhase7ConflictSeverity.P1, field_name, f"{field_name} is required", getattr(obj, "evidence_refs", ())))
            if has_forbidden_phase7_method(obj) or has_forbidden_phase7_field_name(obj) or has_live_phase7_locator(obj):
                conflicts.append(_conflict(PluginPhase7ConflictKind.LIVE_ACTION_CONFLICT, PluginPhase7ConflictSeverity.P0, obj.__class__.__name__, "declaration contains live action, executable locator, or forbidden field", getattr(obj, "evidence_refs", ())))
            if isinstance(obj, PluginL3HandoffDeclaration):
                _require_ref(obj, "orchestration_boundary_ref", conflicts, PluginPhase7ConflictKind.L3_HANDOFF_MISSING_ORCHESTRATION_BOUNDARY_CONFLICT)
            if isinstance(obj, PluginL4AdapterHandoffDeclaration):
                if not _has_refs(obj.adapter_boundary_refs):
                    conflicts.append(_conflict(PluginPhase7ConflictKind.L4_HANDOFF_MISSING_ADAPTER_BOUNDARY_CONFLICT, PluginPhase7ConflictSeverity.P1, "adapter_boundary_refs", "adapter boundary refs are required", obj.evidence_refs))
            if isinstance(obj, PluginL6EntryDeclaration):
                _require_ref(obj, "entry_contract_ref", conflicts, PluginPhase7ConflictKind.L6_ENTRY_MISSING_CONTRACT_CONFLICT)
                if not obj.implementation_absent_required:
                    conflicts.append(_conflict(PluginPhase7ConflictKind.L6_IMPLEMENTATION_IN_L5_CONFLICT, PluginPhase7ConflictSeverity.P0, "implementation_absent_required", "L6 implementation must be absent in L5", obj.evidence_refs))
            if isinstance(obj, PluginRouteDeclaration):
                _require_ref(obj, "contract_ref", conflicts, PluginPhase7ConflictKind.ROUTE_MISSING_CONTRACT_CONFLICT)
            if isinstance(obj, PluginServiceMountBindingDeclaration):
                _require_ref(obj, "no_endpoint_ref", conflicts, PluginPhase7ConflictKind.SERVICE_MOUNT_EXPOSES_ENDPOINT_CONFLICT)
            if isinstance(obj, PluginCapabilityMountBindingDeclaration):
                _require_ref(obj, "boundary_gate_ref", conflicts, PluginPhase7ConflictKind.CAPABILITY_MOUNT_MISSING_BOUNDARY_GATE_CONFLICT)
            if isinstance(obj, PluginHostGovernanceGateDeclaration):
                for name in (
                    "event_gate_ref",
                    "effect_gate_ref",
                    "lease_gate_ref",
                    "policy_gate_ref",
                    "contract_gate_ref",
                    "risk_decision_gate_ref",
                    "human_gate_ref",
                    "audit_evidence_gate_ref",
                    "resource_budget_gate_ref",
                    "privacy_secret_gate_ref",
                    "version_migration_gate_ref",
                    "test_validation_regression_gate_ref",
                    "transaction_compensation_gate_ref",
                    "artifact_provenance_integrity_gate_ref",
                ):
                    _require_ref(obj, name, conflicts, PluginPhase7ConflictKind.GOVERNANCE_MISSING_GATE_CONFLICT, PluginPhase7ConflictSeverity.P1 if production_mount_enabled else PluginPhase7ConflictSeverity.P2)
            if isinstance(obj, AffectivePluginMountDeclaration):
                if precheck is None or precheck.result == GENERIC_HOST_BLOCK_TOOL_ONLY:
                    conflicts.append(_conflict(PluginPhase7ConflictKind.GENERIC_HOST_TOOL_ONLY_CONFLICT, PluginPhase7ConflictSeverity.P1, "affective_mount", "affective mount requires generic host support", obj.evidence_refs))
                for name, kind in (
                    ("modulation_contract_binding_ref", PluginPhase7ConflictKind.AFFECTIVE_MOUNT_MISSING_CONTRACT_CONFLICT),
                    ("safety_boundary_ref", PluginPhase7ConflictKind.AFFECTIVE_MOUNT_MISSING_SAFETY_BOUNDARY_CONFLICT),
                    ("audit_binding_ref", PluginPhase7ConflictKind.AFFECTIVE_MOUNT_MISSING_AUDIT_BINDING_CONFLICT),
                ):
                    _require_ref(obj, name, conflicts, kind)
            if isinstance(obj, PluginArtifactProductionMountBindingDeclaration):
                if precheck is None or precheck.result == GENERIC_HOST_BLOCK_TOOL_ONLY:
                    conflicts.append(_conflict(PluginPhase7ConflictKind.PRODUCTION_MOUNT_ADDED_WITHOUT_GENERIC_HOST_SUPPORT_CONFLICT, PluginPhase7ConflictSeverity.P1, "production_mount", "production mount requires generic host precheck pass", obj.evidence_refs))
                for name, kind in (
                    ("product_spec_contract_ref", PluginPhase7ConflictKind.PRODUCTION_MOUNT_MISSING_PRODUCT_SPEC_CONTRACT_CONFLICT),
                    ("build_plan_contract_ref", PluginPhase7ConflictKind.PRODUCTION_MOUNT_MISSING_BUILD_PLAN_CONTRACT_CONFLICT),
                    ("artifact_build_contract_ref", PluginPhase7ConflictKind.PRODUCTION_MOUNT_MISSING_ARTIFACT_BUILD_CONTRACT_CONFLICT),
                    ("artifact_validation_contract_ref", PluginPhase7ConflictKind.PRODUCTION_MOUNT_MISSING_VALIDATION_CONTRACT_CONFLICT),
                    ("artifact_delivery_contract_ref", PluginPhase7ConflictKind.PRODUCTION_MOUNT_MISSING_DELIVERY_CONTRACT_CONFLICT),
                    ("artifact_integrity_ref", PluginPhase7ConflictKind.PRODUCTION_MOUNT_MISSING_ARTIFACT_INTEGRITY_CONFLICT),
                    ("artifact_provenance_ref", PluginPhase7ConflictKind.PRODUCTION_MOUNT_MISSING_ARTIFACT_PROVENANCE_CONFLICT),
                    ("transaction_compensation_ref", PluginPhase7ConflictKind.PRODUCTION_MOUNT_MISSING_TRANSACTION_COMPENSATION_CONFLICT),
                ):
                    _require_ref(obj, name, conflicts, kind)
        p0, p1, p2, p3 = _count_conflicts(tuple(conflicts))
        return PluginPhase7ValidationReport(
            conflict_refs=_conflict_refs(tuple(conflicts)),
            p0_count=p0,
            p1_count=p1,
            p2_count=p2,
            p3_count=p3,
            passed=p0 == 0 and p1 == 0,
            blocking_reasons=tuple(item.message for item in conflicts if item.blocking),
            evidence_refs=tuple(ref for obj in objects for ref in getattr(obj, "evidence_refs", ())) or ("evidence:l5_phase7_validation",),
        )


PluginCrossLayerHandoffValidator = PluginHostBoundaryGateValidator
PluginL3HandoffValidator = PluginHostBoundaryGateValidator
PluginL4AdapterHandoffValidator = PluginHostBoundaryGateValidator
PluginL6EntryValidator = PluginHostBoundaryGateValidator
PluginRouteValidator = PluginHostBoundaryGateValidator
PluginHookValidator = PluginHostBoundaryGateValidator
PluginEventSubscriptionValidator = PluginHostBoundaryGateValidator
PluginContractBindingValidator = PluginHostBoundaryGateValidator
PluginServiceMountBindingValidator = PluginHostBoundaryGateValidator
PluginCapabilityMountBindingValidator = PluginHostBoundaryGateValidator
PluginArtifactProductionMountValidator = PluginHostBoundaryGateValidator
PluginAffectiveMountValidator = PluginHostBoundaryGateValidator
PluginHostGovernanceGateValidator = PluginHostBoundaryGateValidator


@dataclass(frozen=True, slots=True)
class PluginPhase7QualityGateDecision:
    decision_ref: str
    p0_count: int = 0
    p1_count: int = 0
    p2_count: int = 0
    p3_count: int = 0
    generic_plugin_host_precheck_passed: bool = False
    generic_plugin_host_precheck_result: str = GENERIC_HOST_BLOCK_TOOL_ONLY
    production_mount_enabled: bool = False
    production_mount_blocked_reason_refs: tuple[str, ...] = field(default_factory=tuple)
    host_boundary_gate_passed: bool = False
    l3_handoff_boundary_passed: bool = False
    l4_handoff_boundary_passed: bool = False
    l6_entry_boundary_passed: bool = False
    route_declaration_passed: bool = False
    hook_declaration_passed: bool = False
    event_subscription_declaration_passed: bool = False
    contract_binding_passed: bool = False
    service_mount_binding_passed: bool = False
    capability_mount_binding_passed: bool = False
    production_mount_binding_passed: bool = False
    governance_gate_passed: bool = False
    no_l3_bypass_passed: bool = False
    no_l4_bypass_passed: bool = False
    no_l6_implementation_passed: bool = False
    no_live_plugin_load_passed: bool = False
    no_live_tool_call_passed: bool = False
    no_live_artifact_build_passed: bool = False
    no_live_delivery_passed: bool = False
    product_artifact_factory_mount_ready: bool = False
    phase6_compatibility_passed: bool = False
    phase5_compatibility_passed: bool = False
    phase4_lifecycle_compatibility_passed: bool = False
    phase3_registry_compatibility_passed: bool = False
    public_projection_safety_passed: bool = False
    public_projection_second_leak_test_passed: bool = False
    audit_evidence_chain_passed: bool = False
    forbidden_scan_passed: bool = False
    compileall_passed: bool = False
    collect_only_passed: bool = False
    targeted_pytest_passed: bool = False
    plugin_host_subset_passed: bool = False
    plugin_host_subset_non_empty: bool = False
    full_pytest_passed: bool = False
    hash_compare_passed: bool = False
    test_inventory_compare_passed: bool = False
    allow_enter_l5_phase8: bool = False
    blocking_reasons: tuple[str, ...] = field(default_factory=tuple)
    evidence_index_refs: tuple[str, ...] = field(default_factory=tuple)
    regression_index_refs: tuple[str, ...] = field(default_factory=tuple)
    rule_source_ref: str = "rule:l5_phase7_quality_gate"
    detected_by_ref: str = "detector:l5_phase7_quality_gate"
    actor_ref: str = "actor:l5_phase7"
    scope_ref: str = "scope:l5_phase7"
    trace_ref: str = "trace:l5_phase7_quality_gate"
    policy_refs: tuple[str, ...] = ("policy:l5_phase7_quality_gate",)
    approval_ref: str = "approval:l5_phase7_quality_gate"
    provenance_refs: tuple[str, ...] = ("provenance:l5_phase7_quality_gate",)
    responsibility_chain_ref: str = "responsibility:l5_phase7_quality_gate"
    accountability_ref: str = "accountability:l5_phase7_quality_gate"
    tamper_evidence_ref: str = "tamper:l5_phase7_quality_gate"
    phase: str = PHASE7_PHASE
    quality_gate_digest: str = ""

    def __post_init__(self) -> None:
        ensure_ref_text(self.decision_ref, "PluginPhase7QualityGateDecision.decision_ref")
        if self.generic_plugin_host_precheck_result not in (GENERIC_HOST_PASS, GENERIC_HOST_PASS_WITH_COMPATIBLE_EXTENSION, GENERIC_HOST_BLOCK_TOOL_ONLY):
            raise ValueError("PluginPhase7QualityGateDecision.generic_plugin_host_precheck_result invalid")
        for name in ("p0_count", "p1_count", "p2_count", "p3_count"):
            if not isinstance(getattr(self, name), int) or getattr(self, name) < 0:
                raise ValueError(f"PluginPhase7QualityGateDecision.{name} must be non-negative int")
        boolean_fields = (
            "generic_plugin_host_precheck_passed",
            "production_mount_enabled",
            "host_boundary_gate_passed",
            "l3_handoff_boundary_passed",
            "l4_handoff_boundary_passed",
            "l6_entry_boundary_passed",
            "route_declaration_passed",
            "hook_declaration_passed",
            "event_subscription_declaration_passed",
            "contract_binding_passed",
            "service_mount_binding_passed",
            "capability_mount_binding_passed",
            "production_mount_binding_passed",
            "governance_gate_passed",
            "no_l3_bypass_passed",
            "no_l4_bypass_passed",
            "no_l6_implementation_passed",
            "no_live_plugin_load_passed",
            "no_live_tool_call_passed",
            "no_live_artifact_build_passed",
            "no_live_delivery_passed",
            "product_artifact_factory_mount_ready",
            "phase6_compatibility_passed",
            "phase5_compatibility_passed",
            "phase4_lifecycle_compatibility_passed",
            "phase3_registry_compatibility_passed",
            "public_projection_safety_passed",
            "public_projection_second_leak_test_passed",
            "audit_evidence_chain_passed",
            "forbidden_scan_passed",
            "compileall_passed",
            "collect_only_passed",
            "targeted_pytest_passed",
            "plugin_host_subset_passed",
            "plugin_host_subset_non_empty",
            "full_pytest_passed",
            "hash_compare_passed",
            "test_inventory_compare_passed",
        )
        for name in boolean_fields:
            ensure_bool(getattr(self, name), f"PluginPhase7QualityGateDecision.{name}")
        for name in ("production_mount_blocked_reason_refs", "blocking_reasons", "evidence_index_refs", "regression_index_refs", "policy_refs", "provenance_refs"):
            ensure_ref_items(getattr(self, name), f"PluginPhase7QualityGateDecision.{name}")
        for name in ("rule_source_ref", "detected_by_ref", "actor_ref", "scope_ref", "trace_ref", "approval_ref", "responsibility_chain_ref", "accountability_ref", "tamper_evidence_ref", "phase"):
            ensure_ref_text(getattr(self, name), f"PluginPhase7QualityGateDecision.{name}", required=False)
        required = (
            self.p0_count == 0,
            self.p1_count == 0,
            self.generic_plugin_host_precheck_passed,
            self.generic_plugin_host_precheck_result != GENERIC_HOST_BLOCK_TOOL_ONLY,
            (not self.production_mount_enabled) or (self.production_mount_binding_passed and self.product_artifact_factory_mount_ready),
            self.host_boundary_gate_passed,
            self.l3_handoff_boundary_passed,
            self.l4_handoff_boundary_passed,
            self.l6_entry_boundary_passed,
            self.route_declaration_passed,
            self.hook_declaration_passed,
            self.event_subscription_declaration_passed,
            self.contract_binding_passed,
            self.service_mount_binding_passed,
            self.capability_mount_binding_passed,
            self.governance_gate_passed,
            self.no_l3_bypass_passed,
            self.no_l4_bypass_passed,
            self.no_l6_implementation_passed,
            self.no_live_plugin_load_passed,
            self.no_live_tool_call_passed,
            self.no_live_artifact_build_passed,
            self.no_live_delivery_passed,
            self.phase6_compatibility_passed,
            self.public_projection_safety_passed,
            self.audit_evidence_chain_passed,
            self.forbidden_scan_passed,
            self.compileall_passed,
            self.collect_only_passed,
            self.targeted_pytest_passed,
            self.plugin_host_subset_passed,
            self.plugin_host_subset_non_empty,
            self.full_pytest_passed,
            self.hash_compare_passed,
            self.test_inventory_compare_passed,
        )
        object.__setattr__(self, "allow_enter_l5_phase8", all(required))
        if not self.quality_gate_digest:
            object.__setattr__(self, "quality_gate_digest", phase7_declaration_digest(self, ("quality_gate_digest",)))


class PluginPhase7QualityGate:
    def decide(self, **kwargs: Any) -> PluginPhase7QualityGateDecision:
        return PluginPhase7QualityGateDecision(**kwargs)


@dataclass(frozen=True, slots=True)
class PluginPhase7PublicProjection:
    projection_ref: str
    generic_plugin_host_precheck_summary: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    host_boundary_gate_summary: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    l3_handoff_summary: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    l4_handoff_summary: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    l6_entry_summary: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    route_summary: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    hook_summary: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    event_subscription_summary: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    contract_binding_summary: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    service_mount_binding_summary: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    capability_mount_binding_summary: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    production_mount_binding_summary: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    governance_gate_summary: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    phase7_quality_gate_summary: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    conflict_counts: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    risk_tags: tuple[str, ...] = ("declaration_only", "minimal_disclosure")
    status_text: str = "declaration_only"
    redacted_evidence_refs: tuple[str, ...] = ("evidence:redacted:l5_phase7",)
    trace_ref: str = "trace:l5_phase7_projection"
    responsibility_chain_ref: str = "responsibility:l5_phase7_projection"
    redaction_state: str = "redacted"
    projection_digest: str = ""
    phase: str = PHASE7_PHASE

    def __post_init__(self) -> None:
        ensure_ref_text(self.projection_ref, "PluginPhase7PublicProjection.projection_ref")
        for name in ("risk_tags", "redacted_evidence_refs"):
            ensure_ref_items(getattr(self, name), f"PluginPhase7PublicProjection.{name}")
        for name in ("status_text", "trace_ref", "responsibility_chain_ref", "redaction_state", "phase"):
            ensure_ref_text(getattr(self, name), f"PluginPhase7PublicProjection.{name}", required=False)
        tuple_fields = (
            "generic_plugin_host_precheck_summary",
            "host_boundary_gate_summary",
            "l3_handoff_summary",
            "l4_handoff_summary",
            "l6_entry_summary",
            "route_summary",
            "hook_summary",
            "event_subscription_summary",
            "contract_binding_summary",
            "service_mount_binding_summary",
            "capability_mount_binding_summary",
            "production_mount_binding_summary",
            "governance_gate_summary",
            "phase7_quality_gate_summary",
            "conflict_counts",
        )
        for name in tuple_fields:
            if not isinstance(getattr(self, name), tuple):
                raise ValueError(f"PluginPhase7PublicProjection.{name} must be tuple")
        if not phase7_public_text_is_safe(self):
            raise ValueError("PluginPhase7PublicProjection must not expose complete plans, paths, endpoints, tool schemas, or executable artifacts")
        if not self.projection_digest:
            object.__setattr__(self, "projection_digest", phase7_declaration_digest(self, ("projection_digest",)))


class PluginPhase7ProjectionBuilder:
    def make_projection(self, *, precheck: PluginGenericHostPrecheckReport, quality_gate: PluginPhase7QualityGateDecision, production_mount: PluginArtifactProductionMountBindingDeclaration | None = None) -> PluginPhase7PublicProjection:
        production_summary: tuple[tuple[str, str], ...] = ()
        if production_mount is not None:
            production_summary = (
                ("production_mount_binding_ref", production_mount.production_mount_binding_ref),
                ("artifact_capability_count", str(len(production_mount.artifact_capability_kind_refs))),
                ("artifact_integrity_ref", production_mount.artifact_integrity_ref),
                ("artifact_provenance_ref", production_mount.artifact_provenance_ref),
                ("redaction_state", "redacted"),
            )
        return PluginPhase7PublicProjection(
            projection_ref="projection:l5_phase7",
            generic_plugin_host_precheck_summary=(("result", precheck.result), ("plugin_kind_count", str(len(precheck.plugin_kind_support_refs))), ("capability_kind_count", str(len(precheck.capability_kind_support_refs)))),
            production_mount_binding_summary=production_summary,
            phase7_quality_gate_summary=(("allow_enter_l5_phase8", str(quality_gate.allow_enter_l5_phase8)), ("p0_count", str(quality_gate.p0_count)), ("p1_count", str(quality_gate.p1_count))),
            redacted_evidence_refs=quality_gate.evidence_index_refs or ("evidence:redacted:l5_phase7",),
            trace_ref=quality_gate.trace_ref,
            responsibility_chain_ref=quality_gate.responsibility_chain_ref,
        )


@dataclass(frozen=True, slots=True)
class PluginPhase7AuditIndex:
    audit_index_ref: str
    phase: str = PHASE7_PHASE
    host_boundary_gate_refs: tuple[str, ...] = field(default_factory=tuple)
    l3_handoff_refs: tuple[str, ...] = field(default_factory=tuple)
    l4_handoff_refs: tuple[str, ...] = field(default_factory=tuple)
    l6_entry_refs: tuple[str, ...] = field(default_factory=tuple)
    route_refs: tuple[str, ...] = field(default_factory=tuple)
    hook_refs: tuple[str, ...] = field(default_factory=tuple)
    event_subscription_refs: tuple[str, ...] = field(default_factory=tuple)
    contract_binding_refs: tuple[str, ...] = field(default_factory=tuple)
    service_mount_binding_refs: tuple[str, ...] = field(default_factory=tuple)
    capability_mount_binding_refs: tuple[str, ...] = field(default_factory=tuple)
    production_mount_binding_refs: tuple[str, ...] = field(default_factory=tuple)
    affective_mount_binding_refs: tuple[str, ...] = field(default_factory=tuple)
    governance_gate_refs: tuple[str, ...] = field(default_factory=tuple)
    validation_report_refs: tuple[str, ...] = field(default_factory=tuple)
    conflict_report_refs: tuple[str, ...] = field(default_factory=tuple)
    quality_gate_decision_refs: tuple[str, ...] = field(default_factory=tuple)
    public_projection_refs: tuple[str, ...] = field(default_factory=tuple)
    event_refs: tuple[str, ...] = ("event:l5_phase7",)
    evidence_refs: tuple[str, ...] = ("evidence:l5_phase7",)
    provenance_refs: tuple[str, ...] = ("provenance:l5_phase7",)
    actor_ref: str = "actor:l5_phase7"
    scope_ref: str = "scope:l5_phase7"
    trace_ref: str = "trace:l5_phase7_audit"
    policy_refs: tuple[str, ...] = ("policy:l5_phase7_audit",)
    approval_ref: str = "approval:l5_phase7_audit"
    responsibility_chain_ref: str = "responsibility:l5_phase7_audit"
    accountability_ref: str = "accountability:l5_phase7_audit"
    tamper_evidence_ref: str = "tamper:l5_phase7_audit"
    audit_digest: str = ""

    def __post_init__(self) -> None:
        ensure_ref_text(self.audit_index_ref, "PluginPhase7AuditIndex.audit_index_ref")
        ensure_ref_text(self.phase, "PluginPhase7AuditIndex.phase")
        for item in fields(self):
            value = getattr(self, item.name)
            if item.name.endswith("_refs"):
                ensure_ref_items(value, f"PluginPhase7AuditIndex.{item.name}")
            elif item.name.endswith("_ref") and item.name != "audit_digest":
                ensure_ref_text(value, f"PluginPhase7AuditIndex.{item.name}", required=False)
        if not self.audit_digest:
            object.__setattr__(self, "audit_digest", phase7_declaration_digest(self, ("audit_digest",)))


class PluginPhase7AuditIndexBuilder:
    def make_index(self, *, boundary_gate: PluginHostBoundaryGateDeclaration, l3_handoff: PluginL3HandoffDeclaration, l4_handoff: PluginL4AdapterHandoffDeclaration, l6_entry: PluginL6EntryDeclaration, quality_gate: PluginPhase7QualityGateDecision, production_mount: PluginArtifactProductionMountBindingDeclaration | None = None, affective_mount: AffectivePluginMountDeclaration | None = None) -> PluginPhase7AuditIndex:
        production_refs = (production_mount.production_mount_binding_ref,) if production_mount is not None else ()
        affective_refs = (affective_mount.affective_mount_ref,) if affective_mount is not None else ()
        return PluginPhase7AuditIndex(
            audit_index_ref="audit_index:l5_phase7",
            host_boundary_gate_refs=(boundary_gate.host_boundary_gate_ref,),
            l3_handoff_refs=(l3_handoff.l3_handoff_ref,),
            l4_handoff_refs=(l4_handoff.l4_handoff_ref,),
            l6_entry_refs=(l6_entry.l6_entry_ref,),
            production_mount_binding_refs=production_refs,
            affective_mount_binding_refs=affective_refs,
            quality_gate_decision_refs=(quality_gate.decision_ref,),
            evidence_refs=quality_gate.evidence_index_refs or ("evidence:l5_phase7_audit",),
            provenance_refs=quality_gate.provenance_refs,
            actor_ref=quality_gate.actor_ref,
            scope_ref=quality_gate.scope_ref,
            trace_ref=quality_gate.trace_ref,
            policy_refs=quality_gate.policy_refs,
            approval_ref=quality_gate.approval_ref,
            responsibility_chain_ref=quality_gate.responsibility_chain_ref,
            accountability_ref=quality_gate.accountability_ref,
            tamper_evidence_ref=quality_gate.tamper_evidence_ref,
        )


@dataclass(frozen=True, slots=True)
class L5Phase7InvariantSuite:
    suite_ref: str = "invariant_suite:l5_phase7"
    generic_plugin_host_precheck_required: bool = True
    no_l3_direct_execution: bool = True
    no_l4_direct_adapter_call: bool = True
    no_l6_implementation: bool = True
    no_live_artifact_build: bool = True
    no_live_delivery: bool = True
    production_mount_conditional_only: bool = True
    affective_mount_declaration_only: bool = True
    affective_mount_l6_planning_only: bool = True
    affective_mount_not_authorization: bool = True

    def __post_init__(self) -> None:
        ensure_ref_text(self.suite_ref, "L5Phase7InvariantSuite.suite_ref")
        for item in fields(self):
            if item.name != "suite_ref":
                ensure_bool(getattr(self, item.name), f"L5Phase7InvariantSuite.{item.name}")


__all__ = (
    "PHASE7_PHASE",
    "GENERIC_HOST_PASS",
    "GENERIC_HOST_PASS_WITH_COMPATIBLE_EXTENSION",
    "GENERIC_HOST_BLOCK_TOOL_ONLY",
    "L5Phase7InvariantSuite",
    "PluginGenericHostPrecheckReport",
    "PluginGenericHostPrecheckValidator",
    "PluginHostBoundaryGateDeclaration",
    "PluginL3HandoffDeclaration",
    "PluginL4AdapterHandoffDeclaration",
    "PluginL6EntryDeclaration",
    "PluginRouteDeclaration",
    "PluginHookDeclaration",
    "PluginEventSubscriptionDeclaration",
    "PluginContractBindingDeclaration",
    "PluginServiceMountBindingDeclaration",
    "PluginCapabilityMountBindingDeclaration",
    "PluginArtifactProductionMountBindingDeclaration",
    "AffectivePluginMountDeclaration",
    "PluginHostGovernanceGateDeclaration",
    "PluginPhase7Conflict",
    "PluginPhase7ConflictKind",
    "PluginPhase7ConflictSeverity",
    "PluginPhase7ValidationReport",
    "PluginHostBoundaryGateValidator",
    "PluginCrossLayerHandoffValidator",
    "PluginL3HandoffValidator",
    "PluginL4AdapterHandoffValidator",
    "PluginL6EntryValidator",
    "PluginRouteValidator",
    "PluginHookValidator",
    "PluginEventSubscriptionValidator",
    "PluginContractBindingValidator",
    "PluginServiceMountBindingValidator",
    "PluginCapabilityMountBindingValidator",
    "PluginArtifactProductionMountValidator",
    "PluginAffectiveMountValidator",
    "PluginHostGovernanceGateValidator",
    "PluginPhase7QualityGate",
    "PluginPhase7QualityGateDecision",
    "PluginPhase7PublicProjection",
    "PluginPhase7ProjectionBuilder",
    "PluginPhase7AuditIndex",
    "PluginPhase7AuditIndexBuilder",
    "has_forbidden_phase7_field_name",
    "has_forbidden_phase7_method",
    "has_live_phase7_locator",
    "phase7_declaration_digest",
    "phase7_public_text_is_safe",
)
