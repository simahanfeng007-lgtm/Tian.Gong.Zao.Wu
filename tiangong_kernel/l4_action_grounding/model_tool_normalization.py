"""Model/tool action normalization helpers for L4 phase 4."""

from __future__ import annotations

from dataclasses import dataclass

from tiangong_kernel.l0_primitives.identity import TypedRef

from .adapter_failure import new_adapter_typed_ref
from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_true
from .model_action_failure import ModelActionFailure, ModelActionFailureKind
from .model_action_result import ModelActionResult
from .tool_action_failure import ToolActionFailure, ToolActionFailureKind
from .tool_action_result import ToolActionResult
from .tool_failure_envelope import ToolFailureEnvelope
from .tool_result_envelope import ToolResultEnvelope


@dataclass(frozen=True, slots=True)
class ModelToolNormalization:
    """Normalize phase 4 model/tool results and failures; no external action."""

    normalizer_ref: TypedRef
    normalization_only: bool = True
    real_model_called: bool = False
    real_tool_called: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_true(self.normalization_only, "ModelToolNormalization.normalization_only")
        ensure_false(self.real_model_called, "ModelToolNormalization.real_model_called")
        ensure_false(self.real_tool_called, "ModelToolNormalization.real_tool_called")
        ensure_schema_version(self.schema_version, "ModelToolNormalization.schema_version")

    def normalize_model_result(self, value: ModelActionResult | ModelActionFailure | object, request_ref: TypedRef) -> ModelActionResult | ModelActionFailure:
        if isinstance(value, (ModelActionResult, ModelActionFailure)):
            return value
        return ModelActionFailure(
            failure_ref=new_adapter_typed_ref("model_action_failure"),
            request_ref=request_ref,
            failure_kind=ModelActionFailureKind.NORMALIZATION_FAILED,
            message="model action result normalization failed",
        )

    def normalize_tool_result(self, value: ToolActionResult | ToolActionFailure | object, request_ref: TypedRef) -> ToolActionResult | ToolActionFailure:
        if isinstance(value, (ToolActionResult, ToolActionFailure)):
            return value
        failure_envelope = ToolFailureEnvelope(
            failure_ref=new_adapter_typed_ref("tool_failure_envelope"),
            failure_code="result_normalization_failed",
            message="tool action result normalization failed",
        )
        return ToolActionFailure(
            failure_ref=new_adapter_typed_ref("tool_action_failure"),
            request_ref=request_ref,
            failure_kind=ToolActionFailureKind.RESULT_NORMALIZATION_FAILED,
            failure_envelope=failure_envelope,
            message=failure_envelope.message,
        )

    def normalize_tool_envelope(self, envelope: ToolResultEnvelope) -> ToolResultEnvelope:
        return envelope
