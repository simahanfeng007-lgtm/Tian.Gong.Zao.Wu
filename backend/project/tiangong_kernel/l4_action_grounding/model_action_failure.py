"""Model action failure objects for L4 phase 4."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef

from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_short_text, ensure_true


class ModelActionFailureKind(str, Enum):
    DISABLED_BY_DEFAULT = "disabled_by_default"
    PERMIT_MISSING = "permit_missing"
    PERMIT_SCOPE_MISMATCH = "permit_scope_mismatch"
    PERMIT_EXPIRED = "permit_expired"
    ADAPTER_UNAVAILABLE = "adapter_unavailable"
    NORMALIZATION_FAILED = "normalization_failed"
    DRY_RUN_ONLY = "dry_run_only"


@dataclass(frozen=True, slots=True)
class ModelActionFailure:
    """Standardized model action failure for L3 re-planning."""

    failure_ref: TypedRef
    request_ref: TypedRef | None = None
    failure_kind: ModelActionFailureKind = ModelActionFailureKind.DISABLED_BY_DEFAULT
    message: str = "model action is disabled in L4 phase 4"
    recoverability_hint: str = "replan_or_stop"
    retry_allowed_hint: bool = False
    boundary_recheck_required_hint: bool = False
    real_model_called: bool = False
    failure_only: bool = True
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_short_text(self.message, "ModelActionFailure.message")
        ensure_short_text(self.recoverability_hint, "ModelActionFailure.recoverability_hint", 128)
        ensure_false(self.retry_allowed_hint, "ModelActionFailure.retry_allowed_hint")
        ensure_false(self.real_model_called, "ModelActionFailure.real_model_called")
        ensure_true(self.failure_only, "ModelActionFailure.failure_only")
        ensure_schema_version(self.schema_version, "ModelActionFailure.schema_version")
