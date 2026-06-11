from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from linyuanzhe_frontend.contracts.runtime_snapshot import RuntimeSnapshot, ChatMessage, CHAT_MESSAGE_DISPLAY_LIMIT, CHAT_USER_INPUT_LIMIT, safe_chat_text, safe_text
from linyuanzhe_frontend.contracts.work_modes import sanitize_work_mode_payload

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
        self._chat_cleared = False

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
        """Reload mock data without discarding accumulated UI transcript messages."""
        previous_messages = list(self._snapshot.chat_messages)
        fresh = self._load_snapshot()
        if self._chat_cleared:
            fresh.chat_messages = []
            fresh.visible_message_count = 0
            fresh.hidden_message_count = 0
            self._snapshot = fresh
            return self._snapshot
        merged = []
        seen = set()
        for message in list(fresh.chat_messages) + previous_messages:
            key = (
                safe_text(getattr(message, "role", ""), 32),
                safe_text(getattr(message, "label", ""), 32),
                safe_text(getattr(message, "time", ""), 32),
                safe_text(getattr(message, "text", ""), 500),
            )
            if key in seen:
                continue
            seen.add(key)
            merged.append(message)
        fresh.chat_messages = merged[-240:]
        self._snapshot = fresh
        return self._snapshot

    def clear_local_transcript(self) -> RuntimeSnapshot:
        self._chat_cleared = True
        self._snapshot.chat_messages = []
        self._snapshot.visible_message_count = 0
        self._snapshot.hidden_message_count = 0
        self._snapshot.pending_delta_chars = 0
        self._snapshot.stream_state = "idle"
        self._snapshot.stream_visual_state = "idle"
        self._snapshot.stream_activity_label = ""
        return self._snapshot

    def submit_user_message(self, text: str) -> RuntimeSnapshot:
        self._chat_cleared = False
        self._snapshot.append_user_message(safe_chat_text(text, CHAT_USER_INPUT_LIMIT))
        return self._snapshot


    def _snapshot_copy(self) -> RuntimeSnapshot:
        return RuntimeSnapshot.from_mapping(self._snapshot.to_dict())

    def _notify_stream_snapshot(self, callback: Any) -> None:
        if callable(callback):
            callback(self._snapshot_copy())

    def submit_user_message_streaming(self, text: str, **kwargs: Any) -> RuntimeSnapshot:
        """Run a small frontend-only streaming simulation for UI acceptance.

        This is deliberately marked as Mock. It never calls a Provider SDK,
        Runtime tool, memory writer, QualityGate writer, or audit writer.  The
        purpose is to let the desktop shell validate thinking state, incremental
        transcript repaint, and Markdown streaming without a live gateway.
        """
        on_snapshot = kwargs.get("on_snapshot")
        work_payload = sanitize_work_mode_payload(kwargs.get("work_mode_payload") or {})
        self._chat_cleared = False
        safe_message = safe_chat_text(text, CHAT_USER_INPUT_LIMIT)
        self._snapshot.chat_messages = [*self._snapshot.chat_messages, ChatMessage("user", "你", time.strftime("%H:%M:%S"), safe_message)]
        self._snapshot.source_kind = "mock"
        self._snapshot.runtime_status = "mock_streaming"
        self._snapshot.current_task_status = "RUNNING"
        self._snapshot.current_stage = "Mock 正在准备流式演示"
        self._snapshot.stream_state = "thinking"
        self._snapshot.progress_percent = max(10, min(30, self._snapshot.progress_percent))
        self._snapshot.pending_delta_chars = 0
        self._snapshot.visible_message_count = len(self._snapshot.chat_messages)
        self._snapshot.hidden_message_count = 0
        self._snapshot.stream_activity_label = "正在思考"
        self._snapshot.stream_visual_state = "thinking"
        self._snapshot.tool_execution_mode = safe_text(work_payload.get("tool_mode_requested", "runtime_governed"), 80)
        self._snapshot.planner_mode = "work_mode_requested" if bool(work_payload.get("planner_allowed")) else "chat_only"
        self._notify_stream_snapshot(on_snapshot)
        time.sleep(0.05)

        assistant = ChatMessage("assistant", "临渊者", "流式", "")
        self._snapshot.chat_messages = [*self._snapshot.chat_messages, assistant]
        chunks = [
            "## Mock 流式演示\n",
            f"- 工作模式：{safe_text(work_payload.get('label', '聊天'), 20)}；planner_allowed={bool(work_payload.get('planner_allowed'))}；tools_requested={bool(work_payload.get('tools_requested'))}。\n",
            "- 已接收用户输入，正在执行前端增量渲染回归。\n",
            "- 当前没有调用真实模型、工具、记忆或审计写入；真实执行只由 Runtime 接管。\n\n",
            "```text\nfrontend_execution=false\nruntime_only=true\n```\n",
            "流式演示完成。\n",
        ]
        for index, chunk in enumerate(chunks, start=1):
            assistant.text = safe_chat_text(assistant.text + chunk, CHAT_MESSAGE_DISPLAY_LIMIT)
            self._snapshot.stream_state = "streaming"
            self._snapshot.current_stage = "Mock 正在流式输出"
            self._snapshot.progress_percent = min(95, 30 + index * 12)
            self._snapshot.pending_delta_chars = len(chunk)
            self._snapshot.visible_message_count = len(self._snapshot.chat_messages)
            self._snapshot.stream_activity_label = "正在输出"
            self._snapshot.stream_visual_state = "streaming"
            self._notify_stream_snapshot(on_snapshot)
            time.sleep(0.04)

        self._snapshot.stream_state = "completed"
        self._snapshot.current_task_status = "COMPLETED"
        self._snapshot.current_stage = "Mock 流式演示已完成"
        self._snapshot.progress_percent = 100
        self._snapshot.pending_delta_chars = 0
        self._snapshot.stream_activity_label = "已完成"
        self._snapshot.stream_visual_state = "completed"
        self._snapshot.visible_message_count = len(self._snapshot.chat_messages)
        self._notify_stream_snapshot(on_snapshot)
        return self._snapshot_copy()

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
            message="Session 恢复请求已在前端占位层记录；前端未直接恢复工具；真实恢复只能由 Runtime / TiangongWangguan 执行。",
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
