from tiangong_kernel.l5_plugin_host import (
    PluginRecoveryPermissionValidator,
    PluginHotSwitchPermissionValidator,
    PluginRollbackPermissionValidator,
    PluginReplayPermissionValidator,
    PluginPhase6ConflictKind,
    has_forbidden_phase6_method,
)
from l5_phase6_factories import recovery_perm, hot_switch_perm, rollback_perm, replay_perm


def test_recovery_permission_is_not_grant_and_requires_checkpoint_validation_regression():
    obj = recovery_perm()
    assert obj.permission_not_grant_ref
    assert not has_forbidden_phase6_method(obj)
    assert PluginRecoveryPermissionValidator().review(obj) == tuple()
    conflicts = PluginRecoveryPermissionValidator().review(recovery_perm(checkpoint_ref="", validation_ref="", regression_ref=""))
    kinds = {item.kind for item in conflicts}
    assert PluginPhase6ConflictKind.RECOVERY_PERMISSION_MISSING_CHECKPOINT_CONFLICT in kinds
    assert PluginPhase6ConflictKind.RECOVERY_PERMISSION_MISSING_VALIDATION_CONFLICT in kinds
    assert PluginPhase6ConflictKind.RECOVERY_PERMISSION_MISSING_REGRESSION_CONFLICT in kinds


def test_hot_switch_permission_requires_switch_boundary_refs():
    conflicts = PluginHotSwitchPermissionValidator().review(hot_switch_perm(switch_boundary_decl_ref="", switch_readiness_ref=""))
    kinds = {item.kind for item in conflicts}
    assert PluginPhase6ConflictKind.HOT_SWITCH_PERMISSION_MISSING_SWITCH_BOUNDARY_CONFLICT in kinds
    assert PluginPhase6ConflictKind.HOT_SWITCH_PERMISSION_MISSING_READINESS_CONFLICT in kinds


def test_rollback_permission_requires_anchor_checkpoint_validation():
    conflicts = PluginRollbackPermissionValidator().review(rollback_perm(rollback_anchor_ref="", checkpoint_ref="", validation_ref=""))
    kinds = {item.kind for item in conflicts}
    assert PluginPhase6ConflictKind.ROLLBACK_PERMISSION_MISSING_ANCHOR_CONFLICT in kinds
    assert PluginPhase6ConflictKind.ROLLBACK_PERMISSION_MISSING_CHECKPOINT_CONFLICT in kinds
    assert PluginPhase6ConflictKind.ROLLBACK_PERMISSION_MISSING_VALIDATION_CONFLICT in kinds


def test_replay_permission_requires_compatibility_redaction_resource_guard():
    conflicts = PluginReplayPermissionValidator().review(replay_perm(replay_compatibility_ref="", old_event_redaction_policy_ref="", replay_resource_guard_ref=""))
    kinds = {item.kind for item in conflicts}
    assert PluginPhase6ConflictKind.REPLAY_PERMISSION_MISSING_COMPATIBILITY_CONFLICT in kinds
    assert PluginPhase6ConflictKind.REPLAY_PERMISSION_MISSING_OLD_EVENT_REDACTION_CONFLICT in kinds
    assert PluginPhase6ConflictKind.REPLAY_PERMISSION_MISSING_RESOURCE_GUARD_CONFLICT in kinds
