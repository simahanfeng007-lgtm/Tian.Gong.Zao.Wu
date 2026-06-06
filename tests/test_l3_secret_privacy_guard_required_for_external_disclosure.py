import pytest

from tiangong_kernel.l3_orchestration import SecretPrivacyGuardFlow


def test_l3_secret_privacy_guard_does_not_authorize_external_disclosure():
    flow = SecretPrivacyGuardFlow()
    assert flow.plain_secret_visible is False
    assert flow.external_disclosure_authorized is False
    with pytest.raises(ValueError):
        SecretPrivacyGuardFlow(external_disclosure_authorized=True)
