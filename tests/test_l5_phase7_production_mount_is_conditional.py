from l5_phase7_builders import compatible_precheck, phase7_validation_report


def test_production_mount_allowed_after_compatible_precheck():
    report = phase7_validation_report(precheck=compatible_precheck())
    assert report.p0_count == 0
    assert report.p1_count == 0
    assert report.passed
