"""Tool failure envelope for L4 phase 4."""

from __future__ import annotations

from dataclasses import dataclass

from tiangong_kernel.l0_primitives.identity import TypedRef

from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_short_text, ensure_true


@dataclass(frozen=True, slots=True)
class ToolFailureEnvelope:
    """Standardized tool failure envelope; safe for L3 re-planning."""

    failure_ref: TypedRef
    failure_category: str = "tool_action"
    failure_severity: str = "recoverable"
    failure_code: str = "adapter_disabled"
    message: str = "tool action is disabled in L4 phase 4"
    recoverability_hint: str = "replan_or_stop"
    replan_suggestion_ref: TypedRef | None = None
    boundary_recheck_required_hint: bool = False
    retry_allowed_hint: bool = False
    real_tool_called: bool = False
    failure_envelope_only: bool = True
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for value in (self.failure_category, self.failure_severity, self.failure_code, self.message, self.recoverability_hint):
            ensure_short_text(value, "ToolFailureEnvelope text")
        ensure_false(self.retry_allowed_hint, "ToolFailureEnvelope.retry_allowed_hint")
        ensure_false(self.real_tool_called, "ToolFailureEnvelope.real_tool_called")
        ensure_true(self.failure_envelope_only, "ToolFailureEnvelope.failure_envelope_only")
        ensure_schema_version(self.schema_version, "ToolFailureEnvelope.schema_version")
