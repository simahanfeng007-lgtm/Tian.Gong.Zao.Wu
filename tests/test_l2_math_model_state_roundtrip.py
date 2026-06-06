from __future__ import annotations

import json
from dataclasses import fields, is_dataclass
from enum import Enum
from typing import Any

from tiangong_kernel.l0_primitives.identity import RefId, TypedRef
from tiangong_kernel.l2_state.math_model_governance_state import (
    DriftDetectionRecordState,
    FeatureSnapshotState,
    MathModelRegistryState,
    ModelCalibrationRecordState,
    ModelConflictState,
    ModelEvidenceState,
    ModelGovernanceState,
    ModelParameterGovernanceState,
    ModelReplayState,
    ModelShadowState,
    ModelTelemetryState,
    ScoringSnapshotState,
)
from tiangong_kernel.l2_state.state_identity import L2StateIdentity, L2StateKind
from tiangong_kernel.l2_state.state_status import L2StateStatus, L2StateStatusKind


def _ref(suffix: int, ref_type: str = "math_ref") -> TypedRef:
    return TypedRef(RefId(f"ref:{suffix:032x}"), ref_type)


def _identity(suffix: int) -> L2StateIdentity:
    return L2StateIdentity(_ref(suffix, "l2_state"), L2StateKind.MATH)


def _status() -> L2StateStatus:
    return L2StateStatus(L2StateStatusKind.DECLARED)


def _primitive(value: Any) -> Any:
    if is_dataclass(value):
        return {field.name: _primitive(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, tuple):
        return [_primitive(item) for item in value]
    if isinstance(value, list):
        return [_primitive(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _primitive(item) for key, item in value.items()}
    return value


def test_l2_math_model_states_are_state_only_and_json_roundtrippable() -> None:
    states = (
        MathModelRegistryState(identity=_identity(1), status=_status()),
        ModelParameterGovernanceState(identity=_identity(2), status=_status(), parameter_refs=(_ref(20),)),
        FeatureSnapshotState(identity=_identity(3), status=_status(), feature_refs=(_ref(30),)),
        ScoringSnapshotState(identity=_identity(4), status=_status(), score=0.5, confidence=0.6, uncertainty=0.4),
        ModelEvidenceState(identity=_identity(5), status=_status(), evidence_item_refs=(_ref(50),)),
        ModelCalibrationRecordState(identity=_identity(6), status=_status(), calibration_error=0.1),
        DriftDetectionRecordState(identity=_identity(7), status=_status(), drift_window_ref=_ref(70)),
        ModelReplayState(identity=_identity(8), status=_status(), replay_request_ref=_ref(80)),
        ModelShadowState(identity=_identity(9), status=_status(), shadow_result_ref=_ref(90)),
        ModelGovernanceState(identity=_identity(10), status=_status()),
        ModelConflictState(identity=_identity(11), status=_status(), conflicting_result_refs=(_ref(110),)),
        ModelTelemetryState(identity=_identity(12), status=_status(), latency_ms=1.0, failure_rate=0.0),
    )

    for state in states:
        assert state.state_only is True
        assert state.no_decision is True
        assert state.no_execution is True
        payload = _primitive(state)
        assert json.loads(json.dumps(payload, sort_keys=True, ensure_ascii=False)) == payload


def test_l2_math_model_state_slots_are_frozen_facts() -> None:
    state = ScoringSnapshotState(identity=_identity(100), status=_status())

    assert is_dataclass(state)
    assert hasattr(state, "__slots__")
    assert "score" in state.__slots__
