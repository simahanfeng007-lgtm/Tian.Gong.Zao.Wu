from l5_phase4_helpers import valid_mount, validate_lifecycle
from tiangong_kernel.l5_plugin_host import PluginRegistryConflictKind


def test_mount_declaration_missing_boundary_policy_audit_fails():
    _, mount_report = validate_lifecycle(mounts=(valid_mount(boundary_ref="", policy_refs=(), audit_decl_ref=""),))
    kinds = {c.kind for c in mount_report.conflict_items}
    assert PluginRegistryConflictKind.MOUNT_BOUNDARY_CONFLICT in kinds
    assert PluginRegistryConflictKind.MOUNT_PERMISSION_DECL_CONFLICT in kinds
    assert PluginRegistryConflictKind.MOUNT_AUDIT_DECL_CONFLICT in kinds
