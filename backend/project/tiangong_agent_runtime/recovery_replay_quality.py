"""L6.36 失败恢复、可回放与质量门贯通。

本模块只消费 PlannerExecutionReport 的安全公开摘要，把 L6.35 的执行证据
归一为 FailureTaxonomy / RecoveryPlan / ReplayReport / QualityGateResult。
它不执行工具、不读密钥、不修改注册表、不触碰 ``tiangong_kernel``。
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

L6_36_SCHEMA = "tiangong.l6_36.recovery_replay_quality.v1"
L6_36_CORPUS_SCHEMA = "tiangong.l6_36.replay_corpus.v1"
L6_36_SOURCE_VERSION = "L6.36-recovery-replay-quality-gate"

FAILURE_NEXT_ACTIONS = {
    "model_plan_invalid": "downgrade_to_rule_only_or_reprompt_plan_json",
    "risk_blocked": "stop_for_safety_and_replan",
    "confirmation_required": "ask_confirmation",
    "tool_failed": "retry_or_generate_repair_plan",
    "timeout": "split_step_or_retry_with_timeout_budget",
    "budget_exhausted": "resume_after_budget_review",
    "validation_failed": "run_repair_then_quality_gate",
    "delivery_failed": "repair_delivery_artifact_then_retry",
    "skipped_after_stop": "resume_from_next_step",
}

FAILURE_SEVERITY = {
    "model_plan_invalid": "P1",
    "risk_blocked": "P0",
    "confirmation_required": "P2",
    "tool_failed": "P1",
    "timeout": "P1",
    "budget_exhausted": "P1",
    "validation_failed": "P1",
    "delivery_failed": "P1",
    "skipped_after_stop": "P2",
}


@dataclass(frozen=True)
class FailureClassification:
    step_index: int
    step_id: str
    tool_name: str
    state: str
    status: str
    error_code: str
    failure_type: str
    severity: str
    next_action: str
    resume_candidate: bool = True
    evidence_refs: list[str] = field(default_factory=list)

    def public_dict(self) -> dict[str, Any]:
        return {
            "step_index": self.step_index,
            "step_id": self.step_id,
            "tool_name": self.tool_name,
            "state": self.state,
            "status": self.status,
            "error_code": self.error_code,
            "failure_type": self.failure_type,
            "severity": self.severity,
            "next_action": self.next_action,
            "resume_candidate": self.resume_candidate,
            "evidence_refs": list(self.evidence_refs),
        }


@dataclass(frozen=True)
class RecoveryPlan:
    schema: str
    mode: str
    can_resume: bool
    next_step_index: int
    recommended_action: str
    recovery_steps: list[str]
    stopped_reason: str = ""
    source_report_digest: str = ""
    failure_type_counts: dict[str, int] = field(default_factory=dict)
    unresolved_failures: list[str] = field(default_factory=list)
    confirmation_ticket_ids: list[str] = field(default_factory=list)
    last_checkpoint_ref: str = ""
    direct_execution_now: bool = False
    mutates_budget: bool = False
    spawns_agent: bool = False
    touches_kernel: bool = False

    def __post_init__(self) -> None:
        if self.direct_execution_now or self.mutates_budget or self.spawns_agent or self.touches_kernel:
            raise ValueError("L6.36 RecoveryPlan cannot execute, mutate budget, spawn agent or touch kernel")

    def public_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "mode": self.mode,
            "can_resume": self.can_resume,
            "next_step_index": self.next_step_index,
            "recommended_action": self.recommended_action,
            "recovery_steps": list(self.recovery_steps),
            "stopped_reason": self.stopped_reason,
            "source_report_digest": self.source_report_digest,
            "failure_type_counts": dict(self.failure_type_counts),
            "unresolved_failures": list(self.unresolved_failures),
            "confirmation_ticket_ids": list(self.confirmation_ticket_ids),
            "last_checkpoint_ref": self.last_checkpoint_ref,
            "direct_execution_now": self.direct_execution_now,
            "mutates_budget": self.mutates_budget,
            "spawns_agent": self.spawns_agent,
            "touches_kernel": self.touches_kernel,
        }


@dataclass(frozen=True)
class ReplayReport:
    schema: str
    reconstructable: bool
    event_order_ok: bool
    event_indexes_unique: bool
    step_terminal_events_ok: bool
    source_report_digest: str
    replay_event_count: int
    step_count: int
    missing_event_refs: list[str] = field(default_factory=list)
    final_status: str = ""

    def public_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "reconstructable": self.reconstructable,
            "event_order_ok": self.event_order_ok,
            "event_indexes_unique": self.event_indexes_unique,
            "step_terminal_events_ok": self.step_terminal_events_ok,
            "source_report_digest": self.source_report_digest,
            "replay_event_count": self.replay_event_count,
            "step_count": self.step_count,
            "missing_event_refs": list(self.missing_event_refs),
            "final_status": self.final_status,
        }


@dataclass(frozen=True)
class QualityGateResult:
    schema: str
    decision: str
    allow_continue: bool
    allow_package: bool
    summary: str
    source_report_digest: str
    checks: list[dict[str, Any]] = field(default_factory=list)
    issue_counts: dict[str, int] = field(default_factory=dict)
    recommended_actions: list[str] = field(default_factory=list)

    def public_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "decision": self.decision,
            "allow_continue": self.allow_continue,
            "allow_package": self.allow_package,
            "summary": self.summary,
            "source_report_digest": self.source_report_digest,
            "checks": list(self.checks),
            "issue_counts": dict(self.issue_counts),
            "recommended_actions": list(self.recommended_actions),
        }


@dataclass(frozen=True)
class ReplayCorpusCase:
    case_name: str
    status: str
    execution_status: str
    source_report_digest: str
    failure_types: list[str]
    recovery_mode: str
    quality_decision: str
    reconstructable: bool
    can_resume: bool
    next_action: str

    def public_dict(self) -> dict[str, Any]:
        return {
            "case_name": self.case_name,
            "status": self.status,
            "execution_status": self.execution_status,
            "source_report_digest": self.source_report_digest,
            "failure_types": list(self.failure_types),
            "recovery_mode": self.recovery_mode,
            "quality_decision": self.quality_decision,
            "reconstructable": self.reconstructable,
            "can_resume": self.can_resume,
            "next_action": self.next_action,
        }


@dataclass(frozen=True)
class ReplayCorpusReport:
    schema: str
    source_version: str
    ok: bool
    cases: list[ReplayCorpusCase]

    def public_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "source_version": self.source_version,
            "ok": self.ok,
            "case_count": len(self.cases),
            "passed_cases": sum(1 for case in self.cases if case.status == "passed"),
            "cases": [case.public_dict() for case in self.cases],
        }

    def export_json(self, path: str | Path) -> Path:
        target = Path(path).expanduser().resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.public_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        return target

    def markdown_report(self) -> str:
        lines = [
            "# 临渊者 L6.36 Replay Corpus 报告",
            "",
            f"- schema: `{self.schema}`",
            f"- source_version: `{self.source_version}`",
            f"- ok: `{self.ok}`",
            f"- cases: `{len(self.cases)}`",
            "",
            "## 用例",
            "",
        ]
        for case in self.cases:
            lines.append(
                f"- `{case.case_name}` status=`{case.status}` execution=`{case.execution_status}` "
                f"quality=`{case.quality_decision}` recovery=`{case.recovery_mode}` action=`{case.next_action}`"
            )
        lines.append("")
        lines.append("> L6.36 replay corpus 只使用 RuntimeEntry / PlannerExecutionController 公开摘要，不裸调工具、不读取密钥、不修改内核。")
        return "\n".join(lines)


def enrich_planner_execution_payload(payload: dict[str, Any], *, source_report_digest: str = "") -> dict[str, Any]:
    """给 PlannerExecutionReport 公开摘要添加 L6.36 贯通证据。"""

    enriched = dict(payload)
    source_digest = source_report_digest or str(payload.get("report_digest") or "")
    failure_classifications = classify_failures(payload)
    recovery_plan = build_recovery_plan(payload, failure_classifications=failure_classifications, source_report_digest=source_digest)
    replay_report = build_replay_report(payload, source_report_digest=source_digest)
    quality_gate = build_quality_gate_result(payload, failure_classifications=failure_classifications, replay_report=replay_report, source_report_digest=source_digest)
    enriched["l6_36"] = {
        "schema": L6_36_SCHEMA,
        "source_version": L6_36_SOURCE_VERSION,
        "source_report_digest": source_digest,
        "failure_classifications": [item.public_dict() for item in failure_classifications],
        "failure_type_counts": _count_failure_types(failure_classifications),
        "recovery_plan": recovery_plan.public_dict(),
        "replay_report": replay_report.public_dict(),
        "quality_gate_result": quality_gate.public_dict(),
        "execution_chain_ready": replay_report.reconstructable and quality_gate.decision in {"pass", "warn", "fail"},
        "no_direct_execution": True,
        "no_budget_mutation": True,
        "no_agent_spawn": True,
        "no_kernel_mutation": True,
    }
    return enriched


def classify_failures(report_payload: dict[str, Any]) -> list[FailureClassification]:
    records = list(report_payload.get("step_records") or [])
    stopped_reason = str(report_payload.get("stopped_reason") or "")
    classifications: list[FailureClassification] = []
    for record in records:
        if not isinstance(record, dict):
            continue
        state = str(record.get("state") or "")
        if state == "succeeded":
            continue
        failure_type = _failure_type_for_step(record, stopped_reason=stopped_reason)
        classifications.append(
            FailureClassification(
                step_index=int(record.get("step_index") or 0),
                step_id=str(record.get("step_id") or ""),
                tool_name=str(record.get("tool_name") or ""),
                state=state,
                status=str(record.get("result_status") or ""),
                error_code=str(record.get("error_code") or ""),
                failure_type=failure_type,
                severity=FAILURE_SEVERITY.get(failure_type, "P2"),
                next_action=FAILURE_NEXT_ACTIONS.get(failure_type, "resume_from_next_step"),
                resume_candidate=bool(record.get("resume_candidate", True)),
                evidence_refs=[str(item) for item in record.get("evidence_refs", [])][:12],
            )
        )
    if not records and str(report_payload.get("status") or "") in {"planner_failed", "invalid_plan", "model_plan_invalid"}:
        classifications.append(
            FailureClassification(
                step_index=0,
                step_id="planner",
                tool_name="model_suggest",
                state="failed",
                status="failed",
                error_code="invalid_plan_shape",
                failure_type="model_plan_invalid",
                severity="P1",
                next_action=FAILURE_NEXT_ACTIONS["model_plan_invalid"],
                resume_candidate=False,
            )
        )
    return classifications


def build_recovery_plan(
    report_payload: dict[str, Any],
    *,
    failure_classifications: list[FailureClassification] | None = None,
    source_report_digest: str = "",
) -> RecoveryPlan:
    failures = failure_classifications if failure_classifications is not None else classify_failures(report_payload)
    resume = dict(report_payload.get("resume_envelope") or {})
    failure_counts = _count_failure_types(failures)
    stopped_reason = str(report_payload.get("stopped_reason") or "")

    if not failures and str(report_payload.get("status") or "") == "completed":
        return RecoveryPlan(
            schema=L6_36_SCHEMA,
            mode="completed",
            can_resume=False,
            next_step_index=int(resume.get("next_step_index") or (int(report_payload.get("total_steps") or 0) + 1)),
            recommended_action="执行链已完成，无需恢复。",
            recovery_steps=[],
            stopped_reason=stopped_reason,
            source_report_digest=source_report_digest,
            failure_type_counts=failure_counts,
            last_checkpoint_ref=str(resume.get("last_checkpoint_ref") or ""),
        )

    primary = _primary_failure_type(failures)
    mode = str(resume.get("resume_mode") or _mode_for_failure_type(primary))
    can_resume = bool(resume.get("can_resume"))
    if primary == "risk_blocked":
        can_resume = False
        mode = "blocked_replan"
    elif primary == "confirmation_required":
        mode = "await_confirmation"
    elif primary in {"tool_failed", "timeout", "budget_exhausted", "validation_failed", "delivery_failed", "skipped_after_stop"}:
        can_resume = can_resume or bool(resume.get("next_step_ids"))

    recovery_steps = _recovery_steps_for(primary, can_resume=can_resume)
    return RecoveryPlan(
        schema=L6_36_SCHEMA,
        mode=mode,
        can_resume=can_resume,
        next_step_index=int(resume.get("next_step_index") or 1),
        recommended_action=str(resume.get("recommended_action") or FAILURE_NEXT_ACTIONS.get(primary, "resume_from_next_step")),
        recovery_steps=recovery_steps,
        stopped_reason=stopped_reason,
        source_report_digest=source_report_digest,
        failure_type_counts=failure_counts,
        unresolved_failures=[str(item) for item in resume.get("unresolved_failures", [])][:20],
        confirmation_ticket_ids=[str(item) for item in resume.get("confirmation_ticket_ids", [])][:20],
        last_checkpoint_ref=str(resume.get("last_checkpoint_ref") or ""),
    )


def build_replay_report(report_payload: dict[str, Any], *, source_report_digest: str = "") -> ReplayReport:
    events = [event for event in report_payload.get("replay_events", []) if isinstance(event, dict)]
    records = [record for record in report_payload.get("step_records", []) if isinstance(record, dict)]
    indexes = [int(event.get("event_index") or 0) for event in events]
    event_order_ok = indexes == sorted(indexes)
    event_indexes_unique = len(indexes) == len(set(indexes))
    events_by_step: dict[str, set[str]] = {}
    for event in events:
        step_id = str(event.get("step_id") or "")
        events_by_step.setdefault(step_id, set()).add(str(event.get("event_type") or ""))

    missing: list[str] = []
    for record in records:
        step_id = str(record.get("step_id") or "")
        expected = {"planned", "queued", "running", str(record.get("state") or "")}
        found = events_by_step.get(step_id, set())
        absent = sorted(item for item in expected if item and item not in found)
        if absent:
            missing.append(f"{step_id}:{','.join(absent)}")
    step_terminal_events_ok = not missing
    reconstructable = bool(events) and event_order_ok and event_indexes_unique and step_terminal_events_ok
    return ReplayReport(
        schema=L6_36_SCHEMA,
        reconstructable=reconstructable,
        event_order_ok=event_order_ok,
        event_indexes_unique=event_indexes_unique,
        step_terminal_events_ok=step_terminal_events_ok,
        source_report_digest=source_report_digest,
        replay_event_count=len(events),
        step_count=len(records),
        missing_event_refs=missing[:20],
        final_status=str(report_payload.get("status") or ""),
    )


def build_quality_gate_result(
    report_payload: dict[str, Any],
    *,
    failure_classifications: list[FailureClassification] | None = None,
    replay_report: ReplayReport | None = None,
    source_report_digest: str = "",
    quality_gate_verdict: dict[str, Any] | None = None,
) -> QualityGateResult:
    failures = failure_classifications if failure_classifications is not None else classify_failures(report_payload)
    replay = replay_report if replay_report is not None else build_replay_report(report_payload, source_report_digest=source_report_digest)
    checks: list[dict[str, Any]] = []
    checks.append({"name": "planner_report_has_steps", "status": "ok" if report_payload.get("step_records") else "failed"})
    checks.append({"name": "replay_events_reconstructable", "status": "ok" if replay.reconstructable else "failed"})
    checks.append({"name": "resume_envelope_present", "status": "ok" if report_payload.get("resume_envelope") else "failed"})
    checks.append({"name": "failure_taxonomy_complete", "status": "ok" if _failure_taxonomy_complete(report_payload, failures) else "failed"})
    if quality_gate_verdict:
        checks.append(
            {
                "name": "l6_18_quality_gate_verdict",
                "status": str(quality_gate_verdict.get("decision") or "unknown"),
                "allow_continue": bool(quality_gate_verdict.get("allow_continue")),
                "allow_package": bool(quality_gate_verdict.get("allow_package")),
            }
        )

    issue_counts = {"P0": 0, "P1": 0, "P2": 0, "P3": 0}
    for failure in failures:
        issue_counts[failure.severity] = issue_counts.get(failure.severity, 0) + 1
    if not replay.reconstructable:
        issue_counts["P1"] = issue_counts.get("P1", 0) + 1
    if not report_payload.get("resume_envelope"):
        issue_counts["P1"] = issue_counts.get("P1", 0) + 1

    if issue_counts.get("P0", 0) > 0 or str(report_payload.get("status") or "") == "blocked":
        decision = "blocked"
        allow_continue = False
        allow_package = False
        summary = "执行链质量门阻断：存在安全阻断或 P0 失败类型。"
    elif issue_counts.get("P1", 0) > 0:
        decision = "fail"
        allow_continue = True
        allow_package = False
        summary = "执行链质量门失败：存在可恢复失败、超时、验证缺口或回放证据缺失。"
    elif issue_counts.get("P2", 0) > 0:
        decision = "warn"
        allow_continue = True
        allow_package = True
        summary = "执行链质量门警告：存在确认等待或跳过步骤，允许续接但需披露。"
    else:
        decision = "pass"
        allow_continue = True
        allow_package = True
        summary = "执行链质量门通过：状态完成、回放可重建、恢复信封完整。"

    recommended = _recommended_actions_for_quality(decision, failures)
    return QualityGateResult(
        schema=L6_36_SCHEMA,
        decision=decision,
        allow_continue=allow_continue,
        allow_package=allow_package,
        summary=summary,
        source_report_digest=source_report_digest,
        checks=checks,
        issue_counts=issue_counts,
        recommended_actions=recommended,
    )


def run_l6_36_replay_corpus(workspace: str | Path, *, export_dir: str | Path | None = None) -> ReplayCorpusReport:
    """运行 L6.36 离线 replay corpus。

    只在给定工作区内构造小型文件与 RuntimeEntry 用例；不会触网、不会读取凭证、不会修改内核。
    """

    from tiangong_agent_shell.tool_bridge import ToolExecutionMode

    from .runtime_entry import RuntimeEntry
    from .tool_invocation import ToolInvocation

    root = Path(workspace).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    (root / "README.md").write_text("# L6.36 replay corpus\n", encoding="utf-8")
    (root / "demo.py").write_text("print('ok')\n", encoding="utf-8")

    case_plans: list[tuple[str, list[ToolInvocation]]] = [
        ("code_generation", [ToolInvocation("return_code", {"language": "python", "content": "print('ok')"})]),
        ("code_analysis", [ToolInvocation("return_analysis", {"content": "分析 demo.py 的执行意图。"})]),
        ("file_read", [ToolInvocation("list_dir", {"path": "."}), ToolInvocation("read_file", {"path": "README.md"})]),
        ("project_diagnosis", [ToolInvocation("scan_project", {"path": "."}), ToolInvocation("diagnose_project", {"path": "."})]),
        ("recoverable_failure", [ToolInvocation("read_file", {"path": "missing.txt"}), ToolInvocation("return_analysis", {"content": "should resume"})]),
        ("safety_blocked", [ToolInvocation("read_file", {"path": ".env"}), ToolInvocation("return_analysis", {"content": "after blocked"})]),
        ("confirmation_required", [ToolInvocation("write_workspace_file", {"path": str(root / "absolute.txt"), "content": "x"})]),
        ("delivery_package", [ToolInvocation("create_zip_package", {"source": ".", "target": "dist/l6_36_corpus.zip"})]),
        ("quality_compileall", [ToolInvocation("run_python_quality_check", {"command": "compileall", "target": ".", "timeout": 30})]),
    ]

    cases: list[ReplayCorpusCase] = []
    for case_name, plan in case_plans:
        runtime = RuntimeEntry()
        runtime.execute_plan(plan, workspace=root, tool_mode=ToolExecutionMode.RUNTIME_GOVERNED, max_steps=max(8, len(plan) + 2))
        payload = runtime.planner_execution_snapshot()
        l6_36 = dict(payload.get("l6_36") or {})
        quality = dict(l6_36.get("quality_gate_result") or {})
        replay = dict(l6_36.get("replay_report") or {})
        recovery = dict(l6_36.get("recovery_plan") or {})
        failure_types = sorted((l6_36.get("failure_type_counts") or {}).keys())
        expected_ok = _case_expected_ok(case_name, quality.get("decision"), recovery.get("mode"), replay.get("reconstructable"))
        cases.append(
            ReplayCorpusCase(
                case_name=case_name,
                status="passed" if expected_ok else "failed",
                execution_status=str(payload.get("status") or ""),
                source_report_digest=str(payload.get("report_digest") or ""),
                failure_types=failure_types,
                recovery_mode=str(recovery.get("mode") or ""),
                quality_decision=str(quality.get("decision") or ""),
                reconstructable=bool(replay.get("reconstructable")),
                can_resume=bool(recovery.get("can_resume")),
                next_action=_primary_next_action(l6_36),
            )
        )

    report = ReplayCorpusReport(
        schema=L6_36_CORPUS_SCHEMA,
        source_version=L6_36_SOURCE_VERSION,
        ok=all(case.status == "passed" for case in cases),
        cases=cases,
    )
    if export_dir is not None:
        target_dir = Path(export_dir).expanduser().resolve()
        target_dir.mkdir(parents=True, exist_ok=True)
        report.export_json(target_dir / "replay_corpus_result.json")
        (target_dir / "replay_corpus_report.txt").write_text(report.markdown_report(), encoding="utf-8")
    return report


def _failure_type_for_step(record: dict[str, Any], *, stopped_reason: str) -> str:
    state = str(record.get("state") or "")
    tool_name = str(record.get("tool_name") or "")
    error_code = str(record.get("error_code") or "").lower()
    if state == "blocked":
        return "risk_blocked"
    if state == "confirmation_required":
        return "confirmation_required"
    if state == "timeout" or error_code in {"timeout", "step_timeout", "adapter_timeout"}:
        return "timeout"
    if state == "skipped":
        if stopped_reason == "failure_budget_exhausted":
            return "budget_exhausted"
        return "skipped_after_stop"
    if state == "failed":
        if tool_name in {"run_python_quality_check", "evaluate_quality_gate"} or "quality" in error_code:
            return "validation_failed"
        if tool_name in {"create_zip_package", "create_release_bundle"} or "zip" in error_code or "delivery" in error_code:
            return "delivery_failed"
        return "tool_failed"
    return "skipped_after_stop"


def _mode_for_failure_type(failure_type: str) -> str:
    return {
        "model_plan_invalid": "replan_model_output",
        "risk_blocked": "blocked_replan",
        "confirmation_required": "await_confirmation",
        "tool_failed": "recover_failed_step",
        "timeout": "recover_timeout_step",
        "budget_exhausted": "resume_after_budget_review",
        "validation_failed": "repair_then_validate",
        "delivery_failed": "repair_delivery_then_retry",
        "skipped_after_stop": "resume_from_next_step",
    }.get(failure_type, "resume_from_next_step")


def _primary_failure_type(failures: list[FailureClassification]) -> str:
    priority = [
        "risk_blocked",
        "confirmation_required",
        "timeout",
        "validation_failed",
        "delivery_failed",
        "tool_failed",
        "budget_exhausted",
        "model_plan_invalid",
        "skipped_after_stop",
    ]
    present = {failure.failure_type for failure in failures}
    for item in priority:
        if item in present:
            return item
    return failures[0].failure_type if failures else ""


def _recovery_steps_for(failure_type: str, *, can_resume: bool) -> list[str]:
    if not failure_type:
        return []
    if failure_type == "risk_blocked":
        return ["停止自动链路", "保留审计证据", "要求 Planner 重新规划为低风险路径"]
    if failure_type == "confirmation_required":
        return ["等待用户确认票据", "确认后通过 Runtime 原链路续接", "拒绝时生成替代计划"]
    if failure_type == "model_plan_invalid":
        return ["回退 rule_only 或重新提示模型输出 JSON plan", "保留最近会话上下文", "重新进入 plan_schema 校验"]
    if failure_type == "timeout":
        return ["拆分超时步骤", "从 timeout step 续接" if can_resume else "重新规划超时步骤", "复跑质量门"]
    if failure_type == "validation_failed":
        return ["进入诊断", "生成最小修复草案", "运行分片回归", "重新评估质量门"]
    if failure_type == "delivery_failed":
        return ["检查交付路径与敏感文件排除", "重建交付 manifest", "重新打包并校验 SHA256"]
    if failure_type == "budget_exhausted":
        return ["检查失败预算", "从首个未完成步骤续接", "必要时拆分任务链"]
    return ["定位失败步骤", "生成修复计划", "从失败步骤续接" if can_resume else "重新规划剩余步骤"]


def _failure_taxonomy_complete(report_payload: dict[str, Any], failures: list[FailureClassification]) -> bool:
    records = [record for record in report_payload.get("step_records", []) if isinstance(record, dict)]
    non_success = [record for record in records if str(record.get("state") or "") != "succeeded"]
    return len(failures) == len(non_success)


def _count_failure_types(failures: list[FailureClassification]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for failure in failures:
        counts[failure.failure_type] = counts.get(failure.failure_type, 0) + 1
    return counts


def _recommended_actions_for_quality(decision: str, failures: list[FailureClassification]) -> list[str]:
    if decision == "pass":
        return ["允许进入交付报告或下一阶段回归。"]
    if decision == "warn":
        return ["等待确认或从未执行步骤续接。", "在报告中披露确认/跳过状态。"]
    if decision == "fail":
        actions = []
        for failure_type in sorted({failure.failure_type for failure in failures}):
            actions.append(FAILURE_NEXT_ACTIONS.get(failure_type, "resume_from_next_step"))
        return actions or ["补齐回放证据并重新运行质量门。"]
    return ["停止自动链路。", "按安全阻断证据重新规划。"]


def _case_expected_ok(case_name: str, decision: Any, mode: Any, reconstructable: Any) -> bool:
    decision = str(decision or "")
    mode = str(mode or "")
    if not reconstructable:
        return False
    expected = {
        "code_generation": {"pass"},
        "code_analysis": {"pass"},
        "file_read": {"pass"},
        "project_diagnosis": {"pass", "warn"},
        "recoverable_failure": {"fail"},
        "safety_blocked": {"blocked"},
        "confirmation_required": {"warn"},
        "delivery_package": {"pass", "warn"},
        "quality_compileall": {"pass", "warn"},
    }
    if decision not in expected.get(case_name, {"pass", "warn", "fail", "blocked"}):
        return False
    if case_name == "recoverable_failure" and mode not in {"recover_failed_step", "resume_from_next_step"}:
        return False
    if case_name == "safety_blocked" and mode != "blocked_replan":
        return False
    if case_name == "confirmation_required" and mode != "await_confirmation":
        return False
    return True


def _primary_next_action(l6_36: dict[str, Any]) -> str:
    failures = list(l6_36.get("failure_classifications") or [])
    for item in failures:
        if isinstance(item, dict) and item.get("next_action"):
            return str(item.get("next_action"))
    recovery = dict(l6_36.get("recovery_plan") or {})
    if recovery.get("recommended_action"):
        return str(recovery.get("recommended_action"))
    return "none"
