import pytest

from tiangong_kernel.l6_plugins.governance_control import *

def test_credential_ref_not_secret_access():
    ref = CredentialRequirementRef()
    assert ref.secret_access_granted is False
    assert ref.material_loaded is False
    assert CredentialScopeHint().contains_locator is False
    with pytest.raises(ValueError):
        CredentialRequirementRef(secret_access_granted=True)
    with pytest.raises(ValueError):
        CredentialScopeHint(contains_secret_material=True)
