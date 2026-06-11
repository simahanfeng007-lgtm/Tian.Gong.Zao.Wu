"""L6 event contract declarations.

Events are ref/summary/digest envelopes only. A contract never links plugin
functions together and never mutates another plugin's state.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from ._common import L6_COMMON_SCHEMA_VERSION, ensure_ref_items, ensure_ref_text, ensure_schema_version


class L6EventPayloadPolicy(str, Enum):
    REF_ONLY = "ref_only"
    SUMMARY_ONLY = "summary_only"
    DIGEST_ONLY = "digest_only"
    REF_SUMMARY_DIGEST_ONLY = "ref_summary_digest_only"


@dataclass(frozen=True, slots=True)
class L6EventContract:
    event_contract_ref: str = "event:l6_event_contract"
    event_kind_ref: str = "event:l6_event_kind"
    producer_plugin_ref: str = "l6:producer_plugin_ref"
    consumer_group_refs: tuple[str, ...] = field(default_factory=lambda: ("l6:consumer_group_ref",))
    payload_policy: L6EventPayloadPolicy | str = L6EventPayloadPolicy.REF_SUMMARY_DIGEST_ONLY
    allowed_payload_ref_kinds: tuple[str, ...] = field(default_factory=lambda: ("ref", "summary", "digest"))
    forbidden_payload_refs: tuple[str, ...] = field(default_factory=lambda: ("forbid:raw_context", "forbid:credential", "forbid:callable", "forbid:tool_schema", "forbid:function_schema"))
    schema_ref: str = "decl:l6_event_schema_ref"
    version_ref: str = "decl:l6_event_version_ref"
    audit_requirement_ref: str = "audit:l6_event_audit_requirement"
    no_direct_plugin_function_call: bool = True
    no_direct_state_write: bool = True
    no_implicit_cycle: bool = True
    no_raw_payload: bool = True
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.event_contract_ref, "L6EventContract.event_contract_ref")
        ensure_ref_text(self.event_kind_ref, "L6EventContract.event_kind_ref")
        ensure_ref_text(self.producer_plugin_ref, "L6EventContract.producer_plugin_ref")
        ensure_ref_items(self.consumer_group_refs, "L6EventContract.consumer_group_refs", required=True)
        object.__setattr__(self, "payload_policy", L6EventPayloadPolicy(self.payload_policy))
        ensure_ref_items(self.allowed_payload_ref_kinds, "L6EventContract.allowed_payload_ref_kinds", required=True)
        ensure_ref_items(self.forbidden_payload_refs, "L6EventContract.forbidden_payload_refs", required=True)
        ensure_ref_text(self.schema_ref, "L6EventContract.schema_ref")
        ensure_ref_text(self.version_ref, "L6EventContract.version_ref")
        ensure_ref_text(self.audit_requirement_ref, "L6EventContract.audit_requirement_ref")
        if not self.no_direct_plugin_function_call or not self.no_direct_state_write or not self.no_implicit_cycle or not self.no_raw_payload:
            raise ValueError("L6 events must stay ref/summary/digest only and cannot directly connect plugins or states")
        ensure_schema_version(self.schema_version)
