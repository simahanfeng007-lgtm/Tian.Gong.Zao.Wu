from l5_phase4_helpers import valid_phase3_snapshot, valid_state_machine, validate_lifecycle
from tiangong_kernel.l5_plugin_host import PluginRegistrySnapshot


def test_phase3_snapshot_can_be_read_as_input_but_not_mutated():
    snapshot = valid_phase3_snapshot()
    before = snapshot.snapshot_digest
    sm = valid_state_machine(registry_snapshot_ref=snapshot.snapshot_ref)
    report, _ = validate_lifecycle(sm)
    assert isinstance(snapshot, PluginRegistrySnapshot)
    assert report.registry_snapshot_ref == snapshot.snapshot_ref
    assert snapshot.snapshot_digest == before
