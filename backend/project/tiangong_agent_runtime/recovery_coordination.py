"""L6.29 自修复 / 多智能体 / 预算联动外壳。

本模块把失败诊断、修复候选、Handoff 摘要、预算状态和续接计划压缩成一条
Planner 可直接消费的恢复路径。它只做协调外壳，不自动派生子智能体、不执行补丁、
不改写预算、不写文件、不注册 Tool/Skill、不触碰 tiangong_kernel。

执行力口径：遇到失败时，优先给出下一步可执行恢复路径；治理口径：真正执行仍必须
回到 Runtime registry / permit / audit / quality gate 链路。
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from time import time
from typing import Any

from tiangong_agent_shell.safe_logging import redact_text

from .tool_invocation import ToolInvocation
from .tool_result import ToolResult, ToolResultStatus
from .turn_context import TurnContext

RECOVERY_COORDINATION_SCHEMA = "tiangong.l6_29.recovery_coordination.v1"
SENSITIVE_PATTERN = re.compile(
    r"(?i)(api[_-]?key|authorization|bearer|token|secret|password|credential)\s*[:=]\s*[^\s,;]+"
)
SENSITIVE_WORDS = ("api_key", "apikey", "authorization", "bearer", "token", "secret", "password", "credential")


@dataclass(frozen=True)
class FailureSignal:
    """可公开的失败信号，只保留安全摘要。"""

    signal_ref: str
    source_ref: str
    source_kind: str
    severity: str
    status: str
    summary: str
    error_code: str = ""
    suggested_recovery_mode: str = "diagnose_repair_retest_resume"
    blocks_release: bool = True
    requires_human_confirmation: bool = False

    def public_dict(self) -> dict[str, Any]:
        return {
            "signal_ref": self.signal_ref,
            "source_ref": self.source_ref,
            "source_kind": self.source_kind,
            "severity": self.severity,
            "status": self.status,
            "summary": self.summary,
            "error_code": self.error_code,
            "suggested_recovery_mode": self.suggested_recovery_mode,
            "blocks_release": self.blocks_release,
            "requires_human_confirmation": self.requires_human_confirmation,
        }


@dataclass(frozen=True)
class RepairCandidate:
    """恢复候选，不直接应用修复。"""

    candidate_ref: str
    failure_ref: str
    title: str
    priority: str
    planner_hint: str
    recommended_steps: list[dict[str, Any]] = field(default_factory=list)
    validation_steps: list[str] = field(default_factory=list)
    applies_patch_now: bool = False
    writes_file_now: bool = False
    bypasses_runtime: bool = False

    def __post_init__(self) -> None:
        if self.applies_patch_now or self.writes_file_now or self.bypasses_runtime:
            raise ValueError("L6.29 RepairCandidate cannot apply/write/bypass runtime")

    def public_dict(self) -> dict[str, Any]:
        return {
            "candidate_ref": self.candidate_ref,
            "failure_ref": self.failure_ref,
            "title": self.title,
            "priority": self.priority,
            "planner_hint": self.planner_hint,
            "recommended_steps": list(self.recommended_steps),
            "validation_steps": list(self.validation_steps),
            "applies_patch_now": self.applies_patch_now,
            "writes_file_now": self.writes_file_now,
            "bypasses_runtime": self.bypasses_runtime,
        }


@dataclass(frozen=True)
class HandoffDigest:
    """多智能体交接摘要。只是任务边界，不派生子智能体。"""

    handoff_ref: str
    failure_ref: str
    suggested_role: str
    task_boundary: str
    input_summary: str
    expected_output: str
    parent_resume_contract: str
    no_recursive_spawn: bool = True
    no_direct_tool_execution: bool = True
    spawn_now: bool = False

    def __post_init__(self) -> None:
        if not self.no_recursive_spawn or not self.no_direct_tool_execution or self.spawn_now:
            raise ValueError("L6.29 HandoffDigest cannot spawn agents or bypass tool governance")

    def public_dict(self) -> dict[str, Any]:
        return {
            "handoff_ref": self.handoff_ref,
            "failure_ref": self.failure_ref,
            "suggested_role": self.suggested_role,
            "task_boundary": self.task_boundary,
            "input_summary": self.input_summary,
            "expected_output": self.expected_output,
            "parent_resume_contract": self.parent_resume_contract,
            "no_recursive_spawn": self.no_recursive_spawn,
            "no_direct_tool_execution": self.no_direct_tool_execution,
            "spawn_now": self.spawn_now,
        }


@dataclass(frozen=True)
class BudgetUpdate:
    """预算状态投影。不改写真实预算。"""

    budget_ref: str
    budget_pool: str
    consumed_steps: int
    planned_recovery_steps: int
    remaining_step_hint: int
    failure_budget_state: str
    continuation_policy: str
    projected_only: bool = True
    mutates_budget: bool = False

    def __post_init__(self) -> None:
        if not self.projected_only or self.mutates_budget:
            raise ValueError("L6.29 BudgetUpdate is projection-only and cannot mutate budget")

    def public_dict(self) -> dict[str, Any]:
        return {
            "budget_ref": self.budget_ref,
            "budget_pool": self.budget_pool,
            "consumed_steps": self.consumed_steps,
            "planned_recovery_steps": self.planned_recovery_steps,
            "remaining_step_hint": self.remaining_step_hint,
            "failure_budget_state": self.failure_budget_state,
            "continuation_policy": self.continuation_policy,
            "projected_only": self.projected_only,
            "mutates_budget": self.mutates_budget,
        }


@dataclass(frozen=True)
class ResumePlan:
    """下一轮可续接计划。"""

    plan_ref: str
    title: str
    next_action: str
    ordered_steps: list[str] = field(default_factory=list)
    preflight_checks: list[str] = field(default_factory=list)
    stop_conditions: list[str] = field(default_factory=list)
    quality_gate_policy: str = "repair_then_compileall_then_targeted_pytest_before_delivery"
    ready_for_next_run: bool = True
    direct_execution_now: bool = False
    touches_kernel: bool = False

    def __post_init__(self) -> None:
        if not self.ready_for_next_run or self.direct_execution_now or self.touches_kernel:
            raise ValueError("L6.29 ResumePlan must be next-run ready but not directly executing or touching kernel")

    def public_dict(self) -> dict[str, Any]:
        return {
            "plan_ref": self.plan_ref,
            "title": self.title,
            "next_action": self.next_action,
            "ordered_steps": list(self.ordered_steps),
            "preflight_checks": list(self.preflight_checks),
            "stop_conditions": list(self.stop_conditions),
            "quality_gate_policy": self.quality_gate_policy,
            "ready_for_next_run": self.ready_for_next_run,
            "direct_execution_now": self.direct_execution_now,
            "touches_kernel": self.touches_kernel,
        }


@dataclass(frozen=True)
class RecoveryCoordinationReport:
    schema: str
    generated_at: float
    status: str
    summary: str
    failure_signals: list[FailureSignal] = field(default_factory=list)
    repair_candidates: list[RepairCandidate] = field(default_factory=list)
    handoff_digests: list[HandoffDigest] = field(default_factory=list)
    budget_updates: list[BudgetUpdate] = field(default_factory=list)
    resume_plans: list[ResumePlan] = field(default_factory=list)
    source_schemas: list[str] = field(default_factory=list)
    notes_used: bool = False
    execution_first: bool = True
    shell_only: bool = True
    recovery_path_ready: bool = True
    multi_agent_projection_only: bool = True
    budget_projection_only: bool = True
    uses_runtime_governance: bool = True
    blocks_only_a5_or_release: bool = True
    spawns_agent: bool = False
    invokes_tool: bool = False
    applies_patch: bool = False
    writes_file: bool = False
    mutates_budget: bool = False
    registers_tool: bool = False
    registers_skill: bool = False
    modifies_kernel: bool = False
    report_digest: str = ""

    def __post_init__(self) -> None:
        required = (
            self.execution_first,
            self.shell_only,
            self.recovery_path_ready,
            self.multi_agent_projection_only,
            self.budget_projection_only,
            self.uses_runtime_governance,
            self.blocks_only_a5_or_release,
        )
        if not all(required):
            raise ValueError("L6.29 recovery coordination must remain execution-first, shell-only and governance-routed")
        forbidden = (
            self.spawns_agent,
            self.invokes_tool,
            self.applies_patch,
            self.writes_file,
            self.mutates_budget,
            self.registers_tool,
            self.registers_skill,
            self.modifies_kernel,
        )
        if any(forbidden):
            raise ValueError("L6.29 recovery coordination cannot spawn/execute/write/mutate/register/touch kernel")

    @property
    def failure_signal_count(self) -> int:
        return len(self.failure_signals)

    @property
    def repair_candidate_count(self) -> int:
        return len(self.repair_candidates)

    @property
    def handoff_digest_count(self) -> int:
        return len(self.handoff_digests)

    @property
    def budget_update_count(self) -> int:
        return len(self.budget_updates)

    @property
    def resume_plan_count(self) -> int:
        return len(self.resume_plans)

    def public_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "generated_at": self.generated_at,
            "status": self.status,
            "summary": self.summary,
            "failure_signals": [item.public_dict() for item in self.failure_signals],
            "repair_candidates": [item.public_dict() for item in self.repair_candidates],
            "handoff_digests": [item.public_dict() for item in self.handoff_digests],
            "budget_updates": [item.public_dict() for item in self.budget_updates],
            "resume_plans": [item.public_dict() for item in self.resume_plans],
            "source_schemas": list(self.source_schemas),
            "notes_used": self.notes_used,
            "execution_first": self.execution_first,
            "shell_only": self.shell_only,
            "recovery_path_ready": self.recovery_path_ready,
            "multi_agent_projection_only": self.multi_agent_projection_only,
            "budget_projection_only": self.budget_projection_only,
            "uses_runtime_governance": self.uses_runtime_governance,
            "blocks_only_a5_or_release": self.blocks_only_a5_or_release,
            "failure_signal_count": self.failure_signal_count,
            "repair_candidate_count": self.repair_candidate_count,
            "handoff_digest_count": self.handoff_digest_count,
            "budget_update_count": self.budget_update_count,
            "resume_plan_count": self.resume_plan_count,
            "spawns_agent": self.spawns_agent,
            "invokes_tool": self.invokes_tool,
            "applies_patch": self.applies_patch,
            "writes_file": self.writes_file,
            "mutates_budget": self.mutates_budget,
            "registers_tool": self.registers_tool,
            "registers_skill": self.registers_skill,
            "modifies_kernel": self.modifies_kernel,
            "report_digest": self.report_digest,
        }

    def summary_text(self) -> str:
        return (
            "L6.29 自修复/多智能体/预算联动："
            f"status={self.status}；failures={self.failure_signal_count}；"
            f"repairs={self.repair_candidate_count}；handoffs={self.handoff_digest_count}；"
            f"budgets={self.budget_update_count}；resume={self.resume_plan_count}。{self.summary}"
        )

    def markdown_report(self) -> str:
        lines = [
            "# 临渊者 L6.29 自修复 / 多智能体 / 预算联动报告",
            "",
            f"- schema: `{self.schema}`",
            f"- status: `{self.status}`",
            f"- execution_first: `{self.execution_first}`",
            f"- shell_only: `{self.shell_only}`",
            f"- report_digest: `{self.report_digest}`",
            "",
            "## 摘要",
            "",
            self.summary,
            "",
            "## 失败信号",
            "",
        ]
        if not self.failure_signals:
            lines.append("未发现显式失败信号，已生成预防性续接路径。")
        for item in self.failure_signals:
            lines.append(f"- `{item.signal_ref}` [{item.severity}] {item.summary}")
        lines.extend(["", "## 修复候选", ""])
        for item in self.repair_candidates:
            lines.append(f"- `{item.candidate_ref}` {item.title}: {item.planner_hint}")
        lines.extend(["", "## Handoff 摘要", ""])
        for item in self.handoff_digests:
            lines.append(f"- `{item.handoff_ref}` {item.suggested_role}: {item.task_boundary}")
        lines.extend(["", "## 预算更新", ""])
        for item in self.budget_updates:
            lines.append(f"- `{item.budget_ref}` pool={item.budget_pool} remaining_hint={item.remaining_step_hint} policy={item.continuation_policy}")
        lines.extend(["", "## 续接计划", ""])
        for item in self.resume_plans:
            lines.append(f"- `{item.plan_ref}` {item.next_action}")
        lines.append("")
        lines.append("> L6.29 只给恢复协调与续接计划；补丁、子智能体派生、预算变更和工具调用仍必须回到 Runtime 治理链。")
        return "\n".join(lines)


class RecoveryCoordinationBridge:
    """Runtime 外壳层恢复协调器。"""

    def __init__(self) -> None:
        self._last_report: RecoveryCoordinationReport | None = None

    @property
    def last_report(self) -> RecoveryCoordinationReport | None:
        return self._last_report

    def reset(self) -> None:
        self._last_report = None

    def build(
        self,
        *,
        diagnosis_report: dict[str, Any] | None = None,
        quality_gate_report: dict[str, Any] | None = None,
        project_repair_report: dict[str, Any] | None = None,
        learning_convergence_report: dict[str, Any] | None = None,
        delivery_standardization_report: dict[str, Any] | None = None,
        audit_events: list[dict[str, Any]] | None = None,
        notes: str = "",
        max_items: int = 12,
        step_budget: int = 20,
    ) -> RecoveryCoordinationReport:
        limit = max(1, min(int(max_items), 40))
        safe_notes = _safe_text(notes, limit=700)
        diagnosis = diagnosis_report or {}
        quality = quality_gate_report or {}
        repair = project_repair_report or {}
        learning = learning_convergence_report or {}
        delivery = delivery_standardization_report or {}
        audit = audit_events or []

        failure_signals = _build_failure_signals(diagnosis, quality, repair, delivery, audit, safe_notes, limit=limit)
        if not failure_signals and safe_notes:
            failure_signals.append(
                FailureSignal(
                    signal_ref=_ref("failure", "manual", safe_notes),
                    source_ref="manual:l6_29_notes",
                    source_kind="manual_notes",
                    severity="P2",
                    status="attention_required",
                    summary=f"用户要求进入恢复协调链：{safe_notes}",
                    error_code="manual_recovery_request",
                    blocks_release=False,
                )
            )
        if not failure_signals:
            failure_signals.append(
                FailureSignal(
                    signal_ref=_ref("failure", "preventive", time()),
                    source_ref="runtime:l6_29_preventive",
                    source_kind="preventive_recovery",
                    severity="P3",
                    status="preventive",
                    summary="未发现显式失败，生成预防性长链续接与预算投影。",
                    error_code="none",
                    blocks_release=False,
                )
            )

        repair_candidates = _build_repair_candidates(failure_signals, repair, learning, limit=limit)
        handoff_digests = _build_handoff_digests(failure_signals, repair_candidates, limit=limit)
        budget_updates = _build_budget_updates(failure_signals, repair_candidates, step_budget=step_budget)
        resume_plans = _build_resume_plans(failure_signals, repair_candidates, handoff_digests, budget_updates, limit=limit)
        status = "recovery_coordination_ready" if resume_plans else "recovery_coordination_empty"
        source_schemas = _source_schemas(diagnosis, quality, repair, learning, delivery)
        summary = _summary(failure_signals, repair_candidates, handoff_digests, budget_updates, resume_plans)
        report = RecoveryCoordinationReport(
            schema=RECOVERY_COORDINATION_SCHEMA,
            generated_at=time(),
            status=status,
            summary=summary,
            failure_signals=failure_signals,
            repair_candidates=repair_candidates,
            handoff_digests=handoff_digests,
            budget_updates=budget_updates,
            resume_plans=resume_plans,
            source_schemas=source_schemas,
            notes_used=bool(safe_notes),
        )
        report = RecoveryCoordinationReport(**{**report.__dict__, "report_digest": stable_recovery_coordination_digest(report)})
        self._last_report = report
        return report

    def public_dict(self) -> dict[str, Any]:
        if self._last_report is None:
            return {
                "schema": RECOVERY_COORDINATION_SCHEMA,
                "status": "empty",
                "message": "暂无 L6.29 恢复协调报告，请先执行 /recovery-build。",
            }
        return self._last_report.public_dict()

    def export_json(self, path: str | Path) -> Path:
        target = Path(path).expanduser().resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.public_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        return target

    def build_planner_hint(self) -> str:
        if self._last_report is None or self._last_report.status == "empty":
            return ""
        report = self._last_report
        plans = "; ".join(item.next_action for item in report.resume_plans[:3]) or "无"
        failures = ", ".join(item.error_code or item.status for item in report.failure_signals[:3]) or "无"
        return (
            "最近 L6.29 恢复协调："
            f"status={report.status}; failures={report.failure_signal_count}; repairs={report.repair_candidate_count}; "
            f"handoffs={report.handoff_digest_count}; budget_projection_only={report.budget_projection_only}; "
            f"resume={plans}; failure_codes={failures}; shell_only=True; spawns_agent=False; applies_patch=False"
        )[:1600]


def build_recovery_coordination_adapter(
    bridge: RecoveryCoordinationBridge,
    diagnostics: Any,
    quality_gate: Any,
    project_repair: Any,
    learning_convergence: Any,
    delivery_standardization: Any,
    audit: Any,
):
    def recovery_coordination_adapter(invocation: ToolInvocation, context: TurnContext) -> ToolResult:
        try:
            report = bridge.build(
                diagnosis_report=diagnostics.public_dict(),
                quality_gate_report=quality_gate.public_dict(),
                project_repair_report=project_repair.public_dict(),
                learning_convergence_report=learning_convergence.public_dict(),
                delivery_standardization_report=delivery_standardization.public_dict(),
                audit_events=audit.recent_summary() if hasattr(audit, "recent_summary") else [],
                notes=str(invocation.arguments.get("notes") or invocation.arguments.get("manual_notes") or ""),
                max_items=int(invocation.arguments.get("max_items") or 12),
                step_budget=int(invocation.arguments.get("step_budget") or context.max_steps or 20),
            )
        except (TypeError, ValueError) as exc:
            return ToolResult(
                invocation.step_id,
                invocation.tool_name,
                ToolResultStatus.FAILED,
                f"恢复协调失败：{exc}",
                error_code="recovery_coordination_failed",
            )
        return ToolResult(
            step_id=invocation.step_id,
            tool_name=invocation.tool_name,
            status=ToolResultStatus.OK,
            output_summary=report.summary_text(),
            data=report.public_dict(),
        )

    return recovery_coordination_adapter


def stable_recovery_coordination_digest(report: RecoveryCoordinationReport) -> str:
    payload = report.public_dict()
    payload.pop("generated_at", None)
    payload.pop("report_digest", None)
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:16]


def _build_failure_signals(
    diagnosis: dict[str, Any],
    quality: dict[str, Any],
    repair: dict[str, Any],
    delivery: dict[str, Any],
    audit: list[dict[str, Any]],
    notes: str,
    *,
    limit: int,
) -> list[FailureSignal]:
    signals: list[FailureSignal] = []
    for item in _as_dicts(quality.get("issues")):
        severity = _safe_text(item.get("severity"), limit=20) or "P1"
        code = _safe_text(item.get("code"), limit=120) or "quality_issue"
        summary = _safe_text(item.get("message"), limit=520) or "质量门发现问题。"
        decision = _safe_text(quality.get("decision"), limit=80) or _safe_text(quality.get("status"), limit=80) or "quality_issue"
        signals.append(
            FailureSignal(
                signal_ref=_ref("failure", "quality", code, summary),
                source_ref=f"quality_gate:{code}",
                source_kind="quality_gate",
                severity=severity,
                status=decision,
                summary=summary,
                error_code=code,
                blocks_release=True,
                requires_human_confirmation=decision == "blocked" or severity == "P0",
            )
        )
        if len(signals) >= limit:
            return signals
    for item in _as_dicts(diagnosis.get("issues")):
        severity = _safe_text(item.get("severity"), limit=20) or "P2"
        if severity.upper() not in {"P0", "P1", "P2"}:
            continue
        code = _safe_text(item.get("code"), limit=120) or "diagnosis_issue"
        summary = _safe_text(item.get("message"), limit=520) or "工程诊断发现问题。"
        signals.append(
            FailureSignal(
                signal_ref=_ref("failure", "diagnosis", code, summary),
                source_ref=f"diagnosis:{code}",
                source_kind="engineering_diagnosis",
                severity=severity,
                status=_safe_text(diagnosis.get("status"), limit=80) or "needs_repair",
                summary=summary,
                error_code=code,
                blocks_release=severity.upper() in {"P0", "P1"},
                requires_human_confirmation=severity.upper() == "P0",
            )
        )
        if len(signals) >= limit:
            return signals
    for item in _as_dicts(delivery.get("todo_report")):
        priority = _safe_text(item.get("priority") or item.get("severity"), limit=20) or "P2"
        if priority.upper() not in {"P0", "P1", "P2"}:
            continue
        title = _safe_text(item.get("title") or item.get("summary"), limit=220) or "交付链待办"
        signals.append(
            FailureSignal(
                signal_ref=_ref("failure", "delivery", title),
                source_ref=f"delivery_todo:{title[:40]}",
                source_kind="delivery_standardization",
                severity=priority,
                status=_safe_text(delivery.get("status"), limit=80) or "todo",
                summary=title,
                error_code="delivery_todo",
                blocks_release=priority.upper() in {"P0", "P1"},
            )
        )
        if len(signals) >= limit:
            return signals
    if _safe_text(repair.get("status"), limit=80) in {"repair_plan_ready", "needs_repair"} and repair.get("patch_plan"):
        signals.append(
            FailureSignal(
                signal_ref=_ref("failure", "repair_plan", repair.get("status"), len(repair.get("patch_plan", []))),
                source_ref="project_repair:patch_plan",
                source_kind="project_repair_plan",
                severity="P2",
                status="repair_plan_available",
                summary="已有工程修复计划，可进入恢复协调与续接路径。",
                error_code="repair_plan_available",
                blocks_release=False,
            )
        )
    for event in _as_dicts(audit)[:limit]:
        status = _safe_text(event.get("status") or event.get("result_status"), limit=80)
        if status not in {"failed", "blocked", "confirmation_required"}:
            continue
        tool = _safe_text(event.get("tool_name") or event.get("tool"), limit=120) or "unknown_tool"
        signals.append(
            FailureSignal(
                signal_ref=_ref("failure", "audit", tool, status),
                source_ref=f"audit:{tool}",
                source_kind="audit_event",
                severity="P1" if status in {"failed", "blocked"} else "P2",
                status=status,
                summary=f"审计摘要显示 {tool} 状态为 {status}。",
                error_code=_safe_text(event.get("error_code"), limit=120) or status,
                blocks_release=status in {"failed", "blocked"},
                requires_human_confirmation=status in {"blocked", "confirmation_required"},
            )
        )
        if len(signals) >= limit:
            return signals
    return signals[:limit]


def _build_repair_candidates(failures: list[FailureSignal], repair: dict[str, Any], learning: dict[str, Any], *, limit: int) -> list[RepairCandidate]:
    candidates: list[RepairCandidate] = []
    patch_steps = _as_dicts(repair.get("patch_plan"))
    regressions = _as_dicts(repair.get("regression_hints"))
    cards = _as_dicts(learning.get("consumption_cards"))
    for failure in failures[:limit]:
        steps = []
        for raw in patch_steps[:4]:
            steps.append(
                {
                    "phase": _safe_text(raw.get("phase"), limit=80) or "repair",
                    "target_path": _safe_text(raw.get("target_path"), limit=240) or ".",
                    "operation": _safe_text(raw.get("operation"), limit=120) or "minimal_change_plan",
                    "risk_level": _safe_text(raw.get("risk_level"), limit=80) or "A3_when_applied",
                    "applies_now": False,
                }
            )
        if not steps:
            steps = [
                {"tool_name": "scan_project", "arguments": {"path": "."}, "reason": "刷新项目雷达。"},
                {"tool_name": "diagnose_project", "arguments": {"path": "."}, "reason": "重新归因失败。"},
                {"tool_name": "run_python_quality_check", "arguments": {"command": "compileall", "target": "."}, "reason": "先做语法层复测。"},
            ]
        validation = [
            f"{_safe_text(item.get('command'), limit=40) or 'compileall'}:{_safe_text(item.get('target'), limit=160) or '.'}"
            for item in regressions[:4]
        ] or ["compileall:.", "targeted_pytest_if_tests_exist"]
        card_hint = _safe_text(cards[0].get("immediate_next_action"), limit=320) if cards else "按项目修复计划执行最小补丁，再复测。"
        candidates.append(
            RepairCandidate(
                candidate_ref=_ref("repair", failure.signal_ref, card_hint),
                failure_ref=failure.signal_ref,
                title=f"恢复候选：{failure.error_code or failure.status}",
                priority="P0" if failure.severity.upper() == "P0" else "P1_execution" if failure.blocks_release else "P2_execution",
                planner_hint=card_hint,
                recommended_steps=steps,
                validation_steps=validation,
            )
        )
    return candidates[:limit]


def _build_handoff_digests(failures: list[FailureSignal], candidates: list[RepairCandidate], *, limit: int) -> list[HandoffDigest]:
    digests: list[HandoffDigest] = []
    for failure, candidate in zip(failures[:limit], candidates[:limit], strict=False):
        role = "工程修复子任务审阅员" if failure.blocks_release else "长链续接整理员"
        boundary = "只分析失败摘要、建议最小补丁与复测顺序，不直接写文件、不调用工具。"
        digests.append(
            HandoffDigest(
                handoff_ref=_ref("handoff", failure.signal_ref, candidate.candidate_ref),
                failure_ref=failure.signal_ref,
                suggested_role=role,
                task_boundary=boundary,
                input_summary=f"失败={failure.error_code or failure.status}；候选={candidate.title}；优先级={candidate.priority}。",
                expected_output="返回最小修复顺序、风险点、复测命令和父链续接摘要。",
                parent_resume_contract="父链接收 HandoffDigest 后必须回到 Runtime 计划/治理/审计链执行，不得递归派生。",
            )
        )
    return digests[:limit]


def _build_budget_updates(failures: list[FailureSignal], candidates: list[RepairCandidate], *, step_budget: int) -> list[BudgetUpdate]:
    consumed = min(max(len(failures), 1), max(step_budget, 1))
    planned = max(3, min(12, len(candidates) * 3 if candidates else 3))
    remaining = max(step_budget - consumed - planned, 0)
    if any(item.requires_human_confirmation for item in failures):
        state = "confirmation_or_block_required"
        policy = "stop_before_execution_until_user_confirms_or_boundary_fixed"
    elif any(item.blocks_release for item in failures):
        state = "repair_budget_required"
        policy = "continue_repair_with_small_batches_and_retest_after_each_patch"
    else:
        state = "healthy_or_preventive"
        policy = "continue_normal_long_chain_with_periodic_checkpoints"
    return [
        BudgetUpdate(
            budget_ref=_ref("budget", state, step_budget, planned),
            budget_pool="main_recovery_chain",
            consumed_steps=consumed,
            planned_recovery_steps=planned,
            remaining_step_hint=remaining,
            failure_budget_state=state,
            continuation_policy=policy,
        )
    ]


def _build_resume_plans(
    failures: list[FailureSignal],
    candidates: list[RepairCandidate],
    handoffs: list[HandoffDigest],
    budgets: list[BudgetUpdate],
    *,
    limit: int,
) -> list[ResumePlan]:
    plans: list[ResumePlan] = []
    budget_policy = budgets[0].continuation_policy if budgets else "continue_with_runtime_governance"
    for index, candidate in enumerate(candidates[:limit], start=1):
        handoff = handoffs[index - 1] if index - 1 < len(handoffs) else None
        failure = next((item for item in failures if item.signal_ref == candidate.failure_ref), failures[0])
        if failure.requires_human_confirmation:
            next_action = "先请求用户确认或修正治理边界，再恢复执行链。"
            stop = ["A5/blocked/confirmation_required 未解除", "缺少用户确认", "边界仍不清晰"]
        else:
            next_action = "按恢复候选生成最小补丁计划，执行前置检查，然后复测。"
            stop = ["质量门 blocked", "连续失败超过恢复预算", "目标路径触及 tiangong_kernel 或凭证路径"]
        ordered = [
            "刷新项目雷达与工程诊断",
            "读取失败摘要涉及的最小文件集",
            "生成最小补丁计划而非大面积重构",
            "运行 compileall，必要时运行 targeted pytest",
            "更新交付证据与恢复摘要",
        ]
        if handoff:
            ordered.insert(1, f"必要时把分析任务交给 {handoff.suggested_role}，但不自动派生。")
        plans.append(
            ResumePlan(
                plan_ref=_ref("resume", candidate.candidate_ref, budget_policy),
                title=f"恢复续接计划 {index}",
                next_action=next_action,
                ordered_steps=ordered,
                preflight_checks=["kernel hash baseline", "forbidden/secret scan before delivery", "Runtime governed mode", budget_policy],
                stop_conditions=stop,
            )
        )
    return plans[:limit]


def _summary(
    failures: list[FailureSignal],
    candidates: list[RepairCandidate],
    handoffs: list[HandoffDigest],
    budgets: list[BudgetUpdate],
    resumes: list[ResumePlan],
) -> str:
    blocking = sum(1 for item in failures if item.blocks_release)
    confirm = sum(1 for item in failures if item.requires_human_confirmation)
    return (
        f"已把失败信号压缩为恢复路径：failure={len(failures)}，blocking={blocking}，confirmation={confirm}，"
        f"repair_candidate={len(candidates)}，handoff_digest={len(handoffs)}，budget_projection={len(budgets)}，resume_plan={len(resumes)}。"
        "本阶段只生成协调外壳，真实执行仍走 Runtime 治理链。"
    )


def _source_schemas(*reports: dict[str, Any]) -> list[str]:
    schemas: list[str] = []
    for report in reports:
        if isinstance(report, dict):
            schema = _safe_text(report.get("schema"), limit=180)
            if schema and schema not in schemas:
                schemas.append(schema)
    return schemas


def _safe_text(value: Any, *, limit: int = 500) -> str:
    text = "" if value is None else str(value)
    text = redact_text(text)
    text = SENSITIVE_PATTERN.sub("[REDACTED]", text)
    for word in SENSITIVE_WORDS:
        text = re.sub(re.escape(word), "[REDACTED]", text, flags=re.IGNORECASE)
    text = " ".join(text.split())
    return text[:limit]


def _as_dicts(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _ref(prefix: str, *parts: Any) -> str:
    payload = json.dumps([_safe_text(part, limit=240) for part in parts], ensure_ascii=False, sort_keys=True)
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:12]
    return f"{prefix}:{digest}"
