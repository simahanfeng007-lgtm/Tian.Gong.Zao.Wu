import pytest

from tiangong_kernel.l6_plugins.mind import *


def test_no_raw_secret_or_provider_locator_public_outputs():
    assert L6Phase3MindQualityGateDecision(no_raw_secret_passed=False).allow_enter_phase4 is False
    assert L6Phase3MindQualityGateDecision(no_provider_base_url_or_api_key_passed=False).allow_enter_phase4 is False
    with pytest.raises(ValueError):
        MindOutputBase(summary="api_key=abc")
    with pytest.raises(ValueError):
        MindOutputBase(summary="https://example.invalid")
