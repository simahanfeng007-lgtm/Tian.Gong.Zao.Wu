from __future__ import annotations
from dataclasses import dataclass, field

L6_PHASE7_FORBIDDEN_PATTERNS: tuple[str, ...] = (
    "openai", "anthropic", "google.genai", "dashscope", "zhipuai", "minimax", "deepseek",
    "requests", "httpx", "urllib", "aiohttp", "base_url", "endpoint", "api_key",
    "subprocess", "os.system", "os.popen", "shell=True", "socket", "Path.write_text", "Path.write_bytes",
    "Path.unlink", "shutil.rmtree", "shutil.copy", "zipfile.ZipFile", "pytest.main", "compileall.compile_dir",
    "fetch_secret", "decrypt_secret", "refresh_token", "save_api_key", "save_token", "save_secret",
    "write_l2_fact", "write_memory", "delete_memory", "write_audit", "charge_budget",
    "write_skill", "register_skill", "publish_skill", "write_knowledge", "produce_tool_now", "patch_file_now",
    "apply_patch_now", "run_tests_now", "auto_heal", "auto_repair", "auto_iterate", "auto_evolve",
    "auto_migrate", "auto_rollback", "hot_switch_now", "apply_contract_patch", "merge_iteration",
    "activate_version_slot", "direct_plugin_dispatch", "execute_collaboration_plan", "merge_handoff_results",
    "resolve_conflict_now", "parallel_agent_scheduler",
)

@dataclass(frozen=True)
class L6Phase7ForbiddenScanRuleSet:
    rule_ref: str = "forbid:l6_phase7_rule_set"
    forbidden_patterns: tuple[str, ...] = field(default_factory=lambda: L6_PHASE7_FORBIDDEN_PATTERNS)
    inert_pattern_only: bool = True
    actionable_findings: int = 0

    @property
    def passed(self) -> bool:
        return self.inert_pattern_only and self.actionable_findings == 0
