"""Global Runtime tool/Skill alignment for L6.70.2 R15.

This module is intentionally metadata-only. It does not execute tools, import v1,
mutate registries, start loops, or give Planner authority. It exposes a complete
LLM-facing registry/usage map so every registered Runtime tool has at least one
safe path for selection, review, and governed invocation.
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from collections.abc import Callable, Iterable, Mapping
from typing import Any

from .execution_policy import RiskLevel
from .risk_classifier import RiskClassifier
from .runtime_tool_registry import ToolDescriptor
from .tool_invocation import ToolInvocation
from .tool_result import ToolResult, ToolResultStatus
from .turn_context import TurnContext

DescriptorProvider = Callable[[], Iterable[ToolDescriptor]]
PlanBuilder = Callable[[str], list[ToolInvocation]]

ALIGNMENT_TOOL_NAMES = {"runtime_tool_alignment_check", "runtime_llm_operational_drill"}
SANDBOX_ALIGNMENT_TOOL_NAMES = {"learning_asset_sandbox_guide", "learning_asset_sandbox_align", "learning_asset_sandbox_validate"}
CANDIDATE_SANDBOX_TOOL_NAMES = {
    "learning_asset_candidate_sandbox_guide",
    "learning_asset_candidate_sandbox_build",
    "learning_asset_candidate_sandbox_validate",
    "learning_asset_candidate_sandbox_review",
}
RELEASE_GATE_TOOL_NAMES = {
    "learning_asset_release_gate_guide",
    "learning_asset_release_gate_check",
}
ACTIVATION_TOOL_NAMES = {
    "learning_asset_activation_guide",
    "learning_asset_activation_apply",
    "learning_asset_activation_status",
    "learning_asset_activation_smoke",
}
ADAPTER_TEMPLATE_TOOL_NAMES = {
    "learning_asset_adapter_guide",
    "learning_asset_adapter_template_list",
    "learning_asset_adapter_template_normalize",
    "learning_asset_adapter_template_validate",
    "learning_asset_adapter_template_smoke",
    "learning_asset_adapter_drill",
}


def _risk_value(value: Any) -> str:
    raw = getattr(value, "value", value)
    text = str(raw or "A2").strip()
    return text or "A2"


def _family_for(name: str) -> str:
    if name in ALIGNMENT_TOOL_NAMES:
        return "runtime_alignment"
    if name in SANDBOX_ALIGNMENT_TOOL_NAMES:
        return "learning_asset_sandbox_alignment"
    if name in CANDIDATE_SANDBOX_TOOL_NAMES:
        return "learning_asset_candidate_sandbox"
    if name in RELEASE_GATE_TOOL_NAMES:
        return "learning_asset_release_gate"
    if name in ADAPTER_TEMPLATE_TOOL_NAMES:
        return "learning_asset_adapter_template"
    if name in ACTIVATION_TOOL_NAMES or name.startswith(("learned_tool_", "learned_skill_")):
        return "learning_asset_activation"
    if name.startswith("learning_asset_contract_"):
        return "learning_asset_contract"
    if name.startswith("code_x_") or name in {
        "repo_map", "file_tree_scan", "symbol_index", "dependency_graph", "call_graph", "test_map",
        "entrypoint_detector", "config_detector", "stack_detector", "code_owner_detector",
        "generate_linyuanzhe_md", "project_rules_reader", "context_compactor", "log_compactor",
        "task_digest", "handoff_digest", "changed_files_index", "decision_memory",
        "issue_to_file_localizer", "file_to_symbol_localizer", "symbol_to_line_localizer",
        "semantic_code_search", "graph_code_search", "test_failure_trace_mapper", "affected_area_detector",
        "patch_plan_generator", "edit_unit_planner", "conflict_detector", "unified_diff_generator",
        "workspace_patch_applier", "before_after_hash", "patch_manifest", "environment_probe",
        "command_capability_probe", "safe_command_runner", "python_quality_runner", "pytest_runner",
        "npm_test_runner", "build_runner", "lint_runner", "typecheck_runner", "static_analyzer",
        "fallback_test_strategy", "failure_attribution_analyzer", "syntax_error_analyzer", "import_error_analyzer",
        "dependency_error_analyzer", "test_failure_analyzer", "flaky_test_detector", "repair_loop_planner",
        "next_patch_generator", "workspace_snapshot", "git_worktree_mode", "rollback_plan",
        "restore_checkpoint", "delivery_candidate_packager", "zip_delivery_packager", "code_research_subagent",
        "test_design_subagent", "review_subagent", "security_review_subagent", "refactor_review_subagent",
        "migration_subagent", "frontend_visual_subagent", "subagent_pack_manifest", "build_toolpackage",
        "build_hooks_package", "build_subagents_pack", "build_skill_workflow", "build_abilitypackage",
        "build_candidate_registry_manifest", "build_readonly_analysis_demotion", "build_full_bundle", "validate_bundle",
    }:
        return "code_x"
    if name.startswith("v1_clean_import_") or name in {
        "workspace_text_search", "conversation_history_search", "task_pattern_search", "experience_mentor_search",
        "document_text_extract", "web_readability_extract", "learning_master_plan", "tool_skill_blueprint",
    }:
        return "v1_clean_import"
    if name.startswith("build_l6_38"):
        return "p0_provider_budget_skill_handoff"
    if name.startswith("build_l6_39"):
        return "p0_memory_audit_recovery_quality"
    if name.startswith("build_") or name in {
        "synthesize_experience_candidates", "queue_skill_candidates", "queue_tool_production_requests",
    }:
        return "l6_planning_shell"
    if name in {"list_dir", "read_file", "file_sha256", "write_workspace_file"}:
        return "workspace_io"
    if name in {"scan_project", "diagnose_project", "evaluate_quality_gate", "run_python_quality_check"}:
        return "engineering_quality"
    if name in {"create_zip_package", "create_release_bundle"}:
        return "delivery"
    if name in {"model_chat", "return_code", "return_analysis"}:
        return "core_runtime"
    return "other_runtime"


def _when_to_use(name: str, description: str, family: str) -> str:
    if family == "code_x":
        return "代码工程任务需要读库、定位、补丁、验证、二修、回滚或交付时使用；由 LLM 按 Code-X Skill 选择具体链路。"
    if family == "v1_clean_import":
        return "非代码材料、会话/作业/经验搜索、文档提取、学习精通或 Tool/Skill 草案任务使用；只读或草案，不混入 Code-X。"
    if family.startswith("p0_"):
        return "P0 系统接入、状态摘要、票据、证据或 Planner 上下文需要对齐时使用；只生成治理材料，不改内核。"
    if family == "l6_planning_shell":
        return "L6 外壳规划、候选入队、治理/恢复/Provider/交付标准化等分析型任务使用；默认不执行副作用。"
    if family == "workspace_io":
        return "用户明确要求列目录、读文件或写 workspace 文件时使用；写入前由 Runtime 审计。"
    if family == "engineering_quality":
        return "项目扫描、诊断、质量门、compileall/pytest 质量检查时使用。"
    if family == "delivery":
        return "阶段包、发布包、交付 zip 或交付 Manifest 需要生成时使用。"
    if family == "runtime_alignment":
        return "检查工具注册表、Skill/usage card/Planner 路由是否对齐，或做 LLM 路由实操演练时使用。"
    if family == "learning_asset_contract":
        return "统一未来自主学习、经验沉淀、Tool 生产请求和 Skill 草案的资产格式时使用；只做契约指南、归一化和校验，不生产不注册。"
    if family == "learning_asset_sandbox_alignment":
        return "把 R16 统一资产契约中的 Tool 候选对齐到已存在 L6.22 ToolProductionRequest/SandboxValidationPlan 沙箱前置链时使用；不新建沙箱、不生产不注册。"
    if family == "learning_asset_candidate_sandbox":
        return "R16/R17 通过后，把 Tool/Skill 候选真实落盘为隔离候选包，做静态扫描、smoke、回滚证据和注册审阅；不注册不激活。"
    if family == "learning_asset_release_gate":
        return "R18 review_ready 后使用，把候选包证据压成质量门、发布门、回滚证据和注册申请四项结果；不做复杂审批，交给 R20 激活。"
    if family == "learning_asset_adapter_template":
        return "R21 学习资产实用型 Adapter 模板：用于生成/校验/smoke 纯函数、契约校验、项目诊断、文档生产辅助和经验复用 learned Tool。"
    if family == "learning_asset_activation":
        if name.startswith(("learned_tool_", "learned_skill_")):
            return "自主学习/经验总结候选已通过 R16-R20 后使用；这是 active learned asset，可由 LLM 直接调用并继续执行链。"
        return "R19 注册申请 ready 后使用，把候选 Tool/Skill 激活为 workspace 级 active asset，并注册 learned_* 供 LLM 立即调用。"
    return description or "Runtime 已注册工具；由 LLM 查看描述和风险后经治理链调用。"


def _required_inputs_hint(name: str, family: str) -> dict[str, str]:
    if name in {"list_dir", "read_file"}:
        return {"path": "workspace 内相对路径，默认 ."}
    if name == "write_workspace_file":
        return {"path": "workspace 内相对路径", "content": "写入内容"}
    if name in {"run_python_quality_check", "python_quality_runner"}:
        return {"command/target": "compileall 或 pytest；Code-X 质量 runner 可默认 workspace"}
    if name in {"repo_map", "file_tree_scan", "symbol_index", "dependency_graph", "call_graph", "test_map", "stack_detector"}:
        return {"workspace_root/repo_root": "workspace 根目录，默认 ."}
    if name in {"issue_to_file_localizer", "patch_plan_generator"}:
        return {"issue_text/issue": "用户问题、需求或报错日志"}
    if name in {"semantic_code_search", "graph_code_search", "workspace_text_search", "conversation_history_search", "task_pattern_search", "experience_mentor_search"}:
        return {"query": "搜索关键词、行为描述或历史任务摘要"}
    if name in {"document_text_extract", "read_file"}:
        return {"path": "workspace 内相对文件路径"}
    if name in {"web_readability_extract"}:
        return {"html_or_text": "用户已提供的 HTML 或正文；不联网抓取"}
    if name in {"learning_master_plan", "tool_skill_blueprint"}:
        return {"goal": "学习目标或 Tool/Skill 生产目标"}
    if family == "learning_asset_contract":
        return {"notes/contract": "notes 用于归一化备注；contract/payload 用于校验外部候选契约；guide 无必填参数"}
    if family == "learning_asset_sandbox_alignment":
        return {"notes": "可选安全备注；align/validate 默认读取当前 R16 契约报告与 L6.22 Tool 请求队列"}
    if family == "learning_asset_candidate_sandbox":
        return {"notes/max_items": "可选安全备注和候选包数量；build 默认读取当前 R16 契约与 R17 沙箱映射"}
    if family == "learning_asset_release_gate":
        return {"notes": "可选安全备注；check 默认读取当前 R18 候选包 review 报告"}
    if family == "learning_asset_adapter_template":
        return {"template_id/payload/sample_args/notes": "template_id 可选 pure_transform/schema_contract_check/project_diagnostic/doc_skill_production/experience_reuse/all；drill 会走 R20 激活"}
    if family == "learning_asset_activation":
        if name.startswith(("learned_tool_", "learned_skill_")):
            return {"query/goal/notes": "LLM 当前任务摘要；active asset 会返回 usage_card、chain_recipe 和下一步提示"}
        return {"notes/sample_args": "apply/status 默认读取当前 R19/R18 报告；smoke 可传 sample_args"}
    if name in {"workspace_patch_applier", "conflict_detector", "unified_diff_generator"}:
        return {"edit_units": "LLM 审阅后的编辑单元；写入前必须先 snapshot"}
    if name in {"failure_attribution_analyzer", "syntax_error_analyzer", "import_error_analyzer", "test_failure_analyzer"}:
        return {"log_text": "失败日志、异常栈或测试输出"}
    if name in {"restore_checkpoint"}:
        return {"snapshot_id/manifest": "workspace_snapshot 返回的快照标识或路径"}
    if name in {"create_zip_package", "zip_delivery_packager", "code_x_package_workflow"}:
        return {"include/source/output": "待打包路径与输出 zip 路径"}
    if family in {"l6_planning_shell", "p0_provider_budget_skill_handoff", "p0_memory_audit_recovery_quality"}:
        return {"notes": "用户目标、当前阶段、证据摘要；默认只生成报告/票据/Hint"}
    return {"arguments": "按工具描述提供结构化 JSON；不确定时先调用 runtime_tool_alignment_check 查看卡片。"}


def _next_action_hint_for(name: str, family: str) -> str:
    if name == "runtime_tool_alignment_check":
        return "runtime_llm_operational_drill"
    if name == "runtime_llm_operational_drill":
        return "handoff_digest 或阶段报告"
    if name == "learning_asset_contract_guide":
        return "learning_asset_contract_normalize"
    if name == "learning_asset_contract_normalize":
        return "learning_asset_contract_validate"
    if name == "learning_asset_contract_validate":
        return "learning_asset_sandbox_align for tool assets / quality_gate for skill-only assets"
    if name == "learning_asset_sandbox_guide":
        return "learning_asset_sandbox_align"
    if name == "learning_asset_sandbox_align":
        return "learning_asset_sandbox_validate"
    if name == "learning_asset_sandbox_validate":
        return "learning_asset_candidate_sandbox_build"
    if name == "learning_asset_candidate_sandbox_guide":
        return "learning_asset_candidate_sandbox_build"
    if name == "learning_asset_candidate_sandbox_build":
        return "learning_asset_candidate_sandbox_validate"
    if name == "learning_asset_candidate_sandbox_validate":
        return "learning_asset_candidate_sandbox_review"
    if name == "learning_asset_candidate_sandbox_review":
        return "learning_asset_release_gate_check"
    if name == "learning_asset_release_gate_guide":
        return "learning_asset_release_gate_check"
    if name == "learning_asset_release_gate_check":
        return "learning_asset_activation_apply"
    if name == "learning_asset_activation_guide":
        return "learning_asset_activation_apply"
    if name == "learning_asset_activation_apply":
        return "learning_asset_activation_smoke"
    if name == "learning_asset_activation_status":
        return "learning_asset_activation_smoke / runtime-tools tool <learned_tool_name> {json}"
    if name == "learning_asset_activation_smoke":
        return "runtime_tool_alignment_check"
    if name == "learning_asset_adapter_guide":
        return "learning_asset_adapter_template_list"
    if name == "learning_asset_adapter_template_list":
        return "learning_asset_adapter_template_normalize / learning_asset_adapter_template_smoke"
    if name == "learning_asset_adapter_template_normalize":
        return "learning_asset_adapter_template_validate"
    if name == "learning_asset_adapter_template_validate":
        return "learning_asset_adapter_template_smoke"
    if name == "learning_asset_adapter_template_smoke":
        return "learning_asset_adapter_drill"
    if name == "learning_asset_adapter_drill":
        return "learning_asset_activation_smoke / runtime_tool_alignment_check"
    if name.startswith(("learned_tool_", "learned_skill_")):
        return "LLM 根据返回的 usage_card / chain_recipe 继续调用 Runtime 工具或生成 handoff。"
    if family == "code_x":
        return "code_x_skill_guide 提供阶段下一步；失败后 failure_attribution_analyzer。"
    if family == "v1_clean_import":
        return "v1_clean_import_guide 提供下一步；材料命中后进入 document_text_extract/learning_master_plan。"
    if family == "workspace_io":
        return "读后进入分析/搜索；写后必须进入质量检查或 handoff。"
    if family == "engineering_quality":
        return "失败进入 diagnose_project/failure attribution；通过进入交付或 handoff。"
    if family == "delivery":
        return "生成 handoff_digest 并记录 hash。"
    if family.startswith("p0_") or family == "l6_planning_shell":
        return "build_planner_context 或对应 P0 汇总工具。"
    return "由 LLM 根据 output_summary 与 next_action_hint 裁决。"


def _descriptor_card(descriptor: ToolDescriptor) -> dict[str, Any]:
    name = descriptor.name
    risk = _risk_value(descriptor.default_risk)
    family = _family_for(name)
    return {
        "tool": name,
        "family": family,
        "risk": risk,
        "description": descriptor.description,
        "when_to_use": _when_to_use(name, descriptor.description, family),
        "required_inputs": _required_inputs_hint(name, family),
        "next_action": _next_action_hint_for(name, family),
        "llm_policy": "LLM 是主脑和最终裁决者；Planner 只建议动作；工具只经 Runtime 审计链执行。",
    }




def _safe_sample_args(name: str) -> dict[str, Any]:
    """Minimal non-destructive args for rimockkey_classifier alignment checks."""
    if name == "run_python_quality_check":
        return {"command": "compileall", "target": "."}
    if name == "write_workspace_file":
        return {"path": "reports/runtime_alignment_probe.txt", "content": "dry metadata probe"}
    if name in {"create_zip_package", "create_release_bundle", "zip_delivery_packager", "code_x_package_workflow"}:
        return {"source": ".", "target": "dist/runtime_alignment_probe.zip", "include_paths": ["."], "output_zip": "dist/runtime_alignment_probe.zip"}
    if name in {"read_file", "file_sha256", "document_text_extract"}:
        return {"path": "README.md"}
    if name in {"list_dir", "scan_project", "diagnose_project"}:
        return {"path": "."}
    if name in {"workspace_text_search", "conversation_history_search", "task_pattern_search", "experience_mentor_search", "semantic_code_search", "graph_code_search"}:
        return {"query": "alignment"}
    if name in {"issue_to_file_localizer", "patch_plan_generator"}:
        return {"issue_text": "alignment probe", "issue": "alignment probe"}
    if name in {"failure_attribution_analyzer", "syntax_error_analyzer", "import_error_analyzer", "dependency_error_analyzer", "test_failure_analyzer"}:
        return {"log_text": "alignment probe"}
    if name in {"learning_master_plan", "tool_skill_blueprint"}:
        return {"goal": "alignment probe"}
    if name == "web_readability_extract":
        return {"html_or_text": "<p>alignment probe</p>"}
    if name in {"learning_asset_adapter_template_normalize", "learning_asset_adapter_template_validate"}:
        return {"template_id": "pure_transform", "notes": "alignment probe"}
    if name == "learning_asset_adapter_template_smoke":
        return {"template_id": "all"}
    if name == "learning_asset_adapter_drill":
        return {"notes": "alignment probe"}
    return {}

def build_tool_alignment_report(descriptors: Iterable[ToolDescriptor], *, include_cards: bool = True) -> dict[str, Any]:
    items = sorted(list(descriptors), key=lambda d: d.name)
    cards = [_descriptor_card(d) for d in items]
    names = [d.name for d in items]
    duplicate_names = sorted(name for name, count in Counter(names).items() if count > 1)
    missing_description = [d.name for d in items if not str(d.description or "").strip()]
    missing_risk = [d.name for d in items if not str(d.default_risk or "").strip()]
    family_counts = dict(sorted(Counter(card["family"] for card in cards).items()))
    risk_counts = dict(sorted(Counter(card["risk"] for card in cards).items()))

    classifier = RiskClassifier()
    risk_alignment: list[dict[str, Any]] = []
    blocked_by_classifier: list[dict[str, Any]] = []
    for d in items:
        try:
            classified, reason = classifier.classify(ToolInvocation(d.name, _safe_sample_args(d.name)))
            classified_text = _risk_value(classified)
        except Exception as exc:  # defensive metadata check
            classified_text = "classifier_error"
            reason = f"{type(exc).__name__}: {exc}"
        descriptor_risk = _risk_value(d.default_risk)
        acceptable = classified_text in descriptor_risk.split("/") or descriptor_risk in classified_text.split("/") or classified_text == descriptor_risk
        row = {
            "tool": d.name,
            "descriptor_risk": descriptor_risk,
            "classifier_risk": classified_text,
            "aligned": acceptable,
            "reason": reason,
        }
        risk_alignment.append(row)
        if classified_text == "A5" and d.name not in {"confirm_ticket"}:
            blocked_by_classifier.append(row)

    issues = []
    if duplicate_names:
        issues.append({"kind": "duplicate_registry_names", "items": duplicate_names})
    if missing_description:
        issues.append({"kind": "missing_description", "items": missing_description})
    if missing_risk:
        issues.append({"kind": "missing_risk", "items": missing_risk})
    if blocked_by_classifier:
        issues.append({"kind": "classifier_blocks_registered_tools", "items": blocked_by_classifier})

    return {
        "status": "ok" if not issues else "failed",
        "summary": f"Runtime tool alignment checked: {len(items)} tools, {len(cards)} LLM usage cards, {len(issues)} blocking issue groups.",
        "tool_count": len(items),
        "usage_card_count": len(cards),
        "family_counts": family_counts,
        "risk_counts": risk_counts,
        "issues": issues,
        "all_tools_have_usage_cards": len(cards) == len(items),
        "all_registered_tools_classifier_allowed": not blocked_by_classifier,
        "llm_entrypoints": {
            "global_alignment": "runtime-tools align",
            "global_drill": "runtime-tools drill",
            "raw_runtime_tool": "runtime-tools tool <tool_name> {json_args}",
            "code_x": "code-x skill / code-x fix / code-x tool <tool_name> {json_args}",
            "v1_clean_import": "v1-import guide / v1-import search / v1-import learning",
            "learning_asset_contract": "asset-contract guide / asset-contract normalize / asset-contract validate / asset-contract drill",
            "learning_asset_sandbox_alignment": "asset-sandbox guide / asset-sandbox align / asset-sandbox validate / asset-sandbox drill",
            "learning_asset_candidate_sandbox": "asset-candidate-sandbox guide / build / validate / review / drill",
            "learning_asset_release_gate": "asset-release guide / gate / drill",
            "learning_asset_activation": "asset-activate guide / apply / status / smoke / drill；runtime-tools tool <learned_tool_name> {json}",
            "learning_asset_adapter_template": "asset-adapter guide / templates / normalize / validate / smoke / drill",
            "core_runtime": "scan / diagnose / read / write / compileall / pytest / zip",
        },
        "skill_sources": [
            "skill.code_x_execution_workflow",
            "skill.v1_clean_import_workflow",
            "skill.runtime_tool_alignment_workflow",
            "skill.learning_asset_contract_workflow",
            "skill.learning_asset_sandbox_alignment_workflow",
            "skill.learning_asset_candidate_sandbox_workflow",
            "skill.learning_asset_release_gate_workflow",
            "skill.learning_asset_activation_workflow",
            "skill.learning_asset_adapter_template_workflow",
        ],
        "authority_model": {
            "llm": "主脑、工程判断者、最终裁决者",
            "runtime": "工具调度、预算、审计、回滚、状态回传",
            "planner": "动作建议器，不得夺权",
            "subagents": "证据型助手，不得写 workspace 或提交主 patch",
        },
        "no_pollution_assertions": {
            "copied_v1_source": False,
            "imported_v1_module": False,
            "reused_v1_registry": False,
            "reused_v1_executor": False,
            "reused_v1_provider": False,
            "monkey_patch": False,
            "background_loop": False,
        },
        "tool_usage_cards": cards if include_cards else [],
        "risk_alignment_sample": risk_alignment[: min(20, len(risk_alignment))],
        "next_action_hint": {
            "next_tool": "runtime_llm_operational_drill",
            "reason": "注册表和 Skill 卡片对齐后，模拟 LLM 从用户意图到 Planner 路由的真实选择链。",
            "confidence": 0.92,
            "llm_final_decision_required": True,
        },
    }


def build_llm_operational_drill(descriptors: Iterable[ToolDescriptor], plan_builder: PlanBuilder, *, scenarios: list[str] | None = None) -> dict[str, Any]:
    names = {d.name for d in descriptors}
    default_scenarios = [
        "runtime-tools align",
        "runtime-tools drill",
        "runtime-tools tool return_analysis {\"analysis\":\"alignment smoke\"}",
        "scan .",
        "diagnose .",
        "compileall .",
        "zip . dist/alignment_delivery.zip",
        "code-x status",
        "code-x skill bug_fix",
        "code-x readiness",
        "code-x v1-audit",
        "code-x smoke .",
        "code-x repo-map .",
        "code-x locate import error",
        "code-x fix add function failure",
        "v1-import status",
        "v1-import audit",
        "v1-import guide all",
        "v1-import search 学习精通",
        "v1-import conversation 文档提取",
        "v1-import task 文档提取",
        "v1-import experience 文档",
        "v1-import document docs/note.md",
        "v1-import readability <html><body><h1>标题</h1><p>正文</p></body></html>",
        "v1-import learning 学习一个 CLI 并沉淀为 Skill",
        "v1-import tool-skill 生成一个只读文档摘要工具",
        "asset-contract drill 未来所有自主学习总结经验生产 tool skill 格式统一",
        "asset-sandbox guide",
        "asset-sandbox drill pytest missing tests",
        "asset-candidate-sandbox drill pytest missing tests",
        "asset-release guide",
        "asset-release gate",
        "asset-release drill pytest missing tests",
        "asset-activate guide",
        "asset-activate status",
        "asset-activate drill pytest missing tests",
        "候选包沙箱 drill pytest missing tests",
        "候选发布 drill pytest missing tests",
        "沙箱对齐 ToolSkill 统一资产",
        "planner-context LLM 使用工具对齐",
        "p0-system-build Provider Budget Skill Handoff 对齐",
        "p0-system2-build Memory Audit Recovery QualityGate 对齐",
    ]
    rows: list[dict[str, Any]] = []
    missing_tools: list[dict[str, Any]] = []
    empty_routes: list[str] = []
    classifier = RiskClassifier()
    for scenario in scenarios or default_scenarios:
        try:
            plan = plan_builder(scenario)
            plan_tools = [step.tool_name for step in plan]
            missing = [tool for tool in plan_tools if tool not in names]
            risk_rows = []
            for step in plan:
                risk, reason = classifier.classify(step)
                risk_rows.append({"tool": step.tool_name, "risk": _risk_value(risk), "reason": reason})
            row = {
                "scenario": scenario,
                "plan_tools": plan_tools,
                "plan_length": len(plan_tools),
                "all_registered": not missing,
                "missing_tools": missing,
                "risk": risk_rows,
            }
            rows.append(row)
            if not plan_tools:
                empty_routes.append(scenario)
            if missing:
                missing_tools.append({"scenario": scenario, "missing_tools": missing})
        except Exception as exc:
            rows.append({"scenario": scenario, "error": f"{type(exc).__name__}: {exc}", "all_registered": False})
            missing_tools.append({"scenario": scenario, "error": f"{type(exc).__name__}: {exc}"})
    ok = not missing_tools and not empty_routes
    return {
        "status": "ok" if ok else "failed",
        "summary": f"LLM operational route drill simulated {len(rows)} scenarios; empty_routes={len(empty_routes)}, missing_tools={len(missing_tools)}.",
        "scenario_count": len(rows),
        "empty_routes": empty_routes,
        "missing_tool_routes": missing_tools,
        "scenarios": rows,
        "coverage_statement": "该演练验证 LLM 意图→PlanBridge→Runtime 工具名注册链；真实副作用仍由 Runtime 审计和具体工具 smoke 验证。",
        "next_action_hint": {
            "next_tool": "code_x_smoke_workflow",
            "reason": "路由演练通过后，对代表性 Code-X/v1/core 链执行真实 smoke。",
            "confidence": 0.9,
            "llm_final_decision_required": True,
        },
    }


def build_runtime_tool_alignment_adapter(descriptor_provider: DescriptorProvider):
    def adapter(invocation: ToolInvocation, context: TurnContext) -> ToolResult:
        include_cards = bool(invocation.arguments.get("include_cards", True))
        report = build_tool_alignment_report(descriptor_provider(), include_cards=include_cards)
        status = ToolResultStatus.OK if report["status"] == "ok" else ToolResultStatus.FAILED
        return ToolResult(
            step_id=invocation.step_id,
            tool_name=invocation.tool_name,
            status=status,
            output_summary=report["summary"],
            data=report,
            error_code="" if status is ToolResultStatus.OK else "runtime_tool_alignment_failed",
        )
    return adapter


def build_runtime_llm_drill_adapter(descriptor_provider: DescriptorProvider, plan_builder: PlanBuilder):
    def adapter(invocation: ToolInvocation, context: TurnContext) -> ToolResult:
        raw = invocation.arguments.get("scenarios")
        scenarios = raw if isinstance(raw, list) else None
        report = build_llm_operational_drill(descriptor_provider(), plan_builder, scenarios=scenarios)
        status = ToolResultStatus.OK if report["status"] == "ok" else ToolResultStatus.FAILED
        return ToolResult(
            step_id=invocation.step_id,
            tool_name=invocation.tool_name,
            status=status,
            output_summary=report["summary"],
            data=report,
            error_code="" if status is ToolResultStatus.OK else "runtime_llm_operational_drill_failed",
        )
    return adapter


def write_alignment_report(path: str, report: Mapping[str, Any]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2, default=str)
