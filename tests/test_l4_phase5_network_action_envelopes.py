import pytest

from l4_phase5_builders import network_request
from tiangong_kernel.l4_action_grounding import NetworkActionEnvelope, NetworkActionRequest, action_grounding_stable_hash, action_grounding_to_primitive


def test_l4_phase5_network_action_request_is_structural_and_serializable():
    request = network_request()
    primitive = action_grounding_to_primitive(request)
    digest = action_grounding_stable_hash(request)

    assert isinstance(request, NetworkActionRequest)
    assert isinstance(request.action_envelope, NetworkActionEnvelope)
    assert primitive["request_only"] is True
    assert primitive["accesses_real_network"] is False
    assert primitive["sends_real_payload"] is False
    assert primitive["caches_real_response_body"] is False
    assert digest


def test_l4_phase5_network_action_request_rejects_real_network_flags():
    base = network_request()
    with pytest.raises(ValueError):
        NetworkActionRequest(
            request_ref=base.request_ref,
            url_ref=base.url_ref,
            method_ref=base.method_ref,
            payload_ref=base.payload_ref,
            headers_ref=base.headers_ref,
            action_envelope=base.action_envelope,
            scope=base.scope,
            side_effect=base.side_effect,
            reversibility=base.reversibility,
            resource_usage=base.resource_usage,
            risk_surface=base.risk_surface,
            accesses_real_network=True,
        )
