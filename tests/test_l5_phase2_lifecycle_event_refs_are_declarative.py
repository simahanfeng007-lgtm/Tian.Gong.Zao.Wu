from l5_phase2_sample_factory import complete_manifest


def test_lifecycle_event_refs_are_tuple_refs_not_emitted_events():
    manifest = complete_manifest()
    assert manifest.lifecycle_event_refs == ("lifecycle_event:declared",)
    assert not hasattr(manifest, "emit")
    assert not hasattr(manifest, "publish")
