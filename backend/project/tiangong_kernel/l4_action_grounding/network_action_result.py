"""Network action result envelopes for L4 phase 5."""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_short_text, ensure_true


@dataclass(frozen=True, slots=True)
class NetworkActionResult:
    """Standard network action result; response content is represented by ref."""

    result_ref: TypedRef
    request_ref: TypedRef
    response_ref: TypedRef | None = None
    status_ref: TypedRef | None = None
    observation_ref: TypedRef | None = None
    usage_summary: str = "none"
    audit_requirement_ref: TypedRef | None = None
    payload_items: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    dry_run_only: bool = False
    fake_result: bool = False
    no_op_result: bool = False
    real_network_access: bool = False
    caches_real_response_body: bool = False
    writes_l2_state: bool = False
    writes_audit_store: bool = False
    result_envelope_only: bool = True
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_short_text(self.usage_summary, "NetworkActionResult.usage_summary")
        for key, value in self.payload_items:
            ensure_short_text(key, "NetworkActionResult.payload_items key", 128)
            ensure_short_text(value, "NetworkActionResult.payload_items value")
        ensure_false(self.real_network_access, "NetworkActionResult.real_network_access")
        ensure_false(self.caches_real_response_body, "NetworkActionResult.caches_real_response_body")
        ensure_false(self.writes_l2_state, "NetworkActionResult.writes_l2_state")
        ensure_false(self.writes_audit_store, "NetworkActionResult.writes_audit_store")
        ensure_true(self.result_envelope_only, "NetworkActionResult.result_envelope_only")
        ensure_schema_version(self.schema_version, "NetworkActionResult.schema_version")
