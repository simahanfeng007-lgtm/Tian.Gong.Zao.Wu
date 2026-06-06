from l5_phase3_sample_factory import complete_record, complete_snapshot


def test_snapshot_hash_changes_when_record_content_changes():
    first = complete_snapshot((complete_record(summary="one"),))
    second = complete_snapshot((complete_record(summary="two"),))
    assert first.snapshot_digest != second.snapshot_digest
