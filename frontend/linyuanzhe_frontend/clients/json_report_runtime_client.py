from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional

from linyuanzhe_frontend.clients.mock_runtime_client import MockRuntimeClient
from linyuanzhe_frontend.contracts.runtime_snapshot import RuntimeSnapshot, ChatMessage, StepSummary, safe_text, digest_text

from linyuanzhe_frontend.contracts.file_transfer import FileTransferPublicRecord, FileTransferRequest
from linyuanzhe_frontend.contracts.workspace import FileAuthorizationPublicRecord, FileAuthorizationRequest
from linyuanzhe_frontend.contracts.connectors import ConnectorRegistrationPublicRecord, ConnectorRegistrationRequest


class JsonReportRuntimeClient(MockRuntimeClient):
    """Read-only JSON report client for FE.01.

    Supported inputs:
    - a normalized runtime_snapshot JSON file;
    - a directory containing L6.39 p0_system2.json and optional planner_execution.json;
    - a single L6.39 p0_system2.json report.

    This client is read-only. submit_* methods only update frontend memory state;
    they do not write to backend Runtime or trigger execution.
    """

    def __init__(self, report_path: str | Path) -> None:
        self.report_path = Path(report_path)
        self._snapshot = self._load_from_report()

    def _read_json(self, path: Path) -> Dict[str, Any]:
        return json.loads(path.read_text(encoding="utf-8"))

    def _resolve_file(self, name: str) -> Optional[Path]:
        if self.report_path.is_file() and self.report_path.name == name:
            return self.report_path
        if self.report_path.is_dir():
            p = self.report_path / name
            if p.exists():
                return p
        return None


    def refresh_snapshot(self) -> RuntimeSnapshot:
        """Reload the sanitized JSON report from disk. This remains read-only."""
        self._snapshot = self._load_from_report()
        return self._snapshot

    def _load_from_report(self) -> RuntimeSnapshot:
        if self.report_path.is_file():
            raw = self._read_json(self.report_path)
            if raw.get("schema_version", "").startswith("linyuanzhe.frontend"):
                snap = RuntimeSnapshot.from_mapping(raw)
                snap.source_kind = "json_snapshot"
                return snap
            return self._from_l6_reports(p0_system2=raw, planner_execution=None)

        if self.report_path.is_dir():
            normalized = self._resolve_file("runtime_snapshot.json")
            if normalized:
                snap = RuntimeSnapshot.from_mapping(self._read_json(normalized))
                snap.source_kind = "json_snapshot"
                return snap
            p0 = self._resolve_file("p0_system2.json")
            planner = self._resolve_file("planner_execution.json")
            p0_data = self._read_json(p0) if p0 else {}
            planner_data = self._read_json(planner) if planner else None
            return self._from_l6_reports(p0_system2=p0_data, planner_execution=planner_data)

        return RuntimeSnapshot(source_kind="json_report_missing", connection_status="未连接：JSON 报告不存在")

    def _from_l6_reports(
        self,
        p0_system2: Mapping[str, Any],
        planner_execution: Optional[Mapping[str, Any]],
    ) -> RuntimeSnapshot:
        memory = dict(p0_system2.get("memory", {}) or {})
        audit = dict(p0_system2.get("audit", {}) or {})
        recovery = dict(p0_system2.get("recovery", {}) or {})
        quality = dict(p0_system2.get("quality_gate", {}) or {})

        steps: List[StepSummary] = []
        success_count = 0
        blocked_count = 0
        pending_count = 0
        status = safe_text(p0_system2.get("status", "p0_systems_two_ready"), 64)
        current_task_status = "READY" if "ready" in status else "RUNNING"
        execution_stage = "P0 系统接入摘要"
        current_stage = "Memory / Audit / Recovery / QualityGate 接入"
        plan_id = safe_text(p0_system2.get("source_version", "L6.39-P0-memory-audit-recovery-qualitygate"), 120)

        if planner_execution:
            raw_steps = list(planner_execution.get("step_records", []) or [])
            for raw in raw_steps[:50]:
                steps.append(StepSummary.from_mapping(raw))
            success_count = int(planner_execution.get("succeeded_steps", 0) or 0)
            blocked_count = int(planner_execution.get("blocked_steps", 0) or 0)
            pending_count = int(planner_execution.get("confirmation_required_steps", 0) or 0)
            total = int(planner_execution.get("total_steps", len(raw_steps)) or len(raw_steps) or 1)
            executed = int(planner_execution.get("executed_steps", success_count) or success_count)
            progress = min(100, max(0, round(executed * 100 / max(total, 1))))
            execution_stage = safe_text(planner_execution.get("status", "执行链摘要"), 64)
            current_task_status = "COMPLETED" if planner_execution.get("status") == "completed" else "RUNNING"
            task_id = safe_text(planner_execution.get("task_id", "execute_plan"), 80)
            run_id = safe_text(planner_execution.get("run_id", ""), 80)
            plan_id = f"{task_id}:{run_id}" if run_id else task_id
        else:
            progress = 67
            success_count = int(audit.get("status_counts", {}).get("ok", audit.get("event_count", 8)) or 8)
            blocked_count = 0 if quality.get("allow_continue", True) else 1
            pending_count = 0

        if not steps:
            steps = [
                StepSummary("Memory 接入", "succeeded", "A2", "memory_route", "只输出安全摘要，不写长期记忆"),
                StepSummary("Audit 接入", "succeeded", "A2", "audit_evidence", "只读取安全审计摘要"),
                StepSummary("QualityGate 接入", "running", "A2", "quality_gate_evidence", "质量门摘要已生成"),
            ]

        recent_summaries = memory.get("recent_summaries", []) or []
        memory_summary = recent_summaries[0] if recent_summaries else memory.get("planner_hint", "")
        evidence_refs = audit.get("evidence_refs", []) or []
        evidence_ref = evidence_refs[-1] if evidence_refs else audit.get("envelope_id", "") or quality.get("evidence_id", "")
        memory_ref = memory.get("route_id", "") or memory.get("snapshot_ref", "")

        snap = RuntimeSnapshot(
            session_id=safe_text(p0_system2.get("report_digest", "json-report-session"), 80),
            runtime_status="运行中" if p0_system2.get("runtime_governed", True) else "未知",
            model_provider="DeepSeek-R1 32K",
            planner_mode="PlannerExecutionController",
            tool_execution_mode="runtime_governed" if p0_system2.get("runtime_governed", True) else "read_only_json",
            connection_status="JSON 报告已加载",
            current_task_status=current_task_status,
            progress_percent=progress,
            plan_id=plan_id,
            current_stage=current_stage,
            eta="待真实 Runtime 接线",
            success_count=success_count,
            blocked_count=blocked_count,
            pending_confirmation_count=pending_count,
            execution_stage=execution_stage,
            execution_steps=steps,
            quality_decision=safe_text(quality.get("decision", "not_evaluated"), 64),
            quality_allow_continue=bool(quality.get("allow_continue", True)),
            quality_allow_package=bool(quality.get("allow_package", False)),
            quality_gate_status=safe_text(quality.get("gate_status", "unknown"), 64),
            blocking_reasons=[safe_text(x, 160) for x in quality.get("blocking_reasons", []) or []],
            audit_count=int(audit.get("event_count", audit.get("audit_count", 0)) or 0),
            evidence_ref=safe_text(evidence_ref, 80),
            memory_sanitized_summary=safe_text(memory_summary, 260),
            memory_digest=digest_text(memory_summary),
            memory_evidence_ref=safe_text(memory_ref, 80),
            recovery_ticket_id=safe_text(recovery.get("ticket_id", ""), 100),
            recovery_failure_count=int(recovery.get("failure_count", 0) or 0),
            recovery_resume_plan_count=int(recovery.get("resume_plan_count", 0) or 0),
            recovery_next_actions=[safe_text(x, 160) for x in recovery.get("next_actions", []) or []],
            recovery_requires_human_confirmation=bool(recovery.get("requires_human_confirmation", False)),
            source_kind="json_report",
        )
        return snap

    def submit_user_message_streaming(self, text: str, **_kwargs: Any) -> RuntimeSnapshot:
        return self.submit_user_message(text)

    def request_task_stop(self, reason: str = "user_requested") -> RuntimeSnapshot:
        self._snapshot.control_state = "stop_frontend_only"
        self._snapshot.append_assistant_notice_once("控制", "停止请求已在前端占位层记录；Mock/JSON/Future 客户端不会直接停止 Runtime。", "停止请求已在前端占位层记录", window=20)
        return self._snapshot

    def request_task_reset(self, reason: str = "user_requested") -> RuntimeSnapshot:
        self._snapshot.control_state = "reset_frontend_only"
        self._snapshot.append_assistant_notice_once("控制", "复位请求已在前端占位层记录；Mock/JSON/Future 客户端不会直接复位 Runtime。", "复位请求已在前端占位层记录", window=20)
        return self._snapshot

    def request_task_interrupt(self, reason: str = "user_requested") -> RuntimeSnapshot:
        self._snapshot.control_state = "interrupt_frontend_only"
        self._snapshot.append_assistant_notice_once("控制", "中断请求已在前端占位层记录；真实中断只能由 Runtime / TiangongWangguan 执行。", "中断请求已在前端占位层记录", window=20)
        return self._snapshot

    def request_file_transfer(self, file_path: str, purpose: str = "user_attachment") -> RuntimeSnapshot:
        try:
            request = FileTransferRequest.from_path(file_path, purpose=purpose)
            record = FileTransferPublicRecord.from_request_result(
                request,
                status="frontend_only_recorded",
                message="文件传输请求已在前端占位层记录；真实传输必须经 Runtime 授权。",
                transfer_id="FT-FRONTEND-ONLY",
                frontend_only_fallback=True,
            )
        except Exception as exc:
            record = FileTransferPublicRecord(
                transfer_id="FT-FRONTEND-ERROR",
                status="frontend_error",
                message=f"文件传输请求准备失败：{safe_text(exc, 160)}",
                frontend_only_fallback=True,
            )
        self._snapshot.add_file_transfer_record(record)
        return self._snapshot

    def request_session_resume(self, session_id_digest: str, reason: str = "user_requested_resume") -> RuntimeSnapshot:
        self._snapshot.record_session_resume_request(
            session_id_digest,
            status="frontend_only_recorded",
            message="Session 恢复请求已在 JSON 报告客户端记录；真实恢复只能由 Runtime / TiangongWangguan 执行。",
        )
        return self._snapshot

    def request_session_search(self, query: str) -> RuntimeSnapshot:
        self._snapshot.record_session_search(query)
        return self._snapshot
