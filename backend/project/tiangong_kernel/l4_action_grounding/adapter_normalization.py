"""Adapter result and failure normalization helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from tiangong_kernel.l0_primitives.identity import TypedRef

from .adapter_envelope import AdapterFailureEnvelope, AdapterOutputEnvelope
from .adapter_failure import AdapterFailure, AdapterFailureKind, new_adapter_typed_ref
from .adapter_mode import AdapterMode
from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_true


def _safe_debug_summary(value: BaseException | object) -> str:
    if isinstance(value, BaseException):
        return type(value).__name__
    return type(value).__name__


@dataclass(frozen=True, slots=True)
class AdapterResultNormalizer:
    """Normalize adapter output without claiming real success."""

    normalizer_ref: TypedRef
    normalizer_only: bool = True
    real_action_performed: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_true(self.normalizer_only, "AdapterResultNormalizer.normalizer_only")
        ensure_false(self.real_action_performed, "AdapterResultNormalizer.real_action_performed")
        ensure_schema_version(self.schema_version, "AdapterResultNormalizer.schema_version")

    def normalize(
        self,
        raw: Any,
        *,
        adapter_id: str,
        adapter_kind: str,
        action_kind: str,
        mode: AdapterMode,
        success: bool = True,
    ) -> AdapterOutputEnvelope:
        if isinstance(raw, AdapterOutputEnvelope):
            return raw
        payload = (("raw_result_type", _safe_debug_summary(raw)),)
        return AdapterOutputEnvelope(
            output_ref=new_adapter_typed_ref("adapter_output"),
            adapter_id=adapter_id,
            adapter_kind=adapter_kind,
            action_kind=action_kind,
            mode=mode,
            success=success,
            result_payload=payload,
            side_effect_summary="none",
        )


@dataclass(frozen=True, slots=True)
class AdapterFailureNormalizer:
    """Normalize adapter errors without leaking internals."""

    normalizer_ref: TypedRef
    normalizer_only: bool = True
    real_action_performed: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_true(self.normalizer_only, "AdapterFailureNormalizer.normalizer_only")
        ensure_false(self.real_action_performed, "AdapterFailureNormalizer.real_action_performed")
        ensure_schema_version(self.schema_version, "AdapterFailureNormalizer.schema_version")

    def normalize(
        self,
        error: AdapterFailureEnvelope | AdapterFailure | BaseException | object,
        *,
        adapter_id: str,
        adapter_kind: str,
        action_kind: str,
        mode: AdapterMode,
    ) -> AdapterFailureEnvelope:
        if isinstance(error, AdapterFailureEnvelope):
            return error
        if isinstance(error, AdapterFailure):
            return error.to_envelope()
        failure = AdapterFailure(
            failure_ref=new_adapter_typed_ref("adapter_failure"),
            failure_kind=AdapterFailureKind.INVARIANT_VIOLATION,
            message=f"adapter failure normalized as {_safe_debug_summary(error)}",
            adapter_id=adapter_id,
            adapter_kind=adapter_kind,
            action_kind=action_kind,
            mode=mode,
        )
        return failure.to_envelope()
