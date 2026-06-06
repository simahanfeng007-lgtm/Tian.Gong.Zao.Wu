from l5_phase3_sample_factory import complete_record, complete_snapshot
from tiangong_kernel.l5_plugin_host import build_registry_delta


def test_delta_has_no_apply_or_execution_methods():
    delta = build_registry_delta("delta:test", complete_snapshot((complete_record(summary="base"),)), complete_snapshot((complete_record(summary="target"),)))
    names = set(dir(delta))
    for forbidden in ("apply", "commit", "rollback", "hot_switch", "mount", "unmount", "enable", "disable", "isolate"):
        assert forbidden not in names
