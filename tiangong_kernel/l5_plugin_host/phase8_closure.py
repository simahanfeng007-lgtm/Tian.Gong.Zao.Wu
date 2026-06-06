"""L5 phase 8 final closure, public projection, and L5-to-L6 handoff freeze.

This module is intentionally inert. It provides declaration-only closure
records, final public projection summaries, governance/readiness matrices,
quality-gate decisions, and audit indexes for the L5 plugin host final freeze.
It does not load plugins, call L3, call L4 adapters, release tool schemas,
create routes, generate files, build artifacts, deliver artifacts, issue
permits, create leases, create tickets, mint tokens, run health checks, modify
registries, or implement L6 plugins.
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields, is_dataclass
from enum import Enum
import re
from typing import Any

from ._common import ensure_bool, ensure_ref_items, ensure_ref_text, ensure_short_text, stable_digest, stable_primitive
from .phase7_boundary_gate import (
    GENERIC_HOST_BLOCK_TOOL_ONLY,
    GENERIC_HOST_PASS,
    GENERIC_HOST_PASS_WITH_COMPATIBLE_EXTENSION,
)
from .affective_plugin_declaration import (
    AFFECTIVE_ALLOWED_MODULATION_REFS,
    AFFECTIVE_CAPABILITY_KIND_REFS,
    AFFECTIVE_FORBIDDEN_MISUSE_REFS,
    AFFECTIVE_PLUGIN_KIND_REF,
)

PHASE8_PHASE = "L5_PHASE8_FINAL_FREEZE"
L5_FINAL_PHASE = "L5_FINAL"

_PHASE_REFS = (
    "phase:l5_phase1",
    "phase:l5_phase2",
    "phase:l5_phase3",
    "phase:l5_phase4",
    "phase:l5_phase5",
    "phase:l5_phase6",
    "phase:l5_phase7",
)

_CORE_GOVERNANCE_GATES = (
    "gate:event",
    "gate:effect",
    "gate:lease",
    "gate:policy",
    "gate:contract",
    "gate:risk_decision",
    "gate:human_gate",
    "gate:audit_evidence",
    "gate:resource_budget",
    "gate:privacy_secret",
    "gate:version_migration",
    "gate:test_validation_regression",
    "gate:transaction_compensation",
    "gate:artifact_provenance_integrity",
    "gate:context_safety_boundary",
    "gate:belief_event_precedence",
    "gate:world_state_evidence_staleness",
    "gate:tool_output_demotion",
    "gate:model_output_demotion",
    "gate:memory_injection_boundary",
    "gate:context_pollution_review",
    "gate:message_envelope_first",
    "gate:conversation_channel_protocol",
    "gate:ack_nack_result_return",
    "gate:self_healing_recovery_plan",
    "gate:self_evolution_commit_boundary",
    "gate:memory_forgetting_governance",
    "gate:skill_tool_release_boundary",
)

_GENERAL_PLUGIN_KINDS = (
    "ToolPlugin",
    "SkillPlugin",
    "MemoryPlugin",
    "PolicyPlugin",
    "AdapterPlugin",
    "GovernancePlugin",
    "ObservationPlugin",
    "CommunicationHandoffPlugin",
    "SelfHealingPlugin",
    "SelfEvolutionPlugin",
    "MemoryGovernancePlugin",
    "ForgettingPlugin",
)

_PRODUCTION_PLUGIN_KINDS = (
    "ProductionPlugin",
    "ArtifactFactoryPlugin",
    "ProductBuilderPlugin",
    "DeliveryPlugin",
    "ValidationPlugin",
)
_AFFECTIVE_PLUGIN_KINDS = ("AffectivePlugin",)

_GENERAL_CAPABILITY_KINDS = (
    "ToolCapability",
    "SkillCapability",
    "MemoryCapability",
    "PolicyCapability",
    "AdapterCapability",
    "GovernanceCapability",
    "ObservationCapability",
    "CommunicationHandoffCapability",
    "SelfHealingCapability",
    "SelfEvolutionCapability",
    "MemoryGovernanceCapability",
    "ForgettingCapability",
    "RetentionCapability",
    "DeletionTombstoneCapability",
    "MemoryPrivacyBoundaryCapability",
)

_PRODUCTION_CAPABILITY_KINDS = (
    "ArtifactFactoryCapability",
    "ProductBuilderCapability",
    "ProductSpecCapability",
    "BuildPlanCapability",
    "ArtifactBuildCapability",
    "ArtifactValidationCapability",
    "ArtifactDeliveryCapability",
    "RepairAndRebuildCapability",
)
_AFFECTIVE_CAPABILITY_KINDS = AFFECTIVE_CAPABILITY_KIND_REFS

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
        "callable_ref",
        "handler",
        "endpoint",
        "artifact_output_path",
        "package_path",
        "repository_path",
        "deploy_target",
        "external_account_id",
        "build_command",
        "validation_command",
        "delivery_command",
        "module_path",
        "import_path",
        "entry_point",
        "url",
        "socket",
        "database_uri",
        "raw_credential",
        "secret_handle",
        "plaintext_user_identity",
        "plaintext_identity",
        "raw_manifest",
        "raw_registry_record",
        "raw_declaration",
        "raw_context",
        "raw_memory",
        "raw_model_output",
        "raw_tool_output",
        "credential_handle",
        "path",
        "permit_object",
        "lease_object",
        "confirmation_ticket_object",
    )
)

_LIVE_TEXT_FRAGMENTS = (
    "://",
    "http://",
    "https://",
    "file://",
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
    "BEGIN PRIVATE KEY",
    "BEGIN CERTIFICATE",
    "tool_schema",
    "function_schema",
    "callable_ref",
    "build_command",
    "delivery_command",
    "validation_command",
    "artifact_output_path",
    "deploy_target",
    "secret_value",
    "api_key_value",
    "password_value",
    "token_value",
    "raw credential",
    "raw_manifest",
    "raw_registry_record",
    "raw_declaration",
    "plaintext_identity",
    "plaintext_user_identity",
    "/mnt/",
    "/home/",
    "/var/",
    "/etc/",
)

_LIVE_PATH_RE = re.compile(r"(^|[\s'\"=])([A-Za-z]:\\|\\\\[^\\]+\\[^\\]+|/(?:mnt|home|var|etc|tmp)/)", re.IGNORECASE)
_SECRET_LIKE_RE = re.compile(r"(sk-[A-Za-z0-9_-]{8,}|Bearer\s+[A-Za-z0-9._-]+|AKIA[0-9A-Z]{8,}|(?:password|api[_-]?key|token|secret)\s*=)", re.IGNORECASE)
_REDACTED_EVIDENCE_PREFIXES = ("evidence:redacted:", "redacted_evidence:", "redacted:")
_AFFECTIVE_L6_FORBIDDEN_MISUSE_REFS = frozenset(AFFECTIVE_FORBIDDEN_MISUSE_REFS)
_REQUIRED_L6_FORBIDDEN_MISUSE_REFS = frozenset(
    (
        "forbid:l5_declaration_as_executor",
        "forbid:l5_handoff_as_l3_l4_call",
        "forbid:l5_l6_entry_as_plugin_entry",
        "forbid:route_as_live_router",
        "forbid:hook_as_callback",
        "forbid:event_subscription_as_live_subscription",
        "forbid:capability_mount_as_tool_schema_release",
        "forbid:artifact_production_mount_as_builder",
        "forbid:direct_file_generation",
        "forbid:l1_l4_governance_bypass",
        "forbid:direct_tool_or_adapter_call",
        "forbid:l5_freeze_as_authorization",
        *_AFFECTIVE_L6_FORBIDDEN_MISUSE_REFS,
    )
)


class L5FinalConflictSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    P3 = "p3"
    P2 = "p2"
    P1 = "p1"
    P0 = "p0"


class L5FinalConflictKind(str, Enum):
    L5_PHASE_MISSING_HANDOFF_CONFLICT = "l5_phase_missing_handoff_conflict"
    L5_PHASE_MISSING_QUALITY_GATE_CONFLICT = "l5_phase_missing_quality_gate_conflict"
    L5_PHASE_MISSING_VALIDATION_REPORT_CONFLICT = "l5_phase_missing_validation_report_conflict"
    L5_PHASE_MISSING_TEST_REPORT_CONFLICT = "l5_phase_missing_test_report_conflict"
    L5_PHASE_MISSING_FORBIDDEN_SCAN_CONFLICT = "l5_phase_missing_forbidden_scan_conflict"
    L5_PHASE_MISSING_HASH_COMPARE_CONFLICT = "l5_phase_missing_hash_compare_conflict"
    L5_PHASE_MISSING_ZIP_INTEGRITY_CONFLICT = "l5_phase_missing_zip_integrity_conflict"
    L5_FINAL_PUBLIC_PROJECTION_MISSING_CONFLICT = "l5_final_public_projection_missing_conflict"
    L5_FINAL_PUBLIC_PROJECTION_LEAK_CONFLICT = "l5_final_public_projection_leak_conflict"
    L5_L6_HANDOFF_FREEZE_MISSING_CONFLICT = "l5_l6_handoff_freeze_missing_conflict"
    L5_L6_HANDOFF_ALLOWS_EXECUTION_CONFLICT = "l5_l6_handoff_allows_execution_conflict"
    L5_GOVERNANCE_MATRIX_MISSING_GATE_CONFLICT = "l5_governance_matrix_missing_gate_conflict"
    L5_CAPABILITY_READINESS_UNKNOWN_CONFLICT = "l5_capability_readiness_unknown_conflict"
    L5_GENERIC_PLUGIN_HOST_PRECHECK_MISSING_CONFLICT = "l5_generic_plugin_host_precheck_missing_conflict"
    L5_PRODUCT_FACTORY_READINESS_FALSE_POSITIVE_CONFLICT = "l5_product_factory_readiness_false_positive_conflict"
    L5_FREEZE_ALLOWS_L6_DESPITE_P0_P1_CONFLICT = "l5_freeze_allows_l6_despite_p0_p1_conflict"
    L5_FREEZE_ALLOWS_L6_WITHOUT_FULL_PYTEST_CONFLICT = "l5_freeze_allows_l6_without_full_pytest_conflict"
    L5_FREEZE_LIVE_EXECUTION_CONFLICT = "l5_freeze_live_execution_conflict"
    L5_FREEZE_LEGACY_RUNTIME_CONFLICT = "l5_freeze_legacy_runtime_conflict"
    L5_FREEZE_L6_IMPLEMENTATION_CONFLICT = "l5_freeze_l6_implementation_conflict"


def phase8_declaration_digest(value: Any, excluded: tuple[str, ...] = ()) -> str:
    if is_dataclass(value) and not isinstance(value, type):
        payload = {field.name: getattr(value, field.name) for field in fields(value) if field.name not in excluded and not field.name.endswith("_digest")}
        return stable_digest(payload)
    if isinstance(value, dict):
        return stable_digest({key: item for key, item in value.items() if key not in excluded and not str(key).endswith("_digest")})
    return stable_digest(value)


def has_forbidden_phase8_method(obj: Any) -> bool:
    cls = obj if isinstance(obj, type) else type(obj)
    return any(callable(getattr(cls, name, None)) for name in _EXECUTION_METHOD_NAMES)


def has_forbidden_phase8_field_name(name: str) -> bool:
    normalized = str(name).strip().lower()
    return normalized in _LIVE_FIELD_NAMES


def _iter_public_text_parts(value: Any) -> tuple[str, ...]:
    if is_dataclass(value) and not isinstance(value, type):
        parts: list[str] = []
        for item in fields(value):
            parts.append(item.name)
            parts.extend(_iter_public_text_parts(getattr(value, item.name)))
        return tuple(parts)
    if isinstance(value, dict):
        parts = []
        for key, item in value.items():
            parts.extend(_iter_public_text_parts(key))
            parts.extend(_iter_public_text_parts(item))
        return tuple(parts)
    if isinstance(value, (tuple, list, set, frozenset)):
        parts = []
        for item in value:
            parts.extend(_iter_public_text_parts(item))
        return tuple(parts)
    return (str(stable_primitive(value)),)


def _public_text_part_is_safe(text: str) -> bool:
    normalized = text.strip().lower()
    if has_forbidden_phase8_field_name(normalized):
        return False
    if any(fragment.lower() in normalized for fragment in _LIVE_TEXT_FRAGMENTS):
        return False
    if _LIVE_PATH_RE.search(text) or _SECRET_LIKE_RE.search(text):
        return False
    return True


def has_live_phase8_locator(value: Any) -> bool:
    return any(not _public_text_part_is_safe(part) for part in _iter_public_text_parts(value))


def phase8_public_text_is_safe(value: Any) -> bool:
    return not has_live_phase8_locator(value)


def _check_ref_fields(obj: Any, owner: str) -> None:
    for item in fields(obj):
        value = getattr(obj, item.name)
        if item.name.endswith("_refs"):
            ensure_ref_items(value, f"{owner}.{item.name}")
        elif item.name.endswith("_ref") and not item.name.endswith("digest"):
            ensure_ref_text(value, f"{owner}.{item.name}", required=False)
        elif item.name.endswith("_digest") and value:
            ensure_ref_text(value, f"{owner}.{item.name}", required=False)
        elif item.name.endswith("_passed") or item.name.startswith("allow_") or item.name.endswith("_enabled") or item.name.endswith("_ready") or item.name.endswith("_non_empty"):
            ensure_bool(value, f"{owner}.{item.name}")


def _ensure_phase8_core_refs(obj: Any, owner: str) -> None:
    for item_name in (
        "actor_ref",
        "scope_ref",
        "trace_ref",
        "approval_ref",
        "responsibility_chain_ref",
        "accountability_ref",
        "tamper_evidence_ref",
    ):
        ensure_ref_text(getattr(obj, item_name), f"{owner}.{item_name}", required=True)
    for item_name in ("policy_refs", "evidence_refs", "provenance_refs", "risk_tags"):
        ensure_ref_items(getattr(obj, item_name), f"{owner}.{item_name}", required=True)


def _ensure_redacted_evidence_refs(items: tuple[str, ...], owner: str) -> None:
    ensure_ref_items(items, owner, required=True)
    for item in items:
        if not item.startswith(_REDACTED_EVIDENCE_PREFIXES):
            raise ValueError(f"{owner} must contain redacted evidence refs only")


@dataclass(frozen=True, slots=True)
class _Phase8Base:
    actor_ref: str = "actor:l5_phase8"
    scope_ref: str = "scope:l5_phase8"
    trace_ref: str = "trace:l5_phase8"
    policy_refs: tuple[str, ...] = ("policy:l5_phase8",)
    approval_ref: str = "approval:l5_phase8"
    evidence_refs: tuple[str, ...] = ("evidence:redacted:l5_phase8",)
    provenance_refs: tuple[str, ...] = ("provenance:l5_phase8",)
    responsibility_chain_ref: str = "responsibility:l5_phase8"
    accountability_ref: str = "accountability:l5_phase8"
    tamper_evidence_ref: str = "tamper:l5_phase8"
    source_layer: str = "L5_PHASE8"
    severity: str = L5FinalConflictSeverity.INFO.value
    risk_tags: tuple[str, ...] = ("declaration_only", "final_freeze", "no_live_execution")

    def __post_init__(self) -> None:
        _check_ref_fields(self, type(self).__name__)
        _ensure_phase8_core_refs(self, type(self).__name__)
        ensure_short_text(self.source_layer, f"{type(self).__name__}.source_layer", 128)
        ensure_short_text(self.severity, f"{type(self).__name__}.severity", 32)
        ensure_ref_items(self.risk_tags, f"{type(self).__name__}.risk_tags", required=True)


@dataclass(frozen=True, slots=True)
class L5ClosureSummary(_Phase8Base):
    closure_ref: str = "closure:l5_final"
    phase: str = "L5_CLOSURE"
    l5_version_ref: str = "version:l5_final_candidate"
    source_package_ref: str = "package:l5_phase8_final_freeze"
    consumed_phase_refs: tuple[str, ...] = _PHASE_REFS
    phase1_summary_ref: str = "summary:l5_phase1"
    phase2_summary_ref: str = "summary:l5_phase2"
    phase3_summary_ref: str = "summary:l5_phase3"
    phase4_summary_ref: str = "summary:l5_phase4"
    phase5_summary_ref: str = "summary:l5_phase5"
    phase6_summary_ref: str = "summary:l5_phase6"
    phase7_summary_ref: str = "summary:l5_phase7"
    generic_plugin_host_precheck_ref: str = "precheck:l5_phase7:generic_host"
    production_mount_status_ref: str = "production_mount:declaration_ready"
    affective_mount_status_ref: str = "affective_mount:declaration_ready"
    affective_plugin_scope_ref: str = "scope:affective_plugin:l6_planning_only"
    p0_count: int = 0
    p1_count: int = 0
    p2_count: int = 0
    p3_count: int = 0
    unresolved_risk_refs: tuple[str, ...] = field(default_factory=tuple)
    fixed_risk_refs: tuple[str, ...] = ("risk:l5_phase7_p1_repaired",)
    remaining_limitation_refs: tuple[str, ...] = ("limitation:no_live_execution", "limitation:l6_must_plan_plugins", "limitation:affective_plugin_l6_planning_only")
    freeze_candidate_ref: str = "freeze_candidate:l5_final"
    closure_digest: str = ""

    def __post_init__(self) -> None:
        _Phase8Base.__post_init__(self)
        ensure_ref_items(self.consumed_phase_refs, "L5ClosureSummary.consumed_phase_refs", required=True)
        for count_name in ("p0_count", "p1_count", "p2_count", "p3_count"):
            if not isinstance(getattr(self, count_name), int) or getattr(self, count_name) < 0:
                raise ValueError(f"L5ClosureSummary.{count_name} must be non-negative int")
        if tuple(self.consumed_phase_refs) != _PHASE_REFS:
            raise ValueError("L5ClosureSummary must cover L5 phase1-phase7")
        if not self.closure_digest:
            object.__setattr__(self, "closure_digest", phase8_declaration_digest(self, ("closure_digest",)))


@dataclass(frozen=True, slots=True)
class L5FreezeManifest(_Phase8Base):
    freeze_manifest_ref: str = "freeze_manifest:l5_final"
    l5_version_ref: str = "version:l5_final_candidate"
    frozen_public_object_refs: tuple[str, ...] = ("public_objects:l5_phase1_phase8",)
    frozen_public_export_refs: tuple[str, ...] = ("public_exports:tiangong_kernel.l5_plugin_host",)
    frozen_projection_refs: tuple[str, ...] = ("projection:l5_final",)
    frozen_quality_gate_refs: tuple[str, ...] = ("quality_gate:l5_phase8_final",)
    frozen_handoff_refs: tuple[str, ...] = ("handoff:l5_l6_freeze",)
    frozen_audit_index_refs: tuple[str, ...] = ("audit_index:l5_final",)
    frozen_test_report_refs: tuple[str, ...] = ("test_report:l5_phase8",)
    frozen_hash_manifest_refs: tuple[str, ...] = ("hash_compare:l0_l4", "hash_compare:l5_phase1_phase7")
    frozen_forbidden_scan_refs: tuple[str, ...] = ("forbidden_scan:l5_phase8_final",)
    frozen_zip_integrity_refs: tuple[str, ...] = ("zip_integrity:l5_phase8",)
    frozen_skill_tool_release_refs: tuple[str, ...] = ("skill_tool_release:contract", "skill_tool_release:trace_matrix")
    frozen_context_belief_world_refs: tuple[str, ...] = ("context_belief_world:boundary_matrix", "context_safety_projection:l4")
    frozen_communication_handoff_refs: tuple[str, ...] = ("message_envelope:l5_l6_handoff", "conversation:l5_l6_handoff", "result_return:l5_l6_handoff")
    frozen_self_healing_refs: tuple[str, ...] = ("self_healing:declaration", "recovery_plan:declaration")
    frozen_self_evolution_refs: tuple[str, ...] = ("self_evolution:commit_boundary", "self_evolution:post_commit_observation")
    frozen_memory_forgetting_refs: tuple[str, ...] = ("memory_forgetting:governance", "deletion_tombstone:audit")
    compatibility_matrix_ref: str = "compatibility_matrix:l5_final"
    governance_matrix_ref: str = "governance_matrix:l5_final"
    l6_handoff_freeze_ref: str = "handoff:l5_l6_freeze"
    product_artifact_factory_readiness_ref: str = "readiness:product_artifact_factory:l6_planning_ready"
    affective_plugin_readiness_ref: str = "readiness:affective_plugin:l6_planning_only"
    affective_plugin_mount_ref: str = "affective_mount:declaration_only"
    affective_safety_boundary_ref: str = "safety_boundary:affective_plugin"
    affective_audit_binding_ref: str = "audit_binding:affective_plugin"
    phase5_resource_boundary_summary_ref: str = "resource_boundary:phase5_summary"
    phase5_resource_boundary_digest_ref: str = "resource_boundary_digest:phase5"
    no_runtime_registry_ref: str = "no_runtime_registry:l5_final"
    no_live_plugin_load_ref: str = "no_live_plugin_load:l5_final"
    no_live_tool_call_ref: str = "no_live_tool_call:l5_final"
    no_live_l4_adapter_call_ref: str = "no_live_l4_adapter_call:l5_final"
    no_live_artifact_build_ref: str = "no_live_artifact_build:l5_final"
    freeze_digest: str = ""

    def __post_init__(self) -> None:
        _Phase8Base.__post_init__(self)
        for required_refs in (
            self.frozen_public_object_refs,
            self.frozen_public_export_refs,
            self.frozen_projection_refs,
            self.frozen_quality_gate_refs,
            self.frozen_handoff_refs,
            self.frozen_audit_index_refs,
            self.frozen_test_report_refs,
            self.frozen_hash_manifest_refs,
            self.frozen_forbidden_scan_refs,
            self.frozen_zip_integrity_refs,
            self.frozen_skill_tool_release_refs,
            self.frozen_context_belief_world_refs,
            self.frozen_communication_handoff_refs,
            self.frozen_self_healing_refs,
            self.frozen_self_evolution_refs,
            self.frozen_memory_forgetting_refs,
        ):
            if not required_refs:
                raise ValueError("L5FreezeManifest requires all frozen artifact reference groups")
        if not self.freeze_digest:
            object.__setattr__(self, "freeze_digest", phase8_declaration_digest(self, ("freeze_digest",)))


@dataclass(frozen=True, slots=True)
class L5FinalPublicProjection(_Phase8Base):
    projection_ref: str = "projection:l5_final"
    closure_summary: tuple[tuple[str, str], ...] = (("consumed_phase_count", "7"), ("closure_phase", "phase8_final"), ("status", "freeze_candidate"))
    generic_plugin_host_readiness_summary: tuple[tuple[str, str], ...] = (("precheck", GENERIC_HOST_PASS_WITH_COMPATIBLE_EXTENSION),)
    registry_summary: tuple[tuple[str, str], ...] = (("summary", "declaration_registry"),)
    manifest_capability_summary: tuple[tuple[str, str], ...] = (("summary", "generic_capability_declarations"),)
    lifecycle_mount_summary: tuple[tuple[str, str], ...] = (("summary", "declaration_only"),)
    boundary_privacy_resource_token_trust_summary: tuple[tuple[str, str], ...] = (("summary", "boundary_refs_only"),)
    resource_budget_summary: tuple[tuple[str, str], ...] = (("phase5_resource_boundary", "digest_ref_only"), ("l6_budget_scope", "required"))
    version_migration_summary: tuple[tuple[str, str], ...] = (("version_migration", "planning_refs_only"), ("rollback_hot_switch_replay", "boundary_required"))
    context_belief_world_summary: tuple[tuple[str, str], ...] = (("status", "boundary_refs_only"), ("l6_context_assembler", "required"))
    communication_handoff_summary: tuple[tuple[str, str], ...] = (("message_envelope", "required"), ("result_return", "required"))
    skill_tool_release_summary: tuple[tuple[str, str], ...] = (("status", "contract_refs_only"), ("l5_review_hint", "required"))
    self_healing_summary: tuple[tuple[str, str], ...] = (("status", "declaration_refs_only"), ("recovery_plan", "not_executor"))
    self_evolution_summary: tuple[tuple[str, str], ...] = (("status", "l6_planning_only"), ("commit", "requires_boundary"))
    memory_forgetting_summary: tuple[tuple[str, str], ...] = (("status", "governance_refs_only"), ("deletion_tombstone", "audit_required"))
    health_permission_disposition_summary: tuple[tuple[str, str], ...] = (("summary", "precondition_refs_only"),)
    host_boundary_gate_summary: tuple[tuple[str, str], ...] = (("summary", "deny_by_default"),)
    handoff_summary: tuple[tuple[str, str], ...] = (("l6", "handoff_freeze_not_authorization"),)
    route_hook_subscription_summary: tuple[tuple[str, str], ...] = (("summary", "no_live_dispatch"),)
    contract_service_capability_mount_summary: tuple[tuple[str, str], ...] = (("summary", "contract_refs_only"),)
    production_mount_readiness_summary: tuple[tuple[str, str], ...] = (("status", "l6_planning_ready"), ("execution", "forbidden"), ("build", "forbidden"), ("delivery", "forbidden"), ("tool_call", "forbidden"))
    affective_plugin_readiness_summary: tuple[tuple[str, str], ...] = (("status", "l6_planning_only"), ("execution", "forbidden"), ("authorization", "forbidden"), ("policy_bypass", "forbidden"), ("memory_mutation", "forbidden"), ("projection", "redacted_refs_only"))
    affective_modulation_summary: tuple[tuple[str, str], ...] = (("allowed", "expression_attention_priority_memory_risk_learning"), ("decision_order", "forbidden"), ("side_effect", "forbidden"))
    governance_coverage_summary: tuple[tuple[str, str], ...] = (("gate_count", str(len(_CORE_GOVERNANCE_GATES))),)
    conflict_counts: tuple[tuple[str, str], ...] = (("p0", "0"), ("p1", "0"), ("p2", "0"), ("p3", "0"))
    quality_gate_summary: tuple[tuple[str, str], ...] = (("allow_freeze_l5", "true"),)
    forbidden_scan_summary: tuple[tuple[str, str], ...] = (("blocking_findings", "0"),)
    test_summary: tuple[tuple[str, str], ...] = (("full_pytest", "passed"),)
    hash_compare_summary: tuple[tuple[str, str], ...] = (("l0_l4", "clean"),)
    l6_handoff_summary: tuple[tuple[str, str], ...] = (("general_plugins", "allowed_for_planning"), ("product_artifact_factory", "l6_planning_only"), ("product_artifact_factory_execution", "forbidden"), ("affective_plugin", "l6_planning_only"), ("affective_plugin_execution", "forbidden"))
    redacted_evidence_refs: tuple[str, ...] = ("evidence:redacted:l5_final",)
    redaction_state: str = "redacted"
    projection_digest: str = ""

    def __post_init__(self) -> None:
        _Phase8Base.__post_init__(self)
        for item in fields(self):
            value = getattr(self, item.name)
            if item.name.endswith("_summary") or item.name == "conflict_counts":
                if not isinstance(value, tuple):
                    raise ValueError(f"L5FinalPublicProjection.{item.name} must be tuple")
        _ensure_redacted_evidence_refs(self.redacted_evidence_refs, "L5FinalPublicProjection.redacted_evidence_refs")
        if not phase8_public_text_is_safe(self):
            raise ValueError("L5FinalPublicProjection must not expose executable details, live locators, or secrets")
        if not self.projection_digest:
            object.__setattr__(self, "projection_digest", phase8_declaration_digest(self, ("projection_digest",)))


@dataclass(frozen=True, slots=True)
class L5L6HandoffFreeze(_Phase8Base):
    l6_handoff_freeze_ref: str = "handoff:l5_l6_freeze"
    l5_version_ref: str = "version:l5_final_candidate"
    l6_allowed_consume_object_refs: tuple[str, ...] = (
        "consume:manifest_capability_declarations",
        "consume:registry_snapshot_index_conflicts_projection_audit",
        "consume:lifecycle_mount_state_machine_surface",
        "consume:isolation_dependency_credential_data_resource_boundaries",
        "consume:capability_token_trust_switch_boundaries",
        "consume:health_quality_disposition_permission_preconditions",
        "consume:host_boundary_l3_l4_l6_handoff",
        "consume:route_hook_event_subscription",
        "consume:contract_service_capability_mount",
        "consume:artifact_production_mount_binding",
        "consume:affective_plugin_mount_declaration",
        "consume:affective_modulation_contract_binding",
        "consume:affective_safety_boundary",
        "consume:affective_audit_binding",
        "consume:affective_public_projection_summary",
        "consume:governance_and_readiness_matrices",
        "consume:context_belief_world_boundary",
        "consume:l4_context_safety_projection",
        "consume:l6_context_assembler_precondition",
        "consume:message_envelope_conversation_channel_protocol",
        "consume:ack_nack_result_return",
        "consume:skill_tool_release_contract",
        "consume:self_healing_declaration",
        "consume:recovery_plan_declaration",
        "consume:self_healing_validation_report",
        "consume:self_healing_quality_gate",
        "consume:recovery_permission_preconditions",
        "consume:rollback_permission_preconditions",
        "consume:replay_permission_preconditions",
        "consume:self_evolution_commit_boundary",
        "consume:memory_forgetting_governance",
        "consume:phase5_resource_budget_boundary",
        "consume:version_migration_rollback_hot_switch_replay",
    )
    l6_forbidden_misuse_refs: tuple[str, ...] = (
        "forbid:l5_declaration_as_executor",
        "forbid:l5_handoff_as_l3_l4_call",
        "forbid:l5_l6_entry_as_plugin_entry",
        "forbid:route_as_live_router",
        "forbid:hook_as_callback",
        "forbid:event_subscription_as_live_subscription",
        "forbid:contract_binding_as_live_contract_service",
        "forbid:service_mount_as_endpoint",
        "forbid:capability_mount_as_tool_schema_release",
        "forbid:artifact_production_mount_as_builder",
        "forbid:product_contract_as_execution_plan",
        "forbid:direct_file_generation",
        "forbid:l1_l4_governance_bypass",
        "forbid:direct_tool_or_adapter_call",
        "forbid:l5_freeze_as_authorization",
        "forbid:context_assembly_bypass",
        "forbid:tool_output_as_system_instruction",
        "forbid:model_output_as_system_instruction",
        "forbid:belief_override_event_fact",
        "forbid:world_state_without_evidence",
        "forbid:memory_injection_without_boundary_review",
        "forbid:message_without_envelope",
        "forbid:result_return_without_handoff_envelope",
        "forbid:self_healing_declaration_as_executor",
        "forbid:recovery_plan_as_executor",
        "forbid:recovery_plan_ref_as_executed_recovery",
        "forbid:checkpoint_ref_as_created_checkpoint",
        "forbid:validation_ref_as_validation_passed",
        "forbid:regression_ref_as_regression_passed",
        "forbid:repair_suggestion_ref_as_patch_instruction",
        "forbid:self_evolution_auto_merge",
        "forbid:self_evolution_commit_without_l5_permit",
        "forbid:self_evolution_hot_switch_without_boundary",
        "forbid:self_evolution_rollback_without_validation",
        "forbid:self_evolution_tombstone_as_delete",
        "forbid:l6_memory_plugin_direct_memory_store_access",
        "forbid:l6_forgetting_plugin_direct_deletion_without_tombstone_audit",
        "forbid:memory_context_unfiltered_injection",
        *AFFECTIVE_FORBIDDEN_MISUSE_REFS,
    )
    l6_entry_boundary_refs: tuple[str, ...] = ("boundary:l6_entry",)
    l3_handoff_refs: tuple[str, ...] = ("handoff:l3",)
    l4_handoff_refs: tuple[str, ...] = ("handoff:l4",)
    lifecycle_refs: tuple[str, ...] = ("lifecycle:declaration",)
    registry_refs: tuple[str, ...] = ("registry:declaration",)
    boundary_refs: tuple[str, ...] = ("boundary:plugin_host",)
    health_refs: tuple[str, ...] = ("health:declaration",)
    permission_precondition_refs: tuple[str, ...] = ("permission_precondition:declaration",)
    governance_gate_refs: tuple[str, ...] = _CORE_GOVERNANCE_GATES
    route_hook_subscription_refs: tuple[str, ...] = ("route:declaration", "hook:declaration", "event_subscription:declaration")
    contract_binding_refs: tuple[str, ...] = ("contract_binding:declaration",)
    service_mount_refs: tuple[str, ...] = ("service_mount:declaration",)
    capability_mount_refs: tuple[str, ...] = ("capability_mount:declaration",)
    production_mount_refs: tuple[str, ...] = ("production_mount:declaration_only",)
    affective_mount_refs: tuple[str, ...] = ("affective_mount:declaration_only",)
    affective_modulation_contract_refs: tuple[str, ...] = ("contract_binding:affective_modulation",)
    affective_safety_boundary_refs: tuple[str, ...] = ("safety_boundary:affective_plugin",)
    affective_audit_binding_refs: tuple[str, ...] = ("audit_binding:affective_plugin",)
    affective_public_projection_refs: tuple[str, ...] = ("projection_summary:affective_plugin:redacted",)
    affective_l6_handoff_refs: tuple[str, ...] = ("handoff:l5_l6_affective_plugin",)
    product_artifact_factory_l6_readiness_ref: str = "readiness:product_artifact_factory:l6_planning_ready"
    affective_plugin_l6_readiness_ref: str = "readiness:affective_plugin:l6_planning_only"
    context_belief_world_boundary_refs: tuple[str, ...] = (
        "gate:context_safety_boundary",
        "gate:belief_event_precedence",
        "gate:world_state_evidence_staleness",
        "gate:tool_output_demotion",
        "gate:model_output_demotion",
        "gate:memory_injection_boundary",
        "gate:context_pollution_review",
    )
    required_context_safety_projection_refs: tuple[str, ...] = ("projection:l4_context_safety",)
    required_l6_context_assembler_refs: tuple[str, ...] = ("l6_context_assembler:required",)
    no_context_assembly_bypass_ref: str = "no_context_assembly_bypass:l5_l6_handoff"
    no_tool_output_as_system_instruction_ref: str = "no_tool_output_as_system_instruction:l5_l6_handoff"
    no_model_output_as_system_instruction_ref: str = "no_model_output_as_system_instruction:l5_l6_handoff"
    no_belief_override_event_ref: str = "no_belief_override_event:l5_l6_handoff"
    no_world_state_without_evidence_ref: str = "no_world_state_without_evidence:l5_l6_handoff"
    no_memory_injection_without_boundary_review_ref: str = "no_memory_injection_without_boundary_review:l5_l6_handoff"
    message_envelope_refs: tuple[str, ...] = ("message_envelope:l5_l6_handoff",)
    conversation_refs: tuple[str, ...] = ("conversation:l5_l6_handoff",)
    channel_refs: tuple[str, ...] = ("channel:l5_l6_handoff",)
    protocol_refs: tuple[str, ...] = ("protocol:l5_l6_handoff",)
    reply_to_refs: tuple[str, ...] = ("reply_to:l5_l6_handoff",)
    ack_required_ref: str = "ack_required:l5_l6_handoff"
    nack_required_ref: str = "nack_required:l5_l6_handoff"
    result_return_refs: tuple[str, ...] = ("result_return:l5_l6_handoff",)
    failure_return_refs: tuple[str, ...] = ("failure_return:l5_l6_handoff",)
    skill_tool_release_contract_refs: tuple[str, ...] = ("skill_tool_release:contract", "skill_tool_release:trace_matrix")
    l4_to_l5_skill_tool_release_handoff_refs: tuple[str, ...] = ("handoff:l4_to_l5_skill_tool_release",)
    l4_to_l6_released_tool_view_requirement_refs: tuple[str, ...] = ("released_tool_view_requirement:l4_to_l6",)
    self_healing_refs: tuple[str, ...] = ("self_healing:declaration",)
    recovery_plan_refs: tuple[str, ...] = ("recovery_plan:declaration",)
    self_healing_validation_report_refs: tuple[str, ...] = ("self_healing:validation_report",)
    self_healing_quality_gate_refs: tuple[str, ...] = ("self_healing:quality_gate",)
    self_evolution_requirement_refs: tuple[str, ...] = ("self_evolution:commit_boundary", "self_evolution:post_commit_observation")
    self_evolution_forbidden_misuse_refs: tuple[str, ...] = ("forbid:self_evolution_auto_merge", "forbid:self_evolution_commit_without_l5_permit")
    memory_forgetting_requirement_refs: tuple[str, ...] = ("memory_forgetting:governance", "deletion_tombstone:audit")
    resource_budget_boundary_refs: tuple[str, ...] = ("resource_boundary:phase5_summary", "resource_boundary_digest:phase5")
    version_migration_requirement_refs: tuple[str, ...] = ("version_migration:rollback_hot_switch_replay",)
    no_execution_authorization_ref: str = "no_execution_authorization:l5_l6_handoff"
    no_direct_tool_call_ref: str = "no_direct_tool_call:l5_l6_handoff"
    no_direct_l4_adapter_ref: str = "no_direct_l4_adapter:l5_l6_handoff"
    no_direct_file_generation_ref: str = "no_direct_file_generation:l5_l6_handoff"
    no_direct_delivery_ref: str = "no_direct_delivery:l5_l6_handoff"
    required_l6_design_refs: tuple[str, ...] = ("l6_design:plugin_specific",)
    required_l6_quality_gate_refs: tuple[str, ...] = ("l6_quality_gate:required",)
    required_l6_forbidden_scan_refs: tuple[str, ...] = ("l6_forbidden_scan:required",)
    handoff_digest: str = ""

    def __post_init__(self) -> None:
        _Phase8Base.__post_init__(self)
        required_ref_groups = (
            self.l6_allowed_consume_object_refs,
            self.l6_forbidden_misuse_refs,
            self.message_envelope_refs,
            self.conversation_refs,
            self.channel_refs,
            self.protocol_refs,
            self.result_return_refs,
            self.failure_return_refs,
            self.context_belief_world_boundary_refs,
            self.required_context_safety_projection_refs,
            self.required_l6_context_assembler_refs,
            self.skill_tool_release_contract_refs,
            self.self_healing_refs,
            self.recovery_plan_refs,
            self.self_evolution_requirement_refs,
            self.memory_forgetting_requirement_refs,
            self.resource_budget_boundary_refs,
            self.affective_mount_refs,
            self.affective_modulation_contract_refs,
            self.affective_safety_boundary_refs,
            self.affective_audit_binding_refs,
            self.affective_public_projection_refs,
            self.affective_l6_handoff_refs,
        )
        if any(not group for group in required_ref_groups):
            raise ValueError("L5L6HandoffFreeze requires consume and forbidden misuse refs")
        if _REQUIRED_L6_FORBIDDEN_MISUSE_REFS - set(self.l6_forbidden_misuse_refs):
            raise ValueError("L5L6HandoffFreeze is missing required forbidden misuse refs")
        if not self.handoff_digest:
            object.__setattr__(self, "handoff_digest", phase8_declaration_digest(self, ("handoff_digest",)))


@dataclass(frozen=True, slots=True)
class L5GovernanceCoverageMatrix(_Phase8Base):
    matrix_ref: str = "governance_matrix:l5_final"
    plugin_kind_refs: tuple[str, ...] = _GENERAL_PLUGIN_KINDS + _PRODUCTION_PLUGIN_KINDS + _AFFECTIVE_PLUGIN_KINDS
    governance_gate_refs: tuple[str, ...] = _CORE_GOVERNANCE_GATES
    coverage_rows: tuple[tuple[str, str], ...] = tuple((plugin, "covered") for plugin in _GENERAL_PLUGIN_KINDS + _PRODUCTION_PLUGIN_KINDS + _AFFECTIVE_PLUGIN_KINDS)
    production_plugin_rows_enabled: bool = True
    affective_plugin_rows_enabled: bool = True
    missing_gate_refs: tuple[str, ...] = field(default_factory=tuple)
    matrix_digest: str = ""

    def __post_init__(self) -> None:
        _Phase8Base.__post_init__(self)
        if set(_CORE_GOVERNANCE_GATES) - set(self.governance_gate_refs):
            raise ValueError("L5GovernanceCoverageMatrix must cover all core governance gates")
        if self.production_plugin_rows_enabled and set(_PRODUCTION_PLUGIN_KINDS) - set(self.plugin_kind_refs):
            raise ValueError("L5GovernanceCoverageMatrix must cover production plugin rows when enabled")
        if self.affective_plugin_rows_enabled and set(_AFFECTIVE_PLUGIN_KINDS) - set(self.plugin_kind_refs):
            raise ValueError("L5GovernanceCoverageMatrix must cover affective plugin rows when enabled")
        coverage_map = dict(self.coverage_rows)
        if set(self.plugin_kind_refs) - set(coverage_map):
            raise ValueError("L5GovernanceCoverageMatrix must cover every plugin kind row")
        if any(coverage_map.get(plugin) != "covered" for plugin in self.plugin_kind_refs):
            raise ValueError("L5GovernanceCoverageMatrix coverage rows must all be covered")
        if self.missing_gate_refs:
            raise ValueError("L5GovernanceCoverageMatrix cannot freeze with missing governance gates")
        if not self.matrix_digest:
            object.__setattr__(self, "matrix_digest", phase8_declaration_digest(self, ("matrix_digest",)))


@dataclass(frozen=True, slots=True)
class L5CapabilityReadinessMatrix(_Phase8Base):
    matrix_ref: str = "capability_readiness_matrix:l5_final"
    capability_kind_refs: tuple[str, ...] = _GENERAL_CAPABILITY_KINDS + _PRODUCTION_CAPABILITY_KINDS + _AFFECTIVE_CAPABILITY_KINDS
    readiness_rows: tuple[tuple[str, str], ...] = tuple((capability, "ready") for capability in _GENERAL_CAPABILITY_KINDS) + tuple((capability, "l6_planning_only") for capability in _PRODUCTION_CAPABILITY_KINDS + _AFFECTIVE_CAPABILITY_KINDS)
    product_artifact_factory_precheck_result: str = GENERIC_HOST_PASS_WITH_COMPATIBLE_EXTENSION
    artifact_factory_ready: bool = True
    product_builder_ready: bool = True
    artifact_factory_l6_planning_only: bool = True
    product_builder_l6_planning_only: bool = True
    affective_plugin_ready: bool = True
    affective_plugin_l6_planning_only: bool = True
    allow_execute_product_artifact_factory: bool = False
    allow_execute_affective_plugin: bool = False
    product_artifact_factory_scope: str = "l6_planning_only"
    affective_plugin_scope: str = "l6_planning_only"
    product_artifact_factory_no_execution_ref: str = "no_execution:product_artifact_factory:l5"
    product_artifact_factory_no_build_ref: str = "no_build:product_artifact_factory:l5"
    product_artifact_factory_no_delivery_ref: str = "no_delivery:product_artifact_factory:l5"
    product_artifact_factory_no_tool_call_ref: str = "no_tool_call:product_artifact_factory:l5"
    affective_safety_boundary_ref: str = "safety_boundary:affective_plugin"
    affective_audit_binding_ref: str = "audit_binding:affective_plugin"
    affective_l6_handoff_ref: str = "handoff:l5_l6_affective_plugin"
    affective_no_authorization_ref: str = "no_authorization:affective_plugin"
    affective_no_tool_call_ref: str = "no_tool_call:affective_plugin"
    affective_no_core_mutation_ref: str = "no_core_mutation:affective_plugin"
    blocking_reason_refs: tuple[str, ...] = field(default_factory=tuple)
    matrix_digest: str = ""

    def __post_init__(self) -> None:
        _Phase8Base.__post_init__(self)
        required_caps = set(_GENERAL_CAPABILITY_KINDS + _PRODUCTION_CAPABILITY_KINDS + _AFFECTIVE_CAPABILITY_KINDS)
        readiness_map = dict(self.readiness_rows)
        allowed_states = {"ready", "l6_planning_only", "blocked"}
        if not self.capability_kind_refs or not self.readiness_rows:
            raise ValueError("L5CapabilityReadinessMatrix cannot be empty")
        if required_caps - set(self.capability_kind_refs):
            raise ValueError("L5CapabilityReadinessMatrix must cover all required capability kinds")
        if required_caps - set(readiness_map):
            raise ValueError("L5CapabilityReadinessMatrix readiness rows must cover all required capabilities")
        if any(state not in allowed_states for state in readiness_map.values()):
            raise ValueError("L5CapabilityReadinessMatrix readiness state invalid")
        for capability in _PRODUCTION_CAPABILITY_KINDS:
            if readiness_map.get(capability) != "l6_planning_only" and (self.artifact_factory_ready or self.product_builder_ready):
                raise ValueError("Product artifact factory capabilities are L6 planning only")
        for capability in _AFFECTIVE_CAPABILITY_KINDS:
            if readiness_map.get(capability) != "l6_planning_only" and self.affective_plugin_ready:
                raise ValueError("Affective capabilities are L6 planning only")
        if self.blocking_reason_refs and (self.artifact_factory_ready or self.product_builder_ready or self.affective_plugin_ready):
            raise ValueError("L5 capability matrix cannot be ready with blocking reasons")
        if self.product_artifact_factory_precheck_result == GENERIC_HOST_BLOCK_TOOL_ONLY and (self.artifact_factory_ready or self.product_builder_ready):
            raise ValueError("Product artifact factory capability cannot be ready when precheck blocks tool-only host")
        if self.allow_execute_product_artifact_factory:
            raise ValueError("Product artifact factory execution is forbidden in L5")
        if self.allow_execute_affective_plugin:
            raise ValueError("Affective plugin execution is forbidden in L5")
        ensure_short_text(self.product_artifact_factory_scope, "L5CapabilityReadinessMatrix.product_artifact_factory_scope", 64)
        ensure_short_text(self.affective_plugin_scope, "L5CapabilityReadinessMatrix.affective_plugin_scope", 64)
        if self.product_artifact_factory_scope != "l6_planning_only":
            raise ValueError("Product artifact factory scope must remain l6_planning_only")
        if self.affective_plugin_scope != "l6_planning_only":
            raise ValueError("Affective plugin scope must remain l6_planning_only")
        if not self.affective_plugin_l6_planning_only:
            raise ValueError("Affective plugin must remain L6 planning only")
        if not self.matrix_digest:
            object.__setattr__(self, "matrix_digest", phase8_declaration_digest(self, ("matrix_digest",)))


@dataclass(frozen=True, slots=True)
class L5FinalQualityGateDecision(_Phase8Base):
    decision_ref: str = "quality_gate:l5_phase8_final"
    phase: str = PHASE8_PHASE
    p0_count: int = 0
    p1_count: int = 0
    p2_count: int = 0
    p3_count: int = 0
    phase1_passed: bool = False
    phase2_passed: bool = False
    phase3_passed: bool = False
    phase4_passed: bool = False
    phase5_passed: bool = False
    phase6_passed: bool = False
    phase7_passed: bool = False
    generic_plugin_host_precheck_passed: bool = False
    generic_plugin_host_precheck_result: str = GENERIC_HOST_BLOCK_TOOL_ONLY
    product_artifact_factory_l5_ready: bool = False
    affective_plugin_l5_ready: bool = False
    affective_governance_matrix_passed: bool = False
    affective_capability_readiness_matrix_passed: bool = False
    affective_public_projection_passed: bool = False
    affective_l6_handoff_freeze_passed: bool = False
    affective_audit_binding_passed: bool = False
    affective_targeted_pytest_passed: bool = False
    no_affective_direct_execution_passed: bool = False
    no_affective_authorization_bypass_passed: bool = False
    no_affective_core_mutation_passed: bool = False
    l5_final_public_projection_passed: bool = False
    l5_l6_handoff_freeze_passed: bool = False
    governance_coverage_matrix_passed: bool = False
    capability_readiness_matrix_passed: bool = False
    no_live_plugin_execution_passed: bool = False
    no_live_l4_adapter_call_passed: bool = False
    no_live_tool_call_passed: bool = False
    no_live_artifact_build_passed: bool = False
    no_legacy_runtime_passed: bool = False
    no_l6_implementation_passed: bool = False
    public_projection_safety_passed: bool = False
    public_projection_second_leak_test_passed: bool = False
    context_belief_world_boundary_passed: bool = False
    context_safety_projection_passed: bool = False
    l6_context_assembler_precondition_passed: bool = False
    belief_event_precedence_passed: bool = False
    world_state_evidence_staleness_passed: bool = False
    tool_model_output_demotion_passed: bool = False
    memory_injection_boundary_passed: bool = False
    audit_evidence_chain_passed: bool = False
    forbidden_scan_passed: bool = False
    compileall_passed: bool = False
    collect_only_passed: bool = False
    targeted_pytest_passed: bool = False
    plugin_host_subset_passed: bool = False
    plugin_host_subset_non_empty: bool = False
    full_pytest_passed: bool = False
    hash_compare_l0_l4_passed: bool = False
    hash_compare_l5_phase1_phase7_passed: bool = False
    test_inventory_compare_passed: bool = False
    zip_integrity_passed: bool = False
    allow_freeze_l5: bool = False
    allow_enter_l6_general_plugins: bool = False
    allow_enter_l6_product_artifact_factory: bool = False
    allow_plan_l6_product_artifact_factory: bool = False
    allow_execute_product_artifact_factory: bool = False
    allow_enter_l6_affective_plugin: bool = False
    allow_plan_l6_affective_plugin: bool = False
    allow_execute_l6_affective_plugin: bool = False
    product_artifact_factory_scope: str = "blocked"
    affective_plugin_scope: str = "blocked"
    blocking_reasons: tuple[str, ...] = field(default_factory=tuple)
    evidence_index_refs: tuple[str, ...] = ("evidence:l5_final_quality_gate",)
    regression_index_refs: tuple[str, ...] = ("regression:l5_final",)
    rule_source_ref: str = "rule:l5_final_quality_gate"
    detected_by_ref: str = "detector:l5_final_quality_gate"
    decision_digest: str = ""

    def __post_init__(self) -> None:
        _Phase8Base.__post_init__(self)
        if self.generic_plugin_host_precheck_result not in (GENERIC_HOST_PASS, GENERIC_HOST_PASS_WITH_COMPATIBLE_EXTENSION, GENERIC_HOST_BLOCK_TOOL_ONLY):
            raise ValueError("L5FinalQualityGateDecision.generic_plugin_host_precheck_result invalid")
        for name in ("p0_count", "p1_count", "p2_count", "p3_count"):
            if not isinstance(getattr(self, name), int) or getattr(self, name) < 0:
                raise ValueError(f"L5FinalQualityGateDecision.{name} must be non-negative int")
        hard_checks = {
            "p0_count_zero": self.p0_count == 0,
            "p1_count_zero": self.p1_count == 0,
            "p2_count_zero": self.p2_count == 0,
            "p3_count_zero": self.p3_count == 0,
            "blocking_reasons_empty": not self.blocking_reasons,
            "phase1_passed": self.phase1_passed,
            "phase2_passed": self.phase2_passed,
            "phase3_passed": self.phase3_passed,
            "phase4_passed": self.phase4_passed,
            "phase5_passed": self.phase5_passed,
            "phase6_passed": self.phase6_passed,
            "phase7_passed": self.phase7_passed,
            "generic_plugin_host_precheck_passed": self.generic_plugin_host_precheck_passed,
            "affective_plugin_l5_ready": self.affective_plugin_l5_ready,
            "affective_governance_matrix_passed": self.affective_governance_matrix_passed,
            "affective_capability_readiness_matrix_passed": self.affective_capability_readiness_matrix_passed,
            "affective_public_projection_passed": self.affective_public_projection_passed,
            "affective_l6_handoff_freeze_passed": self.affective_l6_handoff_freeze_passed,
            "affective_audit_binding_passed": self.affective_audit_binding_passed,
            "affective_targeted_pytest_passed": self.affective_targeted_pytest_passed,
            "no_affective_direct_execution_passed": self.no_affective_direct_execution_passed,
            "no_affective_authorization_bypass_passed": self.no_affective_authorization_bypass_passed,
            "no_affective_core_mutation_passed": self.no_affective_core_mutation_passed,
            "l5_final_public_projection_passed": self.l5_final_public_projection_passed,
            "l5_l6_handoff_freeze_passed": self.l5_l6_handoff_freeze_passed,
            "governance_coverage_matrix_passed": self.governance_coverage_matrix_passed,
            "capability_readiness_matrix_passed": self.capability_readiness_matrix_passed,
            "no_live_plugin_execution_passed": self.no_live_plugin_execution_passed,
            "no_live_l4_adapter_call_passed": self.no_live_l4_adapter_call_passed,
            "no_live_tool_call_passed": self.no_live_tool_call_passed,
            "no_live_artifact_build_passed": self.no_live_artifact_build_passed,
            "no_legacy_runtime_passed": self.no_legacy_runtime_passed,
            "no_l6_implementation_passed": self.no_l6_implementation_passed,
            "public_projection_safety_passed": self.public_projection_safety_passed,
            "public_projection_second_leak_test_passed": self.public_projection_second_leak_test_passed,
            "context_belief_world_boundary_passed": self.context_belief_world_boundary_passed,
            "context_safety_projection_passed": self.context_safety_projection_passed,
            "l6_context_assembler_precondition_passed": self.l6_context_assembler_precondition_passed,
            "belief_event_precedence_passed": self.belief_event_precedence_passed,
            "world_state_evidence_staleness_passed": self.world_state_evidence_staleness_passed,
            "tool_model_output_demotion_passed": self.tool_model_output_demotion_passed,
            "memory_injection_boundary_passed": self.memory_injection_boundary_passed,
            "audit_evidence_chain_passed": self.audit_evidence_chain_passed,
            "forbidden_scan_passed": self.forbidden_scan_passed,
            "compileall_passed": self.compileall_passed,
            "collect_only_passed": self.collect_only_passed,
            "targeted_pytest_passed": self.targeted_pytest_passed,
            "plugin_host_subset_passed": self.plugin_host_subset_passed,
            "plugin_host_subset_non_empty": self.plugin_host_subset_non_empty,
            "full_pytest_passed": self.full_pytest_passed,
            "hash_compare_l0_l4_passed": self.hash_compare_l0_l4_passed,
            "hash_compare_l5_phase1_phase7_passed": self.hash_compare_l5_phase1_phase7_passed,
            "test_inventory_compare_passed": self.test_inventory_compare_passed,
            "zip_integrity_passed": self.zip_integrity_passed,
        }
        failed_reasons = tuple(f"quality_gate_failed:{name}" for name, passed in hard_checks.items() if not passed)
        derived_blocking_reasons = tuple(dict.fromkeys(tuple(self.blocking_reasons) + failed_reasons))
        object.__setattr__(self, "blocking_reasons", derived_blocking_reasons)
        freeze = not derived_blocking_reasons
        general_l6 = freeze and self.l5_l6_handoff_freeze_passed and self.generic_plugin_host_precheck_passed
        product_l6 = (
            general_l6
            and self.generic_plugin_host_precheck_result != GENERIC_HOST_BLOCK_TOOL_ONLY
            and self.product_artifact_factory_l5_ready
            and self.capability_readiness_matrix_passed
            and self.no_live_artifact_build_passed
            and self.public_projection_second_leak_test_passed
            and not derived_blocking_reasons
        )
        object.__setattr__(self, "allow_freeze_l5", freeze)
        object.__setattr__(self, "allow_enter_l6_general_plugins", general_l6)
        affective_l6 = (
            general_l6
            and self.affective_plugin_l5_ready
            and self.affective_governance_matrix_passed
            and self.affective_capability_readiness_matrix_passed
            and self.affective_public_projection_passed
            and self.affective_l6_handoff_freeze_passed
            and self.affective_audit_binding_passed
            and self.affective_targeted_pytest_passed
            and self.no_affective_direct_execution_passed
            and self.no_affective_authorization_bypass_passed
            and self.no_affective_core_mutation_passed
            and not derived_blocking_reasons
        )
        object.__setattr__(self, "allow_enter_l6_product_artifact_factory", product_l6)
        object.__setattr__(self, "allow_plan_l6_product_artifact_factory", product_l6)
        object.__setattr__(self, "allow_execute_product_artifact_factory", False)
        object.__setattr__(self, "allow_enter_l6_affective_plugin", affective_l6)
        object.__setattr__(self, "allow_plan_l6_affective_plugin", affective_l6)
        object.__setattr__(self, "allow_execute_l6_affective_plugin", False)
        object.__setattr__(self, "product_artifact_factory_scope", "l6_planning_only" if product_l6 else "blocked")
        object.__setattr__(self, "affective_plugin_scope", "l6_planning_only" if affective_l6 else "blocked")
        if not self.decision_digest:
            object.__setattr__(self, "decision_digest", phase8_declaration_digest(self, ("decision_digest",)))


@dataclass(frozen=True, slots=True)
class L5FinalAuditIndex(_Phase8Base):
    final_audit_index_ref: str = "audit_index:l5_final"
    phase: str = L5_FINAL_PHASE
    consumed_phase_refs: tuple[str, ...] = _PHASE_REFS
    public_projection_refs: tuple[str, ...] = ("projection:l5_final",)
    quality_gate_refs: tuple[str, ...] = ("quality_gate:l5_phase8_final",)
    handoff_refs: tuple[str, ...] = ("handoff:l5_l6_freeze",)
    governance_matrix_refs: tuple[str, ...] = ("governance_matrix:l5_final",)
    capability_readiness_refs: tuple[str, ...] = ("capability_readiness_matrix:l5_final",)
    registry_refs: tuple[str, ...] = ("registry:l5_final",)
    manifest_refs: tuple[str, ...] = ("manifest:l5_final",)
    lifecycle_refs: tuple[str, ...] = ("lifecycle:l5_final",)
    mount_refs: tuple[str, ...] = ("mount:l5_final",)
    boundary_refs: tuple[str, ...] = ("boundary:l5_final",)
    health_refs: tuple[str, ...] = ("health:l5_final",)
    permission_refs: tuple[str, ...] = ("permission_precondition:l5_final",)
    handoff_boundary_refs: tuple[str, ...] = ("handoff_boundary:l5_final",)
    production_mount_refs: tuple[str, ...] = ("production_mount:l5_final",)
    affective_mount_refs: tuple[str, ...] = ("affective_mount:l5_final",)
    affective_modulation_contract_refs: tuple[str, ...] = ("contract_binding:affective_modulation",)
    affective_safety_boundary_refs: tuple[str, ...] = ("safety_boundary:affective_plugin",)
    affective_audit_binding_refs: tuple[str, ...] = ("audit_binding:affective_plugin",)
    affective_public_projection_refs: tuple[str, ...] = ("projection_summary:affective_plugin:redacted",)
    affective_l6_handoff_refs: tuple[str, ...] = ("handoff:l5_l6_affective_plugin",)
    skill_tool_release_contract_refs: tuple[str, ...] = ("skill_tool_release:contract", "skill_tool_release:trace_matrix")
    context_belief_world_refs: tuple[str, ...] = ("context_belief_world:boundary_matrix", "context_safety_projection:l4")
    communication_handoff_refs: tuple[str, ...] = ("message_envelope:l5_l6_handoff", "result_return:l5_l6_handoff")
    self_healing_refs: tuple[str, ...] = ("self_healing:declaration",)
    recovery_plan_refs: tuple[str, ...] = ("recovery_plan:declaration",)
    self_healing_validation_report_refs: tuple[str, ...] = ("self_healing:validation_report",)
    self_healing_quality_gate_refs: tuple[str, ...] = ("self_healing:quality_gate",)
    self_evolution_handoff_refs: tuple[str, ...] = ("self_evolution:handoff",)
    self_evolution_requirement_refs: tuple[str, ...] = ("self_evolution:commit_boundary", "self_evolution:post_commit_observation")
    self_evolution_validation_refs: tuple[str, ...] = ("self_evolution:validation",)
    memory_forgetting_refs: tuple[str, ...] = ("memory_forgetting:governance", "deletion_tombstone:audit")
    resource_budget_refs: tuple[str, ...] = ("resource_boundary:phase5_summary", "resource_boundary_digest:phase5")
    validation_report_refs: tuple[str, ...] = ("validation:l5_phase8",)
    conflict_report_refs: tuple[str, ...] = ("conflict_report:l5_final",)
    test_report_refs: tuple[str, ...] = ("test_report:l5_phase8",)
    forbidden_scan_refs: tuple[str, ...] = ("forbidden_scan:l5_phase8",)
    hash_compare_refs: tuple[str, ...] = ("hash_compare:l5_phase8",)
    zip_integrity_refs: tuple[str, ...] = ("zip_integrity:l5_phase8",)
    event_refs: tuple[str, ...] = (
        "event:l5_final_freeze",
        "event:l5_l6_handoff_freeze",
        "event:l5_final_public_projection_created",
        "event:l5_final_quality_gate_decided",
        "event:l5_final_forbidden_scan_checked",
        "event:l5_final_test_results_verified",
        "event:l5_final_hash_compare_checked",
        "event:l5_final_zip_integrity_checked",
        "event:l5_final_governance_matrix_checked",
        "event:l5_final_capability_readiness_checked",
        "event:l5_final_affective_plugin_mount_checked",
        "event:l5_final_affective_safety_boundary_checked",
    )
    audit_digest: str = ""

    def __post_init__(self) -> None:
        _Phase8Base.__post_init__(self)
        required_groups = (
            self.consumed_phase_refs,
            self.public_projection_refs,
            self.quality_gate_refs,
            self.handoff_refs,
            self.event_refs,
            self.evidence_refs,
            self.provenance_refs,
            self.skill_tool_release_contract_refs,
            self.context_belief_world_refs,
            self.communication_handoff_refs,
            self.affective_mount_refs,
            self.affective_modulation_contract_refs,
            self.affective_safety_boundary_refs,
            self.affective_audit_binding_refs,
            self.affective_public_projection_refs,
            self.affective_l6_handoff_refs,
            self.self_healing_refs,
            self.recovery_plan_refs,
            self.self_evolution_requirement_refs,
            self.memory_forgetting_refs,
            self.resource_budget_refs,
        )
        if any(not group for group in required_groups) or not self.accountability_ref or not self.tamper_evidence_ref:
            raise ValueError("L5FinalAuditIndex requires event-first audit references")
        if not self.audit_digest:
            object.__setattr__(self, "audit_digest", phase8_declaration_digest(self, ("audit_digest",)))


class L5ClosureValidator:
    def check(self, closure: L5ClosureSummary) -> bool:
        return tuple(closure.consumed_phase_refs) == _PHASE_REFS and closure.p0_count == 0 and closure.p1_count == 0


class L5FreezeManifestValidator:
    def check(self, manifest: L5FreezeManifest) -> bool:
        return bool(manifest.frozen_public_export_refs and manifest.frozen_quality_gate_refs and manifest.frozen_handoff_refs)


class L5L6HandoffFreezeValidator:
    def check(self, handoff: L5L6HandoffFreeze) -> bool:
        required_groups = (
            handoff.policy_refs,
            handoff.evidence_refs,
            handoff.provenance_refs,
            handoff.l6_allowed_consume_object_refs,
            handoff.l6_forbidden_misuse_refs,
            handoff.message_envelope_refs,
            handoff.conversation_refs,
            handoff.channel_refs,
            handoff.protocol_refs,
            handoff.result_return_refs,
            handoff.failure_return_refs,
            handoff.governance_gate_refs,
            handoff.context_belief_world_boundary_refs,
            handoff.required_context_safety_projection_refs,
            handoff.required_l6_context_assembler_refs,
        )
        core_refs = (
            handoff.actor_ref,
            handoff.scope_ref,
            handoff.trace_ref,
            handoff.responsibility_chain_ref,
            handoff.accountability_ref,
            handoff.tamper_evidence_ref,
            handoff.no_execution_authorization_ref,
            handoff.no_direct_tool_call_ref,
            handoff.no_direct_l4_adapter_ref,
            handoff.no_direct_file_generation_ref,
            handoff.no_direct_delivery_ref,
            handoff.ack_required_ref,
            handoff.nack_required_ref,
        )
        return bool(
            all(core_refs)
            and all(required_groups)
            and not (_REQUIRED_L6_FORBIDDEN_MISUSE_REFS - set(handoff.l6_forbidden_misuse_refs))
            and not (set(_CORE_GOVERNANCE_GATES) - set(handoff.governance_gate_refs))
        )


class L5GovernanceCoverageMatrixValidator:
    def check(self, matrix: L5GovernanceCoverageMatrix) -> bool:
        coverage_map = dict(matrix.coverage_rows)
        return (
            not (set(_CORE_GOVERNANCE_GATES) - set(matrix.governance_gate_refs))
            and not matrix.missing_gate_refs
            and not (set(matrix.plugin_kind_refs) - set(coverage_map))
            and all(coverage_map.get(plugin) == "covered" for plugin in matrix.plugin_kind_refs)
        )


class L5CapabilityReadinessMatrixValidator:
    def check(self, matrix: L5CapabilityReadinessMatrix) -> bool:
        required_caps = set(_GENERAL_CAPABILITY_KINDS + _PRODUCTION_CAPABILITY_KINDS + _AFFECTIVE_CAPABILITY_KINDS)
        readiness_map = dict(matrix.readiness_rows)
        if matrix.blocking_reason_refs or required_caps - set(matrix.capability_kind_refs) or required_caps - set(readiness_map):
            return False
        if any(readiness_map.get(capability) != "l6_planning_only" for capability in _PRODUCTION_CAPABILITY_KINDS + _AFFECTIVE_CAPABILITY_KINDS):
            return False
        if (
            matrix.allow_execute_product_artifact_factory
            or matrix.allow_execute_affective_plugin
            or matrix.product_artifact_factory_scope != "l6_planning_only"
            or matrix.affective_plugin_scope != "l6_planning_only"
        ):
            return False
        if matrix.product_artifact_factory_precheck_result == GENERIC_HOST_BLOCK_TOOL_ONLY:
            return not matrix.artifact_factory_ready and not matrix.product_builder_ready
        return (
            matrix.artifact_factory_ready
            and matrix.product_builder_ready
            and matrix.artifact_factory_l6_planning_only
            and matrix.product_builder_l6_planning_only
        )


class L5FinalPublicProjectionBuilder:
    def make_projection(self, *, quality_gate: L5FinalQualityGateDecision) -> L5FinalPublicProjection:
        return L5FinalPublicProjection(
            quality_gate_summary=(
                ("allow_freeze_l5", str(quality_gate.allow_freeze_l5)),
                ("allow_enter_l6_general_plugins", str(quality_gate.allow_enter_l6_general_plugins)),
                ("allow_plan_l6_product_artifact_factory", str(quality_gate.allow_plan_l6_product_artifact_factory)),
                ("allow_execute_product_artifact_factory", str(quality_gate.allow_execute_product_artifact_factory)),
                ("product_artifact_factory_scope", quality_gate.product_artifact_factory_scope),
                ("allow_plan_l6_affective_plugin", str(quality_gate.allow_plan_l6_affective_plugin)),
                ("allow_execute_l6_affective_plugin", str(quality_gate.allow_execute_l6_affective_plugin)),
                ("affective_plugin_scope", quality_gate.affective_plugin_scope),
            ),
            redacted_evidence_refs=("evidence:redacted:l5_final_quality_gate",),
            trace_ref=quality_gate.trace_ref,
            responsibility_chain_ref=quality_gate.responsibility_chain_ref,
        )


class L5FinalQualityGate:
    def decide(self, **kwargs: Any) -> L5FinalQualityGateDecision:
        return L5FinalQualityGateDecision(**kwargs)


class L5FinalAuditIndexBuilder:
    def make_index(self, *, quality_gate: L5FinalQualityGateDecision, projection: L5FinalPublicProjection, handoff: L5L6HandoffFreeze) -> L5FinalAuditIndex:
        return L5FinalAuditIndex(
            public_projection_refs=(projection.projection_ref,),
            quality_gate_refs=(quality_gate.decision_ref,),
            handoff_refs=(handoff.l6_handoff_freeze_ref,),
            evidence_refs=quality_gate.evidence_index_refs or ("evidence:l5_final_audit",),
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
class L5FinalInvariantSuite:
    suite_ref: str = "invariant_suite:l5_final"
    no_live_plugin_execution: bool = True
    no_live_l4_adapter_call: bool = True
    no_live_tool_call: bool = True
    no_live_artifact_build: bool = True
    no_legacy_runtime: bool = True
    no_l6_implementation: bool = True
    l6_handoff_not_authorization: bool = True
    product_artifact_factory_l6_planning_only: bool = True
    affective_plugin_l6_planning_only: bool = True
    affective_state_not_authorization: bool = True
    affective_no_policy_bypass: bool = True
    affective_no_core_mutation: bool = True
    affective_no_side_effect: bool = True

    def __post_init__(self) -> None:
        ensure_ref_text(self.suite_ref, "L5FinalInvariantSuite.suite_ref")
        for item in fields(self):
            if item.name != "suite_ref":
                ensure_bool(getattr(self, item.name), f"L5FinalInvariantSuite.{item.name}")


__all__ = (
    "PHASE8_PHASE",
    "L5_FINAL_PHASE",
    "L5FinalConflictSeverity",
    "L5FinalConflictKind",
    "AFFECTIVE_PLUGIN_KIND_REF",
    "AFFECTIVE_CAPABILITY_KIND_REFS",
    "AFFECTIVE_ALLOWED_MODULATION_REFS",
    "AFFECTIVE_FORBIDDEN_MISUSE_REFS",
    "L5ClosureSummary",
    "L5FreezeManifest",
    "L5FinalPublicProjection",
    "L5L6HandoffFreeze",
    "L5GovernanceCoverageMatrix",
    "L5CapabilityReadinessMatrix",
    "L5FinalQualityGateDecision",
    "L5FinalAuditIndex",
    "L5FinalInvariantSuite",
    "L5ClosureValidator",
    "L5FreezeManifestValidator",
    "L5FinalPublicProjectionBuilder",
    "L5L6HandoffFreezeValidator",
    "L5GovernanceCoverageMatrixValidator",
    "L5CapabilityReadinessMatrixValidator",
    "L5FinalQualityGate",
    "L5FinalAuditIndexBuilder",
    "phase8_declaration_digest",
    "has_forbidden_phase8_method",
    "has_forbidden_phase8_field_name",
    "has_live_phase8_locator",
    "phase8_public_text_is_safe",
)
