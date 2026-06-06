from __future__ import annotations

import pytest

from tiangong_kernel.l0_primitives.identity import RefId, TypedRef
from tiangong_kernel.l4_action_grounding.self_healing_handoff import (
    L4FailureRecoveryRequirementBundle,
    L4PostRecoveryValidationRequirement,
    L4SelfHealingHandoffRef,
)


def _ref(suffix: int, ref_type: str = "self_healing") -> TypedRef:
    return TypedRef(RefId(f"ref:{suffix:032x}"), ref_type)


def test_l4_self_healing_handoff_does_not_execute_recovery_or_rollback() -> None:
    handoff = L4SelfHealingHandoffRef(
        _ref(1),
        failure_ref=_ref(2),
        evidence_ref=_ref(3),
        audit_requirement_ref=_ref(4),
        checkpoint_ref=_ref(5),
        transaction_ref=_ref(6),
        rollback_intent_ref=_ref(7),
        recovery_requirement_ref=_ref(8),
        validation_requirement_ref=_ref(9),
        regression_requirement_ref=_ref(10),
    )
    bundle = L4FailureRecoveryRequirementBundle(_ref(11), handoff, handoff_ready=True)
    validation = L4PostRecoveryValidationRequirement(_ref(12), recovery_result_ref=_ref(13), validation_requirement_ref=_ref(14), regression_requirement_ref=_ref(15))

    assert handoff.handoff_only is True
    assert handoff.ref_only is True
    assert handoff.executes_recovery is False
    assert handoff.executes_rollback is False
    assert handoff.writes_l2_state is False
    assert handoff.writes_audit_store is False
    assert bundle.bundle_only is True
    assert bundle.executes_recovery is False
    assert validation.runs_validation is False
    assert validation.writes_l2_state is False

    with pytest.raises(ValueError):
        L4SelfHealingHandoffRef(_ref(16), executes_rollback=True)
    with pytest.raises(ValueError):
        L4FailureRecoveryRequirementBundle(_ref(17), L4SelfHealingHandoffRef(_ref(18)), handoff_ready=True)
