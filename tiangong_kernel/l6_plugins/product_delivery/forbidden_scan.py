"""Forbidden scan declarations for L6 phase6 product delivery."""

from __future__ import annotations

from tiangong_kernel.l6_plugins.common.forbidden_scan import L6ForbiddenScanRule, L6ForbiddenScanSeverity, scan_l6_text


def default_l6_phase6_forbidden_scan_rules() -> tuple[L6ForbiddenScanRule, ...]:
    patterns: tuple[tuple[str, str, L6ForbiddenScanSeverity], ...] = (
        ("forbid:l6_phase6_provider_sdk_openai", "import openai", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase6_provider_sdk_anthropic", "import anthropic", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase6_provider_sdk_google", "google.genai", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase6_provider_sdk_dashscope", "import dashscope", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase6_provider_sdk_zhipu", "import zhipuai", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase6_provider_sdk_minimax", "import minimax", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase6_provider_sdk_deepseek", "import deepseek", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase6_raw_http_requests", "requests.", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase6_raw_httpx", "httpx.", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase6_raw_urllib", "urllib.request", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase6_aiohttp", "aiohttp", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase6_provider_locator_base", "base_url=", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase6_provider_locator_endpoint", "endpoint=", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase6_key_assignment", "api_key=", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase6_subprocess", "subprocess", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase6_os_system", "os.system", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase6_popen", "Popen", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase6_shell_true", "shell=True", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase6_socket", "socket.", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase6_path_write", "Path.write_text", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase6_path_write_bytes", "Path.write_bytes", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase6_path_unlink", "Path.unlink", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase6_remove_tree", "shutil.rmtree", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase6_archive_write", "zipfile.ZipFile", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase6_pytest_main", "pytest.main", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase6_compile_dir", "compileall.compile_dir", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase6_direct_l4_adapter", "L4LiveAdapter", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase6_dispatch_tool", "dispatch_tool", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase6_invoke_tool", "invoke_tool", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase6_model_dispatch", "model_dispatch", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase6_write_l2_fact", "write_l2_fact", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase6_write_memory", "write_memory", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase6_delete_memory", "delete_memory", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase6_write_audit", "write_audit", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase6_charge_budget", "charge_budget", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase6_build_now", "build_artifact_now", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase6_product_file_now", "write_product_file", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase6_archive_now", "create_zip_now", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase6_tests_now", "run_tests_now", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase6_execute_build", "execute_build", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase6_commit_delivery", "commit_delivery", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase6_final_spec", "final_product_spec", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase6_final_plan", "final_build_plan", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase6_artifact_built", "artifact_built", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase6_archive_created", "zip_created", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase6_tests_passed_fake", "tests_passed=True", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase6_delivery_complete", "delivery_completed", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase6_direct_event_queue", "direct_event_queue", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase6_direct_tool_registry", "direct_tool_registry", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase6_direct_model_client", "direct_model_client", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase6_plugin_instance", "plugin_instance", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase6_parallel_runtime", "parallel_runtime", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase6_ability_package_port", "AbilityPackagePort", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase6_ability_package", "AbilityPackage", L6ForbiddenScanSeverity.P0),
    )
    return tuple(L6ForbiddenScanRule(rule_ref=rule_ref, pattern_text=pattern, severity=severity) for rule_ref, pattern, severity in patterns)


def scan_l6_phase6_text(subject_ref: str, source_text: str):
    return scan_l6_text(subject_ref, source_text, default_l6_phase6_forbidden_scan_rules())
