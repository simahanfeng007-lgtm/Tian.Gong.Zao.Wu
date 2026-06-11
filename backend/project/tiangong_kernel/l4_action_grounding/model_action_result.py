"""Model action result objects for L4 phase 4."""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from .audit_requirement import AuditRequirementRef
from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_short_text, ensure_true


@dataclass(frozen=True, slots=True)
class ModelActionResult:
    """Standardized model action result; it never writes state or audit."""

    result_ref: TypedRef
    request_ref: TypedRef
    output_ref: TypedRef | None = None
    usage_summary: str = ""
    observation_ref: TypedRef | None = None
    audit_requirement_ref: AuditRequirementRef | None = None
    trace_ref: TypedRef | None = None
    resource_usage_report_ref: TypedRef | None = None
    cost_actual_ref: TypedRef | None = None
    quota_result_ref: TypedRef | None = None
    rate_limit_result_ref: TypedRef | None = None
    payload_items: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    dry_run_only: bool = True
    fake_result: bool = False
    real_model_called: bool = False
    result_only: bool = True
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_short_text(self.usage_summary, "ModelActionResult.usage_summary")
        for key, value in self.payload_items:
            ensure_short_text(key, "ModelActionResult.payload key", 128)
            ensure_short_text(value, "ModelActionResult.payload value")
        ensure_false(self.real_model_called, "ModelActionResult.real_model_called")
        ensure_true(self.result_only, "ModelActionResult.result_only")
        ensure_schema_version(self.schema_version, "ModelActionResult.schema_version")

    @property
    def has_structured_cost_actual_refs(self) -> bool:
        return self.resource_usage_report_ref is not None and self.cost_actual_ref is not None
