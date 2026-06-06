import pytest

from tiangong_kernel.l6_plugins.mind import *


def test_affective_state_and_projection_are_not_permission():
    assert AffectiveMindState().affective_state_is_permission is False
    assert AffectiveProjection().affective_state_is_permission is False
    assert ActionTendencyHint().grants_action_authority is False
    with pytest.raises(ValueError):
        AffectiveMindState(affective_state_is_permission=True)
    with pytest.raises(ValueError):
        AffectiveProjection(affective_state_is_permission=True)
    with pytest.raises(ValueError):
        ActionTendencyHint(grants_action_authority=True)
