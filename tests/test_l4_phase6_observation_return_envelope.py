import pytest

from l4_phase6_builders import action_ref, observation_return, phase6_ref
from tiangong_kernel.l4_action_grounding import ObservationReturnEnvelope, action_grounding_stable_hash, action_grounding_to_primitive


def test_l4_phase6_observation_return_envelope_is_ref_only():
    envelope = observation_return()
    primitive = action_grounding_to_primitive(envelope)

    assert primitive["samples_real_observation"] is False
    assert primitive["implements_observation_system"] is False
    assert primitive["decides_next_step"] is False
    assert action_grounding_stable_hash(envelope)


def test_l4_phase6_observation_return_rejects_sampling():
    with pytest.raises(ValueError):
        ObservationReturnEnvelope(
            observation_return_ref=phase6_ref(150, "observation_return"),
            action_ref=action_ref(),
            observation_ref=phase6_ref(151, "observation"),
            samples_real_observation=True,
        )
