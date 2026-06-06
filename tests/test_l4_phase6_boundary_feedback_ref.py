import pytest

from l4_phase6_builders import action_ref, boundary_feedback, phase6_ref
from tiangong_kernel.l4_action_grounding import BoundaryFeedbackRef


def test_l4_phase6_boundary_feedback_ref_does_not_decide_boundary():
    feedback = boundary_feedback()

    assert feedback.ref_only is True
    assert feedback.makes_boundary_decision is False
    assert feedback.issues_permit is False
    assert feedback.requires_confirmation_ticket is False


def test_l4_phase6_boundary_feedback_ref_rejects_decision_behavior():
    with pytest.raises(ValueError):
        BoundaryFeedbackRef(
            boundary_feedback_ref=phase6_ref(170, "boundary_feedback"),
            action_ref=action_ref(),
            makes_boundary_decision=True,
        )
