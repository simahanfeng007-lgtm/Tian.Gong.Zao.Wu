from l5_phase4_helpers import valid_mount, valid_state_machine, validate_lifecycle


def test_tamper_evidence_required_for_lifecycle_and_mount():
    sm = valid_state_machine(tamper_evidence_ref="")
    mount = valid_mount(tamper_evidence_ref="")
    report, mount_report = validate_lifecycle(sm, (mount,))
    assert report.p1_count >= 1
    assert mount_report.p1_count >= 1
