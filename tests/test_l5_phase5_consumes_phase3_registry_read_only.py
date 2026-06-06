import copy
from l5_phase4_helpers import valid_phase3_snapshot


def test_phase3_registry_snapshot_is_only_read():
    snapshot = valid_phase3_snapshot()
    before = copy.deepcopy(snapshot)
    _ = snapshot.snapshot_digest
    assert snapshot == before
