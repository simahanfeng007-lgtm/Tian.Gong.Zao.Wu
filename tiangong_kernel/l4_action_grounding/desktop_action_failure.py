"""Desktop action failures for L4 phase 5."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef

from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_short_text, ensure_true


class DesktopActionFailureKind(str, Enum):
    DISABLED_BY_DEFAULT = "disabled_by_default"
    PERMIT_MISSING = "permit_missing"
    UI_SCOPE_MISMATCH = "ui_scope_mismatch"
    INPUT_BLOCKED = "input_blocked"
    SCREEN_ACCESS_BLOCKED = "screen_access_blocked"
    WINDOW_CONTROL_BLOCKED = "window_control_blocked"
    REAL_ACTION_FORBIDDEN = "real_action_forbidden"


@dataclass(frozen=True, slots=True)
class DesktopActionFailure:
    """Standard desktop action failure; no desktop control is performed."""

    failure_ref: TypedRef
    request_ref: TypedRef
    failure_kind: DesktopActionFailureKind = DesktopActionFailureKind.DISABLED_BY_DEFAULT
    message: str = "desktop action disabled by default"
    blocked_invariant_names: tuple[str, ...] = field(default_factory=tuple)
    boundary_feedback_ref: TypedRef | None = None
    audit_requirement_ref: TypedRef | None = None
    requires_l5_permit: bool = True
    real_desktop_control: bool = False
    real_screen_access: bool = False
    real_input_sent: bool = False
    writes_l2_state: bool = False
    writes_audit_store: bool = False
    retryable: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_short_text(self.message, "DesktopActionFailure.message")
        for item in self.blocked_invariant_names:
            ensure_short_text(item, "DesktopActionFailure.blocked_invariant_names", 128)
        ensure_true(self.requires_l5_permit, "DesktopActionFailure.requires_l5_permit")
        ensure_false(self.real_desktop_control, "DesktopActionFailure.real_desktop_control")
        ensure_false(self.real_screen_access, "DesktopActionFailure.real_screen_access")
        ensure_false(self.real_input_sent, "DesktopActionFailure.real_input_sent")
        ensure_false(self.writes_l2_state, "DesktopActionFailure.writes_l2_state")
        ensure_false(self.writes_audit_store, "DesktopActionFailure.writes_audit_store")
        ensure_false(self.retryable, "DesktopActionFailure.retryable")
        ensure_schema_version(self.schema_version, "DesktopActionFailure.schema_version")
