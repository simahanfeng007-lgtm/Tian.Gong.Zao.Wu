"""Tool result envelope for L4 phase 4."""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from .audit_requirement import AuditRequirementRef
from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_short_text, ensure_true


@dataclass(frozen=True, slots=True)
class ToolResultEnvelope:
    """Standardized tool result; it returns data, not state mutation."""

    result_ref: TypedRef
    output_ref: TypedRef | None = None
    normalized_output: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    observation_ref: TypedRef | None = None
    evidence_ref: TypedRef | None = None
    audit_requirement_ref: AuditRequirementRef | None = None
    resource_usage_summary: str = ""
    side_effect_summary: str = "none"
    trace_ref: TypedRef | None = None
    dry_run_only: bool = True
    fake_result: bool = False
    real_tool_called: bool = False
    result_envelope_only: bool = True
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for value in (self.resource_usage_summary, self.side_effect_summary):
            ensure_short_text(value, "ToolResultEnvelope text")
        for key, value in self.normalized_output:
            ensure_short_text(key, "ToolResultEnvelope.output key", 128)
            ensure_short_text(value, "ToolResultEnvelope.output value")
        ensure_false(self.real_tool_called, "ToolResultEnvelope.real_tool_called")
        ensure_true(self.result_envelope_only, "ToolResultEnvelope.result_envelope_only")
        ensure_schema_version(self.schema_version, "ToolResultEnvelope.schema_version")
