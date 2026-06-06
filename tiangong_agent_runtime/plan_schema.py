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
}

REQUIRED_FIELDS: dict[str, frozenset[str]] = {
    "scan_project": frozenset(),
    "diagnose_project": frozenset(),
    "list_dir": frozenset({"path"}),
    "read_file": frozenset({"path"}),
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
}

PATH_FIELDS = {"path", "target", "source"}
QUALITY_COMMANDS = {"compileall", "pytest"}
SENSITIVE_PATH_TERMS = {
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
    "source": ("source", "src", "source_path", "input_path", "folder", "directory", "path", "from", "来源", "源路径"),
    "target": ("target", "dest", "destination", "output", "output_path", "zip_path", "to", "目标", "目标路径", "输出"),
    "content": ("content", "text", "body", "data", "code", "answer", "analysis", "result", "内容", "正文", "代码", "分析", "结果"),
    "language": ("language", "lang", "语言"),
    "command": ("command", "quality_command", "check", "test_command", "cmd", "命令", "检查命令"),
    "max_depth": ("max_depth", "depth"),
    "max_files": ("max_files", "file_limit", "limit"),
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
}

DANGEROUS_UNKNOWN_ARGUMENT_KEYS = {
    "shell",
    "cmd",
    "bash",
    "powershell",
    "command_line",
    "script",
    "url",
    "endpoint",
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
                "scan_project": {"path": "relative directory, default .", "max_depth": "1-12 optional", "max_files": "1-10000 optional"},
                "diagnose_project": {"path": "relative directory, default .", "max_depth": "1-12 optional", "max_files": "1-10000 optional"},
                "list_dir": {"path": "relative directory, default ."},
                "read_file": {"path": "relative text file"},
                "write_workspace_file": {"path": "relative target file", "content": "text"},
                "return_code": {"content": "code text; audit-only virtual return", "language": "optional language", "task": "optional user task summary"},
                "return_analysis": {"content": "analysis text; audit-only virtual return", "task": "optional user task summary"},
                "run_python_quality_check": {"command": "compileall|pytest", "target": "relative path, default ."},
                "create_zip_package": {"source": "relative path", "target": "relative .zip path"},
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
            },
            "safe_prefix_tools": list(WILDCARD_ALLOWED_PREFIXES),
            "forbidden": [
                "shell command strings",
                "absolute paths",
                "paths outside workspace",
                "secrets or credential files",
                "tool names outside allowed_tools",
                "model_chat or recursive model calls",
                "direct provider SDK calls or plaintext credentials",
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

def validate_and_build_plan(payload: Any, *, max_steps: int = 20) -> list[ToolInvocation]:
    steps = coerce_plan_payload(payload)
    issues: list[PlanValidationIssue] = []
    if not steps:
        issues.append(PlanValidationIssue("empty_steps", "计划 steps 不能为空。"))
    if len(steps) > max_steps:
        issues.append(PlanValidationIssue("too_many_steps", f"计划步骤数 {len(steps)} 超过上限 {max_steps}。"))
    invocations: list[ToolInvocation] = []
    for index, raw_step in enumerate(steps[:max_steps]):
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
    key = re.sub(r"[\s\-]+", "_", text).strip().lower()
    compact = re.sub(r"[^0-9a-zA-Z_一-鿿]", "", key)
    return TOOL_NAME_ALIASES.get(key) or TOOL_NAME_ALIASES.get(compact) or key


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
    dangerous_fragments = ("rm -rf", "del /", "format ", "powershell", "curl ", "wget ", "http://", "https://")
    return any(fragment in text for fragment in dangerous_fragments) or any(term in text for term in SENSITIVE_PATH_TERMS)


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
            command = str(value or "").strip().lower()
            if command not in QUALITY_COMMANDS:
                issues.append(PlanValidationIssue("unsafe_quality_command", f"质量检查命令不允许：{command}", index, tool_name))
                continue
            clean[key] = command
        elif key in {"content", "notes", "manual_notes", "task_id", "run_id", "task", "language"}:
            clean[key] = str(value)
        elif key == "max_candidates":
            clean[key] = _clamp_int(value, minimum=1, maximum=50, default=12)
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
    if any(term in lower for term in SENSITIVE_PATH_TERMS):
        return True
    if ".." in PurePosixPath(lower).parts:
        return True
    if PureWindowsPath(text).is_absolute() or PurePosixPath(text).is_absolute():
        return True
    if re.match(r"^[a-zA-Z]:", text):
        return True
    if lower.startswith("~"):
        return True
    return False


def _clamp_int(value: Any, *, minimum: int, maximum: int, default: int) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return default
    return max(minimum, min(number, maximum))
