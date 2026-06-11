"""Desktop action result envelopes for L4 phase 5."""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_short_text, ensure_true


@dataclass(frozen=True, slots=True)
class DesktopActionResult:
    """Standard desktop action result; UI observation is represented by ref."""

    result_ref: TypedRef
    request_ref: TypedRef
    ui_observation_ref: TypedRef | None = None
    gesture_result_ref: TypedRef | None = None
    audit_requirement_ref: TypedRef | None = None
    resource_usage_summary: str = "none"
    payload_items: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    dry_run_only: bool = False
    fake_result: bool = False
    no_op_result: bool = False
    real_desktop_control: bool = False
    real_screen_access: bool = False
    real_input_sent: bool = False
    writes_l2_state: bool = False
    writes_audit_store: bool = False
    result_envelope_only: bool = True
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_short_text(self.resource_usage_summary, "DesktopActionResult.resource_usage_summary")
        for key, value in self.payload_items:
            ensure_short_text(key, "DesktopActionResult.payload_items key", 128)
            ensure_short_text(value, "DesktopActionResult.payload_items value")
        ensure_false(self.real_desktop_control, "DesktopActionResult.real_desktop_control")
        ensure_false(self.real_screen_access, "DesktopActionResult.real_screen_access")
        ensure_false(self.real_input_sent, "DesktopActionResult.real_input_sent")
        ensure_false(self.writes_l2_state, "DesktopActionResult.writes_l2_state")
        ensure_false(self.writes_audit_store, "DesktopActionResult.writes_audit_store")
        ensure_true(self.result_envelope_only, "DesktopActionResult.result_envelope_only")
        ensure_schema_version(self.schema_version, "DesktopActionResult.schema_version")
