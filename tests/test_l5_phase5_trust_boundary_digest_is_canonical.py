from l5_phase5_helpers import valid_trust_boundary


def test_trust_boundary_digest_stable_for_tuple_order_when_same_order():
    a = valid_trust_boundary()
    b = valid_trust_boundary()
    assert a.trust_boundary_digest == b.trust_boundary_digest


def test_trust_boundary_digest_changes_on_key_boundary_change():
    a = valid_trust_boundary()
    b = valid_trust_boundary(host_boundary_ref="boundary:host2")
    assert a.trust_boundary_digest != b.trust_boundary_digest
