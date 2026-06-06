import pytest

from tiangong_kernel.l6_plugins.governance_control import *

def test_permission_requirement_not_authorization():
    req = PermissionRequirement()
    assert req.authorization_granted is False
    assert req.l5_review_required is True
    with pytest.raises(ValueError):
        PermissionRequirement(authorization_granted=True)
