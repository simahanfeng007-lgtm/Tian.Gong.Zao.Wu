import pytest

from tiangong_kernel.l6_plugins.governance_control import *

def test_no_raw_secret_or_provider_locator():
    assert NoPlainSecretRequirement().no_provider_locator_required is True
    assert ProviderLocatorLeakRisk().locator_detail_present is False
    bad = scan_l6_phase5_text('test:l6_phase5_bad_secret', 'save_secret and base_url= and api_key=')
    assert bad.passed is False
    with pytest.raises(ValueError):
        ProviderLocatorLeakRisk(locator_detail_present=True)
