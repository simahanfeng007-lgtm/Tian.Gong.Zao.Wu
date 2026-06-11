"""L6 phase4 forbidden scan rule declarations."""

from __future__ import annotations

from tiangong_kernel.l6_plugins.common.forbidden_scan import L6ForbiddenScanRule, L6ForbiddenScanSeverity, scan_l6_text


def default_l6_phase4_forbidden_scan_rules() -> tuple[L6ForbiddenScanRule, ...]:
    patterns: tuple[tuple[str, str, L6ForbiddenScanSeverity], ...] = (
        ("forbid:l6_phase4_provider_sdk_openai", "import openai", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase4_provider_sdk_anthropic", "import anthropic", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase4_provider_sdk_deepseek", "import deepseek", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase4_provider_sdk_google", "google.genai", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase4_provider_sdk_dashscope", "import dashscope", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase4_provider_sdk_zhipu", "import zhipuai", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase4_provider_sdk_minimax", "import minimax", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase4_raw_http_requests", "requests.", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase4_raw_httpx", "httpx.", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase4_aiohttp", "aiohttp", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase4_provider_locator_base", "base_url=", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase4_provider_locator_endpoint", "endpoint=", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase4_key_assignment", "api_key=", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase4_subprocess", "subprocess", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase4_os_system", "os.system", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase4_popen", "Popen", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase4_shell_true", "shell=True", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase4_file_write_text", "Path.write_text", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase4_file_unlink", "Path.unlink", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase4_remove_tree", "rmtree", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase4_write_fact", "write_fact", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase4_save_fact", "save_fact", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase4_commit_fact", "commit_fact", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase4_memory_store_write", "memory_store.write", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase4_save_memory", "save_memory", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase4_promote_memory", "promote_memory", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase4_forget_now", "forget_now", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase4_dispatch_tool", "dispatch_tool", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase4_invoke_tool", "invoke_tool", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase4_model_dispatch", "model_dispatch", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase4_tool_dispatch_request", "ToolDispatchRequest", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase4_full_affective_profile", "full_affective_profile=", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase4_raw_prompt", "raw_prompt=", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase4_complete_evidence_chain", "complete_evidence_chain=", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase4_execution_plan", "execution_plan=", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase4_delete_memory", "delete_memory", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase4_update_l2", "update_l2", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase4_state_store_write", "state_store.write", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase4_repair_applied", "repair_applied", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase4_patch_applied", "patch_applied", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase4_rollback_applied", "rollback_applied", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase4_auto_evolve", "auto_evolve", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase4_git_commit", "git commit", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase4_git_push", "git push", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase4_product_spec_constructor", "ProductSpec(", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase4_build_plan_constructor", "BuildPlan(", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase4_artifact_build", "ArtifactBuild", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase4_docx_builder", "DocxBuilder", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase4_pdf_builder", "PdfBuilder", L6ForbiddenScanSeverity.P0),
        ("forbid:l6_phase4_pptx_builder", "PptxBuilder", L6ForbiddenScanSeverity.P0),
    )
    return tuple(L6ForbiddenScanRule(rule_ref=rule_ref, pattern_text=pattern, severity=severity) for rule_ref, pattern, severity in patterns)


def scan_l6_phase4_text(subject_ref: str, source_text: str):
    return scan_l6_text(subject_ref, source_text, default_l6_phase4_forbidden_scan_rules())
