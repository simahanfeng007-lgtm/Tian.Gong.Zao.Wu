"""L6.72.55 自适应工作循环观察归一化。

本模块把 PlannerExecutionReport / ToolResult 的失败摘要压缩成安全 repair_context。
它只做脱敏归因，不调用 Provider、不执行工具、不读取文件正文。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from tiangong_agent_shell.safe_logging import redact_text

from .plan_schema import plan_to_public_dict
from .tool_invocation import ToolInvocation
from .tool_result import ToolResult

OBSERVATION_NORMALIZER_SCHEMA = "tiangong.l6_72_55.observation_normalizer.v1"
RECOVERABLE_FAILURE_TYPES = {
    "validation_failed",
    "tool_failed",
    "timeout",
    "delivery_failed",
    "budget_exhausted",
    "skipped_after_stop",
}
TERMINAL_FAILURE_TYPES = {
    "risk_blocked",
    "confirmation_required",
    "blocked_A5",
    "a5_blocked",
}


@dataclass(frozen=True)
class NormalizedFailure:
    step_index: int
    step_id: str
    tool_name: str
    state: str
    status: str
    error_code: str = ""
    failure_type: str = "tool_failed"
    severity: str = "recoverable"
    output_summary: str = ""
    evidence_refs: tuple[str, ...] = tuple()
    can_auto_repair: bool = False
    reason: str = ""

    def public_dict(self) -> dict[str, Any]:
        return {
            "step_index": self.step_index,
            "step_id": _safe(self.step_id, 120),
            "tool_name": _safe(self.tool_name, 120),
            "state": _safe(self.state, 80),
            "status": _safe(self.status, 80),
            "error_code": _safe(self.error_code, 120),
            "failure_type": _safe(self.failure_type, 120),
            "severity": _safe(self.severity, 80),
            "output_summary": _safe(self.output_summary, 900),
            "evidence_refs": [_safe(item, 180) for item in self.evidence_refs[:10]],
            "can_auto_repair": self.can_auto_repair,
            "reason": _safe(self.reason, 360),
        }


@dataclass(frozen=True)
class RepairContext:
    user_goal: str
    failed: bool
    terminal: bool
    can_auto_repair: bool
    primary_failure_type: str
    next_action: str
    summary: str
    failures: tuple[NormalizedFailure, ...] = tuple()
    original_status: str = ""
    original_report_digest: str = ""
    quality_decision: str = ""
    recovery_mode: str = ""
    retry_budget_used: int = 0
    retry_budget_max: int = 1
    original_plan: tuple[dict[str, Any], ...] = field(default_factory=tuple)

    def public_dict(self) -> dict[str, Any]:
        return {
            "schema": OBSERVATION_NORMALIZER_SCHEMA,
            "user_goal_preview": _safe(self.user_goal, 600),
            "failed": self.failed,
            "terminal": self.terminal,
            "can_auto_repair": self.can_auto_repair,
            "primary_failure_type": _safe(self.primary_failure_type, 120),
            "next_action": _safe(self.next_action, 240),
            "summary": _safe(self.summary, 900),
            "failures": [item.public_dict() for item in self.failures],
            "original_status": _safe(self.original_status, 120),
            "original_report_digest": _safe(self.original_report_digest, 200),
            "quality_decision": _safe(self.quality_decision, 120),
            "recovery_mode": _safe(self.recovery_mode, 120),
            "retry_budget": {"used": self.retry_budget_used, "max": self.retry_budget_max},
            "original_plan": list(self.original_plan)[:20],
            "storage_boundary": {
                "no_raw_prompt": True,
                "no_api_key": True,
                "summary_and_refs_only": True,
                "no_full_file_content": True,
            },
        }

    def prompt_card(self, *, max_chars: int = 3600) -> str:
        """给修复 Planner 的安全上下文卡。"""
        rows = [
            "[AdaptiveRepairContext / L6.72.55]",
            f"goal={_safe(self.user_goal, 500)}",
            f"original_status={self.original_status}; primary_failure_type={self.primary_failure_type}; terminal={self.terminal}; can_auto_repair={self.can_auto_repair}",
            f"quality_decision={self.quality_decision}; recovery_mode={self.recovery_mode}; next_action={self.next_action}",
            f"summary={_safe(self.summary, 700)}",
            "failures:",
        ]
        for item in self.failures[:5]:
            rows.append(
                f"- step={item.step_index} tool={item.tool_name} state={item.state} status={item.status} "
                f"error={item.error_code} type={item.failure_type} auto={item.can_auto_repair} :: {_tail_safe(item.output_summary, 620)}"
            )
        rows.extend(
            [
                "repair_plan_constraints:",
                "- 输出 JSON：{\"steps\":[{\"tool_name\":...,\"arguments\":...,\"reason\":...}]}。",
                "- 最多 3 步；优先最小修复 + 复跑验证；不得请求 A5 / 不得读取密钥 / 不得绕过 Runtime。",
                "- 只能使用 Runtime 已注册工具；不能把失败解释当作完成。",
            ]
        )
        return _safe("\n".join(rows), max_chars)


def normalize_execution_observation(
    *,
    user_goal: str,
    results: list[ToolResult],
    planner_report: Any | None,
    original_plan: list[ToolInvocation],
    retry_budget_used: int = 0,
    retry_budget_max: int = 1,
) -> RepairContext:
    payload = _report_public(planner_report)
    original_status = str(payload.get("status") or _status_from_results(results))
    report_digest = str(payload.get("report_digest") or "")
    l6_36 = payload.get("l6_36") if isinstance(payload.get("l6_36"), dict) else {}
    quality = payload.get("quality_gate_result") if isinstance(payload.get("quality_gate_result"), dict) else {}
    if not quality and isinstance(l6_36, dict):
        quality = l6_36.get("quality_gate_result") if isinstance(l6_36.get("quality_gate_result"), dict) else {}
    recovery = payload.get("recovery_plan") if isinstance(payload.get("recovery_plan"), dict) else {}
    if not recovery and isinstance(l6_36, dict):
        recovery = l6_36.get("recovery_plan") if isinstance(l6_36.get("recovery_plan"), dict) else {}
    classifications = payload.get("failure_classifications") if isinstance(payload.get("failure_classifications"), list) else []
    if not classifications and isinstance(l6_36, dict):
        classifications = l6_36.get("failure_classifications") if isinstance(l6_36.get("failure_classifications"), list) else []
    step_records = payload.get("step_records") if isinstance(payload.get("step_records"), list) else []
    failures = _build_failures(results, classifications, step_records)
    failed = bool(failures) or any(not item.ok for item in results or []) or original_status not in {"completed", "ok", "completed_pass"}
    primary = _primary_failure_type(failures, classifications, original_status)
    terminal = primary in TERMINAL_FAILURE_TYPES or any(item.severity == "terminal" for item in failures)
    can_auto = bool(failures) and not terminal and any(item.can_auto_repair for item in failures) and retry_budget_used < retry_budget_max
    next_action = str(recovery.get("next_action") or recovery.get("recommended_action") or "build_repair_plan" if can_auto else "partial_with_resume")
    summary = _summary_from_failures(failures, original_status)
    return RepairContext(
        user_goal=user_goal,
        failed=failed,
        terminal=terminal,
        can_auto_repair=can_auto,
        primary_failure_type=primary,
        next_action=next_action,
        summary=summary,
        failures=tuple(failures),
        original_status=original_status,
        original_report_digest=report_digest,
        quality_decision=str(quality.get("decision") or quality.get("status") or ""),
        recovery_mode=str(recovery.get("mode") or recovery.get("resume_mode") or ""),
        retry_budget_used=retry_budget_used,
        retry_budget_max=retry_budget_max,
        original_plan=tuple(plan_to_public_dict(original_plan or [])),
    )


def _build_failures(results: list[ToolResult], classifications: list[Any], step_records: list[Any]) -> list[NormalizedFailure]:
    by_step_id: dict[str, dict[str, Any]] = {}
    for item in classifications:
        if isinstance(item, dict):
            by_step_id[str(item.get("step_id") or "")] = item
    record_by_step_id: dict[str, dict[str, Any]] = {}
    for item in step_records:
        if isinstance(item, dict):
            record_by_step_id[str(item.get("step_id") or "")] = item
    failures: list[NormalizedFailure] = []
    for index, result in enumerate(results or []):
        status = _status_value(result)
        if status in {"ok", "success", "skipped"}:
            continue
        step_id = str(getattr(result, "step_id", "") or "")
        classification = by_step_id.get(step_id, {})
        record = record_by_step_id.get(step_id, {})
        failure_type = str(classification.get("failure_type") or _fallback_failure_type(result, record))
        error_code = str(getattr(result, "error_code", "") or record.get("error_code") or "")
        tool_name = str(getattr(result, "tool_name", "") or record.get("tool_name") or "")
        summary = str(getattr(result, "output_summary", "") or record.get("output_summary") or "")
        auto, reason = _auto_repair_decision(tool_name, status, error_code, failure_type, summary)
        severity = "terminal" if failure_type in TERMINAL_FAILURE_TYPES else "recoverable"
        failures.append(
            NormalizedFailure(
                step_index=int(record.get("step_index", index)) if isinstance(record, dict) else index,
                step_id=step_id,
                tool_name=tool_name,
                state=str(record.get("state") or status),
                status=status,
                error_code=error_code,
                failure_type=failure_type,
                severity=severity,
                output_summary=summary,
                evidence_refs=tuple(str(x) for x in (record.get("evidence_refs") or [])[:10]) if isinstance(record, dict) else tuple(),
                can_auto_repair=auto,
                reason=reason,
            )
        )
    return failures


def _auto_repair_decision(tool_name: str, status: str, error_code: str, failure_type: str, summary: str) -> tuple[bool, str]:
    lower = f"{tool_name} {status} {error_code} {failure_type} {summary}".lower()
    if failure_type in TERMINAL_FAILURE_TYPES or status in {"blocked", "confirmation_required"}:
        return False, "terminal_or_confirmation_required"
    if tool_name == "read_file" and ("path_not_found" in lower or "not found" in lower or "不存在" in lower):
        return False, "read_file_missing_should_not_auto_create"
    if failure_type in {"validation_failed", "delivery_failed"}:
        return True, "validation_or_delivery_failure_can_try_minimal_repair"
    if "compileall" in lower or "syntaxerror" in lower or "pytest" in lower:
        return True, "quality_failure_has_repairable_evidence"
    if failure_type == "tool_failed" and error_code not in {"path_not_found", "missing_file"}:
        return True, "tool_failed_with_non_terminal_error"
    if failure_type == "timeout":
        return True, "timeout_can_try_smaller_repair_step"
    return False, "no_safe_repair_path"


def _fallback_failure_type(result: ToolResult, record: dict[str, Any]) -> str:
    tool_name = str(getattr(result, "tool_name", "") or record.get("tool_name") or "")
    status = _status_value(result)
    error_code = str(getattr(result, "error_code", "") or record.get("error_code") or "")
    summary = str(getattr(result, "output_summary", "") or record.get("output_summary") or "")
    lower = f"{tool_name} {status} {error_code} {summary}".lower()
    if status == "blocked":
        return "risk_blocked"
    if status == "confirmation_required":
        return "confirmation_required"
    if status == "timeout":
        return "timeout"
    if tool_name == "run_python_quality_check" or "compileall" in lower or "pytest" in lower:
        return "validation_failed"
    if tool_name in {"create_zip_package", "create_release_bundle"}:
        return "delivery_failed"
    return "tool_failed"


def _primary_failure_type(failures: list[NormalizedFailure], classifications: list[Any], original_status: str) -> str:
    priority = ["risk_blocked", "confirmation_required", "validation_failed", "delivery_failed", "timeout", "tool_failed", "budget_exhausted", "skipped_after_stop"]
    types = [item.failure_type for item in failures]
    for item in classifications:
        if isinstance(item, dict):
            types.append(str(item.get("failure_type") or ""))
    for candidate in priority:
        if candidate in types:
            return candidate
    if original_status in {"blocked", "confirmation_required", "timeout_with_resume", "failed_with_resume"}:
        return {
            "blocked": "risk_blocked",
            "confirmation_required": "confirmation_required",
            "timeout_with_resume": "timeout",
            "failed_with_resume": "tool_failed",
        }.get(original_status, "tool_failed")
    return types[0] if types else "none"


def _summary_from_failures(failures: list[NormalizedFailure], original_status: str) -> str:
    if not failures:
        return f"原计划状态：{original_status}；未发现需要 repair 的失败步骤。"
    head = failures[0]
    return _safe(
        f"原计划状态：{original_status}；首个失败步骤 {head.tool_name}/{head.status}/{head.error_code}；失败类型 {head.failure_type}；{_tail_safe(head.output_summary, 760)}",
        900,
    )


def _report_public(report: Any | None) -> dict[str, Any]:
    if report is None:
        return {}
    try:
        payload = report.public_dict() if hasattr(report, "public_dict") else report
        return payload if isinstance(payload, dict) else {}
    except Exception:  # noqa: BLE001
        return {}


def _status_from_results(results: list[ToolResult]) -> str:
    if not results:
        return "empty"
    return "completed" if all(item.ok for item in results) else "failed_with_resume"


def _status_value(result: ToolResult) -> str:
    status = getattr(result, "status", "")
    return str(getattr(status, "value", status) or "unknown")



def _tail_safe(value: Any, limit: int) -> str:
    text = redact_text(str(value or "").replace("\x00", ""))
    if len(text) <= max(1, int(limit)):
        return text
    return text[-max(1, int(limit)):]

def _safe(value: Any, limit: int) -> str:
    return redact_text(str(value or "").replace("\x00", ""))[: max(1, int(limit))]
