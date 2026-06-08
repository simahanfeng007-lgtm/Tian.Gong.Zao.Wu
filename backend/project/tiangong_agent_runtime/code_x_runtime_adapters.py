"""Runtime adapters for L6.70.2 Code-X.

This module turns the clean Code-X candidate tools into v2 native Runtime tools.
It has no startup side effects: tools are registered only when
`register_code_x_runtime_tools(registry)` is called by RuntimeEntry.
"""
from __future__ import annotations

import inspect
import json
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, Mapping

from .runtime_tool_registry import RuntimeToolRegistry, ToolDescriptor
from .tool_invocation import ToolInvocation
from .tool_result import ToolResult, ToolResultStatus
from .turn_context import TurnContext

from .code_x_native import code_x_engineering_perception as perception
from .code_x_native import code_x_context_armor as context_armor
from .code_x_native import code_x_code_localization as localization
from .code_x_native import code_x_patch_production as patching
from .code_x_native import code_x_execution_validation as validation
from .code_x_native import code_x_failure_repair as failure_repair
from .code_x_native import code_x_worktree_rollback_packaging as worktree
from .code_x_native import code_x_subagents as subagents
from .code_x_native import code_x_package_orchestrator as orchestrator
from .code_x_native import code_x_skill_runtime as skill_runtime


CodeXCallable = Callable[..., Any]

A1_CODE_X_TOOLS = {
    "repo_map", "file_tree_scan", "symbol_index", "dependency_graph", "call_graph", "test_map",
    "entrypoint_detector", "config_detector", "stack_detector", "code_owner_detector",
    "project_rules_reader", "context_compactor", "log_compactor", "changed_files_index",
    "issue_to_file_localizer", "file_to_symbol_localizer", "symbol_to_line_localizer",
    "semantic_code_search", "graph_code_search", "test_failure_trace_mapper", "affected_area_detector",
    "environment_probe", "command_capability_probe", "static_analyzer",
}

A2_CODE_X_TOOLS = {
    "generate_linyuanzhe_md", "task_digest", "handoff_digest", "decision_memory",
    "patch_plan_generator", "edit_unit_planner", "conflict_detector", "unified_diff_generator",
    "before_after_hash", "patch_manifest", "failure_attribution_analyzer", "syntax_error_analyzer",
    "import_error_analyzer", "dependency_error_analyzer", "test_failure_analyzer", "flaky_test_detector",
    "repair_loop_planner", "next_patch_generator", "code_research_subagent", "test_design_subagent",
    "review_subagent", "security_review_subagent", "refactor_review_subagent", "migration_subagent",
    "frontend_visual_subagent", "subagent_pack_manifest", "build_toolpackage", "build_hooks_package",
    "build_subagents_pack", "build_skill_workflow", "build_abilitypackage", "build_candidate_registry_manifest",
    "build_readonly_analysis_demotion", "build_full_bundle", "validate_bundle", "code_x_runtime_status",
    "code_x_skill_guide", "code_x_world_class_readiness_check", "code_x_v1_import_audit",
}

A3_CODE_X_TOOLS = {
    "workspace_patch_applier", "safe_command_runner", "python_quality_runner", "pytest_runner", "npm_test_runner",
    "build_runner", "lint_runner", "typecheck_runner", "fallback_test_strategy", "workspace_snapshot",
    "git_worktree_mode", "rollback_plan", "restore_checkpoint", "delivery_candidate_packager",
    "zip_delivery_packager", "code_x_smoke_workflow", "code_x_package_workflow",
}

CODE_X_TOOL_RISK: Dict[str, str] = {
    **{name: "A1" for name in A1_CODE_X_TOOLS},
    **{name: "A2" for name in A2_CODE_X_TOOLS},
    **{name: "A3" for name in A3_CODE_X_TOOLS},
}

TOOL_FUNCTIONS: Dict[str, CodeXCallable] = {
    # R4 engineering perception
    "repo_map": perception.repo_map,
    "file_tree_scan": perception.file_tree_scan,
    "symbol_index": perception.symbol_index,
    "dependency_graph": perception.dependency_graph,
    "call_graph": perception.call_graph,
    "test_map": perception.test_map,
    "entrypoint_detector": perception.entrypoint_detector,
    "config_detector": perception.config_detector,
    "stack_detector": perception.stack_detector,
    "code_owner_detector": perception.code_owner_detector,
    # R5 context armor
    "generate_linyuanzhe_md": context_armor.generate_linyuanzhe_md,
    "project_rules_reader": context_armor.project_rules_reader,
    "context_compactor": context_armor.context_compactor,
    "log_compactor": context_armor.log_compactor,
    "task_digest": context_armor.task_digest,
    "handoff_digest": context_armor.handoff_digest,
    "changed_files_index": context_armor.changed_files_index,
    "decision_memory": context_armor.decision_memory,
    # R6 localization
    "issue_to_file_localizer": localization.issue_to_file_localizer,
    "file_to_symbol_localizer": localization.file_to_symbol_localizer,
    "symbol_to_line_localizer": localization.symbol_to_line_localizer,
    "semantic_code_search": localization.semantic_code_search,
    "graph_code_search": localization.graph_code_search,
    "test_failure_trace_mapper": localization.test_failure_trace_mapper,
    "affected_area_detector": localization.affected_area_detector,
    # R7 patch production
    "patch_plan_generator": patching.patch_plan_generator,
    "edit_unit_planner": patching.edit_unit_planner,
    "conflict_detector": patching.conflict_detector,
    "unified_diff_generator": patching.unified_diff_generator,
    "workspace_patch_applier": patching.workspace_patch_applier,
    "before_after_hash": patching.before_after_hash,
    "patch_manifest": patching.patch_manifest,
    # R8 validation
    "environment_probe": validation.environment_probe,
    "command_capability_probe": validation.command_capability_probe,
    "safe_command_runner": validation.safe_command_runner,
    "python_quality_runner": validation.python_quality_runner,
    "pytest_runner": validation.pytest_runner,
    "npm_test_runner": validation.npm_test_runner,
    "build_runner": validation.build_runner,
    "lint_runner": validation.lint_runner,
    "typecheck_runner": validation.typecheck_runner,
    "static_analyzer": validation.static_analyzer,
    "fallback_test_strategy": validation.fallback_test_strategy,
    # R9 failure attribution / repair loop
    "failure_attribution_analyzer": failure_repair.failure_attribution_analyzer,
    "syntax_error_analyzer": failure_repair.syntax_error_analyzer,
    "import_error_analyzer": failure_repair.import_error_analyzer,
    "dependency_error_analyzer": failure_repair.dependency_error_analyzer,
    "test_failure_analyzer": failure_repair.test_failure_analyzer,
    "flaky_test_detector": failure_repair.flaky_test_detector,
    "repair_loop_planner": failure_repair.repair_loop_planner,
    "next_patch_generator": failure_repair.next_patch_generator,
    # R10 worktree / rollback / packaging
    "workspace_snapshot": worktree.workspace_snapshot,
    "git_worktree_mode": worktree.git_worktree_mode,
    "rollback_plan": worktree.rollback_plan,
    "restore_checkpoint": worktree.restore_checkpoint,
    "delivery_candidate_packager": worktree.delivery_candidate_packager,
    "zip_delivery_packager": worktree.zip_delivery_packager,
    # R11 subagents
    "code_research_subagent": subagents.code_research_subagent,
    "test_design_subagent": subagents.test_design_subagent,
    "review_subagent": subagents.review_subagent,
    "security_review_subagent": subagents.security_review_subagent,
    "refactor_review_subagent": subagents.refactor_review_subagent,
    "migration_subagent": subagents.migration_subagent,
    "frontend_visual_subagent": subagents.frontend_visual_subagent,
    "subagent_pack_manifest": subagents.subagent_pack_manifest,
    # R12 package orchestration
    "build_toolpackage": orchestrator.build_toolpackage,
    "build_hooks_package": orchestrator.build_hooks_package,
    "build_subagents_pack": orchestrator.build_subagents_pack,
    "build_skill_workflow": orchestrator.build_skill_workflow,
    "build_abilitypackage": orchestrator.build_abilitypackage,
    "build_candidate_registry_manifest": orchestrator.build_candidate_registry_manifest,
    "build_readonly_analysis_demotion": orchestrator.build_readonly_analysis_demotion,
    "build_full_bundle": orchestrator.build_full_bundle,
    "validate_bundle": orchestrator.validate_bundle,
    # R13C LLM usage skill and import audit
    "code_x_skill_guide": skill_runtime.code_x_skill_guide,
    "code_x_world_class_readiness_check": skill_runtime.code_x_world_class_readiness_check,
    "code_x_v1_import_audit": skill_runtime.code_x_v1_import_audit,
}

TOOL_DESCRIPTIONS: Dict[str, str] = {
    "repo_map": "Code-X 工程感知：生成压缩仓库地图。",
    "file_tree_scan": "Code-X 工程感知：扫描文件树。",
    "symbol_index": "Code-X 工程感知：建立符号索引。",
    "dependency_graph": "Code-X 工程感知：建立依赖图。",
    "call_graph": "Code-X 工程感知：建立调用图。",
    "test_map": "Code-X 工程感知：映射测试文件。",
    "entrypoint_detector": "Code-X 工程感知：检测入口文件。",
    "config_detector": "Code-X 工程感知：检测配置文件。",
    "stack_detector": "Code-X 工程感知：检测技术栈。",
    "code_owner_detector": "Code-X 工程感知：检测代码归属/规则线索。",
    "workspace_patch_applier": "Code-X Patch：在 workspace 内应用 edit_units，并输出 before/after evidence。",
    "safe_command_runner": "Code-X 验证：运行 allowlist/受控本地命令。",
    "python_quality_runner": "Code-X 验证：运行 Python compileall/基础质量检查。",
    "pytest_runner": "Code-X 验证：运行 pytest。",
    "workspace_snapshot": "Code-X 回滚：创建 workspace 快照。",
    "restore_checkpoint": "Code-X 回滚：从快照恢复 workspace。",
    "delivery_candidate_packager": "Code-X 交付：生成候选交付目录。",
    "zip_delivery_packager": "Code-X 交付：生成 ZIP 交付包。",
    "code_x_skill_guide": "Code-X Skill：向 LLM 暴露代码执行外骨骼使用方法与链路 recipes。",
    "code_x_world_class_readiness_check": "Code-X 审计：确认世界级代码代理能力结构与实证缺口。",
    "code_x_v1_import_audit": "Code-X 审计：报告 v1 代码链语义导入与其他 v1 工具未导入边界。",
}


def register_code_x_runtime_tools(registry: RuntimeToolRegistry) -> None:
    """Register Code-X tools into the provided v2 RuntimeToolRegistry."""
    for name in sorted(TOOL_FUNCTIONS):
        risk = CODE_X_TOOL_RISK.get(name, "A2")
        registry.register(
            ToolDescriptor(name, TOOL_DESCRIPTIONS.get(name, f"Code-X 原生工具：{name}"), risk),
            build_code_x_adapter(name, TOOL_FUNCTIONS[name]),
        )
    registry.register(ToolDescriptor("code_x_runtime_status", "Code-X Runtime 注册状态与可用工具清单。", "A2"), code_x_runtime_status_adapter)
    registry.register(ToolDescriptor("code_x_smoke_workflow", "Code-X 最小可用链路 smoke：repo_map→环境探测→静态检查→fallback/handoff。", "A3"), code_x_smoke_workflow_adapter)
    registry.register(ToolDescriptor("code_x_package_workflow", "Code-X 一步交付：delivery_candidate_packager→zip_delivery_packager。", "A3"), code_x_package_workflow_adapter)


def build_code_x_adapter(tool_name: str, func: CodeXCallable):
    def adapter(invocation: ToolInvocation, context: TurnContext) -> ToolResult:
        try:
            args = _prepare_args(func, invocation.arguments, context)
            payload = func(**args)
            data = _to_dict(payload)
            status = _status_from_payload(data)
            return ToolResult(
                step_id=invocation.step_id,
                tool_name=invocation.tool_name,
                status=status,
                output_summary=_summary_from_payload(data, tool_name),
                data=data,
                artifacts=_artifacts_from_payload(data, context.workspace),
                error_code="" if status is ToolResultStatus.OK else _error_code_from_payload(data),
            )
        except Exception as exc:  # defensive adapter boundary; exception still audited by Runtime
            return ToolResult(
                step_id=invocation.step_id,
                tool_name=invocation.tool_name,
                status=ToolResultStatus.FAILED,
                output_summary=f"Code-X 工具执行失败：{type(exc).__name__}: {exc}",
                error_code="code_x_adapter_error",
                data={"exception_type": type(exc).__name__, "message": str(exc), "tool_name": tool_name},
            )
    return adapter


def _prepare_args(func: CodeXCallable, raw_args: Mapping[str, Any], context: TurnContext) -> Dict[str, Any]:
    args = dict(raw_args or {})
    sig = inspect.signature(func)
    params = sig.parameters
    # Normalize workspace aliases.
    if "repo_root" in params and "repo_root" not in args:
        args["repo_root"] = str(context.workspace)
    if "workspace_root" in params and "workspace_root" not in args:
        args["workspace_root"] = str(context.workspace)
    if "root" in params and "root" not in args:
        args["root"] = str(context.workspace)
    # Helpful defaults for user-message-driven localization.
    if "issue_text" in params and "issue_text" not in args:
        args["issue_text"] = context.user_message
    if "query" in params and "query" not in args and func.__name__ in {"semantic_code_search", "code_research_subagent"}:
        args["query"] = context.user_message
    if "task_state" in params and "task_state" not in args:
        args["task_state"] = {"task_id": context.turn_id, "user_message": context.user_message, "status": "runtime_tool_call"}
    if "task_digest_markdown" in params and "task_digest_markdown" not in args:
        args["task_digest_markdown"] = f"# Code-X Handoff\n\n- turn_id: {context.turn_id}\n- user_message: {context.user_message}\n"
    if "memory_path" in params and "memory_path" not in args:
        args["memory_path"] = str(Path(context.workspace) / ".codex" / "decision_memory.jsonl")
    if "action" in params and "action" not in args and func.__name__ == "decision_memory":
        args["action"] = "read"
    if "sections" in params and "sections" not in args and func.__name__ == "context_compactor":
        args["sections"] = context.user_message
    if "log_text" in params and "log_text" not in args:
        args["log_text"] = context.user_message
    if "issue" in params and "issue" not in args and func.__name__ == "patch_plan_generator":
        args["issue"] = context.user_message
    if "failure_analysis" in params and "failure_analysis" not in args:
        args["failure_analysis"] = {"primary_category": "unknown_failure", "source": "runtime_default"}
    if "bundle" in params and "bundle" not in args and func.__name__ == "validate_bundle":
        args["bundle"] = orchestrator.build_full_bundle()
    # Normalize root-like path arguments to the active Runtime workspace.
    for key in ("repo_root", "workspace_root", "root", "package_root", "output_zip", "worktree_dir", "snapshot_manifest_path"):
        if key in args and isinstance(args[key], str):
            value = args[key].strip()
            if value in {"", "."}:
                args[key] = str(context.workspace)
            else:
                candidate = Path(value).expanduser()
                if not candidate.is_absolute() and key in {"repo_root", "workspace_root", "root", "package_root", "output_zip", "worktree_dir", "snapshot_manifest_path"}:
                    args[key] = str((context.workspace / candidate).resolve())
    # Filter unknown keys to keep adapter stable across old Planner output.
    return {k: v for k, v in args.items() if k in params}


def _to_dict(payload: Any) -> Dict[str, Any]:
    if hasattr(payload, "to_dict") and callable(payload.to_dict):
        return dict(payload.to_dict())
    if isinstance(payload, Mapping):
        return dict(payload)
    return {"value": payload, "status": "ok", "summary": str(payload)[:500]}


def _status_from_payload(data: Mapping[str, Any]) -> ToolResultStatus:
    raw = str(data.get("status") or data.get("result", {}).get("status") or "ok").lower()
    if raw in {"ok", "pass", "passed", "success", "degraded_pass", "warning"}:
        return ToolResultStatus.OK
    if raw in {"blocked", "a5_blocked", "permission_blocked"}:
        return ToolResultStatus.BLOCKED
    if raw in {"timeout", "timed_out"}:
        return ToolResultStatus.TIMEOUT
    if raw in {"skipped"}:
        return ToolResultStatus.SKIPPED
    return ToolResultStatus.FAILED


def _summary_from_payload(data: Mapping[str, Any], tool_name: str) -> str:
    for key in ("summary", "output_summary"):
        if data.get(key):
            return str(data[key])[:12000]
    result = data.get("result")
    if isinstance(result, Mapping):
        for key in ("summary", "message"):
            if result.get(key):
                return str(result[key])[:12000]
    return f"Code-X 工具 {tool_name} 已返回结构化结果。"


def _artifacts_from_payload(data: Mapping[str, Any], workspace: Path) -> list[str]:
    artifacts: list[str] = []
    raw = data.get("artifacts")
    if isinstance(raw, list):
        artifacts.extend(str(x) for x in raw[:20])
    elif isinstance(raw, Mapping):
        for key, value in list(raw.items())[:20]:
            if isinstance(value, (str, int, float)):
                artifacts.append(f"{key}={value}")
    result = data.get("result")
    if isinstance(result, Mapping):
        for key in ("manifest_path", "package_dir", "output_zip", "snapshot_manifest_path", "path"):
            if result.get(key):
                artifacts.append(str(result[key]))
    return artifacts[:50]


def _error_code_from_payload(data: Mapping[str, Any]) -> str:
    if data.get("error_code"):
        return str(data["error_code"])
    result = data.get("result")
    if isinstance(result, Mapping) and result.get("error_code"):
        return str(result["error_code"])
    raw = str(data.get("status") or "failed").lower()
    return f"code_x_{raw}"


def code_x_runtime_status_adapter(invocation: ToolInvocation, context: TurnContext) -> ToolResult:
    by_risk = {"A1": [], "A2": [], "A3": []}
    for name, risk in sorted(CODE_X_TOOL_RISK.items()):
        by_risk.setdefault(risk, []).append(name)
    data = {
        "status": "ok",
        "summary": "Code-X Runtime tools are registered and callable through RuntimeToolRegistry.",
        "tool_count": len(TOOL_FUNCTIONS) + 3,
        "by_risk": by_risk,
        "authority_model": "LLM主脑；Code-X为执行外骨骼；Planner只建议；子代理只回传证据。",
        "workspace": str(context.workspace),
        "usage_skill": {"tool": "code_x_skill_guide", "command": "code-x skill"},
        "readiness_check": {"tool": "code_x_world_class_readiness_check", "command": "code-x readiness"},
        "v1_import_audit": {"tool": "code_x_v1_import_audit", "command": "code-x v1-audit"},
        "next_action_hint": {"next_tool": "code_x_skill_guide", "reason": "Load Code-X workflow skill before selecting a repair chain."},
    }
    return ToolResult(invocation.step_id, invocation.tool_name, ToolResultStatus.OK, data["summary"], data=data)


def code_x_smoke_workflow_adapter(invocation: ToolInvocation, context: TurnContext) -> ToolResult:
    target = str(invocation.arguments.get("path") or invocation.arguments.get("target") or ".")
    workspace = Path(context.workspace)
    root = (workspace / target).resolve() if target != "." else workspace.resolve()
    try:
        root.relative_to(workspace.resolve())
    except ValueError:
        return ToolResult(invocation.step_id, invocation.tool_name, ToolResultStatus.BLOCKED, "Code-X smoke 目标越出 workspace。", error_code="workspace_violation")
    steps: list[dict[str, Any]] = []
    for name, func, kwargs in [
        ("repo_map", perception.repo_map, {"workspace_root": str(root), "task_id": context.turn_id}),
        ("environment_probe", validation.environment_probe, {"repo_root": str(root)}),
        ("static_analyzer", validation.static_analyzer, {"repo_root": str(root)}),
        ("fallback_test_strategy", validation.fallback_test_strategy, {"repo_root": str(root)}),
    ]:
        try:
            payload = _to_dict(func(**kwargs))
            steps.append({"tool_name": name, "status": str(payload.get("status") or "ok"), "summary": _summary_from_payload(payload, name), "data": payload})
        except Exception as exc:
            steps.append({"tool_name": name, "status": "failed", "summary": f"{type(exc).__name__}: {exc}"})
    ok = all(item["status"] in {"ok", "pass", "passed", "success", "degraded_pass", "warning"} for item in steps)
    data = {
        "status": "ok" if ok else "failed",
        "summary": "Code-X smoke workflow completed." if ok else "Code-X smoke workflow found failures.",
        "steps": steps,
        "next_action_hint": {"next_tool": "issue_to_file_localizer" if ok else "failure_attribution_analyzer", "reason": "Continue Code-X chain based on smoke result."},
    }
    return ToolResult(
        invocation.step_id,
        invocation.tool_name,
        ToolResultStatus.OK if ok else ToolResultStatus.FAILED,
        data["summary"],
        data=data,
        error_code="" if ok else "code_x_smoke_failed",
    )


def code_x_package_workflow_adapter(invocation: ToolInvocation, context: TurnContext) -> ToolResult:
    include_paths = invocation.arguments.get("include_paths") or invocation.arguments.get("paths") or ["."]
    if isinstance(include_paths, str):
        include_paths = [include_paths]
    output_zip = str(invocation.arguments.get("output_zip") or "dist/code_x_delivery.zip")
    try:
        staged = worktree.delivery_candidate_packager(str(context.workspace), include_paths=include_paths)
        staged_data = _to_dict(staged)
        package_root = staged_data.get("result", {}).get("package_root") if isinstance(staged_data.get("result"), Mapping) else None
        if not package_root:
            return ToolResult(invocation.step_id, invocation.tool_name, ToolResultStatus.FAILED, "交付候选目录生成失败，缺少 package_root。", error_code="code_x_package_stage_failed", data=staged_data)
        out_path = Path(output_zip)
        if not out_path.is_absolute():
            out_path = (Path(context.workspace) / out_path).resolve()
        zipped = worktree.zip_delivery_packager(package_root, output_zip=str(out_path))
        zip_data = _to_dict(zipped)
        status = _status_from_payload(zip_data)
        data = {"status": "ok" if status is ToolResultStatus.OK else "failed", "summary": "Code-X package workflow completed.", "stage": staged_data, "zip": zip_data}
        return ToolResult(invocation.step_id, invocation.tool_name, status, data["summary"], data=data, artifacts=_artifacts_from_payload(zip_data, context.workspace), error_code="" if status is ToolResultStatus.OK else _error_code_from_payload(zip_data))
    except Exception as exc:
        return ToolResult(invocation.step_id, invocation.tool_name, ToolResultStatus.FAILED, f"Code-X package workflow failed: {type(exc).__name__}: {exc}", error_code="code_x_package_workflow_error")
