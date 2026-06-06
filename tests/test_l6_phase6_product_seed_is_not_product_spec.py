import pytest
from tiangong_kernel.l6_plugins.product_delivery import *

def test_product_seed_is_not_product_spec():
    seed = ProductSpecSeedCandidate()
    assert seed.product_spec_finalized is False
    with pytest.raises(ValueError):
        ProductSpecSeedCandidate(product_spec_finalized=True)
