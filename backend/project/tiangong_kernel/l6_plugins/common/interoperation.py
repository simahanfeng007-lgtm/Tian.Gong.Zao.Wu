"""L6 phase2 plugin interoperation boundary declarations."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from ._common import L6_COMMON_SCHEMA_VERSION, ensure_bool, ensure_ref_items, ensure_ref_text, ensure_schema_version, stable_digest
from .audit import L6AuditTraceEnvelope


class L6InteroperationMode(str, Enum):
    EVENT = "event"
    STATE_PROJECTION = "state_projection"
    HANDOFF = "handoff"
    HOST_MEDIATED_INVOCATION = "host_mediated_invocation"
    PUBLIC_PROJECTION_READ = "public_projection_read"
    REQUIREMENT_RESOLUTION = "requirement_resolution"


class L6ForbiddenInteroperationMode(str, Enum):
    DIRECT_IMPORT = "direct_import"
    DIRECT_CALL = "direct_call"
    DIRECT_STATE_WRITE = "direct_state_write"
    SHARED_GLOBAL_OBJECT = "shared_global_object"
    SHARED_MUTABLE_CACHE = "shared_mutable_cache"
    SHARED_CREDENTIAL = "shared_credential"
    SHARED_BUDGET_ACCOUNT = "shared_budget_account"
    HIDDEN_CALLBACK = "hidden_callback"
    BACKGROUND_LISTENER = "background_listener"
    PRIVATE_SOCKET = "private_socket"
    PRIVATE_QUEUE = "private_queue"
    PRIVATE_FILE_DROP = "private_file_drop"
    DIRECT_EVENT_QUEUE = "direct_event_queue"
    DIRECT_TOOL_REGISTRY = "direct_tool_registry"
    DIRECT_MODEL_CLIENT = "direct_model_client"


@dataclass(frozen=True, slots=True)
class PluginInteroperationBoundaryContract:
    boundary_contract_ref: str = "ref:l6_phase2_interoperation_boundary"
    allowed_interaction_modes: tuple[L6InteroperationMode | str, ...] = field(
        default_factory=lambda: (
            L6InteroperationMode.EVENT,
            L6InteroperationMode.STATE_PROJECTION,
            L6InteroperationMode.HANDOFF,
            L6InteroperationMode.HOST_MEDIATED_INVOCATION,
            L6InteroperationMode.PUBLIC_PROJECTION_READ,
            L6InteroperationMode.REQUIREMENT_RESOLUTION,
        )
    )
    forbidden_interaction_modes: tuple[L6ForbiddenInteroperationMode | str, ...] = field(
        default_factory=lambda: tuple(mode for mode in L6ForbiddenInteroperationMode)
    )
    event_contract_refs: tuple[str, ...] = field(default_factory=lambda: ("event:l6_phase2_event_contract",))
    projection_contract_refs: tuple[str, ...] = field(default_factory=lambda: ("projection:l6_phase2_projection_contract",))
    handoff_contract_refs: tuple[str, ...] = field(default_factory=lambda: ("handoff:l6_phase2_handoff_contract",))
    host_invocation_refs: tuple[str, ...] = field(default_factory=lambda: ("l5:l6_host_mediated_invocation",))
    cross_plugin_direct_import_allowed: bool = False
    cross_plugin_direct_call_allowed: bool = False
    cross_plugin_state_write_allowed: bool = False
    shared_mutable_state_allowed: bool = False
    parallel_runtime_allowed: bool = False
    external_authority_escalation_allowed: bool = False
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.boundary_contract_ref, "PluginInteroperationBoundaryContract.boundary_contract_ref")
        object.__setattr__(self, "allowed_interaction_modes", tuple(L6InteroperationMode(mode) for mode in self.allowed_interaction_modes))
        object.__setattr__(self, "forbidden_interaction_modes", tuple(L6ForbiddenInteroperationMode(mode) for mode in self.forbidden_interaction_modes))
        for field_name in ("event_contract_refs", "projection_contract_refs", "handoff_contract_refs", "host_invocation_refs"):
            ensure_ref_items(getattr(self, field_name), f"PluginInteroperationBoundaryContract.{field_name}", required=True)
        for field_name in (
            "cross_plugin_direct_import_allowed",
            "cross_plugin_direct_call_allowed",
            "cross_plugin_state_write_allowed",
            "shared_mutable_state_allowed",
            "parallel_runtime_allowed",
            "external_authority_escalation_allowed",
        ):
            ensure_bool(getattr(self, field_name), f"PluginInteroperationBoundaryContract.{field_name}")
        if any(
            (
                self.cross_plugin_direct_import_allowed,
                self.cross_plugin_direct_call_allowed,
                self.cross_plugin_state_write_allowed,
                self.shared_mutable_state_allowed,
                self.parallel_runtime_allowed,
                self.external_authority_escalation_allowed,
            )
        ):
            raise ValueError("L6 plugins may interoperate only through envelopes and host-mediated paths")
        ensure_schema_version(self.schema_version)

    @property
    def envelope_only(self) -> bool:
        return True


@dataclass(frozen=True, slots=True)
class InteroperationBoundaryCheck:
    boundary_check_ref: str = "ref:l6_phase2_interoperation_check"
    source_plugin_ref: str = "l6:source_plugin"
    target_plugin_ref: str = "l6:target_plugin"
    checked_plugin_refs: tuple[str, ...] = field(default_factory=lambda: ("l6:source_plugin", "l6:target_plugin"))
    allowed_interaction_modes: tuple[L6InteroperationMode | str, ...] = field(default_factory=lambda: (L6InteroperationMode.EVENT, L6InteroperationMode.STATE_PROJECTION, L6InteroperationMode.HANDOFF))
    forbidden_interaction_modes: tuple[L6ForbiddenInteroperationMode | str, ...] = field(default_factory=lambda: tuple(mode for mode in L6ForbiddenInteroperationMode))
    event_contract_refs: tuple[str, ...] = field(default_factory=lambda: ("event:l6_phase2_event_contract",))
    projection_contract_refs: tuple[str, ...] = field(default_factory=lambda: ("projection:l6_phase2_projection_contract",))
    handoff_contract_refs: tuple[str, ...] = field(default_factory=lambda: ("handoff:l6_phase2_handoff_contract",))
    host_invocation_refs: tuple[str, ...] = field(default_factory=lambda: ("l5:l6_host_mediated_invocation",))
    forbidden_import_refs: tuple[str, ...] = field(default_factory=lambda: ("forbid:l6_direct_plugin_import",))
    forbidden_call_refs: tuple[str, ...] = field(default_factory=lambda: ("forbid:l6_direct_plugin_call",))
    forbidden_state_write_refs: tuple[str, ...] = field(default_factory=lambda: ("forbid:l6_cross_plugin_state_write",))
    forbidden_shared_secret_refs: tuple[str, ...] = field(default_factory=lambda: ("forbid:l6_shared_secret",))
    forbidden_side_channel_refs: tuple[str, ...] = field(default_factory=lambda: ("forbid:l6_side_channel",))
    p0_count: int = 0
    p1_count: int = 0
    evidence_refs: tuple[str, ...] = field(default_factory=lambda: ("evidence:l6_interoperation_check",))
    trace_ref: str = "ref:l6_interoperation_trace"
    rule_source_ref: str = "policy:l6_interoperation_boundary_rules"
    detected_by_ref: str = "ref:l6_phase2_static_check"
    responsibility_chain_ref: str = "responsibility:l6_interoperation_chain"
    tamper_evidence_ref: str = "evidence:l6_interoperation_tamper"
    audit_trace: L6AuditTraceEnvelope = field(default_factory=L6AuditTraceEnvelope)
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for field_name in ("boundary_check_ref", "source_plugin_ref", "target_plugin_ref", "trace_ref", "rule_source_ref", "detected_by_ref", "responsibility_chain_ref", "tamper_evidence_ref"):
            ensure_ref_text(getattr(self, field_name), f"InteroperationBoundaryCheck.{field_name}")
        for field_name in (
            "checked_plugin_refs",
            "event_contract_refs",
            "projection_contract_refs",
            "handoff_contract_refs",
            "host_invocation_refs",
            "forbidden_import_refs",
            "forbidden_call_refs",
            "forbidden_state_write_refs",
            "forbidden_shared_secret_refs",
            "forbidden_side_channel_refs",
            "evidence_refs",
        ):
            ensure_ref_items(getattr(self, field_name), f"InteroperationBoundaryCheck.{field_name}", required=field_name != "evidence_refs" or True)
        object.__setattr__(self, "allowed_interaction_modes", tuple(L6InteroperationMode(mode) for mode in self.allowed_interaction_modes))
        object.__setattr__(self, "forbidden_interaction_modes", tuple(L6ForbiddenInteroperationMode(mode) for mode in self.forbidden_interaction_modes))
        for name in ("p0_count", "p1_count"):
            value = getattr(self, name)
            if not isinstance(value, int) or value < 0:
                raise ValueError(f"InteroperationBoundaryCheck.{name} must be non-negative integer")
        if not isinstance(self.audit_trace, L6AuditTraceEnvelope):
            raise ValueError("InteroperationBoundaryCheck.audit_trace must be L6AuditTraceEnvelope")
        ensure_schema_version(self.schema_version)

    @property
    def passed(self) -> bool:
        return self.p0_count == 0 and self.p1_count == 0

    @property
    def digest(self) -> str:
        return stable_digest(self)


@dataclass(frozen=True, slots=True)
class ActorCollaborationBoundaryContract(PluginInteroperationBoundaryContract):
    boundary_contract_ref: str = "ref:l6_actor_collaboration_boundary"
    collaboration_requires_handoff: bool = True
    collaboration_requires_result_return: bool = True

    def __post_init__(self) -> None:
        PluginInteroperationBoundaryContract.__post_init__(self)
        if not self.collaboration_requires_handoff or not self.collaboration_requires_result_return:
            raise ValueError("L6 actor collaboration must use handoff and result return envelopes")
