from tiangong_kernel.l6_plugins.final_closure import L6StageInventory

def test_hash_digest_canonicalization():
    a = L6StageInventory().digest
    b = L6StageInventory().digest
    assert a == b
    assert len(a) == 64
