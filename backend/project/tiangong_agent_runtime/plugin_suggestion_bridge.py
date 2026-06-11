"""插件建议桥。

L6.11 口径：插件建议只转成受控 ToolInvocation 计划，不能绕过治理执行。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .tool_invocation import ToolInvocation
from .suggestions import HandoffSuggestion, PlanSuggestion, QualityGateSuggestion, RepairSuggestion

ALLOWED_SUGGESTION_TOOLS = {
    "list_dir",
    "read_file",
    "write_workspace_file",
    "run_python_quality_check",
    "create_zip_package",
}


@dataclass(frozen=True)
class SuggestionBridgeResult:
    plan: list[ToolInvocation] = field(default_factory=list)
    rejected: list[str] = field(default_factory=list)
    summaries: list[str] = field(default_factory=list)

    @property
    def accepted_count(self) -> int:
        return len(self.plan)


class PluginSuggestionBridge:
    """将 L6 插件建议转换为显式计划。"""

    def to_plan(self, suggestions: list[PlanSuggestion | RepairSuggestion | QualityGateSuggestion | HandoffSuggestion]) -> SuggestionBridgeResult:
        plan: list[ToolInvocation] = []
        rejected: list[str] = []
        summaries: list[str] = []
        for suggestion in suggestions:
            summaries.append(f"{suggestion.source_plugin}: {suggestion.summary}")
            if isinstance(suggestion, PlanSuggestion):
                if suggestion.direct_execution_requested:
                    rejected.append(f"{suggestion.source_plugin}: 请求直接执行，已拒绝；必须走治理链。")
                    continue
                for raw_step in suggestion.steps:
                    invocation = ToolInvocation.from_dict(raw_step)
                    if invocation.tool_name not in ALLOWED_SUGGESTION_TOOLS:
                        rejected.append(f"{suggestion.source_plugin}: 未允许的建议工具 {invocation.tool_name}")
                        continue
                    plan.append(invocation)
            elif isinstance(suggestion, RepairSuggestion):
                for raw_step in suggestion.proposed_steps:
                    invocation = ToolInvocation.from_dict(raw_step)
                    if invocation.tool_name not in ALLOWED_SUGGESTION_TOOLS:
                        rejected.append(f"{suggestion.source_plugin}: 未允许的修复工具 {invocation.tool_name}")
                        continue
                    plan.append(invocation)
            elif isinstance(suggestion, QualityGateSuggestion):
                for check in suggestion.required_checks:
                    normalized = check.strip().lower()
                    if normalized in {"compileall", "python -m compileall"}:
                        plan.append(ToolInvocation("run_python_quality_check", {"command": "compileall", "target": "."}))
                    elif normalized in {"pytest", "python -m pytest"}:
                        plan.append(ToolInvocation("run_python_quality_check", {"command": "pytest", "target": "."}))
                    else:
                        rejected.append(f"{suggestion.source_plugin}: 未允许的质量门 {check}")
            elif isinstance(suggestion, HandoffSuggestion):
                # Handoff 建议只进摘要，不产生执行步骤。
                continue
        return SuggestionBridgeResult(plan=plan, rejected=rejected, summaries=summaries)
