"""Runtime adapters for v1 clean semantic import tools.

The adapter registers only v2-native functions from v1_clean_import_runtime.
It does not import any v1 module or legacy registry.
"""
from __future__ import annotations

import inspect
from pathlib import Path
from typing import Any, Callable, Dict, Mapping

from .runtime_tool_registry import RuntimeToolRegistry, ToolDescriptor
from .tool_invocation import ToolInvocation
from .tool_result import ToolResult, ToolResultStatus
from .turn_context import TurnContext
from . import v1_clean_import_runtime as clean

CleanCallable = Callable[..., Any]

A1_TOOLS = {
    "workspace_text_search",
    "conversation_history_search",
    "task_pattern_search",
    "experience_mentor_search",
    "document_text_extract",
    "web_readability_extract",
}

A2_TOOLS = {
    "v1_clean_import_status",
    "v1_clean_import_audit",
    "v1_clean_import_guide",
    "learning_master_plan",
    "tool_skill_blueprint",
}

V1_CLEAN_TOOL_RISK: Dict[str, str] = {
    **{name: "A1" for name in A1_TOOLS},
    **{name: "A2" for name in A2_TOOLS},
}

TOOL_FUNCTIONS: Dict[str, CleanCallable] = {
    "v1_clean_import_status": clean.v1_clean_import_status,
    "v1_clean_import_audit": clean.v1_clean_import_audit,
    "v1_clean_import_guide": clean.v1_clean_import_guide,
    "workspace_text_search": clean.workspace_text_search,
    "conversation_history_search": clean.conversation_history_search,
    "task_pattern_search": clean.task_pattern_search,
    "experience_mentor_search": clean.experience_mentor_search,
    "document_text_extract": clean.document_text_extract,
    "web_readability_extract": clean.web_readability_extract,
    "learning_master_plan": clean.learning_master_plan,
    "tool_skill_blueprint": clean.tool_skill_blueprint,
}

TOOL_DESCRIPTIONS: Dict[str, str] = {
    "v1_clean_import_status": "v1 去重导入状态：显示独立纯净导入层与命令。",
    "v1_clean_import_audit": "v1 去重导入审计：报告哪些语义已去重、重建、暂缓。",
    "v1_clean_import_guide": "v1 去重导入使用指南：给 LLM 的非 Code-X 工具使用卡。",
    "workspace_text_search": "只读全文搜索 workspace 内文本/文档材料。",
    "conversation_history_search": "只读搜索本地会话/Runtime 留痕摘要。",
    "task_pattern_search": "只读搜索历史任务模式，辅助‘先抄再改’复用。",
    "experience_mentor_search": "只读搜索 SKILL.md/经验材料/历史留痕。",
    "document_text_extract": "只读提取 txt/md/json/jsonl/csv/docx/pdf 等文档文本。",
    "web_readability_extract": "对已提供 HTML/网页正文做可读性清洗；不联网抓取。",
    "learning_master_plan": "学习精通规划：L1-L5 深度、可信度、实践转化与资产化候选。",
    "tool_skill_blueprint": "Tool/Skill 生产标准草案：Manifest、SkillVersion、测试矩阵，不注册不执行。",
}


def register_v1_clean_import_tools(registry: RuntimeToolRegistry) -> None:
    for name in sorted(TOOL_FUNCTIONS):
        registry.register(
            ToolDescriptor(name, TOOL_DESCRIPTIONS.get(name, f"v1 clean import tool: {name}"), V1_CLEAN_TOOL_RISK.get(name, "A2")),
            build_clean_import_adapter(name, TOOL_FUNCTIONS[name]),
        )


def build_clean_import_adapter(tool_name: str, func: CleanCallable):
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
        except Exception as exc:
            return ToolResult(
                step_id=invocation.step_id,
                tool_name=invocation.tool_name,
                status=ToolResultStatus.FAILED,
                output_summary=f"v1 clean import 工具执行失败：{type(exc).__name__}: {exc}",
                error_code="v1_clean_import_adapter_error",
                data={"exception_type": type(exc).__name__, "message": str(exc), "tool_name": tool_name},
            )
    return adapter


def _prepare_args(func: CleanCallable, raw_args: Mapping[str, Any], context: TurnContext) -> Dict[str, Any]:
    args = dict(raw_args or {})
    sig = inspect.signature(func)
    params = sig.parameters
    if "root" in params and "root" not in args:
        args["root"] = str(context.workspace)
    if "query" in params and "query" not in args and func.__name__ in {"workspace_text_search", "conversation_history_search", "task_pattern_search", "experience_mentor_search"}:
        args["query"] = context.user_message
    if "goal" in params and "goal" not in args and func.__name__ in {"learning_master_plan", "tool_skill_blueprint"}:
        args["goal"] = context.user_message
    if "html_or_text" in params and "html_or_text" not in args and func.__name__ == "web_readability_extract":
        args["html_or_text"] = context.user_message
    for key in ("root",):
        if key in args and isinstance(args[key], str):
            value = args[key].strip()
            args[key] = str(context.workspace if value in {"", "."} else Path(value).expanduser().resolve() if Path(value).expanduser().is_absolute() else (context.workspace / value).resolve())
    return {k: v for k, v in args.items() if k in params}


def _to_dict(payload: Any) -> Dict[str, Any]:
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
    if data.get("summary"):
        return str(data["summary"])[:12000]
    result = data.get("result")
    if isinstance(result, Mapping) and result.get("summary"):
        return str(result["summary"])[:12000]
    return f"v1 clean import 工具 {tool_name} 已返回结构化结果。"


def _artifacts_from_payload(data: Mapping[str, Any], workspace: Path) -> list[str]:
    result = data.get("result")
    artifacts: list[str] = []
    if isinstance(result, Mapping):
        for key in ("path", "source"):
            value = result.get(key)
            if value:
                artifacts.append(str(value))
    return artifacts[:20]


def _error_code_from_payload(data: Mapping[str, Any]) -> str:
    if data.get("error_code"):
        return str(data["error_code"])
    raw = str(data.get("status") or "failed").lower()
    return f"v1_clean_import_{raw}"
