from dataclasses import FrozenInstanceError

import pytest

from l5_phase3_sample_factory import complete_record, quality_gate, complete_snapshot, conflict_report


def test_registry_record_is_immutable_refs_only_and_quality_gate_passes():
    record = complete_record()
    assert record.registry_key_text
    assert record.canonical_record_digest
    assert record.status_ref == "status:declared_only"
    with pytest.raises(FrozenInstanceError):
        record.status_ref = "status:changed"
    snapshot = complete_snapshot((record,))
    report = conflict_report(snapshot)
    result = quality_gate().evaluate(snapshot, report)
    assert result.passed
