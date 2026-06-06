import pytest

from l4_phase6_builders import action_ref, phase6_ref, result_return
from tiangong_kernel.l4_action_grounding import ActionResultReturnEnvelope, NoL2StateWriteFromReturnInvariant


def test_l4_phase6_return_envelopes_do_not_write_l2_state():
    envelope = result_return()
    invariant = NoL2StateWriteFromReturnInvariant(invariant_ref=envelope.outcome_ref)

    assert envelope.state_update_suggestion_ref is not None
    assert envelope.writes_l2_state is False
    assert invariant.l4_can_override is False


def test_l4_phase6_result_return_rejects_l2_state_write():
    with pytest.raises(ValueError):
        ActionResultReturnEnvelope(
            outcome_ref=phase6_ref(190, "outcome"),
            action_ref=action_ref(),
            result_ref=phase6_ref(191, "result"),
            writes_l2_state=True,
        )
