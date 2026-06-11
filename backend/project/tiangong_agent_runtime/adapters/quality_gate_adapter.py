"""L6.18 质量门 adapter。"""

from __future__ import annotations

from ..quality_gate_bridge import QualityGateBridge
from ..tool_invocation import ToolInvocation
from ..tool_result import ToolResult, ToolResultStatus
from ..turn_context import TurnContext


def build_evaluate_quality_gate_adapter(quality_gate: QualityGateBridge):
    def evaluate_quality_gate_adapter(invocation: ToolInvocation, context: TurnContext) -> ToolResult:
        verdict = quality_gate.evaluate(
            gate_name=str(invocation.arguments.get("gate_name") or "default"),
            quality_results=list(invocation.arguments.get("quality_results") or []),
            diagnosis=dict(invocation.arguments.get("diagnosis") or {}),
            require_pytest=bool(invocation.arguments.get("require_pytest", False)),
        )
        status = ToolResultStatus.OK if verdict.decision in {"pass", "warn"} else ToolResultStatus.FAILED
        return ToolResult(
            step_id=invocation.step_id,
            tool_name=invocation.tool_name,
            status=status,
            output_summary=verdict.summary_text(),
            error_code="" if status is ToolResultStatus.OK else f"quality_gate_{verdict.decision}",
            data=verdict.public_dict(),
        )

    return evaluate_quality_gate_adapter
