from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, List, Tuple

from linyuanzhe_frontend.contracts.action_guard import CONFIRMATION_ENDPOINT
from linyuanzhe_frontend.contracts.provider_settings import ProviderSettingsWriteRequest, PROVIDER_SETTINGS_WRITE_CONTRACT_VERSION
from linyuanzhe_frontend.contracts.runtime_snapshot import digest_text, safe_text
from linyuanzhe_frontend.contracts.file_transfer import FILE_TRANSFER_ENDPOINT
from linyuanzhe_frontend.contracts.connectors import (
    CONNECTOR_REGISTER_ENDPOINT,
    CONNECTOR_REGISTRY_ENDPOINT,
    ConnectorManifestProjection,
    ConnectorRegistryProjection,
    ConnectorRegistrationPublicRecord,
    ConnectorRegistrationRequest,
    connector_registry_policy,
)
from linyuanzhe_frontend.contracts.runtime_controls import TASK_INTERRUPT_ENDPOINT, TASK_RESET_ENDPOINT, TASK_STOP_ENDPOINT
from linyuanzhe_frontend.contracts.session_manager import (
    SESSION_LIST_ENDPOINT,
    SESSION_RESUME_ENDPOINT,
    SESSION_SEARCH_ENDPOINT,
    TaskSessionProjection,
    SessionManagerStats,
)
from linyuanzhe_frontend.contracts.installer_rc import (
    INSTALLER_MANIFEST_ENDPOINT,
    STARTUP_SELF_CHECK_ENDPOINT,
    InstallerManifestProjection,
    VersionSlotProjection,
    StartupSelfCheckRecord,
    CrashReportProjection,
    RepairActionRecord,
    installer_rc_policy,
)
from linyuanzhe_frontend.contracts.sse_events import (
    CHAT_STREAM_ENDPOINT,
    HEALTH_ENDPOINT,
    PRODUCT_METADATA_ENDPOINT,
    PROVIDER_SETTINGS_ENDPOINT,
)


class RuntimeContractHandler(BaseHTTPRequestHandler):
    """Local controlled Runtime contract server for L6.58 desktop E2E/provider settings/RC preflight smoke.

    This server is not a provider mock and never calls DeepSeek. It only emits
    sanitized PublicProjection/SSE events to verify that the desktop shell can
    consume the frozen Runtime contract without obtaining execution authority.
    """

    server_version = "LinyuanzheRuntimeContractL658/1.0"
    confirmation_payloads: List[Dict[str, Any]] = []
    control_payloads: List[Dict[str, Any]] = []
    provider_settings_payloads: List[Dict[str, Any]] = []
    file_transfer_payloads: List[Dict[str, Any]] = []
    connector_registration_payloads: List[Dict[str, Any]] = []
    session_request_payloads: List[Dict[str, Any]] = []

    def _send_json(self, data: Dict[str, Any], status: int = 200) -> None:
        raw = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def _send_sse(self, events: List[Dict[str, Any]]) -> None:
        raw = "".join(
            f"event: {item['event']}\n"
            f"data: {json.dumps(item, ensure_ascii=False)}\n\n"
            for item in events
        ).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def _read_json_body(self) -> Dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0") or "0")
        raw = self.rfile.read(length)
        if not raw:
            return {}
        try:
            parsed = json.loads(raw.decode("utf-8", errors="replace"))
        except json.JSONDecodeError:
            return {"raw_body_digest_only": True}
        return parsed if isinstance(parsed, dict) else {"value": parsed}

    def do_GET(self) -> None:  # noqa: N802 - stdlib handler API
        if self.path == HEALTH_ENDPOINT:
            self._send_json(
                {
                    "runtime_status": "active",
                    "current_task_status": "READY",
                    "current_stage": "L6.58 Runtime contract server ready",
                    "status_bar": {
                        "runtime_status": "active",
                        "provider_model": "deepseek-v4-pro",
                        "budget_pool": "main_task",
                        "budget_used_ratio": "0.26",
                        "gate_status": "A1 allowed",
                        "audit_id": "audit_l657_health",
                        "memory_mode": "read_only_projection",
                        "tools_allowed": 5,
                        "latency_ms": 14,
                    },
                }
            )
            return
        if self.path == PRODUCT_METADATA_ENDPOINT:
            self._send_json(
                {
                    "schema": "tiangong.l6_51_1.product_identity.v1",
                    "product_name": "天工造物 / 临渊者",
                    "unique_developer": "于泳翔",
                    "angel_investor": "胖胖龙",
                    "endpoint": PRODUCT_METADATA_ENDPOINT,
                    "public": True,
                    "runtime_semantics": "metadata_only",
                    "frontend_permission": "read_only_display",
                }
            )
            return
        if self.path == PROVIDER_SETTINGS_ENDPOINT:
            self._send_json(
                {
                    "frontend_contract": PROVIDER_SETTINGS_WRITE_CONTRACT_VERSION,
                    "provider": "deepseek",
                    "model": "deepseek-v4-pro",
                    "api_key_configured": True,
                    "api_key_digest": digest_text("contract-server-key", 16),
                    "base_url_configured": True,
                    "base_url_digest": digest_text("contract-server-base-url", 16),
                    "provider_config_state": "accepted",
                    "config_error_code": "",
                    "message": "Provider 设置投影已脱敏读取。",
                    "audit_id": "audit_l657_provider_get",
                    "planner_mode": "model_suggest",
                    "tool_execution_mode": "runtime_governed",
                    "stream": True,
                }
            )
            return
        if self.path == CONNECTOR_REGISTRY_ENDPOINT:
            manifest = ConnectorManifestProjection.from_mapping(
                {
                    "connector_id": "connector_contract_l666",
                    "display_name": "契约服务器只读连接器",
                    "kind": "mcp_server",
                    "default_mode": "read_only",
                    "trust_level": "builtin",
                    "manifest_digest": digest_text("connector-contract-l666", 24),
                    "quarantined": False,
                    "workspace_authorization_required": True,
                    "quality_gate_required": True,
                    "runtime_authority_required": True,
                    "requested_scopes": ["read_public_metadata", "workspace_read"],
                    "capabilities": ["contract_probe"],
                    "status": "ready",
                    "read_only_default": True,
                }
            )
            registry = ConnectorRegistryProjection(
                registry_id_digest=digest_text("connector-registry-contract-l666", 16),
                registry_state="ready",
                default_mode="disabled",
                connector_count=1,
                enabled_count=0,
                read_only_count=1,
                quarantined_count=0,
                pending_review_count=0,
                allow_market_install=False,
                allow_unsigned_connector=False,
                runtime_authority_required=True,
                quality_gate_required=True,
                workspace_authorization_required=True,
                frontend_may_install_connector=False,
                frontend_may_execute_connector=False,
                frontend_may_store_connector_secret=False,
            )
            self._send_json(
                {
                    "connector_registry_contract": "tiangong.l6_66.connector_registry.v1",
                    "connector_registry_enabled": True,
                    "connector_registry_state": registry.registry_state,
                    "connector_registry_projection": registry.to_dict(),
                    "connector_manifests": [manifest.to_dict()],
                    "connector_registration_records": [],
                    "connector_last_message": "连接器注册表投影已脱敏读取。",
                    "policy": connector_registry_policy(),
                }
            )
            return
        if self.path == INSTALLER_MANIFEST_ENDPOINT:
            slots = [
                VersionSlotProjection(slot_name="active", version_label="FE01 STEP29 / L6.68", state="active", path_digest="SLOT-ACTIVE-CONTRACT", rollback_capable=True, message="contract server active slot"),
                VersionSlotProjection(slot_name="rollback", version_label="FE01 STEP28 / L6.67", state="rollback", path_digest="SLOT-ROLLBACK-CONTRACT", rollback_capable=True, message="contract server rollback slot"),
                VersionSlotProjection(slot_name="candidate", version_label="next-update-candidate", state="candidate", path_digest="SLOT-CANDIDATE-CONTRACT", rollback_capable=False, message="candidate slot disabled"),
            ]
            startup_checks = [
                StartupSelfCheckRecord(check_id="backend_layout", name="后端目录与 run_agent 入口", status="pass", message="contract server self-check projection"),
                StartupSelfCheckRecord(check_id="frontend_layout", name="前端桌面端与 RuntimeClient", status="pass", message="contract server self-check projection"),
                StartupSelfCheckRecord(check_id="launcher_layout", name="统一启动器", status="pass", message="contract server self-check projection"),
                StartupSelfCheckRecord(check_id="reports_writable", name="报告目录可写", status="pass", message="contract server self-check projection"),
            ]
            manifest = InstallerManifestProjection(
                version_label="FE01 STEP29 / L6.68",
                unique_developer="于泳翔",
                angel_investor="胖胖龙",
                startup_self_check_state="pass",
                rollback_ready=True,
                offline_repair_available=True,
                slots=slots,
                startup_checks=startup_checks,
                crash_reports=[CrashReportProjection(report_id_digest="CRASH-CONTRACT-EMPTY", status="empty", crash_count=0, local_only=True, upload_allowed=False)],
                repair_actions=[RepairActionRecord(action_id="startup_self_check", title="启动自检", status="available"), RepairActionRecord(action_id="offline_repair", title="离线修复预检", status="available")],
            )
            self._send_json({"installer_rc_contract": "tiangong.l6_68.installer_rc.v1", "installer_manifest": manifest.to_dict(), "version_slots": [item.to_dict() for item in slots], "startup_self_checks": [item.to_dict() for item in startup_checks], "installer_last_message": "安装器 RC 投影已脱敏读取。", "policy": installer_rc_policy()})
            return
        if self.path == STARTUP_SELF_CHECK_ENDPOINT:
            self._send_json({"contract_version": "tiangong.l6_68.startup_self_check.v1", "ok": True, "checks": [StartupSelfCheckRecord(check_id="contract", name="契约服务器启动自检", status="pass", message="readonly projection").to_dict()]})
            return
        if self.path == SESSION_LIST_ENDPOINT:
            sessions = [
                TaskSessionProjection.from_mapping({"session_id": "contract-active-session", "title": "契约服务器活动任务", "status": "running", "current_stage": "Runtime contract smoke", "progress_percent": 51, "active": True, "audit_id": "audit_l667_session_active", "tags": ["active", "contract"]}),
                TaskSessionProjection.from_mapping({"session_id": "contract-confirmation-session", "title": "等待确认任务", "status": "waiting_confirmation", "current_stage": "等待确认票据", "progress_percent": 42, "waiting_confirmation": True, "recoverable": True, "audit_id": "audit_l667_session_confirm", "tags": ["confirmation"]}),
                TaskSessionProjection.from_mapping({"session_id": "contract-recoverable-session", "title": "失败待恢复任务", "status": "recoverable", "current_stage": "等待恢复请求", "progress_percent": 68, "blocked": True, "recoverable": True, "audit_id": "audit_l667_session_recover", "tags": ["recoverable", "resume"]}),
                TaskSessionProjection.from_mapping({"session_id": "contract-completed-session", "title": "已完成归档任务", "status": "completed", "current_stage": "归档完成", "progress_percent": 100, "audit_id": "audit_l667_session_done", "tags": ["completed"]}),
            ]
            stats = SessionManagerStats.from_sessions(sessions).to_dict()
            self._send_json({"session_manager_contract": "tiangong.l6_67.session_manager.v1", "session_manager_state": "ready", "task_sessions": [item.__dict__ for item in sessions], "session_stats": stats, "session_last_message": "契约服务器任务 Session 投影已读取。"})
            return
        self._send_json({"error": "not_found"}, status=404)

    def do_POST(self) -> None:  # noqa: N802 - stdlib handler API
        parsed = self._read_json_body()
        if self.path == CHAT_STREAM_ENDPOINT:
            resume = bool(parsed.get("resume"))
            message = safe_text(parsed.get("message", parsed.get("user_message", "")), 200)
            events = self._chat_events(resume=resume, message=message)
            self._send_sse(events)
            return
        if self.path == PROVIDER_SETTINGS_ENDPOINT:
            self.__class__.provider_settings_payloads.append(parsed)
            request = ProviderSettingsWriteRequest.from_form(parsed)
            if safe_text(parsed.get("api_key", ""), 120).lower().startswith("bad"):
                self._send_json(
                    {
                        "payload": {
                            "status": "rejected",
                            "provider": request.provider,
                            "model": request.model,
                            "api_key_configured": request.api_key_configured,
                            "api_key_digest": digest_text(request.api_key, 16) if request.api_key_configured else "",
                            "base_url_configured": request.base_url_configured,
                            "base_url_digest": digest_text(request.base_url, 16) if request.base_url_configured else "",
                            "config_error_code": "credential_rejected_by_contract_server",
                            "message": "Runtime 拒绝该 Provider 设置请求；前端只展示错误态。",
                            "audit_id": "audit_l657_provider_rejected",
                        }
                    },
                    status=400,
                )
                return
            self._send_json(
                {
                    "payload": {
                        "status": "accepted",
                        "provider": request.provider,
                        "model": request.model,
                        "api_key_configured": request.api_key_configured,
                        "api_key_digest": digest_text(request.api_key, 16) if request.api_key_configured else "",
                        "base_url_configured": request.base_url_configured,
                        "base_url_digest": digest_text(request.base_url, 16) if request.base_url_configured else "",
                        "config_error_code": "",
                        "message": "Runtime 已接收 Provider 设置；密钥由后端受控配置层处理。",
                        "audit_id": "audit_l657_provider_write",
                        "requires_restart": False,
                    }
                }
            )
            return
        if self.path in {TASK_STOP_ENDPOINT, TASK_RESET_ENDPOINT, TASK_INTERRUPT_ENDPOINT}:
            self.__class__.control_payloads.append(parsed)
            action = "interrupt" if self.path == TASK_INTERRUPT_ENDPOINT else ("stop" if self.path == TASK_STOP_ENDPOINT else "reset")
            self._send_json(
                {
                    "action": action,
                    "status": "accepted",
                    "audit_id": f"audit_l657_{action}",
                    "message": f"Runtime 已接收 {action} 请求；前端未直接执行控制动作。",
                }
            )
            return
        if self.path == FILE_TRANSFER_ENDPOINT:
            self.__class__.file_transfer_payloads.append(parsed)
            self._send_json(
                {
                    "payload": {
                        "transfer_id": "ft_l664_contract",
                        "direction": safe_text(parsed.get("direction", "upload"), 32),
                        "file_name": safe_text(parsed.get("file_name", "attachment.bin"), 160),
                        "size_bytes": int(parsed.get("size_bytes", 0) or 0),
                        "sha256_digest": digest_text(parsed.get("sha256", ""), 16),
                        "mime_type": safe_text(parsed.get("mime_type", "application/octet-stream"), 100),
                        "purpose": safe_text(parsed.get("purpose", "user_attachment"), 120),
                        "status": "accepted",
                        "message": "Runtime contract server accepted sanitized file transfer request.",
                        "audit_id": "audit_l664_file_transfer",
                        "route_to_runtime_only": True,
                        "no_frontend_path_exposure": True,
                    }
                }
            )
            return
        if self.path == CONNECTOR_REGISTER_ENDPOINT:
            self.__class__.connector_registration_payloads.append(parsed)
            request = ConnectorRegistrationRequest.build(
                display_name=safe_text(parsed.get("display_name", "contract connector"), 120),
                kind=safe_text(parsed.get("kind", "mcp_server"), 80),
                requested_scopes=parsed.get("requested_scopes", parsed.get("scopes", ["read_public_metadata"])),
                requested_capabilities=parsed.get("requested_capabilities", parsed.get("capabilities", ["contract_probe"])),
                manifest_text=safe_text(parsed.get("manifest_digest", parsed.get("display_name", "contract connector")), 260),
                source_hint="runtime_contract_server_l666",
            )
            record = ConnectorRegistrationPublicRecord.from_request_result(
                request,
                status="accepted",
                message="Runtime contract server accepted sanitized connector registration request.",
                request_id="conn_req_l666_contract",
                audit_id="audit_l666_connector_register",
            )
            self._send_json({"payload": record.to_dict()})
            return
        if self.path == SESSION_RESUME_ENDPOINT:
            self.__class__.session_request_payloads.append(parsed)
            self._send_json({
                "payload": {
                    "status": "accepted",
                    "session_id_digest": safe_text(parsed.get("session_id_digest", ""), 80),
                    "message": "Runtime contract server accepted Session resume request.",
                    "audit_id": "audit_l667_session_resume",
                    "route_to_runtime_only": True,
                    "no_frontend_execute": True,
                }
            })
            return
        if self.path == SESSION_SEARCH_ENDPOINT:
            self.__class__.session_request_payloads.append(parsed)
            query = safe_text(parsed.get("query", ""), 120)
            session = TaskSessionProjection.from_mapping({"session_id": "contract-search-session", "title": f"搜索命中：{query or '全部'}", "status": "queued", "current_stage": "搜索只读投影", "progress_percent": 0, "tags": ["search"]})
            self._send_json({"payload": {"state": "search_completed", "sessions": [session.__dict__], "stats": SessionManagerStats.from_sessions([session]).to_dict(), "message": "Runtime contract server returned sanitized Session search projection."}})
            return
        if self.path == CONFIRMATION_ENDPOINT:
            self.__class__.confirmation_payloads.append(parsed)
            self._send_json(
                {
                    "payload": {
                        "status": "submitted",
                        "audit_id": "audit_l657_confirm",
                        "message": "confirmation request accepted by Runtime gateway",
                    }
                }
            )
            return
        self._send_json({"error": "not_found"}, status=404)

    @staticmethod
    def _chat_events(*, resume: bool = False, message: str = "") -> List[Dict[str, Any]]:
        run_id = "run_l657_resume" if resume else "run_l657"
        task_id = "task_l657"
        if any(term in message.lower() for term in ("code-x", "codex", "代码外骨骼")):
            return [
                {"event": "run_started", "seq": 1, "run_id": run_id, "task_id": task_id, "timestamp": "2026-06-08T00:00:00Z", "payload": {"runtime_status": "active", "provider_model": "deepseek-v4-pro", "code_x_enabled": True}},
                {"event": "planner_plan", "seq": 2, "run_id": run_id, "task_id": task_id, "timestamp": "2026-06-08T00:00:01Z", "payload": {"steps": [{"name": "Code-X Runtime 状态", "status": "queued", "risk_level": "A2"}, {"name": "repo_map", "status": "queued", "risk_level": "A1"}, {"name": "python_quality_runner", "status": "queued", "risk_level": "A3"}]}},
                {"event": "runtime_state", "seq": 3, "run_id": run_id, "task_id": task_id, "timestamp": "2026-06-08T00:00:02Z", "payload": {"phase": "code_x", "progress_percent": 35, "status_bar": {"runtime_status": "active", "provider_model": "deepseek-v4-pro", "budget_pool": "code_x", "budget_used_ratio": "0.18", "gate_status": "A0-A4 allowed / A5 blocked", "audit_id": "audit_codex_stream", "memory_mode": "read_only_projection", "tools_allowed": 66, "latency_ms": 20}}},
                {"event": "tool_started", "seq": 4, "run_id": run_id, "task_id": task_id, "timestamp": "2026-06-08T00:00:03Z", "payload": {"step_id": "step_codex_1", "tool_name": "code_x_runtime_status"}},
                {"event": "tool_result", "seq": 5, "run_id": run_id, "task_id": task_id, "timestamp": "2026-06-08T00:00:04Z", "payload": {"step_id": "step_codex_1", "tool_name": "code_x_runtime_status", "status": "ok", "risk_level": "A2", "audit_ref": "audit_codex_status", "output_summary": "Code-X Runtime tools are registered and callable."}},
                {"event": "tool_result", "seq": 6, "run_id": run_id, "task_id": task_id, "timestamp": "2026-06-08T00:00:05Z", "payload": {"step_id": "step_codex_2", "tool_name": "repo_map", "status": "ok", "risk_level": "A1", "audit_ref": "audit_codex_repo_map", "output_summary": "repo_map completed; next_action_hint=issue_to_file_localizer"}},
                {"event": "assistant_final", "seq": 7, "run_id": run_id, "task_id": task_id, "timestamp": "2026-06-08T00:00:06Z", "payload": {"content": "Code-X 可用链路已进入 Runtime 可见投影。", "status": "ok"}},
                {"event": "run_terminal", "seq": 8, "run_id": run_id, "task_id": task_id, "timestamp": "2026-06-08T00:00:07Z", "payload": {"terminal": True, "final_event_seen": True}},
            ]
        return [
            {"event": "run_started", "seq": 1, "run_id": run_id, "task_id": task_id, "timestamp": "2026-06-07T00:00:00Z", "payload": {"runtime_status": "active", "provider_model": "deepseek-v4-pro"}},
            {"event": "planner_started", "seq": 2, "run_id": run_id, "task_id": task_id, "timestamp": "2026-06-07T00:00:01Z", "payload": {"planner_mode": "model_suggest", "schema_required": True}},
            {"event": "planner_plan", "seq": 3, "run_id": run_id, "task_id": task_id, "timestamp": "2026-06-07T00:00:02Z", "payload": {"normalized_by_plan_schema": True, "steps": [{"name": "检查运行状态", "status": "queued", "risk_level": "A0"}, {"name": "返回摘要", "status": "queued", "risk_level": "A0"}, {"name": "结束任务", "status": "queued", "risk_level": "A0"}]}},
            {"event": "runtime_state", "seq": 4, "run_id": run_id, "task_id": task_id, "timestamp": "2026-06-07T00:00:03Z", "payload": {"phase": "runtime", "progress_percent": 45, "status_bar": {"runtime_status": "active", "provider_model": "deepseek-v4-pro", "budget_pool": "main_task", "budget_used_ratio": "0.34", "gate_status": "A1 allowed", "audit_id": "audit_l657_stream", "memory_mode": "read_only_projection", "tools_allowed": 5, "latency_ms": 24}, "api_key_configured": True, "api_key_digest": digest_text("credential_l656_event_secret", 16), "base_url_configured": True, "base_url_digest": digest_text("contract-server-base-url", 16)}},
            {"event": "quality_gate", "seq": 5, "run_id": run_id, "task_id": task_id, "timestamp": "2026-06-07T00:00:04Z", "payload": {"risk_level": "A1", "decision": "allowed", "quality_gate_id": "gate_l657", "title": "只读烟测行动守卫", "action_summary": "Runtime 执行只读联调 smoke。", "impact_scope": "无写入，审计只读展示。", "plan_steps": ["检查运行状态", "返回摘要", "结束任务"], "audit_id": "audit_l657_gate", "requires_user_confirmation": False}},
            {"event": "tool_started", "seq": 6, "run_id": run_id, "task_id": task_id, "timestamp": "2026-06-07T00:00:05Z", "payload": {"step_id": "step_l657_1", "tool_name": "runtime_status_probe"}},
            {"event": "tool_result", "seq": 7, "run_id": run_id, "task_id": task_id, "timestamp": "2026-06-07T00:00:06Z", "payload": {"step_id": "step_l657_1", "tool_name": "runtime_status_probe", "status": "ok", "audit_ref": "audit_l657_stream", "output_summary": "Runtime contract ready"}},
            {"event": "audit_event", "seq": 8, "run_id": run_id, "task_id": task_id, "timestamp": "2026-06-07T00:00:07Z", "payload": {"audit_id": "audit_l657_stream", "summary": "E2E smoke recorded", "digest_only": True}},
            {"event": "assistant_delta", "seq": 9, "run_id": run_id, "task_id": task_id, "timestamp": "2026-06-07T00:00:08Z", "payload": {"content": "运行状态已检查，"}},
            {"event": "assistant_delta", "seq": 10, "run_id": run_id, "task_id": task_id, "timestamp": "2026-06-07T00:00:09Z", "payload": {"content": "摘要已返回，"}},
            {"event": "assistant_final", "seq": 11, "run_id": run_id, "task_id": task_id, "timestamp": "2026-06-07T00:00:10Z", "payload": {"content": "任务已按 Runtime 契约收口。", "status": "ok"}},
            {"event": "run_terminal", "seq": 12, "run_id": run_id, "task_id": task_id, "timestamp": "2026-06-07T00:00:11Z", "payload": {"terminal": True, "final_event_seen": True}},
        ]

    def log_message(self, _format: str, *args: Any) -> None:
        return


class RuntimeContractServer:
    def __init__(self) -> None:
        RuntimeContractHandler.confirmation_payloads.clear()
        RuntimeContractHandler.control_payloads.clear()
        RuntimeContractHandler.provider_settings_payloads.clear()
        RuntimeContractHandler.file_transfer_payloads.clear()
        RuntimeContractHandler.connector_registration_payloads.clear()
        RuntimeContractHandler.session_request_payloads.clear()
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), RuntimeContractHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, name="l657-runtime-contract-server", daemon=True)

    @property
    def url(self) -> str:
        host, port = self.server.server_address
        return f"http://{host}:{port}"

    def start(self) -> "RuntimeContractServer":
        self.thread.start()
        return self

    def close(self) -> None:
        self.server.shutdown()
        self.server.server_close()

    def __enter__(self) -> "RuntimeContractServer":
        return self.start()

    def __exit__(self, _exc_type: Any, _exc: Any, _tb: Any) -> None:
        self.close()


def start_contract_server() -> Tuple[RuntimeContractServer, str]:
    server = RuntimeContractServer().start()
    return server, server.url
