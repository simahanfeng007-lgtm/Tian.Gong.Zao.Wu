"""L6.39 P0 系统接入二：Memory / Audit / Recovery / QualityGate。

本模块只在 ``tiangong_agent_runtime`` 外壳层工作，把四个执行支撑系统压缩为
Planner 可消费的 ``MemoryRoute / AuditEvidence / RecoveryTicket / QualityEvidence / Report``。
真实执行仍由 L6.37 冻结执行链负责：``RuntimeEntry → PlannerExecutionController →
LongChainRunner → ExecutionSpine``。

边界：
- 不修改 ``tiangong_kernel``；
- 不新增第二 Runtime；
- 不写入长期记忆，不注入原始记忆正文；
- 不篡改审计，不删除审计，只读取安全摘要；
- 不执行补丁、不派生子智能体、不修改预算；
- 不覆盖质量门裁决，不自动放行发布。
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from time import time
from typing import Any

from tiangong_agent_shell.safe_logging import redact_text, sanitize_mapping

from .tool_invocation import ToolInvocation
from .tool_result import ToolResult, ToolResultStatus
from .turn_context import TurnContext

L6_39_SCHEMA = "tiangong.l6_39.p0_system_integration_two.v1"
L6_39_SOURCE_VERSION = "L6.39-P0-memory-audit-recovery-qualitygate"
SENSITIVE_PATTERN = re.compile(
    r"(?i)(api[_-]?key|authorization|bearer|token|secret|password|credential)\s*[:=]\s*[^\s,;]+"
)


@dataclass(frozen=True)
class MemoryRecallRoute:
    """Memory 接入路由。

    只把当前进程内的安全摘要变成 Planner 提示，不写 L2/L3/L5 记忆，不注入原始正文。
    """

    route_id: str
    snapshot_ref: str
    session_records: int
    recent_summaries: list[str] = field(default_factory=list)
    planner_hint: str = ""
    planner_consumable: bool = True
    summary_only: bool = True
    no_raw_memory_body: bool = True
    no_direct_context_injection: bool = True
    no_long_term_write: bool = True
    no_memory_deletion: bool = True
    writes_l2_fact: bool = False
    mutates_memory_store: bool = False

    def __post_init__(self) -> None:
        required = (
            self.planner_consumable,
            self.summary_only,
            self.no_raw_memory_body,
            self.no_direct_context_injection,
            self.no_long_term_write,
            self.no_memory_deletion,
        )
        if not all(required):
            raise ValueError("MemoryRecallRoute must remain summary-only and planner-consumable")
        if self.writes_l2_fact or self.mutates_memory_store:
            raise ValueError("MemoryRecallRoute cannot write facts or mutate memory store")

    def public_dict(self) -> dict[str, Any]:
        return {
            "route_id": self.route_id,
            "snapshot_ref": self.snapshot_ref,
            "session_records": self.session_records,
            "recent_summaries": list(self.recent_summaries),
            "planner_hint": self.planner_hint,
            "planner_consumable": self.planner_consumable,
            "summary_only": self.summary_only,
            "no_raw_memory_body": self.no_raw_memory_body,
            "no_direct_context_injection": self.no_direct_context_injection,
            "no_long_term_write": self.no_long_term_write,
            "no_memory_deletion": self.no_memory_deletion,
            "writes_l2_fact": self.writes_l2_fact,
            "mutates_memory_store": self.mutates_memory_store,
        }


@dataclass(frozen=True)
class AuditEvidenceEnvelope:
    """Audit 接入证据包。只读取安全摘要，不改写审计链。"""

    envelope_id: str
    event_count: int
    recent_events: list[dict[str, Any]] = field(default_factory=list)
    status_counts: dict[str, int] = field(default_factory=dict)
    risk_counts: dict[str, int] = field(default_factory=dict)
    evidence_refs: list[str] = field(default_factory=list)
    planner_hint: str = ""
    planner_consumable: bool = True
    summary_only: bool = True
    append_only_projection: bool = True
    no_audit_delete: bool = True
    no_audit_rewrite: bool = True
    no_full_prompt: bool = True
    no_plain_secret: bool = True
    mutates_audit_log: bool = False

    def __post_init__(self) -> None:
        required = (
            self.planner_consumable,
            self.summary_only,
            self.append_only_projection,
            self.no_audit_delete,
            self.no_audit_rewrite,
            self.no_full_prompt,
            self.no_plain_secret,
        )
        if not all(required):
            raise ValueError("AuditEvidenceEnvelope boundary flags must remain true")
        if self.mutates_audit_log:
            raise ValueError("AuditEvidenceEnvelope cannot mutate audit log")

    def public_dict(self) -> dict[str, Any]:
        return {
            "envelope_id": self.envelope_id,
            "event_count": self.event_count,
            "recent_events": [dict(item) for item in self.recent_events],
            "status_counts": dict(self.status_counts),
            "risk_counts": dict(self.risk_counts),
            "evidence_refs": list(self.evidence_refs),
            "planner_hint": self.planner_hint,
            "planner_consumable": self.planner_consumable,
            "summary_only": self.summary_only,
            "append_only_projection": self.append_only_projection,
            "no_audit_delete": self.no_audit_delete,
            "no_audit_rewrite": self.no_audit_rewrite,
            "no_full_prompt": self.no_full_prompt,
            "no_plain_secret": self.no_plain_secret,
            "mutates_audit_log": self.mutates_audit_log,
        }


@dataclass(frozen=True)
class RecoveryResumeTicket:
    """Recovery 接入票据。只给恢复续接建议，不执行补丁或派生任务。"""

    ticket_id: str
    source_report_ref: str
    failure_count: int
    resume_plan_count: int
    next_actions: list[str] = field(default_factory=list)
    requires_human_confirmation: bool = False
    planner_hint: str = ""
    planner_consumable: bool = True
    recovery_path_ready: bool = True
    no_patch_execution: bool = True
    no_auto_agent_spawn: bool = True
    no_budget_mutation: bool = True
    no_tool_invocation: bool = True
    no_kernel_mutation: bool = True
    applies_patch: bool = False
    spawns_agent: bool = False
    mutates_budget: bool = False
    invokes_tool: bool = False

    def __post_init__(self) -> None:
        required = (
            self.planner_consumable,
            self.recovery_path_ready,
            self.no_patch_execution,
            self.no_auto_agent_spawn,
            self.no_budget_mutation,
            self.no_tool_invocation,
            self.no_kernel_mutation,
        )
        if not all(required):
            raise ValueError("RecoveryResumeTicket boundary flags must remain true")
        if self.applies_patch or self.spawns_agent or self.mutates_budget or self.invokes_tool:
            raise ValueError("RecoveryResumeTicket cannot execute recovery side effects")

    def public_dict(self) -> dict[str, Any]:
        return {
            "ticket_id": self.ticket_id,
            "source_report_ref": self.source_report_ref,
            "failure_count": self.failure_count,
            "resume_plan_count": self.resume_plan_count,
            "next_actions": list(self.next_actions),
            "requires_human_confirmation": self.requires_human_confirmation,
            "planner_hint": self.planner_hint,
            "planner_consumable": self.planner_consumable,
            "recovery_path_ready": self.recovery_path_ready,
            "no_patch_execution": self.no_patch_execution,
            "no_auto_agent_spawn": self.no_auto_agent_spawn,
            "no_budget_mutation": self.no_budget_mutation,
            "no_tool_invocation": self.no_tool_invocation,
            "no_kernel_mutation": self.no_kernel_mutation,
            "applies_patch": self.applies_patch,
            "spawns_agent": self.spawns_agent,
            "mutates_budget": self.mutates_budget,
            "invokes_tool": self.invokes_tool,
        }


@dataclass(frozen=True)
class QualityGateEvidence:
    """QualityGate 接入证据。

    它引用已有质量门状态。若质量门未运行，则只阻断发布/打包宣称，不阻断继续开发。
    """

    evidence_id: str
    gate_status: str
    decision: str
    allow_continue: bool
    allow_package: bool
    severity_counts: dict[str, int] = field(default_factory=dict)
    issue_count: int = 0
    release_blocked_until_pass: bool = True
    planner_hint: str = ""
    planner_consumable: bool = True
    does_not_override_quality_gate: bool = True
    no_test_execution: bool = True
    no_release_auto_approval: bool = True
    no_kernel_mutation: bool = True
    overrides_quality_gate: bool = False
    auto_approves_release: bool = False
    executes_tests: bool = False

    def __post_init__(self) -> None:
        required = (
            self.planner_consumable,
            self.does_not_override_quality_gate,
            self.no_test_execution,
            self.no_release_auto_approval,
            self.no_kernel_mutation,
        )
        if not all(required):
            raise ValueError("QualityGateEvidence boundary flags must remain true")
        if self.overrides_quality_gate or self.auto_approves_release or self.executes_tests:
            raise ValueError("QualityGateEvidence cannot override gate, approve release or execute tests")

    def public_dict(self) -> dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "gate_status": self.gate_status,
            "decision": self.decision,
            "allow_continue": self.allow_continue,
            "allow_package": self.allow_package,
            "severity_counts": dict(self.severity_counts),
            "issue_count": self.issue_count,
            "release_blocked_until_pass": self.release_blocked_until_pass,
            "planner_hint": self.planner_hint,
            "planner_consumable": self.planner_consumable,
            "does_not_override_quality_gate": self.does_not_override_quality_gate,
            "no_test_execution": self.no_test_execution,
            "no_release_auto_approval": self.no_release_auto_approval,
            "no_kernel_mutation": self.no_kernel_mutation,
            "overrides_quality_gate": self.overrides_quality_gate,
            "auto_approves_release": self.auto_approves_release,
            "executes_tests": self.executes_tests,
        }


@dataclass(frozen=True)
class L639P0IntegrationReport:
    """Memory / Audit / Recovery / QualityGate 四系统接入总报告。"""

    schema: str
    generated_at: float
    status: str
    summary: str
    memory: MemoryRecallRoute | None = None
    audit: AuditEvidenceEnvelope | None = None
    recovery: RecoveryResumeTicket | None = None
    quality_gate: QualityGateEvidence | None = None
    report_digest: str = ""
    planner_consumable: bool = True
    runtime_governed: bool = True
    uses_planner_execution_controller: bool = True
    no_second_runtime: bool = True
    no_kernel_mutation: bool = True
    no_memory_write: bool = True
    no_audit_mutation: bool = True
    no_recovery_execution: bool = True
    no_quality_gate_override: bool = True

    def __post_init__(self) -> None:
        required = (
            self.planner_consumable,
            self.runtime_governed,
            self.uses_planner_execution_controller,
            self.no_second_runtime,
            self.no_kernel_mutation,
            self.no_memory_write,
            self.no_audit_mutation,
            self.no_recovery_execution,
            self.no_quality_gate_override,
        )
        if not all(required):
            raise ValueError("L6.39 P0 report boundary flags must remain true")

    def public_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "source_version": L6_39_SOURCE_VERSION,
            "generated_at": self.generated_at,
            "status": self.status,
            "summary": self.summary,
            "memory": self.memory.public_dict() if self.memory else None,
            "audit": self.audit.public_dict() if self.audit else None,
            "recovery": self.recovery.public_dict() if self.recovery else None,
            "quality_gate": self.quality_gate.public_dict() if self.quality_gate else None,
            "report_digest": self.report_digest,
            "planner_consumable": self.planner_consumable,
            "runtime_governed": self.runtime_governed,
            "uses_planner_execution_controller": self.uses_planner_execution_controller,
            "no_second_runtime": self.no_second_runtime,
            "no_kernel_mutation": self.no_kernel_mutation,
            "no_memory_write": self.no_memory_write,
            "no_audit_mutation": self.no_audit_mutation,
            "no_recovery_execution": self.no_recovery_execution,
            "no_quality_gate_override": self.no_quality_gate_override,
        }

    def summary_text(self) -> str:
        return (
            "L6.39 P0 系统接入二："
            f"status={self.status}；memory={self.memory is not None}；audit={self.audit is not None}；"
            f"recovery={self.recovery is not None}；quality_gate={self.quality_gate is not None}；"
            "已接入 PlannerExecutionController 统一执行链，不新增 Runtime，不改内核。"
        )

    def markdown_report(self) -> str:
        payload = self.public_dict()
        lines = [
            "# 临渊者 L6.39 P0 系统接入二报告",
            "",
            f"- schema: `{self.schema}`",
            f"- status: `{self.status}`",
            f"- digest: `{self.report_digest}`",
            f"- runtime_governed: `{self.runtime_governed}`",
            f"- uses_planner_execution_controller: `{self.uses_planner_execution_controller}`",
            f"- no_kernel_mutation: `{self.no_kernel_mutation}`",
            "",
            "## 四系统状态",
            "",
            f"- Memory: `{payload['memory']['route_id'] if payload.get('memory') else 'missing'}`",
            f"- Audit: `{payload['audit']['envelope_id'] if payload.get('audit') else 'missing'}`",
            f"- Recovery: `{payload['recovery']['ticket_id'] if payload.get('recovery') else 'missing'}`",
            f"- QualityGate: `{payload['quality_gate']['evidence_id'] if payload.get('quality_gate') else 'missing'}`",
            "",
            "## 硬边界",
            "",
            "- Memory 只输出安全摘要路由，不写长期记忆，不注入原始正文。",
            "- Audit 只读取安全摘要，不删除、不重写、不伪造审计。",
            "- Recovery 只输出续接票据，不执行补丁、不派生子智能体、不改预算。",
            "- QualityGate 只引用裁决证据，不自动放行发布，不覆盖质量门。",
        ]
        return "\n".join(lines)


class L639P0SystemIntegrationBridge:
    """L6.39 四系统接入桥。"""

    def __init__(self) -> None:
        self.memory: MemoryRecallRoute | None = None
        self.audit: AuditEvidenceEnvelope | None = None
        self.recovery: RecoveryResumeTicket | None = None
        self.quality_gate: QualityGateEvidence | None = None
        self._last_report: L639P0IntegrationReport | None = None

    @property
    def last_report(self) -> L639P0IntegrationReport | None:
        return self._last_report

    def reset(self) -> None:
        self.memory = None
        self.audit = None
        self.recovery = None
        self.quality_gate = None
        self._last_report = None

    def build_memory(
        self,
        *,
        context_snapshot: dict[str, Any] | None = None,
        notes: str = "",
        max_items: int = 5,
    ) -> MemoryRecallRoute:
        source = context_snapshot or {}
        recent = source.get("recent") if isinstance(source, dict) else None
        summaries: list[str] = []
        for item in (recent or [])[: max(1, min(int(max_items), 20))]:
            if not isinstance(item, dict):
                continue
            status = _safe_text(item.get("status"), 60)
            intent = _safe_text(item.get("intent"), 100)
            summary = _safe_text(item.get("summary"), 260)
            if status or intent or summary:
                summaries.append(f"{status or 'unknown'} | {intent or 'runtime_task'} | {summary}"[:420])
        if not summaries:
            note = _safe_text(notes, 260) or "暂无可用上下文记忆摘要，保持空路由。"
            summaries = [note]
        session_records = int(source.get("session_records") or len(summaries)) if isinstance(source, dict) else len(summaries)
        planner_hint = _safe_text(source.get("planner_hint") if isinstance(source, dict) else "", 700)
        if not planner_hint:
            planner_hint = "Memory 接入：仅提供最近任务安全摘要，不注入原始正文，不写长期记忆。"
        route = MemoryRecallRoute(
            route_id=_ref("memory_route", session_records, summaries, notes),
            snapshot_ref=_ref("context_snapshot", session_records, summaries),
            session_records=session_records,
            recent_summaries=summaries,
            planner_hint=planner_hint,
        )
        self.memory = route
        self._last_report = self._build_report()
        return route

    def build_audit(
        self,
        *,
        audit_events: list[dict[str, Any]] | None = None,
        notes: str = "",
        max_events: int = 20,
    ) -> AuditEvidenceEnvelope:
        limit = max(1, min(int(max_events), 80))
        clean_events: list[dict[str, Any]] = []
        for event in (audit_events or [])[-limit:]:
            if not isinstance(event, dict):
                continue
            clean_events.append(_safe_mapping(event, limit=500))
        status_counts = _count_by(clean_events, "output_status", fallback="status")
        risk_counts = _count_by(clean_events, "risk_level")
        evidence_refs = [str(item.get("audit_id") or item.get("audit_ref") or _ref("audit_event", item)) for item in clean_events[-limit:]]
        if not clean_events and notes:
            evidence_refs = [_ref("audit_note", notes)]
        hint = (
            f"Audit 接入：读取 {len(clean_events)} 条安全摘要；"
            "只作为证据引用进入 Planner，不删除、不重写、不包含明文凭证。"
        )
        envelope = AuditEvidenceEnvelope(
            envelope_id=_ref("audit_evidence", clean_events, notes),
            event_count=len(clean_events),
            recent_events=clean_events,
            status_counts=status_counts,
            risk_counts=risk_counts,
            evidence_refs=evidence_refs,
            planner_hint=hint,
        )
        self.audit = envelope
        self._last_report = self._build_report()
        return envelope

    def build_recovery(
        self,
        *,
        recovery_report: dict[str, Any] | None = None,
        notes: str = "",
        max_items: int = 6,
    ) -> RecoveryResumeTicket:
        source = recovery_report or {}
        failure_count = int(source.get("failure_signal_count") or len(source.get("failure_signals") or []) or 0) if isinstance(source, dict) else 0
        resume_count = int(source.get("resume_plan_count") or len(source.get("resume_plans") or []) or 0) if isinstance(source, dict) else 0
        actions: list[str] = []
        for item in (source.get("resume_plans") or [])[: max(1, min(int(max_items), 20))] if isinstance(source, dict) else []:
            if not isinstance(item, dict):
                continue
            action = _safe_text(item.get("next_action") or item.get("planner_hint") or item.get("summary"), 360)
            if action:
                actions.append(action)
        if not actions:
            actions.append(_safe_text(notes, 300) or "无显式失败时，保持预防性续接：诊断→最小修复建议→复测→父链回流。")
        requires_human = False
        for item in (source.get("failure_signals") or []) if isinstance(source, dict) else []:
            if isinstance(item, dict) and bool(item.get("requires_human_confirmation")):
                requires_human = True
                break
        if not requires_human:
            requires_human = any(str(item.get("severity", "")).upper() == "P0" for item in (source.get("failure_signals") or []) if isinstance(item, dict)) if isinstance(source, dict) else False
        ticket = RecoveryResumeTicket(
            ticket_id=_ref("recovery_resume_ticket", source.get("report_digest") if isinstance(source, dict) else "", actions, notes),
            source_report_ref=_safe_text(source.get("report_digest") if isinstance(source, dict) else "", 120) or _ref("recovery_report", source),
            failure_count=failure_count,
            resume_plan_count=resume_count,
            next_actions=actions,
            requires_human_confirmation=requires_human,
            planner_hint="Recovery 接入：只提供恢复续接票据；补丁、派生、预算变更和工具执行仍回到 Runtime 治理链。",
        )
        self.recovery = ticket
        self._last_report = self._build_report()
        return ticket

    def build_quality_gate(
        self,
        *,
        quality_gate_report: dict[str, Any] | None = None,
        notes: str = "",
    ) -> QualityGateEvidence:
        source = quality_gate_report or {}
        status = _safe_text(source.get("status") if isinstance(source, dict) else "", 80) or "empty"
        decision = _safe_text(source.get("decision") if isinstance(source, dict) else "", 80)
        if not decision:
            decision = "not_evaluated" if status == "empty" else status
        allow_continue = bool(source.get("allow_continue", True)) if isinstance(source, dict) else True
        allow_package = bool(source.get("allow_package", False)) if isinstance(source, dict) else False
        issues = source.get("issues") if isinstance(source, dict) else []
        issue_count = len(issues) if isinstance(issues, list) else 0
        severity_counts = dict(source.get("severity_counts") or {}) if isinstance(source, dict) else {}
        release_blocked = not bool(allow_package and decision in {"pass", "warn"})
        if decision == "not_evaluated":
            release_blocked = True
            allow_continue = True
            allow_package = False
        hint = (
            f"QualityGate 接入：decision={decision}; allow_continue={allow_continue}; "
            f"allow_package={allow_package}; release_blocked_until_pass={release_blocked}。"
        )
        if notes:
            hint += f" 备注：{_safe_text(notes, 180)}"
        evidence = QualityGateEvidence(
            evidence_id=_ref("quality_gate_evidence", decision, severity_counts, issue_count, notes),
            gate_status=status,
            decision=decision,
            allow_continue=allow_continue,
            allow_package=allow_package,
            severity_counts={str(k): int(v) for k, v in severity_counts.items() if str(k)},
            issue_count=issue_count,
            release_blocked_until_pass=release_blocked,
            planner_hint=hint,
        )
        self.quality_gate = evidence
        self._last_report = self._build_report()
        return evidence

    def build_report(self, *, notes: str = "") -> L639P0IntegrationReport:
        if self.memory is None:
            self.build_memory(notes=notes)
        if self.audit is None:
            self.build_audit(notes=notes)
        if self.recovery is None:
            self.build_recovery(notes=notes)
        if self.quality_gate is None:
            self.build_quality_gate(notes=notes)
        self._last_report = self._build_report(notes=notes)
        return self._last_report

    def public_dict(self) -> dict[str, Any]:
        if self._last_report is None:
            return {"schema": L6_39_SCHEMA, "status": "empty", "message": "暂无 L6.39 P0 系统接入二报告。"}
        return self._last_report.public_dict()

    def export_json(self, path: str | Path) -> Path:
        target = Path(path).expanduser().resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.public_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        return target

    def build_planner_hint(self) -> str:
        if self._last_report is None:
            return ""
        payload = self._last_report.public_dict()
        return (
            "L6.39 P0 接入二摘要："
            f"status={payload.get('status')}；memory={bool(payload.get('memory'))}；"
            f"audit={bool(payload.get('audit'))}；recovery={bool(payload.get('recovery'))}；"
            f"quality_gate={bool(payload.get('quality_gate'))}；"
            "四系统均只能输出安全摘要/证据/票据/质量引用并进入 PlannerExecutionController。"
        )[:1200]

    def _build_report(self, *, notes: str = "") -> L639P0IntegrationReport:
        present = [self.memory is not None, self.audit is not None, self.recovery is not None, self.quality_gate is not None]
        status = "p0_systems_two_ready" if all(present) else "partial"
        missing = [name for name, ok in zip(("memory", "audit", "recovery", "quality_gate"), present) if not ok]
        safe_notes = _safe_text(notes, 500)
        summary = "Memory / Audit / Recovery / QualityGate 已按 L6.37 冻结执行链接入。" if not missing else f"P0 接入二部分完成，缺失：{', '.join(missing)}。"
        if safe_notes:
            summary += f" 备注：{safe_notes}"
        report = L639P0IntegrationReport(
            schema=L6_39_SCHEMA,
            generated_at=time(),
            status=status,
            summary=summary,
            memory=self.memory,
            audit=self.audit,
            recovery=self.recovery,
            quality_gate=self.quality_gate,
        )
        return L639P0IntegrationReport(
            schema=report.schema,
            generated_at=report.generated_at,
            status=report.status,
            summary=report.summary,
            memory=report.memory,
            audit=report.audit,
            recovery=report.recovery,
            quality_gate=report.quality_gate,
            report_digest=stable_l6_39_digest(report.public_dict()),
        )



def build_l6_39_memory_adapter(bridge: L639P0SystemIntegrationBridge, context_memory_source: Any):
    def adapter(invocation: ToolInvocation, context: TurnContext) -> ToolResult:
        try:
            max_items = int(invocation.arguments.get("max_items") or invocation.arguments.get("max_records") or 5)
            route = bridge.build_memory(
                context_snapshot=_context_memory_snapshot(context_memory_source, limit=max_items),
                notes=str(invocation.arguments.get("notes") or invocation.arguments.get("manual_notes") or ""),
                max_items=max_items,
            )
        except (TypeError, ValueError) as exc:
            return ToolResult(invocation.step_id, invocation.tool_name, ToolResultStatus.FAILED, f"L6.39 Memory 接入失败：{exc}", error_code="l6_39_memory_failed")
        return ToolResult(
            step_id=invocation.step_id,
            tool_name=invocation.tool_name,
            status=ToolResultStatus.OK,
            output_summary="L6.39 Memory 接入完成：MemoryRecallRoute 已生成；只输出安全摘要，不写长期记忆，不注入原始正文。",
            data=route.public_dict(),
        )

    return adapter



def build_l6_39_audit_adapter(bridge: L639P0SystemIntegrationBridge, audit_source: Any):
    def adapter(invocation: ToolInvocation, context: TurnContext) -> ToolResult:
        try:
            max_events = int(invocation.arguments.get("max_events") or invocation.arguments.get("max_items") or 20)
            envelope = bridge.build_audit(
                audit_events=_audit_events(audit_source, limit=max_events),
                notes=str(invocation.arguments.get("notes") or invocation.arguments.get("manual_notes") or ""),
                max_events=max_events,
            )
        except (TypeError, ValueError) as exc:
            return ToolResult(invocation.step_id, invocation.tool_name, ToolResultStatus.FAILED, f"L6.39 Audit 接入失败：{exc}", error_code="l6_39_audit_failed")
        return ToolResult(
            step_id=invocation.step_id,
            tool_name=invocation.tool_name,
            status=ToolResultStatus.OK,
            output_summary="L6.39 Audit 接入完成：AuditEvidenceEnvelope 已生成；只读取安全摘要，不删除、不重写、不伪造审计。",
            data=envelope.public_dict(),
        )

    return adapter



def build_l6_39_recovery_adapter(bridge: L639P0SystemIntegrationBridge, recovery_source: Any):
    def adapter(invocation: ToolInvocation, context: TurnContext) -> ToolResult:
        try:
            ticket = bridge.build_recovery(
                recovery_report=_public_dict(recovery_source),
                notes=str(invocation.arguments.get("notes") or invocation.arguments.get("manual_notes") or ""),
                max_items=int(invocation.arguments.get("max_items") or 6),
            )
        except (TypeError, ValueError) as exc:
            return ToolResult(invocation.step_id, invocation.tool_name, ToolResultStatus.FAILED, f"L6.39 Recovery 接入失败：{exc}", error_code="l6_39_recovery_failed")
        return ToolResult(
            step_id=invocation.step_id,
            tool_name=invocation.tool_name,
            status=ToolResultStatus.OK,
            output_summary="L6.39 Recovery 接入完成：RecoveryResumeTicket 已生成；不执行补丁、不派生子智能体、不改预算。",
            data=ticket.public_dict(),
        )

    return adapter



def build_l6_39_quality_gate_adapter(bridge: L639P0SystemIntegrationBridge, quality_gate_source: Any):
    def adapter(invocation: ToolInvocation, context: TurnContext) -> ToolResult:
        try:
            evidence = bridge.build_quality_gate(
                quality_gate_report=_public_dict(quality_gate_source),
                notes=str(invocation.arguments.get("notes") or invocation.arguments.get("manual_notes") or ""),
            )
        except (TypeError, ValueError) as exc:
            return ToolResult(invocation.step_id, invocation.tool_name, ToolResultStatus.FAILED, f"L6.39 QualityGate 接入失败：{exc}", error_code="l6_39_quality_gate_failed")
        return ToolResult(
            step_id=invocation.step_id,
            tool_name=invocation.tool_name,
            status=ToolResultStatus.OK,
            output_summary="L6.39 QualityGate 接入完成：QualityGateEvidence 已生成；不覆盖质量门，不自动放行发布。",
            data=evidence.public_dict(),
        )

    return adapter



def build_l6_39_p0_report_adapter(bridge: L639P0SystemIntegrationBridge):
    def adapter(invocation: ToolInvocation, context: TurnContext) -> ToolResult:
        try:
            report = bridge.build_report(notes=str(invocation.arguments.get("notes") or invocation.arguments.get("manual_notes") or ""))
        except (TypeError, ValueError) as exc:
            return ToolResult(invocation.step_id, invocation.tool_name, ToolResultStatus.FAILED, f"L6.39 P0 接入二总报告生成失败：{exc}", error_code="l6_39_p0_report_failed")
        return ToolResult(
            step_id=invocation.step_id,
            tool_name=invocation.tool_name,
            status=ToolResultStatus.OK,
            output_summary=report.summary_text(),
            data=report.public_dict(),
        )

    return adapter



def stable_l6_39_digest(payload: Any) -> str:
    data = json.loads(json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str))
    if isinstance(data, dict):
        data.pop("report_digest", None)
        data.pop("generated_at", None)
    text = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:24]



def _context_memory_snapshot(source: Any, *, limit: int) -> dict[str, Any]:
    if source is None:
        return {}
    if hasattr(source, "snapshot"):
        value = source.snapshot(limit=limit)
        if hasattr(value, "public_dict"):
            return dict(value.public_dict())
        if isinstance(value, dict):
            return dict(value)
    return _public_dict(source)



def _audit_events(source: Any, *, limit: int) -> list[dict[str, Any]]:
    if source is None:
        return []
    if hasattr(source, "recent_summary"):
        value = source.recent_summary(limit=limit)
        if isinstance(value, list):
            return [dict(item) for item in value if isinstance(item, dict)]
    value = _public_dict(source)
    events = value.get("events") or value.get("recent_events") or []
    return [dict(item) for item in events if isinstance(item, dict)][-limit:]



def _public_dict(source: Any) -> dict[str, Any]:
    if source is None:
        return {}
    if hasattr(source, "public_dict"):
        value = source.public_dict()
        return dict(value) if isinstance(value, dict) else {}
    if isinstance(source, dict):
        return dict(source)
    return {}



def _safe_text(value: Any, limit: int = 240) -> str:
    text = str(value or "").replace("\x00", "").strip()
    text = SENSITIVE_PATTERN.sub(lambda match: f"{match.group(1)}=<redacted>", text)
    text = redact_text(text)
    return text[:limit]



def _safe_mapping(value: dict[str, Any], *, limit: int = 500) -> dict[str, Any]:
    clean = sanitize_mapping(value)
    result: dict[str, Any] = {}
    allowed = {
        "audit_id",
        "timestamp",
        "step_id",
        "tool_name",
        "risk_level",
        "permit_status",
        "output_status",
        "output_summary",
        "artifacts",
        "error_code",
        "audit_ref",
        "status",
    }
    for key, item in clean.items():
        if str(key) not in allowed:
            continue
        if isinstance(item, list):
            result[str(key)] = [_safe_text(x, 180) for x in item[:8]]
        elif isinstance(item, dict):
            result[str(key)] = {str(k): _safe_text(v, 180) for k, v in list(item.items())[:12]}
        else:
            result[str(key)] = _safe_text(item, limit)
    return result



def _count_by(items: list[dict[str, Any]], key: str, *, fallback: str = "") -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        value = str(item.get(key) or (item.get(fallback) if fallback else "") or "unknown")
        value = _safe_text(value, 80) or "unknown"
        counts[value] = counts.get(value, 0) + 1
    return counts



def _ref(prefix: str, *parts: Any) -> str:
    safe = json.dumps(parts, ensure_ascii=False, sort_keys=True, default=str)
    digest = hashlib.sha256(safe.encode("utf-8")).hexdigest()[:16]
    return f"{prefix}:{digest}"
