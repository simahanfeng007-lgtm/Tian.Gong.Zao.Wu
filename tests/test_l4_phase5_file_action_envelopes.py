import pytest

from l4_phase5_builders import file_request
from tiangong_kernel.l4_action_grounding import FileActionEnvelope, FileActionRequest, action_grounding_stable_hash, action_grounding_to_primitive


def test_l4_phase5_file_action_request_is_structural_and_serializable():
    request = file_request()
    primitive = action_grounding_to_primitive(request)
    digest = action_grounding_stable_hash(request)

    assert isinstance(request, FileActionRequest)
    assert isinstance(request.action_envelope, FileActionEnvelope)
    assert primitive["request_only"] is True
    assert primitive["reads_real_file"] is False
    assert primitive["writes_real_file"] is False
    assert primitive["deletes_real_file"] is False
    assert primitive["overwrites_real_file"] is False
    assert digest


def test_l4_phase5_file_action_request_rejects_real_file_flags():
    base = file_request()
    with pytest.raises(ValueError):
        FileActionRequest(
            request_ref=base.request_ref,
            path_intent_ref=base.path_intent_ref,
            operation_ref=base.operation_ref,
            action_envelope=base.action_envelope,
            scope=base.scope,
            side_effect=base.side_effect,
            reversibility=base.reversibility,
            resource_usage=base.resource_usage,
            risk_surface=base.risk_surface,
            writes_real_file=True,
        )
