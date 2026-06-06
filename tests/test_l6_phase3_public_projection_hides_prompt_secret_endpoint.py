import pytest

from tiangong_kernel.l6_plugins.mind import *


def test_public_projection_hides_prompt_secret_and_provider_locator():
    public = MindOutputBase(disclosure_level=MindProjectionDisclosureLevel.PUBLIC_MINIMAL)
    assert public.contains_raw_prompt is False
    assert public.contains_raw_credential is False
    assert public.contains_provider_locator is False
    with pytest.raises(ValueError):
        MindOutputBase(contains_raw_prompt=True)
    with pytest.raises(ValueError):
        MindOutputBase(contains_provider_locator=True)
