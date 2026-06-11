"""L6.35 Planner 驱动真实执行主链控制器。

本模块把 L6.31 的 ``UnifiedPlannerContext`` / ``ExecutionStepDraft`` 推进到
可执行状态机：Planner 仍只产出计划，真正执行仍走 ``LongChainRunner`` 与
``ExecutionSpine``，每一步继续经过风险分级、PermitGateway、Registry、Adapter、Audit。

L6.35 增强点：
- 输出完整 step 生命周期语义：planned / queued / running / terminal；
- 单步记录 started_at / finished_at / duration_ms / adapter_name / evidence_refs；
- 区分 failed / blocked / confirmation_required / timeout / skipped；
- 提供 ``execute_resume``，从上一份报告的断点继续，不重跑已成功步骤；
- 保持外壳层治理，不产生第二 Runtime，不污染 ``tiangong_kernel``。
"""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
from time import time
from typing import Any

from tiangong_agent_shell.safe_logging import redact_text

from .long_chain_runner import LongChainRunSummary, LongChainRunner
from .risk_classifier import RiskClassifier
from .tool_invocation import ToolInvocation
from .tool_result import ToolResult, ToolResultStatus
from .turn_context import TurnContext

PLANNER_EXECUTION_SCHEMA = "tiangong.l6_35.planner_execution_controller.v1"
SOURCE_VERSION = "L6.35-step-state-machine-pressure-baseline"
TERMINAL_STATES = {
    "succeeded",
    "failed",
    "blocked",
    "confirmation_required",
    "skipped",
    "recovered",
    "timeout",
}
EXECUTION_LIFECYCLE_STATES = {"planned", "queued", "running"} | TERMINAL_STATES


@dataclass(frozen=True)
class PlannerReplayEvent:
    """可回放事件，只保留安全摘要。"""

    event_index: int
    event_type: str
    step_index: int
    step_id: str
    tool_name: str
    status: str = ""
    audit_ref: str = ""
    error_code: str = ""
    summary: str = ""
    timestamp: float = field(default_factory=time)

    def public_dict(self) -> dict[str, Any]:
        return {
            "event_index": self.event_index,
            "event_type": self.event_type,
            "step_index": self.step_index,
            "step_id": self.step_id,
            "tool_name": self.tool_name,
            "status": self.status,
            "audit_ref": self.audit_ref,
            "error_code": self.error_code,
            "summary": _safe_text(self.summary, limit=280),
            "timestamp": self.timestamp,
        }


@dataclass(frozen=True)
class PlannerExecutionStepRecord:
    """单步生命周期记录。"""

    step_index: int
    step_id: str
    tool_name: str
    state: str
    state_history: list[str]
    result_status: str = ""
    risk_level: str = ""
    reason: str = ""
    audit_ref: str = ""
    error_code: str = ""
    output_summary: str = ""
    argument_keys: list[str] = field(default_factory=list)
    arguments_digest: str = ""
    checkpoint_ref: str = ""
    resume_candidate: bool = False
    replay_event_refs: list[str] = field(default_factory=list)
    parent_step_id: str = ""
    source_plan_id: str = ""
    lifecycle_states: list[str] = field(default_factory=list)
    adapter_name: str = ""
    queued_at: float = 0.0
    started_at: float = 0.0
    finished_at: float = 0.0
    duration_ms: int = 0
    evidence_refs: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.state not in TERMINAL_STATES:
            raise ValueError("L6.35 step state must be terminal and replayable")
        if not self.state_history or self.state_history[0] != "planned":
            raise ValueError("L6.35 step history must start with planned")
        if self.state not in self.state_history:
            raise ValueError("L6.35 step history must include final state")
        lifecycle = self.lifecycle_states or list(self.state_history)
        if lifecycle[0] != "planned":
            raise ValueError("L6.35 lifecycle must start with planned")
        if self.state not in lifecycle:
            raise ValueError("L6.35 lifecycle must include final state")
        if any(state not in EXECUTION_LIFECYCLE_STATES for state in lifecycle):
            raise ValueError("L6.35 lifecycle contains unknown state")
        if self.duration_ms < 0:
            raise ValueError("L6.35 duration_ms must be non-negative")

    def public_dict(self) -> dict[str, Any]:
        return {
            "step_index": self.step_index,
            "step_id": self.step_id,
            "parent_step_id": self.parent_step_id,
            "source_plan_id": self.source_plan_id,
            "tool_name": self.tool_name,
            "adapter_name": self.adapter_name,
            "state": self.state,
            "state_history": list(self.state_history),
            "lifecycle_states": list(self.lifecycle_states or self.state_history),
            "result_status": self.result_status,
            "risk_level": self.risk_level,
            "reason": _safe_text(self.reason, limit=260),
            "audit_ref": self.audit_ref,
            "error_code": self.error_code,
            "output_summary": _safe_text(self.output_summary, limit=420),
            "argument_keys": list(self.argument_keys),
            "arguments_digest": self.arguments_digest,
            "checkpoint_ref": self.checkpoint_ref,
            "resume_candidate": self.resume_candidate,
            "replay_event_refs": list(self.replay_event_refs),
            "evidence_refs": list(self.evidence_refs),
            "queued_at": self.queued_at,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "duration_ms": self.duration_ms,
        }


@dataclass(frozen=True)
class PlannerExecutionResumeEnvelope:
    """L6.35 断点续接信封。"""

    resume_mode: str
    can_resume: bool
    next_step_index: int
    next_step_ids: list[str] = field(default_factory=list)
    unresolved_failures: list[str] = field(default_factory=list)
    confirmation_ticket_ids: list[str] = field(default_factory=list)
    last_checkpoint_ref: str = ""
    recommended_action: str = ""
    stopped_reason: str = ""
    remaining_step_count: int = 0
    replay_required: bool = True
    direct_execution_now: bool = False
    mutates_budget: bool = False
    spawns_agent: bool = False
    touches_kernel: bool = False

    def __post_init__(self) -> None:
        if self.direct_execution_now or self.mutates_budget or self.spawns_agent or self.touches_kernel:
            raise ValueError("L6.35 resume envelope cannot execute, mutate budget, spawn agent or touch kernel")
        if self.next_step_index < 0:
            raise ValueError("L6.35 resume next_step_index must be non-negative")

    def public_dict(self) -> dict[str, Any]:
        return {
            "resume_mode": self.resume_mode,
            "can_resume": self.can_resume,
            "next_step_index": self.next_step_index,
            "next_step_ids": list(self.next_step_ids),
            "unresolved_failures": list(self.unresolved_failures),
            "confirmation_ticket_ids": list(self.confirmation_ticket_ids),
            "last_checkpoint_ref": self.last_checkpoint_ref,
            "recommended_action": _safe_text(self.recommended_action, limit=360),
            "stopped_reason": self.stopped_reason,
            "remaining_step_count": self.remaining_step_count,
            "replay_required": self.replay_required,
            "direct_execution_now": self.direct_execution_now,
            "mutates_budget": self.mutates_budget,
            "spawns_agent": self.spawns_agent,
            "touches_kernel": self.touches_kernel,
        }


@dataclass(frozen=True)
class PlannerExecutionReport:
    """L6.35 执行主链报告。"""

    task_id: str
    run_id: str
    source_version: str
    total_steps: int
    executed_steps: int
    succeeded_steps: int
    failed_steps: int
    blocked_steps: int
    confirmation_required_steps: int
    skipped_steps: int
    recovered_steps: int
    stopped_reason: str
    step_records: list[PlannerExecutionStepRecord]
    replay_events: list[PlannerReplayEvent]
    resume_envelope: PlannerExecutionResumeEnvelope
    started_at: float
    finished_at: float
    timeout_steps: int = 0
    progress_snapshots: list[dict[str, Any]] = field(default_factory=list)
    planner_context_digest: str = ""
    resumed_from_report_digest: str = ""
    original_total_steps: int = 0
    resumed_from_next_step_index: int = 0
    execution_first: bool = True
    runtime_governed: bool = True
    uses_long_chain_runner: bool = True
    uses_execution_spine: bool = True
    replayable: bool = True
    resumable: bool = True
    no_parallel_runtime: bool = True
    no_direct_adapter_call: bool = True
    no_registry_mutation: bool = True
    no_kernel_mutation: bool = True
    no_secret_read: bool = True
    no_provider_call: bool = True

    def __post_init__(self) -> None:
        required = (
            self.execution_first,
            self.runtime_governed,
            self.uses_long_chain_runner,
            self.uses_execution_spine,
            self.replayable,
            self.resumable,
            self.no_parallel_runtime,
            self.no_direct_adapter_call,
            self.no_registry_mutation,
            self.no_kernel_mutation,
            self.no_secret_read,
            self.no_provider_call,
        )
        if not all(required):
            raise ValueError("L6.35 planner execution report boundary flags must stay true")
        if self.total_steps != len(self.step_records):
            raise ValueError("L6.35 total_steps must equal step_records length")
        if self.timeout_steps != sum(1 for record in self.step_records if record.state == "timeout"):
            raise ValueError("L6.35 timeout_steps must match timeout step records")

    @property
    def status(self) -> str:
        if self.blocked_steps:
            return "blocked"
        if self.confirmation_required_steps:
            return "confirmation_required"
        if self.timeout_steps:
            return "timeout_with_resume"
        if self.failed_steps:
            return "failed_with_resume"
        if self.executed_steps == self.total_steps:
            return "completed"
        return "partial"

    @property
    def report_digest(self) -> str:
        return stable_planner_execution_digest(self)

    def public_dict(self) -> dict[str, Any]:
        payload = _report_public_payload(self)
        base_digest = stable_planner_execution_digest(payload)
        # L6.36：在不改变 L6.35 schema 兼容性的前提下，补充失败分类、恢复计划、回放报告与执行质量门结果。
        from .recovery_replay_quality import enrich_planner_execution_payload

        payload = enrich_planner_execution_payload(payload, source_report_digest=base_digest)
        payload["report_digest"] = stable_planner_execution_digest(payload)
        return payload


class PlannerExecutionController:
    """Planner 执行主链控制器。

    它只包裹现有 LongChainRunner，不直接调用 adapter。这样 L6.35 增强执行力，
    但不产生第二条执行链，也不污染内核。
    """

    def __init__(self) -> None:
        self.last_report: PlannerExecutionReport | None = None

    def reset(self) -> None:
        self.last_report = None

    def public_dict(self) -> dict[str, Any]:
        if self.last_report is None:
            return {"schema": PLANNER_EXECUTION_SCHEMA, "status": "empty", "message": "暂无 L6.35 Planner 执行主链报告。"}
        return self.last_report.public_dict()

    def export_json(self, path: str | Path) -> Path:
        target = Path(path).expanduser().resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.public_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        return target

    def build_planner_hint(self) -> str:
        if self.last_report is None:
            return ""
        payload = self.last_report.public_dict()
        resume = payload.get("resume_envelope", {})
        return (
            "L6.32 Planner 执行主链摘要（L6.35 状态机）："
            f"status={payload.get('status')}；executed={payload.get('executed_steps')}/{payload.get('total_steps')}；"
            f"timeout={payload.get('timeout_steps')}；stopped_reason={payload.get('stopped_reason')}；"
            f"resume_mode={resume.get('resume_mode')}；next_step_index={resume.get('next_step_index')}。"
        )[:1200]

    def execute(
        self,
        context: TurnContext,
        plan: list[ToolInvocation],
        runner: LongChainRunner,
        *,
        task_id: str,
        run_id: str,
        planner_context_digest: str = "",
        resumed_from_report_digest: str = "",
        original_total_steps: int = 0,
        resumed_from_next_step_index: int = 0,
    ) -> tuple[list[ToolResult], LongChainRunSummary, PlannerExecutionReport]:
        started_at = time()
        replay_events = _build_pre_events(plan)
        results = runner.run(context, plan)
        chain_summary = runner.last_summary
        finished_at = time()
        step_records, post_events = _build_step_records_and_post_events(plan, results, chain_summary, len(replay_events), started_at, finished_at)
        replay_events.extend(post_events)
        resume_envelope = _build_resume_envelope(plan, step_records, chain_summary, results)
        report = PlannerExecutionReport(
            task_id=task_id,
            run_id=run_id,
            source_version=SOURCE_VERSION,
            total_steps=len(plan),
            executed_steps=sum(1 for record in step_records if "running" in record.lifecycle_states or "running" in record.state_history),
            succeeded_steps=sum(1 for record in step_records if record.state == "succeeded"),
            failed_steps=sum(1 for record in step_records if record.state == "failed"),
            blocked_steps=sum(1 for record in step_records if record.state == "blocked"),
            confirmation_required_steps=sum(1 for record in step_records if record.state == "confirmation_required"),
            skipped_steps=sum(1 for record in step_records if record.state == "skipped"),
            recovered_steps=sum(1 for record in step_records if record.state == "recovered"),
            timeout_steps=sum(1 for record in step_records if record.state == "timeout"),
            stopped_reason=chain_summary.stopped_reason,
            planner_context_digest=planner_context_digest,
            resumed_from_report_digest=resumed_from_report_digest,
            original_total_steps=original_total_steps or len(plan),
            resumed_from_next_step_index=resumed_from_next_step_index,
            step_records=step_records,
            replay_events=replay_events,
            resume_envelope=resume_envelope,
            progress_snapshots=[snapshot.public_dict() for snapshot in getattr(chain_summary, "progress_snapshots", [])],
            started_at=started_at,
            finished_at=finished_at,
        )
        self.last_report = report
        return results, chain_summary, report

    def execute_resume(
        self,
        context: TurnContext,
        original_plan: list[ToolInvocation],
        runner: LongChainRunner,
        *,
        previous_report: PlannerExecutionReport | dict[str, Any],
        task_id: str,
        run_id: str,
        planner_context_digest: str = "",
    ) -> tuple[list[ToolResult], LongChainRunSummary, PlannerExecutionReport]:
        """从上一份 PlannerExecutionReport 的断点继续。

        只执行 ``previous_report.resume_envelope.next_step_index`` 之后的尾部计划，
        不重跑已成功步骤。该方法仍使用 LongChainRunner / ExecutionSpine，不直接调用 adapter。
        """
        payload = previous_report.public_dict() if isinstance(previous_report, PlannerExecutionReport) else dict(previous_report)
        resume = dict(payload.get("resume_envelope") or {})
        if not resume.get("can_resume"):
            raise ValueError("L6.35 previous report is not resumable")
        next_step_index = int(resume.get("next_step_index") or 1)
        if next_step_index < 1 or next_step_index > len(original_plan) + 1:
            raise ValueError("L6.35 resume next_step_index outside original plan")
        tail_plan = original_plan[next_step_index - 1 :]
        previous_digest = str(payload.get("report_digest") or stable_planner_execution_digest(payload))
        return self.execute(
            context,
            tail_plan,
            runner,
            task_id=task_id,
            run_id=run_id,
            planner_context_digest=planner_context_digest,
            resumed_from_report_digest=previous_digest,
            original_total_steps=len(original_plan),
            resumed_from_next_step_index=next_step_index,
        )


def stable_planner_execution_digest(report: PlannerExecutionReport | dict[str, Any]) -> str:
    if isinstance(report, PlannerExecutionReport):
        payload = _report_public_payload(report)
    else:
        payload = deepcopy(dict(report))
    payload.pop("report_digest", None)
    # 时间戳不参与稳定摘要，避免同一结构在不同运行时间下不可比较。
    payload.pop("started_at", None)
    payload.pop("finished_at", None)
    payload.pop("duration_seconds", None)
    for event in payload.get("replay_events", []) or []:
        if isinstance(event, dict):
            event.pop("timestamp", None)
    for record in payload.get("step_records", []) or []:
        if isinstance(record, dict):
            record.pop("queued_at", None)
            record.pop("started_at", None)
            record.pop("finished_at", None)
            record.pop("duration_ms", None)
    data = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(data.encode("utf-8")).hexdigest()[:24]


def _report_public_payload(report: PlannerExecutionReport) -> dict[str, Any]:
    return {
        "schema": PLANNER_EXECUTION_SCHEMA,
        "task_id": report.task_id,
        "run_id": report.run_id,
        "source_version": report.source_version,
        "status": report.status,
        "total_steps": report.total_steps,
        "original_total_steps": report.original_total_steps or report.total_steps,
        "resumed_from_next_step_index": report.resumed_from_next_step_index,
        "executed_steps": report.executed_steps,
        "succeeded_steps": report.succeeded_steps,
        "failed_steps": report.failed_steps,
        "timeout_steps": report.timeout_steps,
        "blocked_steps": report.blocked_steps,
        "confirmation_required_steps": report.confirmation_required_steps,
        "skipped_steps": report.skipped_steps,
        "recovered_steps": report.recovered_steps,
        "stopped_reason": report.stopped_reason,
        "planner_context_digest": report.planner_context_digest,
        "resumed_from_report_digest": report.resumed_from_report_digest,
        "step_records": [record.public_dict() for record in report.step_records],
        "replay_events": [event.public_dict() for event in report.replay_events],
        "replay_event_count": len(report.replay_events),
        "progress_snapshots": list(report.progress_snapshots),
        "progress_snapshot_count": len(report.progress_snapshots),
        "resume_envelope": report.resume_envelope.public_dict(),
        "started_at": report.started_at,
        "finished_at": report.finished_at,
        "duration_seconds": max(0.0, report.finished_at - report.started_at),
        "execution_first": report.execution_first,
        "runtime_governed": report.runtime_governed,
        "uses_long_chain_runner": report.uses_long_chain_runner,
        "uses_execution_spine": report.uses_execution_spine,
        "replayable": report.replayable,
        "resumable": report.resumable,
        "no_parallel_runtime": report.no_parallel_runtime,
        "no_direct_adapter_call": report.no_direct_adapter_call,
        "no_registry_mutation": report.no_registry_mutation,
        "no_kernel_mutation": report.no_kernel_mutation,
        "no_secret_read": report.no_secret_read,
        "no_provider_call": report.no_provider_call,
    }


def _build_pre_events(plan: list[ToolInvocation]) -> list[PlannerReplayEvent]:
    events: list[PlannerReplayEvent] = []
    event_index = 1
    for event_type, summary in (
        ("planned", "Planner step accepted into governed execution chain."),
        ("queued", "Step queued for LongChainRunner."),
        ("running", "Step scheduled for ExecutionSpine."),
    ):
        for step_index, invocation in enumerate(plan, start=1):
            events.append(
                PlannerReplayEvent(
                    event_index=event_index,
                    event_type=event_type,
                    step_index=step_index,
                    step_id=invocation.step_id,
                    tool_name=invocation.tool_name,
                    summary=summary,
                )
            )
            event_index += 1
    return events


def _build_step_records_and_post_events(
    plan: list[ToolInvocation],
    results: list[ToolResult],
    chain_summary: LongChainRunSummary,
    start_event_index: int,
    run_started_at: float,
    run_finished_at: float,
) -> tuple[list[PlannerExecutionStepRecord], list[PlannerReplayEvent]]:
    risk_classifier = RiskClassifier()
    result_by_step = {result.step_id: result for result in results}
    event_index = start_event_index + 1
    post_events: list[PlannerReplayEvent] = []
    records: list[PlannerExecutionStepRecord] = []
    checkpoint_by_step = {checkpoint.step_id: checkpoint for checkpoint in chain_summary.checkpoints}
    started_at_by_step = _derive_step_times(plan, results, run_started_at, run_finished_at)

    for step_index, invocation in enumerate(plan, start=1):
        result = result_by_step.get(invocation.step_id)
        step_started_at, step_finished_at = started_at_by_step.get(invocation.step_id, (0.0, 0.0))
        if result is None:
            final_state = "skipped"
            result_status = ToolResultStatus.SKIPPED.value
            history = ["planned", "skipped"]
            lifecycle = ["planned", "skipped"]
            summary = "前置步骤停止后，本步骤未执行，等待断点续接。"
            audit_ref = ""
            error_code = "not_executed_after_stop"
            step_started_at = 0.0
            step_finished_at = 0.0
        else:
            final_state = _state_from_result(result)
            result_status = result.status.value
            # 兼容旧测试：state_history 仍保留 planned/running/final；L6.35 完整生命周期放入 lifecycle_states。
            history = ["planned", "running", final_state]
            lifecycle = ["planned", "queued", "running", final_state]
            summary = result.output_summary
            audit_ref = result.audit_ref
            error_code = result.error_code

        risk, risk_reason = risk_classifier.classify(invocation)
        checkpoint = checkpoint_by_step.get(invocation.step_id)
        checkpoint_ref = f"checkpoint:{checkpoint.index}:{checkpoint.audit_ref or invocation.step_id}" if checkpoint else ""
        resume_candidate = final_state in {"failed", "blocked", "confirmation_required", "skipped", "timeout"}
        event_refs = [f"event:{idx}" for idx in _event_refs_for_step(step_index, len(plan), bool(result))]
        duration_ms = int(max(0.0, step_finished_at - step_started_at) * 1000) if step_started_at and step_finished_at else 0
        evidence_refs = []
        if audit_ref:
            evidence_refs.append(f"audit:{audit_ref}")
        if checkpoint_ref:
            evidence_refs.append(checkpoint_ref)
        record = PlannerExecutionStepRecord(
            step_index=step_index,
            step_id=invocation.step_id,
            parent_step_id=str(invocation.arguments.get("parent_step_id") or ""),
            source_plan_id=str(invocation.arguments.get("source_plan_id") or ""),
            tool_name=invocation.tool_name,
            adapter_name=invocation.tool_name,
            state=final_state,
            state_history=history,
            lifecycle_states=lifecycle,
            result_status=result_status,
            risk_level=risk.value,
            reason=risk_reason,
            audit_ref=audit_ref,
            error_code=error_code,
            output_summary=summary,
            argument_keys=sorted(str(key) for key in invocation.arguments.keys()),
            arguments_digest=_arguments_digest(invocation.arguments),
            checkpoint_ref=checkpoint_ref,
            resume_candidate=resume_candidate,
            replay_event_refs=event_refs,
            queued_at=step_started_at if result is not None else 0.0,
            started_at=step_started_at,
            finished_at=step_finished_at,
            duration_ms=duration_ms,
            evidence_refs=evidence_refs,
        )
        records.append(record)
        post_events.append(
            PlannerReplayEvent(
                event_index=event_index,
                event_type=final_state,
                step_index=step_index,
                step_id=invocation.step_id,
                tool_name=invocation.tool_name,
                status=result_status,
                audit_ref=audit_ref,
                error_code=error_code,
                summary=summary,
            )
        )
        event_index += 1

    return records, post_events


def _build_resume_envelope(
    plan: list[ToolInvocation],
    step_records: list[PlannerExecutionStepRecord],
    chain_summary: LongChainRunSummary,
    results: list[ToolResult],
) -> PlannerExecutionResumeEnvelope:
    stopped_reason = chain_summary.stopped_reason
    last_checkpoint_ref = ""
    if chain_summary.checkpoints:
        last_checkpoint = chain_summary.checkpoints[-1]
        last_checkpoint_ref = f"checkpoint:{last_checkpoint.index}:{last_checkpoint.audit_ref or last_checkpoint.step_id}"

    confirmation_ticket_ids: list[str] = []
    unresolved_failures: list[str] = []
    for result in results:
        if result.status is ToolResultStatus.CONFIRMATION_REQUIRED:
            ticket_id = result.data.get("ticket_id") or (result.data.get("ticket") or {}).get("ticket_id")
            if ticket_id:
                confirmation_ticket_ids.append(str(ticket_id))
        if result.status in {ToolResultStatus.FAILED, ToolResultStatus.BLOCKED, ToolResultStatus.TIMEOUT} or _is_timeout_result(result):
            unresolved_failures.append(f"{result.tool_name}:{result.error_code or result.status.value}")

    candidate = next((record for record in step_records if record.resume_candidate), None)
    if candidate is None:
        return PlannerExecutionResumeEnvelope(
            resume_mode="completed",
            can_resume=False,
            next_step_index=len(plan) + 1,
            next_step_ids=[],
            last_checkpoint_ref=last_checkpoint_ref,
            recommended_action="任务链已完成，无需断点续接。",
            stopped_reason=stopped_reason,
            remaining_step_count=0,
            replay_required=False,
        )

    remaining = [record.step_id for record in step_records if record.step_index >= candidate.step_index]
    if candidate.state == "confirmation_required":
        mode = "await_confirmation"
        action = "等待用户确认票据；确认后仍经 Registry / Adapter / Audit 执行。"
        can_resume = bool(confirmation_ticket_ids)
    elif candidate.state == "blocked":
        mode = "blocked_replan"
        action = "命中硬边界，停止本链并要求 Planner 重新规划。"
        can_resume = False
    elif candidate.state == "timeout":
        mode = "recover_timeout_step"
        action = "从超时步骤开始重试，或拆分该步骤后续接剩余步骤。"
        can_resume = True
    elif candidate.state == "failed":
        mode = "recover_failed_step"
        action = "从失败步骤开始重试或先生成修复计划，再续接剩余步骤。"
        can_resume = True
    else:
        mode = "resume_from_next_step"
        action = "从第一个未执行步骤继续。"
        can_resume = True

    return PlannerExecutionResumeEnvelope(
        resume_mode=mode,
        can_resume=can_resume,
        next_step_index=candidate.step_index,
        next_step_ids=remaining[:20],
        unresolved_failures=unresolved_failures[:20],
        confirmation_ticket_ids=confirmation_ticket_ids[:20],
        last_checkpoint_ref=last_checkpoint_ref,
        recommended_action=action,
        stopped_reason=stopped_reason,
        remaining_step_count=len(remaining),
        replay_required=True,
    )


def _state_from_result(result: ToolResult) -> str:
    if result.status is ToolResultStatus.OK:
        return "succeeded"
    if _is_timeout_result(result):
        return "timeout"
    if result.status is ToolResultStatus.FAILED:
        return "failed"
    if result.status is ToolResultStatus.BLOCKED:
        return "blocked"
    if result.status is ToolResultStatus.CONFIRMATION_REQUIRED:
        return "confirmation_required"
    if result.status is ToolResultStatus.SKIPPED:
        return "skipped"
    return "failed"


def _is_timeout_result(result: ToolResult) -> bool:
    return result.status is ToolResultStatus.TIMEOUT or str(result.error_code).lower() in {"timeout", "step_timeout", "adapter_timeout"}


def _event_refs_for_step(step_index: int, total_steps: int, has_result: bool) -> list[int]:
    refs = [step_index, total_steps + step_index]
    if has_result:
        refs.append((total_steps * 3) + step_index)
    return refs


def _derive_step_times(
    plan: list[ToolInvocation],
    results: list[ToolResult],
    run_started_at: float,
    run_finished_at: float,
) -> dict[str, tuple[float, float]]:
    if not results:
        return {}
    total_window = max(run_finished_at - run_started_at, 0.000001)
    slot = total_window / max(len(results), 1)
    times: dict[str, tuple[float, float]] = {}
    for offset, result in enumerate(results):
        started = run_started_at + (slot * offset)
        finished = run_started_at + (slot * (offset + 1))
        times[result.step_id] = (started, finished)
    return times


def _arguments_digest(arguments: dict[str, Any]) -> str:
    try:
        safe = json.dumps(_sanitize_args(arguments), ensure_ascii=False, sort_keys=True, default=str)
    except TypeError:
        safe = str(sorted(arguments.keys()))
    return hashlib.sha256(safe.encode("utf-8")).hexdigest()[:16]


def _sanitize_args(arguments: dict[str, Any]) -> dict[str, Any]:
    sanitized: dict[str, Any] = {}
    for key, value in arguments.items():
        text = _safe_text(value, limit=120)
        if _looks_sensitive(str(key)) or _looks_sensitive(text):
            sanitized[str(key)] = "[REDACTED]"
        else:
            sanitized[str(key)] = text
    return sanitized


def _safe_text(value: Any, *, limit: int = 500) -> str:
    return redact_text(str(value or ""))[:limit]


def _looks_sensitive(value: str) -> bool:
    lowered = value.lower()
    return any(term in lowered for term in ("api_key", "apikey", "authorization", "bearer", "token", "secret", "password", "credential"))
