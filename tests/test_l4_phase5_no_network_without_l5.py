from l4_phase5_builders import network_request
from tiangong_kernel.l4_action_grounding import DisabledRealNetworkAdapterStub, NoRealNetworkAccessInvariant


def test_l4_phase5_no_network_without_l5_permit():
    request = network_request()
    failure = DisabledRealNetworkAdapterStub().prepare_network_action(request)
    invariant = NoRealNetworkAccessInvariant(invariant_ref=request.request_ref)

    assert request.permit_ref is None
    assert failure.real_network_access is False
    assert failure.sends_payload is False
    assert invariant.live_action_allowed is False
