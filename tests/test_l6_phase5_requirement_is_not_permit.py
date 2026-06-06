import pytest

from tiangong_kernel.l6_plugins.governance_control import *

def test_requirement_is_not_permit():
    req = PermissionRequirement()
    assert req.requirement_only is True
    assert req.permit_issued is False
    assert req.authorization_granted is False
    with pytest.raises(ValueError):
        PermissionRequirement(permit_issued=True)
