"""L6 phase5 governance-control forbidden scan declarations."""

from __future__ import annotations

from tiangong_kernel.l6_plugins.common.forbidden_scan import L6ForbiddenScanRule, L6ForbiddenScanSeverity, scan_l6_text


def default_l6_phase5_forbidden_scan_rules() -> tuple[L6ForbiddenScanRule, ...]:
    patterns: tuple[tuple[str, str, L6ForbiddenScanSeverity], ...] = (
        ("forbid:l6_phase5_provider_sdk_openai", "import openai", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase5_provider_sdk_anthropic", "import anthropic", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase5_provider_sdk_google", "google.genai", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase5_provider_sdk_dashscope", "import dashscope", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase5_provider_sdk_zhipu", "import zhipuai", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase5_provider_sdk_minimax", "import minimax", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase5_provider_sdk_deepseek", "import deepseek", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase5_raw_http_requests", "requests.", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase5_raw_httpx", "httpx.", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase5_raw_urllib", "urllib.request", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase5_aiohttp", "aiohttp", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase5_provider_locator_base", "base_url=", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase5_provider_locator_endpoint", "endpoint=", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase5_key_assignment", "api_key=", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase5_save_token", "save_token", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase5_save_secret", "save_secret", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase5_credential_value", "credential_value", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase5_plaintext_secret", "plaintext_secret", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase5_subprocess", "subprocess", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase5_os_system", "os.system", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase5_popen", "Popen", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase5_shell_true", "shell=True", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase5_socket", "socket.", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase5_path_write", "Path.write_text", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase5_path_unlink", "Path.unlink", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase5_remove_tree", "shutil.rmtree", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase5_sqlite", "sqlite3", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase5_redis", "redis", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase5_write_l2_fact", "write_l2_fact", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase5_write_memory", "write_memory", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase5_promote_memory", "promote_memory", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase5_delete_memory", "delete_memory", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase5_write_audit", "write_audit", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase5_charge_budget", "charge_budget", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase5_allocate_budget", "allocate_budget", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase5_issue_permit", "issue_permit", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase5_grant_permission", "grant_permission", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase5_final_allow", "final_allow", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase5_final_deny", "final_deny", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase5_direct_event_queue", "direct_event_queue", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase5_direct_tool_registry", "direct_tool_registry", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase5_direct_model_client", "direct_model_client", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase5_plugin_instance", "plugin_instance", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase5_parallel_runtime", "parallel_runtime", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase5_ability_package_port", "AbilityPackagePort", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase5_ability_package", "AbilityPackage", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase5_decrement_budget", "decrement_budget", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase5_consume_budget", "consume_budget", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase5_reserve_quota", "reserve_quota", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase5_allocate_resource", "allocate_resource", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase5_release_resource", "release_resource", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase5_start_limiter", "start_limiter", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase5_approve_execution", "approve_execution", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase5_governance_execute", "governance_decision_execute", L6ForbiddenScanSeverity.P0),
    )
    return tuple(L6ForbiddenScanRule(rule_ref=rule_ref, pattern_text=pattern, severity=severity) for rule_ref, pattern, severity in patterns)


def scan_l6_phase5_text(subject_ref: str, source_text: str):
    return scan_l6_text(subject_ref, source_text, default_l6_phase5_forbidden_scan_rules())
