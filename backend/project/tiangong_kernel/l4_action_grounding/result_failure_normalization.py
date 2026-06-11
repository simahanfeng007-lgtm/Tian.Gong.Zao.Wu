"""Result and failure normalization failures for L4 phase 6."""

from __future__ import annotations

from dataclasses import dataclass

from tiangong_kernel.l0_primitives.identity import TypedRef

from .failure_category import FailureCategory
from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_short_text, ensure_true


@dataclass(frozen=True, slots=True)
class ResultNormalizationFailure:
    """Result normalization failure; error and trace refs are preserved."""

    normalization_failure_ref: TypedRef
    action_ref: TypedRef
    error_ref: TypedRef
    trace_ref: TypedRef
    failure_category: FailureCategory = FailureCategory.NORMALIZATION_FAILED
    message: str = "result normalization failed"
    failure_only: bool = True
    swallows_error: bool = False
    writes_l2_state: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_short_text(self.message, "ResultNormalizationFailure.message")
        ensure_true(self.failure_only, "ResultNormalizationFailure.failure_only")
        ensure_false(self.swallows_error, "ResultNormalizationFailure.swallows_error")
        ensure_false(self.writes_l2_state, "ResultNormalizationFailure.writes_l2_state")
        ensure_schema_version(self.schema_version, "ResultNormalizationFailure.schema_version")


@dataclass(frozen=True, slots=True)
class FailureNormalizationFailure:
    """Failure normalization failure; error and trace refs are preserved."""

    normalization_failure_ref: TypedRef
    action_ref: TypedRef
    error_ref: TypedRef
    trace_ref: TypedRef
    failure_category: FailureCategory = FailureCategory.NORMALIZATION_FAILED
    message: str = "failure normalization failed"
    failure_only: bool = True
    swallows_error: bool = False
    writes_l2_state: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_short_text(self.message, "FailureNormalizationFailure.message")
        ensure_true(self.failure_only, "FailureNormalizationFailure.failure_only")
        ensure_false(self.swallows_error, "FailureNormalizationFailure.swallows_error")
        ensure_false(self.writes_l2_state, "FailureNormalizationFailure.writes_l2_state")
        ensure_schema_version(self.schema_version, "FailureNormalizationFailure.schema_version")
