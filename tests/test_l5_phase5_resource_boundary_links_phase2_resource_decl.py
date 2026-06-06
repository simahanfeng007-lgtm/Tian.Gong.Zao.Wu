from l5_phase5_helpers import valid_resource


def test_resource_boundary_links_phase2_resource_decl():
    decl = valid_resource()
    assert decl.phase2_resource_decl_ref
    assert decl.manifest_resource_decl_ref
    assert decl.resource_decl_digest_ref
