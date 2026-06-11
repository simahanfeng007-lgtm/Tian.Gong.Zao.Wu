"""L6 phase2 plugin handoff and return-path envelopes."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from ._common import (
    L6_COMMON_SCHEMA_VERSION,
    ensure_bool,
    ensure_digest,
    ensure_no_live_or_sensitive_text,
    ensure_ref_items,
    ensure_ref_text,
    ensure_schema_version,
    stable_digest,
)
from .audit import L6AuditTraceEnvelope


class L6HandoffKind(str, Enum):
    INVOCATION_REQUEST = "invocation_request"
    COLLABORATION_REQUEST = "collaboration_request"
    DELEGATION_REQUEST = "delegation_request"
    RESULT_RETURN = "result_return"
    FAILURE_RETURN = "failure_return"
    ACK = "ack"
    NACK = "nack"
    CANCEL = "cancel"
    TIMEOUT = "timeout"
    ESCALATION = "escalation"
    AGGREGATION = "aggregation"
    PROJECTION_EMITTED = "projection_emitted"
    CLOSED = "closed"


@dataclass(frozen=True, slots=True)
class VersionedPluginHandoffEnvelope:
    envelope_id: str = "handoff:l6_phase2_envelope"
    schema_version: str = L6_COMMON_SCHEMA_VERSION
    handoff_ref: str = "handoff:l6_phase2_handoff"
    handoff_kind: L6HandoffKind | str = L6HandoffKind.INVOCATION_REQUEST
    created_at_ref: str = "ref:l6_handoff_created_at"
    source_plugin_ref: str = "l6:source_plugin"
    source_plugin_version_ref: str = "ref:l6_source_plugin_version"
    target_plugin_ref: str = "l6:target_plugin"
    target_plugin_kind_ref: str = "ref:l6_target_plugin_kind"
    receiver_selector_ref: str = "ref:l6_receiver_selector"
    sender_actor_ref: str = "ref:l6_sender_actor"
    receiver_actor_ref: str = "ref:l6_receiver_actor"
    sender_plugin_ref: str = "l6:sender_plugin"
    receiver_plugin_ref: str = "l6:receiver_plugin"
    receiver_requirement_ref: str = "ref:l6_receiver_requirement"
    parent_message_ref: str = "ref:l6_parent_message"
    parent_handoff_ref: str = "handoff:l6_parent_handoff"
    root_marker: str = "ref:l6_root_marker"
    parent_task_ref: str = "ref:l6_parent_task"
    child_task_refs: tuple[str, ...] = field(default_factory=tuple)
    trace_ref: str = "ref:l6_handoff_trace"
    conversation_ref: str = "ref:l6_conversation"
    channel_ref: str = "ref:l6_channel"
    protocol_ref: str = "ref:l6_protocol"
    scope_ref: str = "ref:l6_scope"
    authority_ref: str = "policy:l6_no_authority_transfer"
    policy_refs: tuple[str, ...] = field(default_factory=lambda: ("policy:l6_handoff_not_authorization",))
    lease_ref: str = "ref:l6_handoff_lease"
    budget_ref: str = "budget:l6_handoff_budget"
    context_summary_ref: str = "summary:l6_handoff_context_summary"
    input_refs: tuple[str, ...] = field(default_factory=lambda: ("ref:l6_handoff_input",))
    input_digest: str = ""
    payload_schema_ref: str = "handoff:l6_handoff_payload_schema"
    output_contract_ref: str = "ref:l6_handoff_output_contract"
    result_return_ref: str = "handoff:l6_result_return"
    failure_return_ref: str = "handoff:l6_failure_return"
    responsibility_chain_ref: str = "responsibility:l6_handoff_chain"
    accountability_ref: str = "responsibility:l6_handoff_accountability"
    evidence_refs: tuple[str, ...] = field(default_factory=lambda: ("evidence:l6_handoff",))
    provenance_refs: tuple[str, ...] = field(default_factory=lambda: ("evidence:l6_handoff_provenance",))
    redaction_policy_ref: str = "policy:l6_handoff_redaction"
    deadline_ref: str = "ref:l6_handoff_deadline"
    idempotency_key_ref: str = "ref:l6_handoff_idempotency"
    replay_policy_ref: str = "policy:l6_handoff_replay"
    tamper_evidence_ref: str = "evidence:l6_handoff_tamper"
    compatibility_matrix_ref: str = "ref:l6_handoff_compatibility_matrix"
    migration_note_ref: str = "migration:l6_handoff_migration_note"
    rollback_anchor_ref: str = "rollback:l6_handoff_rollback_anchor"
    rollback_route_ref: str = "rollback:l6_handoff_rollback_route"
    replay_compatibility_ref: str = "ref:l6_handoff_replay_compatibility"
    no_auto_merge_guarantee_ref: str = "policy:l6_handoff_no_auto_merge"
    public_projection_ref: str = "public:l6_handoff_projection"
    audit_trace: L6AuditTraceEnvelope = field(default_factory=L6AuditTraceEnvelope)
    transfers_authorization: bool = False
    auto_merge_allowed: bool = False
    direct_target_plugin_call: bool = False
    bypasses_l3_l5: bool = False
    writes_state: bool = False
    stale: bool = False
    duplicate: bool = False

    def __post_init__(self) -> None:
        ensure_schema_version(self.schema_version)
        object.__setattr__(self, "handoff_kind", L6HandoffKind(self.handoff_kind))
        for field_name in (
            "envelope_id",
            "handoff_ref",
            "created_at_ref",
            "source_plugin_ref",
            "source_plugin_version_ref",
            "target_plugin_ref",
            "target_plugin_kind_ref",
            "receiver_selector_ref",
            "sender_actor_ref",
            "receiver_actor_ref",
            "sender_plugin_ref",
            "receiver_plugin_ref",
            "receiver_requirement_ref",
            "parent_message_ref",
            "parent_handoff_ref",
            "root_marker",
            "parent_task_ref",
            "trace_ref",
            "conversation_ref",
            "channel_ref",
            "protocol_ref",
            "scope_ref",
            "authority_ref",
            "lease_ref",
            "budget_ref",
            "context_summary_ref",
            "payload_schema_ref",
            "output_contract_ref",
            "result_return_ref",
            "failure_return_ref",
            "responsibility_chain_ref",
            "accountability_ref",
            "redaction_policy_ref",
            "deadline_ref",
            "idempotency_key_ref",
            "replay_policy_ref",
            "tamper_evidence_ref",
            "compatibility_matrix_ref",
            "migration_note_ref",
            "rollback_anchor_ref",
            "rollback_route_ref",
            "replay_compatibility_ref",
            "no_auto_merge_guarantee_ref",
            "public_projection_ref",
        ):
            ensure_ref_text(getattr(self, field_name), f"VersionedPluginHandoffEnvelope.{field_name}")
        for field_name in ("child_task_refs", "policy_refs", "input_refs", "evidence_refs", "provenance_refs"):
            ensure_ref_items(getattr(self, field_name), f"VersionedPluginHandoffEnvelope.{field_name}")
        ensure_digest(self.input_digest, "VersionedPluginHandoffEnvelope.input_digest", required=False)
        if not isinstance(self.audit_trace, L6AuditTraceEnvelope):
            raise ValueError("VersionedPluginHandoffEnvelope.audit_trace must be L6AuditTraceEnvelope")
        for field_name in (
            "transfers_authorization",
            "auto_merge_allowed",
            "direct_target_plugin_call",
            "bypasses_l3_l5",
            "writes_state",
            "stale",
            "duplicate",
        ):
            ensure_bool(getattr(self, field_name), f"VersionedPluginHandoffEnvelope.{field_name}")
        if self.transfers_authorization or self.auto_merge_allowed or self.direct_target_plugin_call or self.bypasses_l3_l5 or self.writes_state:
            raise ValueError("L6 handoff is not authorization, auto-merge, direct plugin call, bypass, or state write")
        ensure_schema_version(self.schema_version)

    @property
    def handoff_is_auto_merge(self) -> bool:
        return False

    @property
    def handoff_is_execution_authorization(self) -> bool:
        return False

    @property
    def has_quality_evidence(self) -> bool:
        return bool(self.trace_ref and self.policy_refs and self.evidence_refs and self.responsibility_chain_ref)

    @property
    def digest(self) -> str:
        return stable_digest(self)


@dataclass(frozen=True, slots=True)
class ResultReturnEnvelope(VersionedPluginHandoffEnvelope):
    handoff_kind: L6HandoffKind | str = L6HandoffKind.RESULT_RETURN
    result_summary_ref: str = "summary:l6_result_return"
    result_digest: str = ""
    no_auto_merge: bool = True

    def __post_init__(self) -> None:
        VersionedPluginHandoffEnvelope.__post_init__(self)
        ensure_ref_text(self.result_summary_ref, "ResultReturnEnvelope.result_summary_ref")
        ensure_digest(self.result_digest, "ResultReturnEnvelope.result_digest", required=False)
        if not self.parent_handoff_ref or self.parent_handoff_ref == "":
            raise ValueError("L6 result return requires parent_handoff_ref")
        if not self.no_auto_merge:
            raise ValueError("L6 result return cannot auto-merge")


@dataclass(frozen=True, slots=True)
class FailureReturnEnvelope(VersionedPluginHandoffEnvelope):
    handoff_kind: L6HandoffKind | str = L6HandoffKind.FAILURE_RETURN
    failure_reason_ref: str = "ref:l6_failure_reason"
    failure_evidence_refs: tuple[str, ...] = field(default_factory=lambda: ("evidence:l6_failure",))

    def __post_init__(self) -> None:
        VersionedPluginHandoffEnvelope.__post_init__(self)
        ensure_ref_text(self.failure_reason_ref, "FailureReturnEnvelope.failure_reason_ref")
        ensure_ref_items(self.failure_evidence_refs, "FailureReturnEnvelope.failure_evidence_refs", required=True)


@dataclass(frozen=True, slots=True)
class AckEnvelope(VersionedPluginHandoffEnvelope):
    handoff_kind: L6HandoffKind | str = L6HandoffKind.ACK
    ack_summary: str = "summary:received_for_governance"
    starts_work: bool = False
    means_success: bool = False
    grants_authorization: bool = False

    def __post_init__(self) -> None:
        VersionedPluginHandoffEnvelope.__post_init__(self)
        ensure_no_live_or_sensitive_text(self.ack_summary, "AckEnvelope.ack_summary")
        if self.starts_work or self.means_success or self.grants_authorization:
            raise ValueError("L6 ACK only confirms receipt into governance chain")


@dataclass(frozen=True, slots=True)
class NackEnvelope(VersionedPluginHandoffEnvelope):
    handoff_kind: L6HandoffKind | str = L6HandoffKind.NACK
    rejection_reason_ref: str = "ref:l6_nack_reason"
    rejection_evidence_refs: tuple[str, ...] = field(default_factory=lambda: ("evidence:l6_nack",))

    def __post_init__(self) -> None:
        VersionedPluginHandoffEnvelope.__post_init__(self)
        ensure_ref_text(self.rejection_reason_ref, "NackEnvelope.rejection_reason_ref")
        ensure_ref_items(self.rejection_evidence_refs, "NackEnvelope.rejection_evidence_refs", required=True)


@dataclass(frozen=True, slots=True)
class CancelEnvelope(VersionedPluginHandoffEnvelope):
    handoff_kind: L6HandoffKind | str = L6HandoffKind.CANCEL
    cancel_reason_ref: str = "ref:l6_cancel_reason"

    def __post_init__(self) -> None:
        VersionedPluginHandoffEnvelope.__post_init__(self)
        ensure_ref_text(self.cancel_reason_ref, "CancelEnvelope.cancel_reason_ref")


@dataclass(frozen=True, slots=True)
class TimeoutEnvelope(VersionedPluginHandoffEnvelope):
    handoff_kind: L6HandoffKind | str = L6HandoffKind.TIMEOUT
    timeout_policy_ref: str = "policy:l6_timeout_policy"
    fallback_handoff_ref: str = "handoff:l6_timeout_fallback"

    def __post_init__(self) -> None:
        VersionedPluginHandoffEnvelope.__post_init__(self)
        ensure_ref_text(self.timeout_policy_ref, "TimeoutEnvelope.timeout_policy_ref")
        ensure_ref_text(self.fallback_handoff_ref, "TimeoutEnvelope.fallback_handoff_ref")


@dataclass(frozen=True, slots=True)
class AggregationEnvelope(VersionedPluginHandoffEnvelope):
    handoff_kind: L6HandoffKind | str = L6HandoffKind.AGGREGATION
    result_return_refs: tuple[str, ...] = field(default_factory=lambda: ("handoff:l6_result_return",))
    aggregation_projection_ref: str = "projection:l6_result_aggregation"
    auto_merge: bool = False

    def __post_init__(self) -> None:
        VersionedPluginHandoffEnvelope.__post_init__(self)
        ensure_ref_items(self.result_return_refs, "AggregationEnvelope.result_return_refs", required=True)
        ensure_ref_text(self.aggregation_projection_ref, "AggregationEnvelope.aggregation_projection_ref")
        if self.auto_merge:
            raise ValueError("L6 aggregation is not auto-merge")


@dataclass(frozen=True, slots=True)
class MessageEnvelopeContract:
    contract_ref: str = "handoff:l6_message_envelope_contract"
    trace_required: bool = True
    evidence_required: bool = True
    responsibility_required: bool = True
    direct_channel_allowed: bool = False
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.contract_ref, "MessageEnvelopeContract.contract_ref")
        if not self.trace_required or not self.evidence_required or not self.responsibility_required or self.direct_channel_allowed:
            raise ValueError("L6 message envelopes require trace/evidence/responsibility and no direct channel")
        ensure_schema_version(self.schema_version)


@dataclass(frozen=True, slots=True)
class HandoffEnvelopeContract(MessageEnvelopeContract):
    contract_ref: str = "handoff:l6_handoff_envelope_contract"
    auto_merge_allowed: bool = False

    def __post_init__(self) -> None:
        MessageEnvelopeContract.__post_init__(self)
        if self.auto_merge_allowed:
            raise ValueError("L6 handoff envelope contract forbids auto-merge")


@dataclass(frozen=True, slots=True)
class ResultReturnEnvelopeContract(HandoffEnvelopeContract):
    contract_ref: str = "handoff:l6_result_return_envelope_contract"
    parent_handoff_required: bool = True

    def __post_init__(self) -> None:
        HandoffEnvelopeContract.__post_init__(self)
        if not self.parent_handoff_required:
            raise ValueError("L6 result return requires parent handoff")


@dataclass(frozen=True, slots=True)
class FailureReturnEnvelopeContract(HandoffEnvelopeContract):
    contract_ref: str = "handoff:l6_failure_return_envelope_contract"
    failure_reason_required: bool = True

    def __post_init__(self) -> None:
        HandoffEnvelopeContract.__post_init__(self)
        if not self.failure_reason_required:
            raise ValueError("L6 failure return requires failure reason")


@dataclass(frozen=True, slots=True)
class AckNackEnvelopeContract(HandoffEnvelopeContract):
    contract_ref: str = "handoff:l6_ack_nack_envelope_contract"
    ack_is_only_receipt: bool = True
    nack_requires_reason: bool = True

    def __post_init__(self) -> None:
        HandoffEnvelopeContract.__post_init__(self)
        if not self.ack_is_only_receipt or not self.nack_requires_reason:
            raise ValueError("L6 ACK/NACK contract preserves receipt-only ACK and reasoned NACK")
