from __future__ import annotations

from tiangong_kernel.l0_primitives.identity import RefId, TypedRef
from tiangong_kernel.l1_ports.self_healing_ports import FailureDiagnosisRequest, RecoveryPlanIntentRequest
from tiangong_kernel.l2_state.self_healing_state import RecoveryPlanState
from tiangong_kernel.l2_state.state_identity import L2StateIdentity, L2StateKind
from tiangong_kernel.l2_state.state_status import L2StateStatus, L2StateStatusKind
from tiangong_kernel.l3_orchestration.self_healing_flow import PostRecoveryValidationAdvice, SelfHealingFlowEnvelope, SelfHealingReadiness
from tiangong_kernel.l4_action_grounding.self_healing_handoff import L4FailureRecoveryRequirementBundle, L4SelfHealingHandoffRef


def _ref(suffix: int, ref_type: str = "self_healing") -> TypedRef:
    return TypedRef(RefId(f"ref:{suffix:032x}"), ref_type)


def test_self_healing_chain_requires_validation_and_regression_without_execution() -> None:
    failure_ref = _ref(1, "failure")
    checkpoint_ref = _ref(2, "checkpoint")
    validation_ref = _ref(3, "validation")
    regression_ref = _ref(4, "regression")
    diagnosis_request = FailureDiagnosisRequest(_ref(5), failure_ref=failure_ref)
    plan_request = RecoveryPlanIntentRequest(_ref(6), diagnosis_refs=(_ref(7),), checkpoint_refs=(checkpoint_ref,), validation_refs=(validation_ref,), regression_refs=(regression_ref,))
    plan_state = RecoveryPlanState(
        identity=L2StateIdentity(_ref(8, "l2_state"), L2StateKind.RECOVERY),
        status=L2StateStatus(L2StateStatusKind.DECLARED),
        failure_ref=failure_ref,
        checkpoint_ref=checkpoint_ref,
        validation_requirement_ref=validation_ref,
        regression_requirement_ref=regression_ref,
    )
    l3_envelope = SelfHealingFlowEnvelope(
        _ref(9),
        failure_ref=failure_ref,
        checkpoint_ref=checkpoint_ref,
        validation_requirement_ref=validation_ref,
        regression_requirement_ref=regression_ref,
        advices=(PostRecoveryValidationAdvice(_ref(10), validation_requirement_ref=validation_ref, regression_requirement_ref=regression_ref),),
        readiness=SelfHealingReadiness.READY_FOR_BOUNDARY_REVIEW,
    )
    handoff = L4SelfHealingHandoffRef(_ref(11), failure_ref=failure_ref, checkpoint_ref=checkpoint_ref, validation_requirement_ref=validation_ref, regression_requirement_ref=regression_ref)
    bundle = L4FailureRecoveryRequirementBundle(_ref(12), handoff, handoff_ready=True)

    assert diagnosis_request.request_only is True
    assert plan_request.request_only is True
    assert plan_state.executes_recovery is False
    assert plan_state.validation_requirement_ref == validation_ref
    assert plan_state.regression_requirement_ref == regression_ref
    assert l3_envelope.executes_recovery is False
    assert bundle.executes_recovery is False
