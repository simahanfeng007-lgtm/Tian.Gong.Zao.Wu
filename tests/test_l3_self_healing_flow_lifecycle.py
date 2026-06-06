from __future__ import annotations

import pytest

from tiangong_kernel.l0_primitives.identity import RefId, TypedRef
from tiangong_kernel.l3_orchestration.self_healing_flow import (
    DiagnosisToRecoveryPlanAdvice,
    FailureToDiagnosisAdvice,
    PostRecoveryValidationAdvice,
    RecoveryExecutionHandoffAdvice,
    RecoveryPlanToBoundaryReviewAdvice,
    SelfHealingClosureAdvice,
    SelfHealingFlowEnvelope,
    SelfHealingReadiness,
)


def _ref(suffix: int, ref_type: str = "self_healing") -> TypedRef:
    return TypedRef(RefId(f"ref:{suffix:032x}"), ref_type)


def test_l3_self_healing_advices_are_advisory_only() -> None:
    advices = (
        FailureToDiagnosisAdvice(_ref(1), failure_ref=_ref(2)),
        DiagnosisToRecoveryPlanAdvice(_ref(3), diagnosis_ref=_ref(4), recovery_plan_ref=_ref(5)),
        RecoveryPlanToBoundaryReviewAdvice(_ref(6), recovery_plan_ref=_ref(7), boundary_review_ref=_ref(8)),
        RecoveryExecutionHandoffAdvice(_ref(9), l4_handoff_ref=_ref(10)),
        PostRecoveryValidationAdvice(_ref(11), validation_requirement_ref=_ref(12), regression_requirement_ref=_ref(13)),
        SelfHealingClosureAdvice(_ref(14), postmortem_ref=_ref(15), learning_candidate_refs=(_ref(16),)),
    )

    for advice in advices:
        assert advice.advisory_only is True
        assert advice.ref_only is True
        assert advice.executes_recovery is False
        assert advice.executes_rollback is False
        assert advice.writes_state is False
        assert advice.signs_permission is False

    with pytest.raises(ValueError):
        FailureToDiagnosisAdvice(_ref(17), executes_recovery=True)


def test_l3_self_healing_ready_envelope_requires_checkpoint_validation_regression() -> None:
    envelope = SelfHealingFlowEnvelope(
        _ref(20),
        checkpoint_ref=_ref(21),
        validation_requirement_ref=_ref(22),
        regression_requirement_ref=_ref(23),
        readiness=SelfHealingReadiness.READY_FOR_BOUNDARY_REVIEW,
    )
    assert envelope.readiness is SelfHealingReadiness.READY_FOR_BOUNDARY_REVIEW
    assert envelope.executes_recovery is False

    with pytest.raises(ValueError):
        SelfHealingFlowEnvelope(_ref(24), readiness=SelfHealingReadiness.READY_FOR_BOUNDARY_REVIEW)
