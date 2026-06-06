from l5_phase4_helpers import valid_mount, validate_lifecycle
from tiangong_kernel.l5_plugin_host import PluginRegistryConflictKind, PluginRegistryConflictSeverity


def test_mount_declaration_rejects_file_path_as_mount_point():
    _, mount_report = validate_lifecycle(mounts=(valid_mount(mount_point_ref="/tmp/plugin.py"),))
    assert any(c.kind is PluginRegistryConflictKind.MOUNT_LIVE_ENTRY_CONFLICT and c.severity is PluginRegistryConflictSeverity.P0 for c in mount_report.conflict_items)


def test_mount_declaration_rejects_url_or_import_path():
    for value in ("https://example.invalid/plugin", "package.module:function"):
        _, mount_report = validate_lifecycle(mounts=(valid_mount(mount_point_ref=value),))
        assert mount_report.p0_count >= 1
