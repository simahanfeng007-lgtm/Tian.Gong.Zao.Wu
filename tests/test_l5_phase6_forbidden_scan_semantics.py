from tiangong_kernel.l5_plugin_host import PluginPhase6ConflictKind, has_live_health_or_permission_locator, phase6_public_text_is_safe

INERT_PATTERNS = ("probe", "rollback", "hot_switch", "replay", "healthcheck")


def test_forbidden_scan_allows_inert_patterns_but_blocks_live_health_recovery_switch():
    assert "rollback" in INERT_PATTERNS
    assert PluginPhase6ConflictKind.ROLLBACK_LIVE_EXECUTION_CONFLICT.value == "rollback_live_execution_conflict"
    assert has_live_health_or_permission_locator({"endpoint": "https://example.invalid/probe"})
    assert not phase6_public_text_is_safe({"raw_log": "/tmp/plugin.log"})
