from __future__ import annotations

from dataclasses import is_dataclass

import pytest

from tiangong_kernel.l0_primitives.identity import RefId, TypedRef
from tiangong_kernel.l2_state.self_healing_state import (
    CriticalFailureStepState,
    FailureDiagnosisState,
    PostRecoveryValidationState,
    PostmortemState,
    RecoveryPlanState,
    RegressionOutcomeState,
    RootCauseAnalysisState,
    SelfHealingAttemptState,
)
from tiangong_kernel.l2_state.state_identity import L2StateIdentity, L2StateKind
from tiangong_kernel.l2_state.state_status import L2StateStatus, L2StateStatusKind


def _ref(suffix: int, ref_type: str = "self_healing") -> TypedRef:
    return TypedRef(RefId(f"ref:{suffix:032x}"), ref_type)


def _identity(suffix: int) -> L2StateIdentity:
    return L2StateIdentity(_ref(suffix, "l2_state"), L2StateKind.RECOVERY)


def _status() -> L2StateStatus:
    return L2StateStatus(L2StateStatusKind.DECLARED)


def test_l2_self_healing_states_are_frozen_ref_only_facts() -> None:
    states = (
        FailureDiagnosisState(identity=_identity(1), status=_status(), diagnosis_ref=_ref(2), diagnosis_confidence=0.8),
        CriticalFailureStepState(identity=_identity(3), status=_status(), critical_step_ref=_ref(4)),
        RootCauseAnalysisState(identity=_identity(5), status=_status(), root_cause_refs=(_ref(6),), confidence=0.7),
        RecoveryPlanState(identity=_identity(7), status=_status(), checkpoint_ref=_ref(8), validation_requirement_ref=_ref(9), regression_requirement_ref=_ref(10), readiness_score=0.6),
        SelfHealingAttemptState(identity=_identity(11), status=_status(), recovery_plan_ref=_ref(12)),
        PostRecoveryValidationState(identity=_identity(13), status=_status(), validation_refs=(_ref(14),), regression_refs=(_ref(15),)),
        RegressionOutcomeState(identity=_identity(16), status=_status(), regression_ref=_ref(17)),
        PostmortemState(identity=_identity(18), status=_status(), postmortem_ref=_ref(19), learning_candidate_refs=(_ref(20),)),
    )

    for state in states:
        assert is_dataclass(state)
        assert hasattr(state, "__slots__")
        assert state.state_only is True
        assert state.ref_only is True
        assert state.executes_recovery is False
        assert state.executes_rollback is False
        assert state.writes_audit_store is False
        assert state.writes_l2_state is False

    with pytest.raises(ValueError):
        FailureDiagnosisState(identity=_identity(21), status=_status(), diagnosis_confidence=1.2)
    with pytest.raises(ValueError):
        PostRecoveryValidationState(identity=_identity(22), status=_status(), marks_recovery_complete=True)
