import pytest

from tiangong_kernel.l6_plugins.cognitive_continuity import *

def test_product_bridge_seed_inert():
    seed = ProductSpecSeedCandidate()
    state = ProductBridgeSeedState()
    assert seed.is_product_spec is False
    assert seed.build_action_allowed is False
    assert state.product_spec_created is False
    with pytest.raises(ValueError):
        ProductSpecSeedCandidate(is_product_spec=True)
