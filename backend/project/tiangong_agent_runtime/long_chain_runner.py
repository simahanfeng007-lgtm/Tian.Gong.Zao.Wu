"""长链执行器。

L6.11 口径：长链执行器不是绕过治理的批处理器，而是把每个步骤逐一送入
ExecutionSpine。每一步仍然经过风险分级、permit、registry、adapter 和审计桥。
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from time import time

from .budget_guard import StepBudgetGuard
from .execution_spine import ExecutionSpine
from .tool_invocation import ToolInvocation
from .tool_result import ToolResult, ToolResultStatus
from .turn_context import TurnContext


@dataclass(frozen=True)
class LongChainCheckpoint:
    """长链执行检查点，只保存安全摘要。"""

    index: int
    step_id: str
    tool_name: str
    status: str
    audit_ref: str = ""
    error_code: str = ""
    timestamp: float = field(default_factory=time)


@dataclass(frozen=True)
class LongChainProgressSnapshot:
    """长链进度快照。

    只记录工具名、索引和安全摘要，不携带参数正文或敏感输出。
    """

    completed_steps: int
    total_steps: int
    completed_tool_names: list[str] = field(default_factory=list)
    message: str = ""
    timestamp: float = field(default_factory=time)

    def public_dict(self) -> dict[str, object]:
        return {
            "completed_steps": self.completed_steps,
            "total_steps": self.total_steps,
            "completed_tool_names": list(self.completed_tool_names),
            "message": self.message,
            "timestamp": self.timestamp,
        }


@dataclass(frozen=True)
class LongChainRunSummary:
    """长链运行摘要。"""

    total_steps: int
    executed_steps: int
    failure_count: int
    stopped_reason: str = "completed"
    checkpoints: list[LongChainCheckpoint] = field(default_factory=list)
    progress_snapshots: list[LongChainProgressSnapshot] = field(default_factory=list)


class LongChainRunner:
    """受治理长链 Runner。

    - A1-A3 是否自动执行由 ExecutionSpine/PermitGateway 判定；
    - A4/A5 会由 ExecutionSpine 返回 confirmation_required/blocked，并触发停止；
    - 普通失败由 failure_budget 控制，默认 1 次失败即停止后续步骤；
    - 这里不直接调用 adapter，避免产生第二条执行通道。
    """

    def __init__(self, spine: ExecutionSpine) -> None:
        self.spine = spine
        self.last_summary = LongChainRunSummary(total_steps=0, executed_steps=0, failure_count=0)

    def run(
        self,
        context: TurnContext,
        plan: list[ToolInvocation],
        *,
        failure_budget: int = 1,
        stop_on_failure: bool = True,
        progress_interval: int = 5,
        progress_callback: Callable[[LongChainProgressSnapshot], None] | None = None,
    ) -> list[ToolResult]:
        StepBudgetGuard(context.max_steps).check(len(plan))
        results: list[ToolResult] = []
        checkpoints: list[LongChainCheckpoint] = []
        progress_snapshots: list[LongChainProgressSnapshot] = []
        failure_count = 0
        stopped_reason = "completed"

        for index, invocation in enumerate(plan[: context.max_steps], start=1):
            # 单步送入脊柱，确保每步独立经过 permit 与 audit。
            step_results = self.spine.execute_plan(context, [invocation])
            if not step_results:
                stopped_reason = "empty_step_result"
                break
            result = step_results[0]
            results.append(result)
            checkpoints.append(
                LongChainCheckpoint(
                    index=index,
                    step_id=result.step_id,
                    tool_name=result.tool_name,
                    status=result.status.value,
                    audit_ref=result.audit_ref,
                    error_code=result.error_code,
                )
            )
            if progress_interval > 0 and (index % progress_interval == 0 or index == min(len(plan), context.max_steps)):
                snapshot = _build_progress_snapshot(index, len(plan), checkpoints)
                progress_snapshots.append(snapshot)
                if progress_callback is not None:
                    progress_callback(snapshot)

            if result.status is ToolResultStatus.CONFIRMATION_REQUIRED:
                stopped_reason = "confirmation_required"
                break
            if result.status is ToolResultStatus.BLOCKED:
                stopped_reason = "blocked"
                break
            if _is_timeout_result(result):
                stopped_reason = "timeout"
                break
            if result.status is ToolResultStatus.FAILED:
                failure_count += 1
                if stop_on_failure or failure_count >= failure_budget:
                    stopped_reason = "failure_budget_exhausted"
                    break

        self.last_summary = LongChainRunSummary(
            total_steps=len(plan),
            executed_steps=len(results),
            failure_count=failure_count,
            stopped_reason=stopped_reason,
            checkpoints=checkpoints,
            progress_snapshots=progress_snapshots,
        )
        return results


def _build_progress_snapshot(index: int, total_steps: int, checkpoints: list[LongChainCheckpoint]) -> LongChainProgressSnapshot:
    recent_tools = [checkpoint.tool_name for checkpoint in checkpoints[-5:]]
    message = f"[长链] 进度 {index}/{total_steps} — 最近完成 " + ", ".join(recent_tools)
    return LongChainProgressSnapshot(
        completed_steps=index,
        total_steps=total_steps,
        completed_tool_names=recent_tools,
        message=message,
    )


def _is_timeout_result(result: ToolResult) -> bool:
    return result.status is ToolResultStatus.TIMEOUT or str(result.error_code).lower() in {"timeout", "step_timeout", "adapter_timeout"}
