from l5_phase5_helpers import valid_resource


def test_resource_boundary_digest_is_stable_and_content_sensitive():
    a = valid_resource()
    b = valid_resource()
    c = valid_resource(quota_policy_ref="policy:quota2")
    assert a.resource_boundary_digest == b.resource_boundary_digest
    assert a.resource_boundary_digest != c.resource_boundary_digest
