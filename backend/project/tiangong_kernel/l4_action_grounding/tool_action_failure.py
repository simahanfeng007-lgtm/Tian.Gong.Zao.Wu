"""Tool action failure objects for L4 phase 4."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef

from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_short_text, ensure_true
from .tool_failure_envelope import ToolFailureEnvelope


class ToolActionFailureKind(str, Enum):
    TOOL_NOT_FOUND_REF = "tool_not_found_ref"
    ADAPTER_DISABLED = "adapter_disabled"
    PERMIT_MISSING = "permit_missing"
    PERMIT_SCOPE_MISMATCH = "permit_scope_mismatch"
    ARGUMENT_INVALID = "argument_invalid"
    RESULT_NORMALIZATION_FAILED = "result_normalization_failed"
    SIDE_EFFECT_BLOCKED = "side_effect_blocked"


@dataclass(frozen=True, slots=True)
class ToolActionFailure:
    """Standardized tool action failure; no tool registry is implemented."""

    failure_ref: TypedRef
    request_ref: TypedRef | None = None
    failure_kind: ToolActionFailureKind = ToolActionFailureKind.ADAPTER_DISABLED
    tool_not_found_ref: TypedRef | None = None
    failure_envelope: ToolFailureEnvelope | None = None
    message: str = "tool action is disabled in L4 phase 4"
    recoverability_hint: str = "replan_or_stop"
    retry_allowed_hint: bool = False
    real_tool_called: bool = False
    failure_only: bool = True
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_short_text(self.message, "ToolActionFailure.message")
        ensure_short_text(self.recoverability_hint, "ToolActionFailure.recoverability_hint", 128)
        ensure_false(self.retry_allowed_hint, "ToolActionFailure.retry_allowed_hint")
        ensure_false(self.real_tool_called, "ToolActionFailure.real_tool_called")
        ensure_true(self.failure_only, "ToolActionFailure.failure_only")
        ensure_schema_version(self.schema_version, "ToolActionFailure.schema_version")
