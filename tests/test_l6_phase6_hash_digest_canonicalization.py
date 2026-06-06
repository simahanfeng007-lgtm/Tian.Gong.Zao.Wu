from tiangong_kernel.l6_plugins.product_delivery import *

def test_hash_digest_canonicalization():
    left = ProductSpecSeedCandidate()
    right = ProductSpecSeedCandidate()
    assert left.digest == right.digest
    assert len(left.digest) == 64
