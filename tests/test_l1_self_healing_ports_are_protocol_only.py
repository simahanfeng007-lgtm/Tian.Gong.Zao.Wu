from __future__ import annotations

from inspect import isabstract

import pytest

from tiangong_kernel.l0_primitives.identity import RefId, TypedRef
from tiangong_kernel.l1_ports.self_healing_ports import (
    FailureDiagnosisPort,
    FailureDiagnosisRequest,
    FailureDiagnosisResponse,
    PostRecoveryValidationRequest,
    PostRecoveryValidationResponse,
    PostmortemRecordRequest,
    PostmortemRecordResponse,
    RecoveryPlanIntentRequest,
    RecoveryPlanIntentResponse,
    SelfHealingLifecycleRequest,
    SelfHealingLifecycleResponse,
)


def _ref(suffix: int, ref_type: str = "self_healing") -> TypedRef:
    return TypedRef(RefId(f"ref:{suffix:032x}"), ref_type)


def test_l1_self_healing_requests_and_responses_do_not_execute() -> None:
    diagnosis_request = FailureDiagnosisRequest(_ref(1), failure_ref=_ref(2), evidence_refs=(_ref(3),))
    diagnosis_response = FailureDiagnosisResponse(_ref(4), diagnosis_refs=(_ref(5),))
    plan_request = RecoveryPlanIntentRequest(_ref(6), diagnosis_refs=(_ref(7),), checkpoint_refs=(_ref(8),), validation_refs=(_ref(9),), regression_refs=(_ref(10),))
    plan_response = RecoveryPlanIntentResponse(_ref(11), recovery_plan_refs=(_ref(12),))
    lifecycle_request = SelfHealingLifecycleRequest(_ref(13), failure_ref=_ref(14), recovery_plan_ref=_ref(15))
    lifecycle_response = SelfHealingLifecycleResponse(_ref(16), lifecycle_refs=(_ref(17),))
    validation_request = PostRecoveryValidationRequest(_ref(18), validation_refs=(_ref(19),), regression_refs=(_ref(20),))
    validation_response = PostRecoveryValidationResponse(_ref(21), validation_result_refs=(_ref(22),), regression_outcome_refs=(_ref(23),))
    postmortem_request = PostmortemRecordRequest(_ref(24), failure_ref=_ref(25), learning_candidate_refs=(_ref(26),))
    postmortem_response = PostmortemRecordResponse(_ref(27), postmortem_refs=(_ref(28),))

    assert diagnosis_request.request_only is True
    assert diagnosis_response.performs_diagnosis is False
    assert plan_request.request_only is True
    assert plan_response.executes_recovery is False
    assert lifecycle_request.request_only is True
    assert lifecycle_response.executes_lifecycle is False
    assert validation_request.request_only is True
    assert validation_response.runs_validation is False
    assert postmortem_request.request_only is True
    assert postmortem_response.writes_postmortem_store is False
    assert isabstract(FailureDiagnosisPort)

    with pytest.raises(ValueError):
        RecoveryPlanIntentResponse(_ref(29), executes_recovery=True)
