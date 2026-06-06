import pytest

from tiangong_kernel.l6_plugins.governance_control import *

def test_public_projection_safety_no_sensitive_leak():
    hint = PublicProjectionSafetyHint()
    assert hint.exposes_prompt is False
    assert hint.exposes_memory_body is False
    assert hint.exposes_provider_locator is False
    assert hint.exposes_credential_material is False
    assert PublicProjectionSafetyPluginPlan().minimal_disclosure_required is True
    with pytest.raises(ValueError):
        PublicProjectionSafetyHint(exposes_prompt=True)
