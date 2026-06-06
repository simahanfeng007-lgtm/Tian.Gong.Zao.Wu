from l5_phase4_helpers import valid_mount, validate_lifecycle


def test_mount_point_ref_accepts_opaque_declaration_ref():
    _, mount_report = validate_lifecycle(mounts=(valid_mount(mount_point_ref="mount:opaque_reference"),))
    assert mount_report.p0_count == 0


def test_mount_point_ref_rejects_windows_path():
    _, mount_report = validate_lifecycle(mounts=(valid_mount(mount_point_ref=r"C:\\plugins\\x.py"),))
    assert mount_report.p0_count >= 1
