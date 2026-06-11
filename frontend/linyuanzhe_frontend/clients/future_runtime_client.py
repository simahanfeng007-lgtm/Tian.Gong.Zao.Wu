from __future__ import annotations

from typing import Any, Dict, List

from linyuanzhe_frontend.contracts.runtime_snapshot import RuntimeSnapshot, ChatMessage, safe_text

from linyuanzhe_frontend.contracts.file_transfer import FileTransferPublicRecord, FileTransferRequest
from linyuanzhe_frontend.contracts.workspace import FileAuthorizationPublicRecord, FileAuthorizationRequest
from linyuanzhe_frontend.contracts.connectors import ConnectorRegistrationPublicRecord, ConnectorRegistrationRequest


class FutureRuntimeClient:
    """Placeholder for post-L6.54 real Runtime connection.

    FE.01 intentionally does not implement IPC/HTTP/SSE or any real execution
    channel. The real client may be implemented only after backend Runtime API
    and PublicProjection schema are frozen.
    """

    def __init__(self, endpoint: str = "") -> None:
        self.endpoint = endpoint
        self._snapshot = RuntimeSnapshot(
            source_kind="future_runtime_placeholder",
            runtime_status="未接线",
            connection_status="FutureRuntimeClient 占位：等待 L6.54 真实 Runtime 流式接线",
            current_task_status="DISCONNECTED",
            progress_percent=0,
            current_stage="等待真实 Runtime SSE / IPC 接线",
        )

    def _not_connected(self) -> Dict[str, Any]:
        return {
            "ready": False,
            "reason": "FutureRuntimeClient is intentionally disabled in FE.01.",
            "no_tool_execution": True,
            "no_provider_call": True,
            "no_kernel_mutation": True,
        }

    def get_status(self) -> Dict[str, Any]:
        return self._not_connected()

    def get_tools(self) -> List[Dict[str, Any]]:
        return []

    def get_policy(self) -> Dict[str, Any]:
        return self._not_connected()

    def get_planner_execution(self) -> Dict[str, Any]:
        return self._not_connected()

    def get_public_projection(self) -> Dict[str, Any]:
        return self._snapshot.to_dict()

    def get_audit_summary(self) -> Dict[str, Any]:
        return {}

    def get_quality_gate(self) -> Dict[str, Any]:
        return {}

    def get_memory_summary(self) -> Dict[str, Any]:
        return {}

    def get_recovery_ticket(self) -> Dict[str, Any]:
        return {}

    def get_snapshot(self) -> RuntimeSnapshot:
        return self._snapshot

    def refresh_snapshot(self) -> RuntimeSnapshot:
        return self._snapshot

    def submit_user_message(self, text: str) -> RuntimeSnapshot:
        self._snapshot.append_user_message(text)
        return self._snapshot


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
