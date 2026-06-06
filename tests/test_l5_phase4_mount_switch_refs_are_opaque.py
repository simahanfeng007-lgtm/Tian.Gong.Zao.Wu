from l5_phase4_helpers import valid_mount, validate_lifecycle


def test_mount_switch_refs_are_declarations_not_paths():
    mount = valid_mount(switch_readiness_ref="switch_ready:ref", pre_switch_checkpoint_ref="checkpoint:ref")
    _, report = validate_lifecycle(mounts=(mount,))
    assert report.p0_count == 0


def test_mount_summary_cannot_leak_url():
    mount = valid_mount(summary="https://example.invalid/run")
    _, report = validate_lifecycle(mounts=(mount,))
    assert report.p0_count >= 1
