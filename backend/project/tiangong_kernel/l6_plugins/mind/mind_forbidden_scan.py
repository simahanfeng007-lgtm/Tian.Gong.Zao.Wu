"""L6 phase3 forbidden scan rules for mind plugin work.

Rules are inert pattern declarations and testable samples. They do not import,
load, or call any provider, tool, state, audit, budget, credential, or runtime
component.
"""

from __future__ import annotations

from tiangong_kernel.l6_plugins.common.forbidden_scan import L6ForbiddenScanRule, L6ForbiddenScanSeverity, scan_l6_text


def default_l6_phase3_mind_forbidden_scan_rules() -> tuple[L6ForbiddenScanRule, ...]:
    patterns: tuple[tuple[str, str, L6ForbiddenScanSeverity], ...] = (
        ("forbid:l6_phase3_provider_sdk_openai", "import openai", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase3_provider_sdk_anthropic", "import anthropic", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase3_provider_sdk_google_genai", "google.genai", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase3_provider_sdk_dashscope", "import dashscope", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase3_provider_sdk_zhipuai", "import zhipuai", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase3_provider_sdk_minimax", "import minimax", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase3_provider_sdk_deepseek", "import deepseek", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase3_raw_http_requests", "requests.", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase3_raw_httpx", "httpx.", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase3_raw_urllib", "urllib", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase3_raw_aiohttp", "aiohttp", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase3_provider_locator", "base_url=", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase3_provider_endpoint", "endpoint=", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase3_raw_key", "api_key=", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase3_subprocess", "subprocess", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase3_os_system", "os.system", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase3_os_popen", "os.popen", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase3_shell_true", "shell=True", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase3_socket", "socket.", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase3_sqlite", "sqlite3", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase3_postgres", "psycopg", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase3_mysql", "pymysql", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase3_redis", "redis", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase3_boto", "boto3", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase3_file_write_text", "Path.write_text", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase3_file_write_bytes", "Path.write_bytes", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase3_file_unlink", "Path.unlink", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase3_tree_remove", "shutil.rmtree", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase3_tree_copy", "shutil.copy", L6ForbiddenScanSeverity.P1),
        ("forbid:l6_phase3_l2_write", "write_l2_fact", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase3_memory_write", "write_memory", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase3_memory_promote", "promote_memory", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase3_memory_delete", "delete_memory", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase3_audit_write", "write_audit", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase3_budget_charge", "charge_budget", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase3_secret_fetch", "fetch_secret", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase3_secret_decrypt", "decrypt_secret", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase3_token_refresh", "refresh_token", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase3_plugin_instance", "plugin_instance", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase3_direct_event_queue", "direct_event_queue", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase3_direct_tool_registry", "direct_tool_registry", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase3_direct_model_client", "direct_model_client", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase3_global_registry", "global_registry", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase3_transition_to", "transition_to", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase3_validate_apply", "validate_and_apply", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase3_auto_migrate", "auto_migrate", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase3_auto_rollback", "auto_rollback", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase3_hot_switch", "hot_switch", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase3_replay_events", "replay_events", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase3_merge_handoff", "merge_handoff", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase3_runtime_legacy", "UnifiedRuntimeEntry", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase3_capability_port_legacy", "CapabilityPort", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase3_ability_package_port_legacy", "AbilityPackagePort", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase3_ability_package_legacy", "AbilityPackage", L6ForbiddenScanSeverity.P0),
    )
    return tuple(L6ForbiddenScanRule(rule_ref=rule_ref, pattern_text=pattern, severity=severity) for rule_ref, pattern, severity in patterns)


def scan_l6_phase3_mind_text(subject_ref: str, source_text: str):
    return scan_l6_text(subject_ref, source_text, default_l6_phase3_mind_forbidden_scan_rules())
