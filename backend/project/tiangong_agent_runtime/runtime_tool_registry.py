"""运行时工具注册表。"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import re

from .tool_invocation import ToolInvocation
from .tool_result import ToolResult
from .turn_context import TurnContext

ToolAdapter = Callable[[ToolInvocation, TurnContext], ToolResult]


_TOOL_NAME_ALIASES = {
    "safecommandrunner": "safe_command_runner",
    "safecommand_runner": "safe_command_runner",
    "safe_commandrunner": "safe_command_runner",
    "safe_command_runner": "safe_command_runner",
    "safe-command-runner": "safe_command_runner",
    "safe command runner": "safe_command_runner",
    "codex_safe_command_runner": "safe_command_runner",
    "code_x_safe_command_runner": "safe_command_runner",
    "codex.safe_command_runner": "safe_command_runner",
    "code_x.safe_command_runner": "safe_command_runner",
    "documentparse": "document_parse",
    "document_parse": "document_parse",
    "parse_document": "document_parse",
    "doc_parse": "document_parse",
    "documentquery": "document_query",
    "document_query": "document_query",
    "doc_query": "document_query",
    "query_document": "document_query",
    "文档追问": "document_query",
    "文档查询": "document_query",
    "documentexport": "document_export",
    "document_export": "document_export",
    "doc_export": "document_export",
    "export_document": "document_export",
    "文档导出": "document_export",
    "documentrewriteplan": "document_rewrite_plan",
    "document_rewrite_plan": "document_rewrite_plan",
    "document_rewrite": "document_rewrite_plan",
    "document_edit_plan": "document_rewrite_plan",
    "文档修改计划": "document_rewrite_plan",
    "documentapplyrewrite": "document_apply_rewrite",
    "document_apply_rewrite": "document_apply_rewrite",
    "document_writeback": "document_apply_rewrite",
    "document_write_back": "document_apply_rewrite",
    "document_edit_apply": "document_apply_rewrite",
    "apply_document_rewrite": "document_apply_rewrite",
    "apply_rewrite": "document_apply_rewrite",
    "文档写回": "document_apply_rewrite",
    "应用文档修改": "document_apply_rewrite",
    "documentrollback": "document_rollback",
    "document_rollback": "document_rollback",
    "rollback_document": "document_rollback",
    "document_writeback_rollback": "document_rollback",
    "文档回滚": "document_rollback",
}



def canonical_tool_name(tool_name: str) -> str:
    text = str(tool_name or "").strip()
    if not text:
        return ""
    split_camel = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", text)
    key = re.sub(r"[\s\-]+", "_", split_camel).strip().lower()
    no_prefix = re.sub(r"^(?:code_x|codex|code-x|code x)[._:]+", "", key)
    compact = re.sub(r"[^0-9a-zA-Z_一-鿿]", "", key)
    compact_no_prefix = re.sub(r"^(?:code_x|codex)_?", "", compact)
    return (
        _TOOL_NAME_ALIASES.get(key)
        or _TOOL_NAME_ALIASES.get(no_prefix)
        or _TOOL_NAME_ALIASES.get(compact)
        or _TOOL_NAME_ALIASES.get(compact_no_prefix)
        or key
    )


@dataclass(frozen=True)
class ToolDescriptor:
    name: str
    description: str
    default_risk: str


class RuntimeToolRegistry:
    def __init__(self) -> None:
        self._adapters: dict[str, ToolAdapter] = {}
        self._descriptors: dict[str, ToolDescriptor] = {}

    def register(self, descriptor: ToolDescriptor, adapter: ToolAdapter) -> None:
        canonical = canonical_tool_name(descriptor.name)
        self._descriptors[canonical] = ToolDescriptor(canonical, descriptor.description, descriptor.default_risk)
        self._adapters[canonical] = adapter

    def get(self, tool_name: str) -> ToolAdapter | None:
        return self._adapters.get(canonical_tool_name(tool_name))

    def describe(self) -> list[ToolDescriptor]:
        return [self._descriptors[name] for name in sorted(self._descriptors)]

    def names(self) -> list[str]:
        return sorted(self._adapters)
