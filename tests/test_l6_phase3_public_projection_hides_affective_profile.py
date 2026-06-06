import pytest

from tiangong_kernel.l6_plugins.mind import *


def test_public_projection_hides_complete_affective_profile():
    assert AffectiveProjection().complete_affective_profile_public is False
    assert AffectiveMindState().complete_profile_public is False
    with pytest.raises(ValueError):
        AffectiveProjection(complete_affective_profile_public=True)
    with pytest.raises(ValueError):
        AffectiveMindState(complete_profile_public=True)
