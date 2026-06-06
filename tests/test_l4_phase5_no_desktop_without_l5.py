from l4_phase5_builders import desktop_request
from tiangong_kernel.l4_action_grounding import DisabledRealDesktopAdapterStub, NoRealDesktopControlInvariant


def test_l4_phase5_no_desktop_without_l5_permit():
    request = desktop_request()
    failure = DisabledRealDesktopAdapterStub().prepare_desktop_action(request)
    invariant = NoRealDesktopControlInvariant(invariant_ref=request.request_ref)

    assert request.permit_ref is None
    assert failure.real_desktop_control is False
    assert failure.real_screen_access is False
    assert failure.real_input_sent is False
    assert invariant.live_action_allowed is False
