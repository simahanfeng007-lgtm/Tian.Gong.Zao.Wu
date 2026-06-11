"""L6.31 结构化计划 schema 与安全归一化。"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import PurePosixPath, PureWindowsPath
from typing import Any

from .tool_invocation import ToolInvocation

PLANNABLE_TOOLS: dict[str, frozenset[str]] = {
    "scan_project": frozenset({"path", "max_depth", "max_files"}),
    "diagnose_project": frozenset({"path", "max_depth", "max_files"}),
    "list_dir": frozenset({"path"}),
    "read_file": frozenset({"path"}),
    "file_sha256": frozenset({"path"}),
    "document_parse": frozenset({"path", "max_chars"}),
    "document_query": frozenset({"query", "document_id", "path", "top_k", "max_chars"}),
    "document_export": frozenset({"document_id", "path", "target", "format", "query", "top_k", "max_chars", "output_path", "output_format"}),
    "document_rewrite_plan": frozenset({"instruction", "document_id", "path", "output_path", "output_format", "query", "target", "format", "max_chars"}),
    "document_apply_rewrite": frozenset({"instruction", "document_id", "path", "source", "target", "output_path", "content", "new_content", "old_text", "new_text", "replacements", "operation", "mode", "overwrite", "dry_run", "allow_no_match", "max_chars"}),
    "document_rollback": frozenset({"operation_id", "manifest", "manifest_path", "path", "force"}),
    "write_workspace_file": frozenset({"path", "content"}),
    "return_code": frozenset({"content", "language", "notes", "task"}),
    "return_analysis": frozenset({"content", "notes", "task"}),
    "run_python_quality_check": frozenset({"command", "target"}),
    "create_zip_package": frozenset({"source", "target"}),
    "synthesize_experience_candidates": frozenset({"notes", "manual_notes", "max_candidates"}),
    "queue_skill_candidates": frozenset({"notes", "manual_notes", "max_items"}),
    "queue_tool_production_requests": frozenset({"notes", "manual_notes", "max_items"}),
    "build_execution_exoskeleton": frozenset({"notes", "manual_notes", "max_items"}),
    "build_shell_system_mount": frozenset({"notes", "manual_notes"}),
    "build_project_repair_plan": frozenset({"path", "max_depth", "max_files", "notes", "manual_notes", "max_targets", "max_items"}),
    "build_delivery_standardization": frozenset({"path", "notes", "manual_notes"}),
    "build_provider_adaptation": frozenset({"path", "notes", "manual_notes"}),
    "build_learning_convergence": frozenset({"notes", "manual_notes", "max_items"}),
    "build_recovery_coordination": frozenset({"notes", "manual_notes", "max_items", "step_budget"}),
    "build_governance_execution": frozenset({"notes", "manual_notes", "max_items"}),
    "build_planner_context": frozenset({"notes", "manual_notes", "max_items", "task_id", "run_id", "task"}),
    "build_l6_38_provider_integration": frozenset({"notes", "manual_notes", "call_mode", "requested_call_mode"}),
    "build_l6_38_budget_snapshot": frozenset({"notes", "manual_notes", "max_steps", "planned_steps", "step_budget"}),
    "build_l6_38_skill_integration": frozenset({"notes", "manual_notes", "max_items"}),
    "build_l6_38_handoff_integration": frozenset({"notes", "manual_notes", "parent_chain_id", "max_subtasks"}),
    "build_l6_38_p0_integration": frozenset({"notes", "manual_notes"}),
    "build_l6_39_memory_integration": frozenset({"notes", "manual_notes", "max_items", "max_records"}),
    "build_l6_39_audit_integration": frozenset({"notes", "manual_notes", "max_items", "max_events"}),
    "build_l6_39_recovery_integration": frozenset({"notes", "manual_notes", "max_items"}),
    "build_l6_39_quality_gate_integration": frozenset({"notes", "manual_notes"}),
    "build_l6_39_p0_integration": frozenset({"notes", "manual_notes"}),
    "learning_asset_contract_guide": frozenset({"notes", "manual_notes"}),
    "learning_asset_contract_normalize": frozenset({"notes", "manual_notes", "max_items"}),
    "learning_asset_contract_validate": frozenset({"contract", "payload", "notes", "manual_notes"}),
    "learning_asset_sandbox_guide": frozenset({"notes", "manual_notes"}),
    "learning_asset_sandbox_align": frozenset({"notes", "manual_notes", "strict"}),
    "learning_asset_sandbox_validate": frozenset({"notes", "manual_notes"}),
    "learning_asset_candidate_sandbox_guide": frozenset({"notes", "manual_notes"}),
    "learning_asset_candidate_sandbox_build": frozenset({"notes", "manual_notes", "max_items"}),
    "learning_asset_candidate_sandbox_validate": frozenset({"notes", "manual_notes"}),
    "learning_asset_candidate_sandbox_review": frozenset({"notes", "manual_notes"}),
}

REQUIRED_FIELDS: dict[str, frozenset[str]] = {
    "scan_project": frozenset(),
    "diagnose_project": frozenset(),
    "list_dir": frozenset({"path"}),
    "read_file": frozenset({"path"}),
    "file_sha256": frozenset({"path"}),
    "document_parse": frozenset({"path"}),
    "document_query": frozenset(),
    "document_export": frozenset(),
    "document_rewrite_plan": frozenset(),
    "document_apply_rewrite": frozenset(),
    "document_rollback": frozenset(),
    "write_workspace_file": frozenset({"path", "content"}),
    "return_code": frozenset({"content"}),
    "return_analysis": frozenset({"content"}),
    "run_python_quality_check": frozenset({"command"}),
    "create_zip_package": frozenset({"source", "target"}),
    "synthesize_experience_candidates": frozenset(),
    "queue_skill_candidates": frozenset(),
    "queue_tool_production_requests": frozenset(),
    "build_execution_exoskeleton": frozenset(),
    "build_shell_system_mount": frozenset(),
    "build_project_repair_plan": frozenset(),
    "build_delivery_standardization": frozenset(),
    "build_provider_adaptation": frozenset(),
    "build_learning_convergence": frozenset(),
    "build_recovery_coordination": frozenset(),
    "build_governance_execution": frozenset(),
    "build_planner_context": frozenset(),
    "build_l6_38_provider_integration": frozenset(),
    "build_l6_38_budget_snapshot": frozenset(),
    "build_l6_38_skill_integration": frozenset(),
    "build_l6_38_handoff_integration": frozenset(),
    "build_l6_38_p0_integration": frozenset(),
    "build_l6_39_memory_integration": frozenset(),
    "build_l6_39_audit_integration": frozenset(),
    "build_l6_39_recovery_integration": frozenset(),
    "build_l6_39_quality_gate_integration": frozenset(),
    "build_l6_39_p0_integration": frozenset(),
    "learning_asset_contract_guide": frozenset(),
    "learning_asset_contract_normalize": frozenset(),
    "learning_asset_contract_validate": frozenset(),
    "learning_asset_sandbox_guide": frozenset(),
    "learning_asset_sandbox_align": frozenset(),
    "learning_asset_sandbox_validate": frozenset(),
    "learning_asset_candidate_sandbox_guide": frozenset(),
    "learning_asset_candidate_sandbox_build": frozenset(),
    "learning_asset_candidate_sandbox_validate": frozenset(),
    "learning_asset_candidate_sandbox_review": frozenset(),
}

# L6.72.39：执行力优先。模型计划器可以直接规划 Code-X 代码外骨骼工具；
# 未知参数不再在 schema 层制造非 A5 摩擦，真实执行仍由 RuntimeToolRegistry、adapter、
# A5 风险分类、审计与回滚承接。
try:  # keep plan_schema importable even if Code-X pack is absent in a slim build
    from .code_x_runtime_adapters import CODE_X_TOOL_RISK as _CODE_X_TOOL_RISK
except Exception:  # noqa: BLE001
    _CODE_X_TOOL_RISK = {}

_EXECUTION_FIRST_CODEX_ARGS = frozenset({
    "repo_root", "workspace_root", "root", "path", "paths", "file_path", "target_files",
    "changed_files", "include_paths", "source", "target", "output_dir", "output_zip", "package_root",
    "snapshot_id", "snapshot_dir", "snapshot_manifest_path", "worktree_dir", "branch_name",
    "command", "commands", "cwd", "timeout_sec", "timeout_seconds", "max_output_chars",
    "allowed_return_codes", "env_overrides", "test_path", "extra_args", "build_command",
    "lint_command", "typecheck_command", "edit_units", "patch_plan", "proposed_edits", "diff",
    "patch_id", "validation_commands", "status", "query", "issue", "issue_text", "symbol_name",
    "failure_log", "log_text", "command_result", "failure_analysis", "previous_results", "repeated_results",
    "task_type", "current_state", "phase", "task_state", "tool_results", "task_digest_markdown",
    "verification", "next_steps", "sections", "max_chars", "preserve_keywords", "memory_path",
    "action", "record", "limit", "max_files", "max_depth", "depth", "max_cases_per_file",
    "migration_goal", "target_patterns", "localized_targets", "constraints", "dry_run", "overwrite",
    "package_id", "include_manifest_note", "bundle", "project_name", "stack", "command_policy",
    "directory_rules", "notes", "manual_notes", "content", "language", "task", "old_text", "new_text",
    "new_content", "replacements", "operation_id", "manifest", "manifest_path", "force", "mode", "allow_no_match",
})
for _tool_name in sorted(_CODE_X_TOOL_RISK):
    PLANNABLE_TOOLS.setdefault(_tool_name, _EXECUTION_FIRST_CODEX_ARGS)
    REQUIRED_FIELDS.setdefault(_tool_name, frozenset())
PLANNABLE_TOOLS.setdefault("code_x_runtime_status", frozenset({"notes", "manual_notes"}))
PLANNABLE_TOOLS.setdefault("code_x_smoke_workflow", frozenset({"path", "target", "notes", "manual_notes"}))
PLANNABLE_TOOLS.setdefault("code_x_package_workflow", frozenset({"source", "target", "notes", "manual_notes"}))
REQUIRED_FIELDS.setdefault("code_x_runtime_status", frozenset())
REQUIRED_FIELDS.setdefault("code_x_smoke_workflow", frozenset())
REQUIRED_FIELDS.setdefault("code_x_package_workflow", frozenset())

PATH_FIELDS = {"path", "target", "source", "repo_root", "workspace_root", "root", "file_path", "package_root", "output_zip", "output_dir", "worktree_dir", "snapshot_manifest_path", "snapshot_dir", "output_path"}
QUALITY_COMMANDS = {"compileall", "pytest", "python -m compileall", "python -m pytest"}
SENSITIVE_PATH_TERMS = {
    "/etc/passwd",
    "/etc/shadow",
    "/etc/sudoers",
    "windows/system32/config/sam",
    "windows/system32/config/security",
    ".env",
    "id_rsa",
    "id_dsa",
    "id_ecdsa",
    "token",
    "secret",
    "password",
    "credential",
    "credentials",
    "key.pem",
}

# L6.32 P1/P2: 新工具只要遵循安全前缀即可先通过模型计划 schema；
# 是否真实可执行仍由 RuntimeToolRegistry / ExecutionSpine 决定。
WILDCARD_ALLOWED_PREFIXES = ("diagnose_", "scan_", "read_", "list_", "synthesize_")
WILDCARD_ARGUMENTS = frozenset({
    "path",
    "max_depth",
    "max_files",
    "notes",
    "manual_notes",
    "max_items",
    "max_candidates",
    "task",
    "content",
})

PLAN_SEQUENCE_KEYS = (
    "output",
    "steps",
    "step_list",
    "plan",
    "plans",
    "actions",
    "action_plan",
    "tool_calls",
    "tool_call_plan",
    "calls",
    "tool_plan",
    "execution_plan",
    "execution_steps",
    "workflow",
    "operations",
    "tasks",
    "subtasks",
    "items",
    "步骤",
    "计划",
    "动作",
    "工具调用",
)

STEP_TOOL_KEYS = (
    "tool_name",
    "tool",
    "toolName",
    "tool_id",
    "toolId",
    "name",
    "action",
    "operation",
    "kind",
    "function",
    "function_call",
    "tool_call",
    "工具",
    "工具名",
    "工具名称",
    "动作",
    "操作",
)

STEP_ARGUMENT_KEYS = (
    "arguments",
    "args",
    "input",
    "inputs",
    "params",
    "parameters",
    "payload",
    "with",
    "tool_input",
    "tool_args",
    "input_params",
    "function_arguments",
    "arguments_json",
    "参数",
    "输入",
)

STEP_METADATA_KEYS = {
    "id",
    "step",
    "step_id",
    "title",
    "description",
    "summary",
    "reason",
    "rationale",
    "goal",
    "depends_on",
    "risk",
    "risk_level",
    "notes",
    "comment",
    "comments",
    "expected_output",
    "output",
    "type",
    "order",
    "index",
    "phase",
    "status",
    "confidence",
}

ARGUMENT_ALIASES: dict[str, tuple[str, ...]] = {
    "path": ("path", "file", "filepath", "file_path", "target_file", "filename", "dir", "directory", "folder", "target", "目标文件", "文件", "路径", "目录"),
    "repo_root": ("repo_root", "workspace_root", "root", "project_root", "项目根目录", "仓库根目录"),
    "workspace_root": ("workspace_root", "repo_root", "root", "project_root", "工作区", "项目根目录"),
    "root": ("root", "repo_root", "workspace_root", "project_root", "根目录"),
    "file_path": ("file_path", "filepath", "file", "path", "target_file", "目标文件"),
    "paths": ("paths", "files", "file_paths", "文件列表"),
    "changed_files": ("changed_files", "files", "paths", "改动文件"),
    "target_files": ("target_files", "targets", "files", "paths", "目标文件列表"),
    "source": ("source", "src", "source_path", "input_path", "folder", "directory", "path", "from", "来源", "源路径"),
    "target": ("target", "dest", "destination", "output", "output_path", "zip_path", "to", "目标", "目标路径", "输出"),
    "content": ("content", "text", "body", "data", "code", "answer", "analysis", "result", "内容", "正文", "代码", "分析", "结果"),
    "language": ("language", "lang", "语言"),
    "command": ("command", "quality_command", "check", "test_command", "cmd", "shell", "bash", "powershell", "command_line", "script", "命令", "检查命令"),
    "commands": ("commands", "command_list", "cmds", "命令列表"),
    "cwd": ("cwd", "working_directory", "workdir", "运行目录"),
    "timeout_sec": ("timeout_sec", "timeout", "timeout_seconds", "超时"),
    "edit_units": ("edit_units", "edits", "patches", "changes", "修改单元"),
    "patch_plan": ("patch_plan", "plan", "补丁计划"),
    "proposed_edits": ("proposed_edits", "edits", "建议修改"),
    "diff": ("diff", "unified_diff", "patch", "补丁"),
    "query": ("query", "search", "keyword", "问题", "查询", "关键词"),
    "document_id": ("document_id", "doc_id", "document", "doc", "文档id", "文档ID"),
    "instruction": ("instruction", "query", "task", "requirement", "要求", "修改要求", "任务"),
    "old_text": ("old_text", "old", "find", "from", "原文", "查找", "替换前"),
    "new_text": ("new_text", "new", "replace_with", "to", "替换为", "改成", "替换后"),
    "new_content": ("new_content", "full_content", "正文新内容", "新正文"),
    "replacements": ("replacements", "replace", "edits", "修改项", "替换项"),
    "operation": ("operation", "op", "动作", "操作"),
    "mode": ("mode", "写入模式", "模式"),
    "overwrite": ("overwrite", "cover", "覆盖"),
    "dry_run": ("dry_run", "dryrun", "预演"),
    "allow_no_match": ("allow_no_match", "allowNoMatch", "允许无命中"),
    "operation_id": ("operation_id", "id", "op_id", "操作ID", "写回ID"),
    "manifest": ("manifest", "manifest_path", "清单", "回滚清单"),
    "manifest_path": ("manifest_path", "manifest", "path", "清单路径", "回滚清单路径"),
    "force": ("force", "强制", "确认覆盖"),
    "output_path": ("output_path", "target", "dest", "destination", "输出路径", "目标路径"),
    "output_format": ("output_format", "format", "fmt", "格式"),
    "top_k": ("top_k", "limit", "max_items", "数量"),
    "format": ("format", "fmt", "output_format", "格式"),
    "issue": ("issue", "problem", "bug", "需求", "问题"),
    "issue_text": ("issue_text", "issue", "problem", "错误信息"),
    "log_text": ("log_text", "log", "stderr", "stdout", "日志"),
    "failure_analysis": ("failure_analysis", "analysis", "失败分析"),
    "max_depth": ("max_depth", "depth"),
    "max_files": ("max_files", "file_limit", "limit"),
    "max_chars": ("max_chars", "max_characters", "limit_chars", "字符上限"),
    "max_items": ("max_items", "limit", "count"),
    "max_candidates": ("max_candidates", "limit", "count"),
    "max_targets": ("max_targets", "target_limit", "limit"),
    "step_budget": ("step_budget", "budget", "max_steps"),
    "notes": ("notes", "note", "summary", "description", "rationale", "备注", "说明"),
    "manual_notes": ("manual_notes", "manual_note"),
    "task_id": ("task_id", "taskId"),
    "run_id": ("run_id", "runId"),
    "task": ("task", "goal", "objective", "任务", "目标"),
    "call_mode": ("call_mode", "requested_call_mode", "mode", "调用模式"),
    "requested_call_mode": ("requested_call_mode", "call_mode", "mode", "调用模式"),
    "planned_steps": ("planned_steps", "steps", "计划步数"),
    "parent_chain_id": ("parent_chain_id", "parent", "parent_id", "父链"),
    "max_subtasks": ("max_subtasks", "subtasks", "子任务数"),
    "max_records": ("max_records", "records", "record_limit", "记忆条数"),
    "max_events": ("max_events", "events", "event_limit", "审计条数"),
}

TOOL_NAME_ALIASES = {
    "read": "read_file",
    "readfile": "read_file",
    "read_file": "read_file",
    "读取文件": "read_file",
    "读文件": "read_file",
    "document_parse": "document_parse",
    "documentparse": "document_parse",
    "parse_document": "document_parse",
    "doc_parse": "document_parse",
    "文档解析": "document_parse",
    "解析文档": "document_parse",
    "读取文档": "document_parse",
    "总结文档": "document_parse",
    "document_query": "document_query",
    "documentquery": "document_query",
    "doc_query": "document_query",
    "query_document": "document_query",
    "文档追问": "document_query",
    "文档查询": "document_query",
    "document_export": "document_export",
    "documentexport": "document_export",
    "doc_export": "document_export",
    "export_document": "document_export",
    "导出文档": "document_export",
    "文档导出": "document_export",
    "document_rewrite_plan": "document_rewrite_plan",
    "documentrewriteplan": "document_rewrite_plan",
    "document_rewrite": "document_rewrite_plan",
    "document_edit_plan": "document_rewrite_plan",
    "文档修改计划": "document_rewrite_plan",
    "文档改写计划": "document_rewrite_plan",
    "document_apply_rewrite": "document_apply_rewrite",
    "documentapplyrewrite": "document_apply_rewrite",
    "document_writeback": "document_apply_rewrite",
    "document_write_back": "document_apply_rewrite",
    "apply_document_rewrite": "document_apply_rewrite",
    "apply_rewrite": "document_apply_rewrite",
    "应用文档修改": "document_apply_rewrite",
    "文档写回": "document_apply_rewrite",
    "写回文档": "document_apply_rewrite",
    "document_rollback": "document_rollback",
    "documentrollback": "document_rollback",
    "rollback_document": "document_rollback",
    "文档回滚": "document_rollback",
    "回滚文档": "document_rollback",
    "list": "list_dir",
    "ls": "list_dir",
    "listdir": "list_dir",
    "list_dir": "list_dir",
    "列目录": "list_dir",
    "扫描目录": "scan_project",
    "scan": "scan_project",
    "scan_project": "scan_project",
    "诊断项目": "diagnose_project",
    "diagnose": "diagnose_project",
    "diagnose_project": "diagnose_project",
    "write": "write_workspace_file",
    "write_file": "write_workspace_file",
    "writeworkspacefile": "write_workspace_file",
    "write_workspace_file": "write_workspace_file",
    "写文件": "write_workspace_file",
    "return_code": "return_code",
    "code": "return_code",
    "output_code": "return_code",
    "代码": "return_code",
    "返回代码": "return_code",
    "输出代码": "return_code",
    "return_analysis": "return_analysis",
    "analysis": "return_analysis",
    "analyze": "return_analysis",
    "分析": "return_analysis",
    "返回分析": "return_analysis",
    "输出分析": "return_analysis",
    "quality_check": "run_python_quality_check",
    "python_quality_check": "run_python_quality_check",
    "run_python_quality_check": "run_python_quality_check",
    "run_python": "run_python_quality_check",
    "quality": "run_python_quality_check",
    "质量检查": "run_python_quality_check",
    "运行测试": "run_python_quality_check",
    "compileall": "run_python_quality_check",
    "pytest": "run_python_quality_check",
    "zip": "create_zip_package",
    "package": "create_zip_package",
    "create_zip": "create_zip_package",
    "create_zip_package": "create_zip_package",
    "打包": "create_zip_package",
    "build_planner_context": "build_planner_context",
    "planner_context": "build_planner_context",
    "build_governance_execution": "build_governance_execution",
    "governance_execution": "build_governance_execution",
    "build_recovery_coordination": "build_recovery_coordination",
    "recovery_coordination": "build_recovery_coordination",
    "build_learning_convergence": "build_learning_convergence",
    "learning_convergence": "build_learning_convergence",
    "build_provider_adaptation": "build_provider_adaptation",
    "provider_adaptation": "build_provider_adaptation",
    "build_delivery_standardization": "build_delivery_standardization",
    "delivery_standardization": "build_delivery_standardization",
    "build_project_repair_plan": "build_project_repair_plan",
    "project_repair_plan": "build_project_repair_plan",
    "build_shell_system_mount": "build_shell_system_mount",
    "shell_system_mount": "build_shell_system_mount",
    "build_execution_exoskeleton": "build_execution_exoskeleton",
    "execution_exoskeleton": "build_execution_exoskeleton",
    "synthesize_experience_candidates": "synthesize_experience_candidates",
    "queue_skill_candidates": "queue_skill_candidates",
    "queue_tool_production_requests": "queue_tool_production_requests",
    "build_l6_38_provider_integration": "build_l6_38_provider_integration",
    "l6_38_provider": "build_l6_38_provider_integration",
    "build_l6_38_budget_snapshot": "build_l6_38_budget_snapshot",
    "l6_38_budget": "build_l6_38_budget_snapshot",
    "build_l6_38_skill_integration": "build_l6_38_skill_integration",
    "l6_38_skill": "build_l6_38_skill_integration",
    "build_l6_38_handoff_integration": "build_l6_38_handoff_integration",
    "l6_38_handoff": "build_l6_38_handoff_integration",
    "build_l6_38_p0_integration": "build_l6_38_p0_integration",
    "l6_38_p0": "build_l6_38_p0_integration",
    "build_l6_39_memory_integration": "build_l6_39_memory_integration",
    "l6_39_memory": "build_l6_39_memory_integration",
    "build_l6_39_audit_integration": "build_l6_39_audit_integration",
    "l6_39_audit": "build_l6_39_audit_integration",
    "build_l6_39_recovery_integration": "build_l6_39_recovery_integration",
    "l6_39_recovery": "build_l6_39_recovery_integration",
    "build_l6_39_quality_gate_integration": "build_l6_39_quality_gate_integration",
    "l6_39_quality_gate": "build_l6_39_quality_gate_integration",
    "l6_39_qualitygate": "build_l6_39_quality_gate_integration",
    "build_l6_39_p0_integration": "build_l6_39_p0_integration",
    "l6_39_p0": "build_l6_39_p0_integration",
    "shell": "safe_command_runner",
    "cmd": "safe_command_runner",
    "run_command": "safe_command_runner",
    "command": "safe_command_runner",
    "safe_command_runner": "safe_command_runner",
    "safecommandrunner": "safe_command_runner",
    "safecommand_runner": "safe_command_runner",
    "safe_commandrunner": "safe_command_runner",
    "safecommand": "safe_command_runner",
    "safecommandrun": "safe_command_runner",
    "safecommand-runner": "safe_command_runner",
    "safe command runner": "safe_command_runner",
    "safecmdrunner": "safe_command_runner",
    "codex.safe_command_runner": "safe_command_runner",
    "code_x.safe_command_runner": "safe_command_runner",
    "code_x_safe_command_runner": "safe_command_runner",
    "codex_safe_command_runner": "safe_command_runner",
    "执行命令": "safe_command_runner",
    "运行命令": "safe_command_runner",
    "应用补丁": "workspace_patch_applier",
    "写补丁": "workspace_patch_applier",
    "workspace_patch_applier": "workspace_patch_applier",
    "仓库地图": "repo_map",
    "代码搜索": "semantic_code_search",
    "环境探测": "environment_probe",
    "静态分析": "static_analyzer",
    "npm测试": "npm_test_runner",
    "pytest_runner": "pytest_runner",
    "python_quality_runner": "python_quality_runner",
}

DANGEROUS_UNKNOWN_ARGUMENT_KEYS = {
    "api_key",
    "apikey",
    "token",
    "secret",
    "credential",
    "credentials",
    "headers",
}


@dataclass(frozen=True)
class PlanValidationIssue:
    code: str
    message: str
    step_index: int | None = None
    tool_name: str = ""


class PlanValidationError(ValueError):
    def __init__(self, issues: list[PlanValidationIssue]) -> None:
        self.issues = issues
        detail = "; ".join(issue.message for issue in issues) or "计划校验失败。"
        super().__init__(detail)


def planner_schema_prompt() -> str:
    """给模型的最小 schema 说明。不得包含内部路径、API Key 或真实工具实现细节。"""
    return json.dumps(
        {
            "output": {"steps": [{"tool_name": "read_file", "arguments": {"path": "README.md"}, "reason": "optional"}]},
            "allowed_tools": {
                "scan_project": {"path": "relative or absolute directory, default .", "max_depth": "1-12 optional", "max_files": "1-10000 optional"},
                "diagnose_project": {"path": "relative or absolute directory, default .", "max_depth": "1-12 optional", "max_files": "1-10000 optional"},
                "list_dir": {"path": "relative or absolute directory, default ."},
                "read_file": {"path": "relative or absolute text/code file. Do not auto-route to document_parse; use document_parse only when ActivationForm/work intent is document parsing or summarization."},
                "file_sha256": {"path": "relative or absolute workspace file"},
                "document_parse": {"path": "relative or absolute existing document file; use only for explicit document parse/summary/rewrite/export tasks", "max_chars": "optional summary limit"},
                "document_query": {"query": "question about last or specified parsed document", "document_id": "optional", "path": "optional parse-then-query path", "top_k": "1-20 optional"},
                "document_export": {"document_id": "optional", "path": "optional parse-then-export path", "target": "workspace output path", "format": "md|txt|json", "query": "optional focused export query"},
                "document_rewrite_plan": {"instruction": "requested document change", "document_id": "optional", "path": "optional parse-then-plan path", "output_path": "optional target", "output_format": "optional"},
                "document_apply_rewrite": {"instruction": "explicit document edit", "document_id": "optional", "path": "optional source file", "target": "optional output path", "old_text": "text to replace", "new_text": "replacement text", "replacements": "optional list", "overwrite": "false by default", "dry_run": "optional"},
                "document_rollback": {"operation_id": "operation id from document_apply_rewrite", "manifest_path": "optional manifest path", "force": "only if target changed after writeback"},
                "write_workspace_file": {"path": "relative or absolute target file", "content": "text"},
                "return_code": {"content": "code text; audit-only virtual return", "language": "optional language", "task": "optional user task summary"},
                "return_analysis": {"content": "analysis text; audit-only virtual return", "task": "optional user task summary"},
                "run_python_quality_check": {"command": "compileall|pytest", "target": "relative or absolute path, default ."},
                "safe_command_runner": {"command": "local command, non-shell argv preferred", "cwd": "relative or absolute cwd optional", "timeout_sec": "optional"},
                "workspace_patch_applier": {"repo_root": "project root optional", "edit_units": "patch edit units", "dry_run": "false by default"},
                "create_zip_package": {"source": "relative or absolute path", "target": "relative or absolute .zip path"},
                "synthesize_experience_candidates": {"notes": "optional safe summary", "max_candidates": "1-50 optional"},
                "queue_skill_candidates": {"notes": "optional safe summary", "max_items": "1-100 optional"},
                "queue_tool_production_requests": {"notes": "optional safe summary", "max_items": "1-100 optional"},
                "build_execution_exoskeleton": {"notes": "optional safe summary", "max_items": "1-30 optional"},
                "build_shell_system_mount": {"notes": "optional safe summary"},
                "build_project_repair_plan": {"path": "relative directory, default .", "notes": "optional safe summary", "max_targets": "1-40 optional"},
                "build_delivery_standardization": {"path": "relative directory, default .", "notes": "optional safe summary"},
                "build_provider_adaptation": {"path": "relative directory, default .", "notes": "optional safe summary"},
                "build_learning_convergence": {"notes": "optional safe summary", "max_items": "1-50 optional"},
                "build_recovery_coordination": {"notes": "optional safe summary", "max_items": "1-40 optional", "step_budget": "1-200 optional"},
                "build_governance_execution": {"notes": "optional safe summary", "max_items": "1-40 optional"},
                "build_planner_context": {"notes": "optional safe summary", "max_items": "1-60 optional", "task_id": "safe task id optional", "run_id": "safe run id optional", "task": "safe task summary optional"},
                "build_l6_38_provider_integration": {"notes": "optional safe summary", "requested_call_mode": "dry_run|sample_replay optional"},
                "build_l6_38_budget_snapshot": {"notes": "optional safe summary", "max_steps": "1-200 optional", "planned_steps": "0-200 optional"},
                "build_l6_38_skill_integration": {"notes": "optional safe summary", "max_items": "1-20 optional"},
                "build_l6_38_handoff_integration": {"notes": "optional safe summary", "parent_chain_id": "safe ref optional", "max_subtasks": "1-5 optional"},
                "build_l6_38_p0_integration": {"notes": "optional safe summary"},
                "build_l6_39_memory_integration": {"notes": "optional safe summary", "max_items": "1-20 optional"},
                "build_l6_39_audit_integration": {"notes": "optional safe summary", "max_events": "1-80 optional"},
                "build_l6_39_recovery_integration": {"notes": "optional safe summary", "max_items": "1-20 optional"},
                "build_l6_39_quality_gate_integration": {"notes": "optional safe summary"},
                "build_l6_39_p0_integration": {"notes": "optional safe summary"},
                "learning_asset_contract_guide": {"notes": "optional safe summary"},
                "learning_asset_contract_normalize": {"notes": "optional safe summary", "max_items": "1-200 optional"},
                "learning_asset_contract_validate": {"contract": "optional candidate contract payload", "payload": "optional alias"},
                "learning_asset_sandbox_guide": {"notes": "optional safe summary"},
                "learning_asset_sandbox_align": {"notes": "optional safe summary", "strict": "boolean optional"},
                "learning_asset_sandbox_validate": {"notes": "optional safe summary"},
                "learning_asset_candidate_sandbox_guide": {"notes": "optional safe summary"},
                "learning_asset_candidate_sandbox_build": {"notes": "optional safe summary", "max_items": "integer optional"},
                "learning_asset_candidate_sandbox_validate": {"notes": "optional safe summary"},
                "learning_asset_candidate_sandbox_review": {"notes": "optional safe summary"},
            },
            "safe_prefix_tools": list(WILDCARD_ALLOWED_PREFIXES),
            "code_x_tools": sorted(_CODE_X_TOOL_RISK.keys()),
            "execution_first_policy": "A0-A4 default allow; only A5 destructive/credential/privilege operations hard-block.",
            "document_tasks_policy": "Document tools are a work_type=document capability, not a filename-suffix router. Use document_parse only when the LLM ActivationForm/work intent is explicit document parsing, summarization, rewrite, export, or follow-up over a parsed document. Creating files, reading directories, reading source code/text for code/file work, running commands, and writing files must not be hijacked by document_* tools. For explicit document follow-up use document_query; for export use document_export; for edits use document_rewrite_plan/document_apply_rewrite with rollback.",
            "host_file_write_policy": "For Desktop/Downloads/Documents paths, use the desktop bridge relative_path hints; do not invent Users/User/Desktop placeholder paths. Runtime adapters normalize Desktop/桌面/Users/*/Desktop aliases and only report success after physical commit verification.",
            "forbidden": [
                "A5 destructive commands such as rm -rf, format, mkfs, reg delete, destructive del",
                "plaintext API keys, secrets, credentials, private keys",
                "direct provider SDK calls outside Runtime governance",
            ],
        },
        ensure_ascii=False,
        indent=2,
    )


def parse_plan_json(text: str) -> Any:
    """从模型文本中抽取 JSON。支持纯 JSON 或 fenced code block。"""
    raw = (text or "").strip()
    if not raw:
        raise PlanValidationError([PlanValidationIssue("empty_model_plan", "模型计划为空。")])
    candidates = [raw]
    fence_match = re.search(r"```(?:json)?\s*(.*?)```", raw, flags=re.IGNORECASE | re.DOTALL)
    if fence_match:
        candidates.insert(0, fence_match.group(1).strip())
    object_match = re.search(r"(\{.*\}|\[.*\])", raw, flags=re.DOTALL)
    if object_match:
        candidates.append(object_match.group(1).strip())
    last_error = ""
    for candidate in candidates:
        try:
            return json.loads(candidate)
        except json.JSONDecodeError as exc:
            last_error = str(exc)
    raise PlanValidationError([PlanValidationIssue("invalid_json", f"模型计划不是合法 JSON：{last_error}")])


def coerce_plan_payload(payload: Any) -> list[dict[str, Any]]:
    """把常见模型计划外形归一成步骤数组。

    真实模型常输出 ``{steps:[...]}``、``{plan:{steps:[...]}}``、``{actions:[...]}``、
    ``{tool_calls:[...]}``、OpenAI/DeepSeek function-call 形态、中文键名或直接单步对象。
    这里仅做外形兼容；工具名、参数、路径、命令仍在 ``validate_and_build_plan`` 中执行
    白名单与安全校验，不能因为兼容模型格式而放开执行边界。
    """
    steps = _extract_step_sequence(payload)
    if steps is None:
        raise PlanValidationError([PlanValidationIssue("invalid_plan_shape", "计划必须包含 steps/plan/actions/tool_calls 数组，或一个可归一化的单步工具对象。")])
    normalized: list[dict[str, Any]] = []
    for item in steps:
        if isinstance(item, dict):
            normalized.append(_normalize_deepseek_step_object(item))
        else:
            normalized.append(item)
    return normalized


def _extract_step_sequence(value: Any, *, _depth: int = 0) -> list[Any] | None:
    if _depth > 5:
        return None
    if isinstance(value, str):
        text = value.strip()
        if text.startswith(("{", "[")):
            try:
                return _extract_step_sequence(json.loads(text), _depth=_depth + 1)
            except json.JSONDecodeError:
                return None
        return None
    if isinstance(value, list):
        return list(value)
    if not isinstance(value, dict):
        return None
    for key in PLAN_SEQUENCE_KEYS:
        if key in value:
            nested = _extract_step_sequence(value.get(key), _depth=_depth + 1)
            if nested is not None:
                return nested
    if _looks_like_single_step(value):
        return [value]
    return None


def _looks_like_single_step(value: dict[str, Any]) -> bool:
    return (
        any(key in value for key in STEP_TOOL_KEYS)
        or any(key in value for key in STEP_ARGUMENT_KEYS)
        or any(key in value for key in ("code", "代码", "analysis", "分析", "answer", "result", "内容", "正文"))
    )


def _normalize_deepseek_step_object(step: dict[str, Any]) -> dict[str, Any]:
    """兼容 DeepSeek/函数调用常见外形，但不做安全放权。"""
    clean = dict(step)
    function_obj = clean.get("function") or clean.get("function_call")
    if isinstance(function_obj, dict):
        if "tool_name" not in clean and "name" in function_obj:
            clean["tool_name"] = function_obj.get("name")
        for key in STEP_ARGUMENT_KEYS:
            if key in function_obj and key not in clean:
                clean["arguments"] = function_obj.get(key)
                break
    tool_call_obj = clean.get("tool_call")
    if isinstance(tool_call_obj, dict):
        if "tool_name" not in clean:
            nested_tool = tool_call_obj.get("tool_name") or tool_call_obj.get("name") or tool_call_obj.get("tool")
            if nested_tool not in (None, ""):
                clean["tool_name"] = nested_tool
        for key in STEP_ARGUMENT_KEYS:
            if key in tool_call_obj and key not in clean:
                clean["arguments"] = tool_call_obj.get(key)
                break
    if not _extract_tool_name(clean):
        code_payload = clean.get("code") or clean.get("代码")
        analysis_payload = clean.get("analysis") or clean.get("分析") or clean.get("answer") or clean.get("result") or clean.get("content") or clean.get("内容")
        if code_payload not in (None, ""):
            clean["tool_name"] = "return_code"
            clean.setdefault("content", code_payload)
        elif analysis_payload not in (None, ""):
            clean["tool_name"] = "return_analysis"
            clean.setdefault("content", analysis_payload)
    return clean


def _is_tool_allowed(tool_name: str) -> bool:
    return bool(tool_name) and (tool_name in PLANNABLE_TOOLS or tool_name.startswith(WILDCARD_ALLOWED_PREFIXES))


def _allowed_arguments_for_tool(tool_name: str) -> frozenset[str]:
    if tool_name in PLANNABLE_TOOLS:
        return PLANNABLE_TOOLS[tool_name]
    if tool_name.startswith(WILDCARD_ALLOWED_PREFIXES):
        return WILDCARD_ARGUMENTS
    return frozenset()


def _required_arguments_for_tool(tool_name: str) -> frozenset[str]:
    if tool_name in REQUIRED_FIELDS:
        return REQUIRED_FIELDS[tool_name]
    if tool_name.startswith(("read_", "list_", "scan_", "diagnose_")):
        return frozenset({"path"})
    return frozenset()


def build_virtual_return_payload(user_message: str, raw_model_output: str) -> dict[str, Any]:
    """把非 JSON 的模型回答兜底包装成只审计、不写文件的虚拟返回 step。

    该路径用于 DeepSeek/兼容模型把纯代码或纯分析直接作为正文输出的情况。
    内容不会被执行，也不会被写入文件，只经 return_code/return_analysis 适配器进入审计链，
    避免 ``invalid_json`` 后直接回退普通对话造成工程上下文断裂。
    """
    raw = str(raw_model_output or "").strip()
    tool_name = "return_code" if _looks_like_code_answer(raw, user_message) else "return_analysis"
    return {
        "steps": [
            {
                "tool_name": tool_name,
                "arguments": {
                    "content": raw[:20000],
                    "task": str(user_message or "")[:1000],
                    "language": _guess_code_language(raw) if tool_name == "return_code" else "",
                },
                "reason": "模型输出为非 JSON；已归一为审计型虚拟返回步骤。",
            }
        ]
    }


def _looks_like_code_answer(raw: str, user_message: str = "") -> bool:
    text = raw.strip()
    lowered = (str(user_message or "") + "\n" + text).lower()
    code_markers = ("```", "def ", "class ", "import ", "from ", "function ", "const ", "let ", "var ", "public class", "#include", "package ")
    task_markers = ("代码", "函数", "class", "function", "python", "typescript", "javascript", "java", "go ", "rust")
    return any(marker in text for marker in code_markers) or any(marker in lowered for marker in task_markers)


def _guess_code_language(raw: str) -> str:
    fence = re.search(r"```([a-zA-Z0-9_+.-]+)", raw)
    if fence:
        return fence.group(1).lower()[:40]
    lowered = raw.lower()
    if "def " in lowered or "import " in lowered or "from " in lowered:
        return "python"
    if "function " in lowered or "const " in lowered or "let " in lowered:
        return "javascript"
    return "text"

def validate_and_build_plan(payload: Any, *, max_steps: int = 200) -> list[ToolInvocation]:
    steps = coerce_plan_payload(payload)
    issues: list[PlanValidationIssue] = []
    if not steps:
        issues.append(PlanValidationIssue("empty_steps", "计划 steps 不能为空。"))
    # L6.72.39：不再以 20 步硬限制拒绝模型计划；Runtime 预算负责续租/分批执行。
    effective_steps = list(steps)
    invocations: list[ToolInvocation] = []
    for index, raw_step in enumerate(effective_steps):
        if not isinstance(raw_step, dict):
            issues.append(PlanValidationIssue("step_not_object", "步骤必须是对象。", index))
            continue
        raw_tool_name = _extract_tool_name(raw_step)
        tool_name = _normalize_tool_name(raw_tool_name)
        args = _extract_step_arguments(raw_step, tool_name)
        if tool_name == "run_python_quality_check" and "command" not in args:
            command_hint = str(raw_tool_name or "").strip().lower()
            if command_hint in QUALITY_COMMANDS:
                args["command"] = command_hint
        if not isinstance(args, dict):
            issues.append(PlanValidationIssue("arguments_not_object", "arguments 必须是对象。", index, tool_name))
            continue
        reason = _extract_reason(raw_step)
        tool_name, args, reason = _rewrite_document_step(tool_name, args, reason)
        if not _is_tool_allowed(tool_name):
            issues.append(PlanValidationIssue("tool_not_allowed", f"工具 {tool_name or '<空>'} 不在模型计划允许列表或安全前缀中。", index, tool_name))
            continue
        allowed = _allowed_arguments_for_tool(tool_name)
        canonical_args, dropped_unknown = _canonicalize_arguments(tool_name, args)
        dangerous_unknown = sorted(
            key for key in dropped_unknown
            if key.lower() in DANGEROUS_UNKNOWN_ARGUMENT_KEYS or _looks_dangerous_value(args.get(key))
        )
        if dangerous_unknown:
            issues.append(PlanValidationIssue("unsafe_unknown_arguments", f"工具 {tool_name} 出现危险未知字段：{', '.join(dangerous_unknown)}。", index, tool_name))
            continue
        unknown = sorted(set(canonical_args) - set(allowed))
        if unknown:
            issues.append(PlanValidationIssue("unknown_arguments", f"工具 {tool_name} 出现未知字段：{', '.join(unknown)}。", index, tool_name))
            continue
        missing = sorted(_required_arguments_for_tool(tool_name) - set(k for k, v in canonical_args.items() if v not in (None, "")))
        if missing:
            issues.append(PlanValidationIssue("missing_required_arguments", f"工具 {tool_name} 缺少字段：{', '.join(missing)}。", index, tool_name))
            continue
        clean_args = _normalize_arguments(tool_name, canonical_args, index, issues)
        if any(issue.step_index == index for issue in issues):
            continue
        invocations.append(ToolInvocation(tool_name, clean_args, reason=reason[:240]))
    if issues:
        raise PlanValidationError(issues)
    return invocations


def plan_to_public_dict(plan: list[ToolInvocation]) -> list[dict[str, Any]]:
    """供 /plan 预览使用，不包含内部执行对象。"""
    return [
        {
            "step_id": step.step_id,
            "tool_name": step.tool_name,
            "arguments": dict(step.arguments),
            "reason": step.reason,
        }
        for step in plan
    ]



_DOCUMENT_PARSE_EXTENSIONS = {
    ".txt", ".md", ".markdown", ".csv", ".json", ".html", ".htm", ".xml", ".yaml", ".yml", ".toml", ".sql",
    ".py", ".js", ".ts", ".tsx", ".jsx", ".css", ".java", ".cpp", ".c", ".h", ".hpp", ".go", ".rs", ".rb", ".php",
    ".docx", ".pdf", ".xlsx", ".xlsm", ".pptx",
}
_SHELL_DOC_READ_COMMAND_RE = re.compile(r"^\s*(?:cat|type|more|less|gc|get-content|open|start)\b", re.IGNORECASE)
_SHELL_DOC_PATH_RE = re.compile(
    r"(?P<path>(?:[A-Za-z]:)?[^\n\r;&|<>]*?\.(?:txt|md|markdown|csv|json|html?|xml|ya?ml|toml|sql|py|js|ts|tsx|jsx|css|java|cpp|c|h|hpp|go|rs|rb|php|docx|pdf|xlsx|xlsm|pptx))",
    re.IGNORECASE,
)


def _path_suffix(value: Any) -> str:
    text = str(value or "").strip().strip('"\'“”《》<>')
    if not text:
        return ""
    match = re.search(r"(\.[A-Za-z0-9]{1,12})(?:[?#].*)?$", text)
    return match.group(1).lower() if match else ""


def _should_use_document_parse_path(value: Any) -> bool:
    return _path_suffix(value) in _DOCUMENT_PARSE_EXTENSIONS


def _extract_document_path_from_shell_command(command: Any) -> str:
    text = str(command or "").strip()
    if not text or not _SHELL_DOC_READ_COMMAND_RE.search(text):
        return ""
    match = _SHELL_DOC_PATH_RE.search(text)
    if not match:
        return ""
    candidate = match.group("path").strip().strip('"\'“”《》<>')
    return candidate if _should_use_document_parse_path(candidate) else ""


def _rewrite_document_step(tool_name: str, args: dict[str, Any], reason: str) -> tuple[str, dict[str, Any], str]:
    """L6.72.51：文档系统不得按后缀抢路由。

    旧版会把 read_file *.txt/*.md/*.py 自动改成 document_parse，导致
    创建文件、读目录、代码任务被文档系统劫持。现在只保留模型显式规划的
    document_* 工具；schema 层不再根据路径/后缀替 LLM 重判 work_type。
    """
    return tool_name, args, reason

def _extract_tool_name(raw_step: dict[str, Any]) -> str:
    for key in STEP_TOOL_KEYS:
        if key not in raw_step:
            continue
        value = raw_step.get(key)
        if isinstance(value, dict):
            nested = (
                value.get("tool_name")
                or value.get("name")
                or value.get("id")
                or value.get("工具名称")
                or value.get("工具名")
            )
            if nested not in (None, ""):
                return str(nested)
        elif value not in (None, ""):
            return str(value)
    return ""


def _normalize_tool_name(value: str) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    if text in PLANNABLE_TOOLS:
        return text
    # 模型常见输出：safeCommandRunner / code_x.safe_command_runner / safe-command-runner。
    # 这里只做名称归一，不放权；真实可执行性仍由 RuntimeToolRegistry 和 QualityGate 决定。
    split_camel = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", text)
    key = re.sub(r"[\s\-]+", "_", split_camel).strip().lower()
    no_prefix = re.sub(r"^(?:code_x|codex|code-x|code x)[._:]+", "", key)
    compact = re.sub(r"[^0-9a-zA-Z_一-鿿]", "", key)
    compact_no_prefix = re.sub(r"^(?:code_x|codex)_?", "", compact)
    return (
        TOOL_NAME_ALIASES.get(key)
        or TOOL_NAME_ALIASES.get(no_prefix)
        or TOOL_NAME_ALIASES.get(compact)
        or TOOL_NAME_ALIASES.get(compact_no_prefix)
        or key
    )


def _coerce_argument_object(value: Any) -> dict[str, Any] | None:
    if isinstance(value, dict):
        return dict(value)
    if isinstance(value, str):
        text = value.strip()
        if text.startswith("{") and text.endswith("}"):
            try:
                parsed = json.loads(text)
            except json.JSONDecodeError:
                return None
            if isinstance(parsed, dict):
                return parsed
    return None


def _extract_step_arguments(raw_step: dict[str, Any], tool_name: str) -> dict[str, Any]:
    args: dict[str, Any] = {}
    for nested_key in ("tool", "tool_call", "function", "function_call"):
        tool_obj = raw_step.get(nested_key)
        if isinstance(tool_obj, dict):
            for key in STEP_ARGUMENT_KEYS:
                nested = _coerce_argument_object(tool_obj.get(key))
                if nested is not None:
                    args.update(nested)
    for key in STEP_ARGUMENT_KEYS:
        value = _coerce_argument_object(raw_step.get(key))
        if value is not None:
            args.update(value)
    allowed_or_alias_keys = set(_allowed_arguments_for_tool(tool_name)) | set(STEP_METADATA_KEYS) | set(DANGEROUS_UNKNOWN_ARGUMENT_KEYS)
    for aliases in ARGUMENT_ALIASES.values():
        allowed_or_alias_keys.update(aliases)
    for key, value in raw_step.items():
        if key in STEP_TOOL_KEYS or key in STEP_ARGUMENT_KEYS or key == "tool_call":
            continue
        if key in allowed_or_alias_keys:
            args.setdefault(key, value)
    return args


def _extract_reason(raw_step: dict[str, Any]) -> str:
    for key in ("reason", "rationale", "description", "summary", "title", "notes"):
        value = raw_step.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _canonicalize_arguments(tool_name: str, args: dict[str, Any]) -> tuple[dict[str, Any], set[str]]:
    allowed = _allowed_arguments_for_tool(tool_name)
    clean: dict[str, Any] = {}
    consumed: set[str] = set()
    for canonical in allowed:
        aliases = ARGUMENT_ALIASES.get(canonical, (canonical,))
        for alias in aliases:
            if alias in args and args[alias] not in (None, ""):
                clean[canonical] = args[alias]
                consumed.add(alias)
                break
    for key, value in args.items():
        if key in allowed:
            clean[key] = value
            consumed.add(key)
    dropped_unknown = {key for key in args if key not in consumed and key not in STEP_METADATA_KEYS}
    return clean, dropped_unknown


def _looks_dangerous_value(value: Any) -> bool:
    if value is None:
        return False
    text = str(value).strip().lower()
    if not text:
        return False
    # L6.72.39：schema 层只截断 A5 明显破坏性/凭证内容；命令字符串、URL、绝对路径不再默认阻断。
    a5_fragments = ("rm -rf", "format ", "mkfs", "reg delete", "powershell -enc", "curl | sh")
    credential_fragments = ("api_key=", "apikey=", "authorization:", "bearer ", "private key")
    return any(fragment in text for fragment in a5_fragments) or any(fragment in text for fragment in credential_fragments)


def _normalize_arguments(tool_name: str, args: dict[str, Any], index: int, issues: list[PlanValidationIssue]) -> dict[str, Any]:
    clean: dict[str, Any] = {}
    for key, value in args.items():
        if key in PATH_FIELDS:
            text = str(value or "").strip()
            if not text:
                issues.append(PlanValidationIssue("empty_path", f"{tool_name}.{key} 路径不能为空。", index, tool_name))
                continue
            if _is_unsafe_path(text):
                issues.append(PlanValidationIssue("unsafe_path", f"模型计划路径被拒绝：{text}", index, tool_name))
                continue
            clean[key] = text
        elif key == "command":
            if tool_name == "safe_command_runner" and isinstance(value, (list, tuple)):
                command_items = [str(item).strip() for item in value if str(item).strip()]
                command_text = " ".join(command_items)
                if not command_items:
                    issues.append(PlanValidationIssue("empty_command", f"{tool_name}.command cannot be empty.", index, tool_name))
                    continue
                if _looks_dangerous_value(command_text):
                    issues.append(PlanValidationIssue("unsafe_a5_command", f"command contains A5 pattern: {command_text[:120]}", index, tool_name))
                    continue
                clean[key] = command_items
                continue
            command = str(value or "").strip()
            if _looks_dangerous_value(command):
                issues.append(PlanValidationIssue("unsafe_a5_command", f"命令命中 A5 高危模式：{command[:120]}", index, tool_name))
                continue
            clean[key] = command
        elif key in {"content", "notes", "manual_notes", "task_id", "run_id", "task", "language"}:
            clean[key] = str(value)
        elif key == "max_candidates":
            clean[key] = _clamp_int(value, minimum=1, maximum=50, default=12)
        elif key == "max_chars":
            clean[key] = _clamp_int(value, minimum=500, maximum=50000, default=12000)
        elif key == "top_k":
            clean[key] = _clamp_int(value, minimum=1, maximum=20, default=6)
        elif key in {"document_id", "instruction", "output_format", "format", "old_text", "new_text", "new_content", "operation", "mode", "operation_id", "manifest", "manifest_path"}:
            clean[key] = str(value)
        elif key in {"overwrite", "dry_run", "allow_no_match", "force"}:
            clean[key] = value if isinstance(value, bool) else str(value)
        elif key == "replacements":
            clean[key] = value
        elif key == "max_items":
            max_allowed = 30 if tool_name == "build_execution_exoskeleton" else 100
            default_items = 12 if tool_name == "build_execution_exoskeleton" else 20
            if tool_name == "build_learning_convergence":
                max_allowed = 50
                default_items = 18
            if tool_name == "build_recovery_coordination":
                max_allowed = 40
                default_items = 12
            if tool_name == "build_governance_execution":
                max_allowed = 40
                default_items = 12
            if tool_name == "build_planner_context":
                max_allowed = 60
                default_items = 16
            if tool_name == "build_project_repair_plan":
                max_allowed = 40
                default_items = 12
            clean[key] = _clamp_int(value, minimum=1, maximum=max_allowed, default=default_items)
        elif key == "max_targets":
            clean[key] = _clamp_int(value, minimum=1, maximum=40, default=12)
        elif key == "step_budget":
            clean[key] = _clamp_int(value, minimum=1, maximum=200, default=20)
        else:
            clean[key] = value
    if tool_name == "run_python_quality_check" and "target" not in clean:
        clean["target"] = "."
    if tool_name in {"list_dir", "scan_project", "diagnose_project", "build_project_repair_plan", "build_delivery_standardization", "build_provider_adaptation"} and "path" not in clean:
        clean["path"] = "."
    if tool_name in {"scan_project", "diagnose_project", "build_project_repair_plan"}:
        clean["max_depth"] = _clamp_int(clean.get("max_depth", 6), minimum=1, maximum=12, default=6)
        clean["max_files"] = _clamp_int(clean.get("max_files", 1500), minimum=1, maximum=10000, default=1500)
    return clean


def _is_unsafe_path(text: str) -> bool:
    lower = text.lower().replace("\\", "/")
    # L6.72.39：路径不再在 Planner schema 层拦截。绝对路径、~、../ 交由 WorkspaceGuard
    # 结合 host access root 做归一化；只有明显凭证路径按 A5 前置拦截。
    if any(term in lower for term in SENSITIVE_PATH_TERMS):
        return True
    return False


def _clamp_int(value: Any, *, minimum: int, maximum: int, default: int) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return default
    return max(minimum, min(number, maximum))
