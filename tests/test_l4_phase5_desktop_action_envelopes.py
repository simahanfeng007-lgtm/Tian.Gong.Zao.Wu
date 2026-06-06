import pytest

from l4_phase5_builders import desktop_request
from tiangong_kernel.l4_action_grounding import DesktopActionEnvelope, DesktopActionRequest, action_grounding_stable_hash, action_grounding_to_primitive


def test_l4_phase5_desktop_action_request_is_structural_and_serializable():
    request = desktop_request()
    primitive = action_grounding_to_primitive(request)
    digest = action_grounding_stable_hash(request)

    assert isinstance(request, DesktopActionRequest)
    assert isinstance(request.action_envelope, DesktopActionEnvelope)
    assert primitive["request_only"] is True
    assert primitive["clicks_real_ui"] is False
    assert primitive["types_real_input"] is False
    assert primitive["reads_real_screen"] is False
    assert primitive["controls_real_window"] is False
    assert digest


def test_l4_phase5_desktop_action_request_rejects_real_desktop_flags():
    base = desktop_request()
    with pytest.raises(ValueError):
        DesktopActionRequest(
            request_ref=base.request_ref,
            ui_target_ref=base.ui_target_ref,
            gesture_ref=base.gesture_ref,
            screen_region_ref=base.screen_region_ref,
            input_ref=base.input_ref,
            action_envelope=base.action_envelope,
            scope=base.scope,
            side_effect=base.side_effect,
            reversibility=base.reversibility,
            resource_usage=base.resource_usage,
            risk_surface=base.risk_surface,
            controls_real_window=True,
        )
