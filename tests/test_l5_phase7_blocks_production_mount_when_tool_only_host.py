from l5_phase7_builders import phase7_validation_report, tool_only_precheck


def test_tool_only_host_blocks_production_mount():
    report = phase7_validation_report(precheck=tool_only_precheck())
    assert report.p1_count >= 1
    assert not report.passed
