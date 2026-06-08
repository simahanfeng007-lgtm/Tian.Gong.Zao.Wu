
"""Code-X R12 package orchestrator.

Pure candidate package assembly for L6.70.2-CodeX.
This module has no runtime registration side effects and no external project imports.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, List

STAGE = "R12能力包重编排"
DATE = "20260607"

ENGINEERING_TOOLS = ['code_x.repo_map', 'code_x.file_tree_scan', 'code_x.symbol_index', 'code_x.dependency_graph', 'code_x.call_graph', 'code_x.test_map', 'code_x.entrypoint_detector', 'code_x.config_detector', 'code_x.stack_detector', 'code_x.code_owner_detector']
CONTEXT_TOOLS = ['code_x.linyuanzhe_md_generator', 'code_x.project_rules_reader', 'code_x.directory_override_rules_reader', 'code_x.context_compactor', 'code_x.log_compactor', 'code_x.task_digest', 'code_x.changed_files_index', 'code_x.handoff_digest', 'code_x.decision_memory']
LOCALIZATION_TOOLS = ['code_x.issue_to_file_localizer', 'code_x.file_to_symbol_localizer', 'code_x.symbol_to_line_localizer', 'code_x.semantic_code_search', 'code_x.graph_code_search', 'code_x.test_failure_trace_mapper', 'code_x.affected_area_detector']
PATCH_TOOLS = ['code_x.patch_plan_generator', 'code_x.edit_unit_planner', 'code_x.patch_contract_builder', 'code_x.unified_diff_generator', 'code_x.workspace_patch_applier', 'code_x.conflict_detector', 'code_x.before_after_diff', 'code_x.before_after_hash', 'code_x.patch_manifest_generator']
VALIDATION_TOOLS = ['code_x.environment_probe', 'code_x.command_capability_probe', 'code_x.safe_command_runner', 'code_x.python_quality_runner', 'code_x.pytest_runner', 'code_x.npm_test_runner', 'code_x.build_runner', 'code_x.lint_runner', 'code_x.typecheck_runner', 'code_x.static_analyzer', 'code_x.generated_test_runner', 'code_x.fallback_test_strategy']
REPAIR_TOOLS = ['code_x.failure_attribution_analyzer', 'code_x.syntax_error_analyzer', 'code_x.import_error_analyzer', 'code_x.dependency_error_analyzer', 'code_x.test_failure_analyzer', 'code_x.flaky_test_detector', 'code_x.repair_loop_planner', 'code_x.next_patch_generator', 'code_x.verification_loop_controller']
WORKSPACE_TOOLS = ['code_x.workspace_snapshot', 'code_x.git_worktree_mode', 'code_x.patch_manifest', 'code_x.changed_files_manifest', 'code_x.rollback_plan', 'code_x.restore_checkpoint', 'code_x.delivery_candidate_packager', 'code_x.zip_delivery_packager']
SUBAGENTS = ['code_x.code_research_subagent', 'code_x.test_design_subagent', 'code_x.review_subagent', 'code_x.security_review_subagent', 'code_x.refactor_review_subagent', 'code_x.migration_subagent', 'code_x.frontend_visual_subagent']
RULES_AND_HOOKS = ['code_x.permission_profiles', 'code_x.command_rules', 'code_x.pre_tool_gate', 'code_x.post_tool_audit', 'code_x.secret_scan_hook', 'code_x.destructive_command_blocker', 'code_x.patch_audit_hook', 'code_x.command_audit_hook', 'code_x.subagent_start_hook', 'code_x.handoff_audit_hook']

CORE_TOOL_GROUPS = {
    "engineering_sense": ENGINEERING_TOOLS,
    "context_armor": CONTEXT_TOOLS,
    "code_localization": LOCALIZATION_TOOLS,
    "patch_production": PATCH_TOOLS,
    "execution_validation": VALIDATION_TOOLS,
    "failure_repair_loop": REPAIR_TOOLS,
    "workspace_rollback_delivery": WORKSPACE_TOOLS,
}

ALLOWED_RISK_LEVELS = ["A0", "A1", "A2", "A3", "A4"]
HARD_BLOCK_ONLY = ["A5"]
NEVER_LOCK_KEYS = ["rollback", "handoff", "state_recover", "lease_extend"]

@dataclass(frozen=True)
class PackageRef:
    id: str
    kind: str
    stage: str
    status: str
    registration_status: str = "candidate_only_not_registered"


def _tool_meta(tool_id: str, group: str) -> Dict[str, Any]:
    return {
        "id": tool_id,
        "group": group,
        "status": "candidate",
        "runtime_registered": False,
        "source_policy": "v2_native_candidate_no_external_source_copy",
        "result_contract": "tool_result_envelope_with_next_action_hint",
        "permission_profile": "code_x_default_allow_a0_a4_a5_hard_block",
        "lease_policy": "code_x_protected_lease",
        "audit_required": True,
    }


def build_toolpackage() -> Dict[str, Any]:
    tools: List[Dict[str, Any]] = []
    for group, ids in CORE_TOOL_GROUPS.items():
        tools.extend(_tool_meta(tool_id, group) for tool_id in ids)
    return {
        "id": "tp.candidate.code_x_exoskeleton_tools",
        "kind": "ToolPackage",
        "stage": STAGE,
        "date": DATE,
        "status": "candidate_only",
        "runtime_registered": False,
        "tool_count": len(tools),
        "groups": CORE_TOOL_GROUPS,
        "tools": tools,
        "default_execution_policy": {
            "a0_a4_default_allow_with_audit": True,
            "a5_hard_block": True,
            "write_scope": "workspace_only",
            "main_runtime_mutation": False,
            "direct_production_mutation": False,
            "never_lock_keys": NEVER_LOCK_KEYS,
        },
    }


def build_hooks_package() -> Dict[str, Any]:
    return {
        "id": "hooks.code_x_execution_audit",
        "kind": "HookPackage",
        "stage": STAGE,
        "status": "candidate_only",
        "runtime_registered": False,
        "rules": ["permission_profiles", "command_rules"],
        "hooks": [
            {"id": "code_x.pre_tool_gate", "phase": "pre_tool", "hard_block": ["A5"], "audit": True},
            {"id": "code_x.post_tool_audit", "phase": "post_tool", "hard_block": [], "audit": True},
            {"id": "code_x.secret_scan_hook", "phase": "pre_delivery_and_post_patch", "hard_block": ["A5"], "audit": True},
            {"id": "code_x.destructive_command_blocker", "phase": "pre_command", "hard_block": ["A5"], "audit": True},
            {"id": "code_x.patch_audit_hook", "phase": "post_patch", "hard_block": [], "audit": True},
            {"id": "code_x.command_audit_hook", "phase": "post_command", "hard_block": [], "audit": True},
            {"id": "code_x.subagent_start_hook", "phase": "pre_subagent", "hard_block": [], "audit": True},
            {"id": "code_x.handoff_audit_hook", "phase": "handoff", "hard_block": [], "audit": True},
        ],
        "never_lock_assertions": NEVER_LOCK_KEYS,
    }


def build_subagents_pack() -> Dict[str, Any]:
    roles = {
        "code_x.code_research_subagent": "repo evidence and localization research",
        "code_x.test_design_subagent": "test strategy and fixture design",
        "code_x.review_subagent": "general patch review",
        "code_x.security_review_subagent": "secret and risky command review",
        "code_x.refactor_review_subagent": "multi-file refactor risk review",
        "code_x.migration_subagent": "migration and compatibility review",
        "code_x.frontend_visual_subagent": "frontend visual and interaction inspection",
    }
    return {
        "id": "subagents.code_research_pack",
        "kind": "SubagentPack",
        "stage": STAGE,
        "status": "candidate_only",
        "runtime_registered": False,
        "subagent_count": len(SUBAGENTS),
        "subagents": [
            {
                "id": sid,
                "role": roles[sid],
                "evidence_only": True,
                "direct_workspace_write": False,
                "direct_patch_submit": False,
                "decision_owner": "LLM_MAIN_BRAIN",
                "required_return": ["summary", "evidence", "risk", "next_action_hint"],
            }
            for sid in SUBAGENTS
        ],
    }


def build_skill_workflow() -> Dict[str, Any]:
    return {
        "id": "skill.code_x_execution_workflow",
        "kind": "Skill",
        "stage": STAGE,
        "status": "candidate_only",
        "runtime_registered": False,
        "principle": "LLM is the main brain; Code-X is the execution exoskeleton.",
        "workflow": [
            {"step": "intake", "uses": ["task_state", "continue_policy"], "next": "repo_understanding"},
            {"step": "repo_understanding", "uses": ENGINEERING_TOOLS, "next": "context_compaction"},
            {"step": "context_compaction", "uses": CONTEXT_TOOLS, "next": "localization"},
            {"step": "localization", "uses": LOCALIZATION_TOOLS, "next": "patch_planning"},
            {"step": "patch_planning", "uses": ["code_x.patch_plan_generator", "code_x.edit_unit_planner"], "next": "patch_apply"},
            {"step": "patch_apply", "uses": PATCH_TOOLS, "next": "validation"},
            {"step": "validation", "uses": VALIDATION_TOOLS, "next": "repair_or_delivery"},
            {"step": "repair_or_delivery", "uses": REPAIR_TOOLS + WORKSPACE_TOOLS, "next": "handoff"},
            {"step": "handoff", "uses": ["code_x.handoff_digest", "code_x.handoff_audit_hook"], "next": "done_or_resume"},
        ],
        "repair_loop_limits": {"normal_task": 3, "long_chain_task": 6},
        "required_output_every_step": ["status", "summary", "evidence", "next_action_hint"],
    }


def build_abilitypackage() -> Dict[str, Any]:
    return {
        "id": "ab.candidate.llm_code_x",
        "kind": "AbilityPackage",
        "stage": STAGE,
        "status": "candidate_only",
        "runtime_registered": False,
        "composes": {
            "toolpackage": "tp.candidate.code_x_exoskeleton_tools",
            "skill": "skill.code_x_execution_workflow",
            "hooks": "hooks.code_x_execution_audit",
            "subagents": "subagents.code_research_pack",
        },
        "trigger_rules": [
            "code bugfix or feature request",
            "test/build/lint/typecheck failure",
            "multi-file refactor or migration",
            "frontend behavior/visual defect",
            "long-chain coding handoff/resume",
        ],
        "route_priority": "higher_than_code_readonly_analysis_when_write_or_validate_is_needed",
        "demotes": ["tp.candidate.code_readonly_analysis"],
        "decision_owner": "LLM_MAIN_BRAIN",
        "planner_role": "advisor_only",
    }


def build_candidate_registry_manifest() -> Dict[str, Any]:
    refs = [
        PackageRef("tp.candidate.code_x_exoskeleton_tools", "ToolPackage", STAGE, "candidate_only"),
        PackageRef("ab.candidate.llm_code_x", "AbilityPackage", STAGE, "candidate_only"),
        PackageRef("skill.code_x_execution_workflow", "Skill", STAGE, "candidate_only"),
        PackageRef("hooks.code_x_execution_audit", "HookPackage", STAGE, "candidate_only"),
        PackageRef("subagents.code_research_pack", "SubagentPack", STAGE, "candidate_only"),
    ]
    return {
        "id": "candidate_registry.code_x_r12_bundle",
        "stage": STAGE,
        "date": DATE,
        "registration_mode": "candidate_pool_only",
        "runtime_registered": False,
        "refs": [asdict(r) for r in refs],
        "no_pollution_assertions": [
            "no copied external source",
            "no legacy registry reuse",
            "no legacy executor reuse",
            "no runtime main-chain mutation",
            "no background loop",
            "no planner takeover",
            "no subagent takeover",
        ],
        "r13_requires_real_smoke_before_registration": True,
    }


def build_readonly_analysis_demotion() -> Dict[str, Any]:
    return {
        "id": "code_readonly_analysis_demoted_subability",
        "old_role": "candidate main code ability",
        "new_role": "subability under ab.candidate.llm_code_x",
        "reason": "read-only analysis cannot satisfy patch/test/repair/rollback/delivery loop",
        "allowed_stage_usage": ["repo_understanding", "context_compaction", "localization"],
        "not_allowed_as_claim": "complete code production chain",
    }


def build_full_bundle() -> Dict[str, Any]:
    return {
        "stage": STAGE,
        "date": DATE,
        "toolpackage": build_toolpackage(),
        "abilitypackage": build_abilitypackage(),
        "skill": build_skill_workflow(),
        "hooks": build_hooks_package(),
        "subagents": build_subagents_pack(),
        "candidate_registry": build_candidate_registry_manifest(),
        "readonly_analysis_demotion": build_readonly_analysis_demotion(),
    }


def validate_bundle(bundle: Dict[str, Any]) -> List[str]:
    violations: List[str] = []
    if bundle["toolpackage"]["runtime_registered"]:
        violations.append("ToolPackage must not be runtime registered in R12.")
    if bundle["abilitypackage"]["runtime_registered"]:
        violations.append("AbilityPackage must not be runtime registered in R12.")
    tools = bundle["toolpackage"]["tools"]
    if len(tools) != 64:
        violations.append(f"Expected 64 core tools, got {len(tools)}.")
    if len(bundle["subagents"]["subagents"]) != 7:
        violations.append("Expected 7 evidence-only subagents.")
    if len(bundle["hooks"]["hooks"]) != 8:
        violations.append("Expected 8 audit hooks excluding rule assets.")
    for tool in tools:
        if not tool["id"].startswith("code_x."):
            violations.append(f"Bad tool id prefix: {tool['id']}")
        if tool.get("runtime_registered"):
            violations.append(f"Tool unexpectedly registered: {tool['id']}")
        if tool.get("decision_owner") == "PLANNER":
            violations.append(f"Planner takeover risk: {tool['id']}")
    for agent in bundle["subagents"]["subagents"]:
        if not agent["evidence_only"]:
            violations.append(f"Subagent not evidence-only: {agent['id']}")
        if agent["direct_workspace_write"] or agent["direct_patch_submit"]:
            violations.append(f"Subagent has write/patch authority: {agent['id']}")
        if agent["decision_owner"] != "LLM_MAIN_BRAIN":
            violations.append(f"Subagent decision owner is not LLM: {agent['id']}")
    if bundle["abilitypackage"]["planner_role"] != "advisor_only":
        violations.append("Planner role must be advisor_only.")
    for key in NEVER_LOCK_KEYS:
        if key not in bundle["toolpackage"]["default_execution_policy"]["never_lock_keys"]:
            violations.append(f"Missing never-lock key: {key}")
    return violations
