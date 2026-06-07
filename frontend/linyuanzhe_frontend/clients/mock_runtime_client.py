from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from linyuanzhe_frontend.contracts.runtime_snapshot import RuntimeSnapshot, ChatMessage, safe_text

from linyuanzhe_frontend.contracts.file_transfer import FileTransferPublicRecord, FileTransferRequest
from linyuanzhe_frontend.contracts.workspace import FileAuthorizationPublicRecord, FileAuthorizationRequest
from linyuanzhe_frontend.contracts.connectors import ConnectorRegistrationPublicRecord, ConnectorRegistrationRequest


class MockRuntimeClient:
    """Mock client for FE.01 desktop UI validation.

    This client never calls real Runtime, provider SDKs, adapters, or tools.
    It only mutates an in-memory RuntimeSnapshot for UI smoke testing.
    """

    def __init__(self, mock_file: Optional[str | Path] = None) -> None:
        if mock_file is None:
            mock_file = Path(__file__).resolve().parents[1] / "mock_data" / "runtime_snapshot_mock.json"
        self.mock_file = Path(mock_file)
        self._snapshot = self._load_snapshot()

    def _load_snapshot(self) -> RuntimeSnapshot:
        if self.mock_file.exists():
            data = json.loads(self.mock_file.read_text(encoding="utf-8"))
            return RuntimeSnapshot.from_mapping(data)
        return RuntimeSnapshot()

    def get_status(self) -> Dict[str, Any]:
        s = self._snapshot
        return {
            "runtime_status": s.runtime_status,
            "model_provider": s.model_provider,
            "planner_mode": s.planner_mode,
            "tool_execution_mode": s.tool_execution_mode,
            "connection_status": s.connection_status,
        }

    def get_tools(self) -> List[Dict[str, Any]]:
        return []

    def get_policy(self) -> Dict[str, Any]:
        return {
            "frontend_mode": "mock_only",
            "no_tool_execution": True,
            "no_provider_call": True,
            "no_kernel_mutation": True,
        }

    def get_planner_execution(self) -> Dict[str, Any]:
        return {
            "execution_stage": self._snapshot.execution_stage,
            "steps": [step.__dict__ for step in self._snapshot.execution_steps],
        }

    def get_public_projection(self) -> Dict[str, Any]:
        return self._snapshot.to_dict()

    def get_audit_summary(self) -> Dict[str, Any]:
        return {"audit_count": self._snapshot.audit_count, "evidence_ref": self._snapshot.evidence_ref}

    def get_quality_gate(self) -> Dict[str, Any]:
        return {
            "decision": self._snapshot.quality_decision,
            "allow_continue": self._snapshot.quality_allow_continue,
            "allow_package": self._snapshot.quality_allow_package,
            "gate_status": self._snapshot.quality_gate_status,
            "blocking_reasons": self._snapshot.blocking_reasons,
        }

    def get_memory_summary(self) -> Dict[str, Any]:
        return {
            "sanitized_summary": self._snapshot.memory_sanitized_summary,
            "digest": self._snapshot.memory_digest,
            "evidence_ref": self._snapshot.memory_evidence_ref,
        }

    def get_recovery_ticket(self) -> Dict[str, Any]:
        return {
            "ticket_id": self._snapshot.recovery_ticket_id,
            "failure_count": self._snapshot.recovery_failure_count,
            "resume_plan_count": self._snapshot.recovery_resume_plan_count,
            "next_actions": self._snapshot.recovery_next_actions,
            "requires_human_confirmation": self._snapshot.recovery_requires_human_confirmation,
        }

    def get_snapshot(self) -> RuntimeSnapshot:
        return self._snapshot

    def refresh_snapshot(self) -> RuntimeSnapshot:
        """Reload mock data from disk. This is frontend-only and does not execute anything."""
        self._snapshot = self._load_snapshot()
        return self._snapshot

    def submit_user_message(self, text: str) -> RuntimeSnapshot:
        self._snapshot.append_user_message(safe_text(text, 500))
        return self._snapshot


    def submit_user_message_streaming(self, text: str, **_kwargs: Any) -> RuntimeSnapshot:
        return self.submit_user_message(text)

    def request_task_stop(self, reason: str = "user_requested") -> RuntimeSnapshot:
        self._snapshot.control_state = "stop_frontend_only"
        self._snapshot.chat_messages.append(
            ChatMessage("assistant", "临渊者", "控制", "停止请求已在前端占位层记录；Mock/JSON/Future 客户端不会直接停止 Runtime。")
        )
        return self._snapshot

    def request_task_reset(self, reason: str = "user_requested") -> RuntimeSnapshot:
        self._snapshot.control_state = "reset_frontend_only"
        self._snapshot.chat_messages.append(
            ChatMessage("assistant", "临渊者", "控制", "复位请求已在前端占位层记录；Mock/JSON/Future 客户端不会直接复位 Runtime。")
        )
        return self._snapshot

    def request_task_interrupt(self, reason: str = "user_requested") -> RuntimeSnapshot:
        self._snapshot.control_state = "interrupt_frontend_only"
        self._snapshot.chat_messages.append(
            ChatMessage("assistant", "临渊者", "控制", "中断请求已在前端占位层记录；真实中断只能由 Runtime / TiangongWangguan 执行。")
        )
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

    def request_file_authorization(self, file_path: str, mode: str = "read", scope: str = "user_selected_file", purpose: str = "user_attachment") -> RuntimeSnapshot:
        try:
            request = FileAuthorizationRequest.from_path(file_path, mode=mode, scope=scope, purpose=purpose)
            record = FileAuthorizationPublicRecord.from_request_result(
                request,
                status="frontend_only_recorded",
                message="文件授权请求已在前端占位层记录；真实授权必须经 Runtime / QualityGate / TiangongWangguan。",
                authorization_id="AUTH-FRONTEND-ONLY",
                frontend_only_fallback=True,
            )
        except Exception as exc:
            record = FileAuthorizationPublicRecord(
                authorization_id="AUTH-FRONTEND-ERROR",
                status="frontend_error",
                message=f"文件授权请求准备失败：{safe_text(exc, 160)}",
                frontend_only_fallback=True,
            )
        self._snapshot.add_file_authorization_record(record)
        return self._snapshot


    def request_connector_registration(self, display_name: str, kind: str = "mcp_server", scopes: List[str] | None = None, capabilities: List[str] | None = None) -> RuntimeSnapshot:
        try:
            request = ConnectorRegistrationRequest.build(
                display_name=display_name,
                kind=kind,
                requested_scopes=scopes or ["read_public_metadata"],
                requested_capabilities=capabilities or ["registry_review"],
                source_hint="frontend_manual_request",
            )
            record = ConnectorRegistrationPublicRecord.from_request_result(
                request,
                status="frontend_only_recorded",
                message="连接器注册请求已在前端占位层记录；真实注册/安装/执行必须经 Runtime / QualityGate / 工作区授权。",
                request_id="CONN-FRONTEND-ONLY",
                frontend_only_fallback=True,
            )
        except Exception as exc:
            record = ConnectorRegistrationPublicRecord(
                request_id="CONN-FRONTEND-ERROR",
                status="frontend_error",
                message=f"连接器注册请求准备失败：{safe_text(exc, 160)}",
                frontend_only_fallback=True,
            )
        self._snapshot.add_connector_registration_record(record)
        return self._snapshot


    def request_session_resume(self, session_id_digest: str, reason: str = "user_requested_resume") -> RuntimeSnapshot:
        self._snapshot.record_session_resume_request(
            session_id_digest,
            status="frontend_only_recorded",
            message="Session 恢复请求已在前端占位层记录；真实恢复只能由 Runtime / TiangongWangguan 执行。",
        )
        return self._snapshot

    def request_session_search(self, query: str) -> RuntimeSnapshot:
        self._snapshot.record_session_search(query)
        return self._snapshot

    def submit_confirmation(self, ticket_id: str, decision: str) -> RuntimeSnapshot:
        self._snapshot.submit_confirmation(ticket_id, decision)
        return self._snapshot


    def submit_self_iteration_confirmation(self, candidate_id: str, decision: str) -> RuntimeSnapshot:
        self._snapshot.submit_self_iteration_confirmation(candidate_id, decision)
        return self._snapshot
