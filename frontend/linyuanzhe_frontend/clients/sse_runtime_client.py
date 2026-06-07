from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional

from linyuanzhe_frontend.contracts.provider_settings import (
    PROVIDER_SETTINGS_WRITE_CONTRACT_VERSION,
    ProviderSettingsWriteRequest,
    ProviderSettingsWriteResult,
    provider_settings_write_policy,
)
from linyuanzhe_frontend.contracts.runtime_controls import (
    CONTROL_CONTRACT_VERSION,
    RuntimeControlRequest,
    RuntimeControlResult,
    TASK_INTERRUPT_ENDPOINT,
    TASK_RESET_ENDPOINT,
    TASK_STOP_ENDPOINT,
)
from linyuanzhe_frontend.contracts.runtime_snapshot import RuntimeSnapshot, StepSummary, ChatMessage, digest_text, safe_text
from linyuanzhe_frontend.contracts.file_transfer import FILE_TRANSFER_ENDPOINT, FileTransferPublicRecord, FileTransferRequest
from linyuanzhe_frontend.contracts.workspace import FILE_AUTHORIZATION_ENDPOINT, WORKSPACE_POLICY_ENDPOINT, FileAuthorizationPublicRecord, FileAuthorizationRequest, WorkspacePolicyProjection
from linyuanzhe_frontend.contracts.connectors import (
    CONNECTOR_REGISTRY_ENDPOINT,
    CONNECTOR_REGISTER_ENDPOINT,
    ConnectorManifestProjection,
    ConnectorRegistrationPublicRecord,
    ConnectorRegistrationRequest,
    ConnectorRegistryProjection,
    connector_registry_policy,
)
from linyuanzhe_frontend.contracts.session_manager import (
    SESSION_LIST_ENDPOINT,
    SESSION_RESUME_ENDPOINT,
    SESSION_SEARCH_ENDPOINT,
    SessionResumeRequest,
    SessionSearchRequest,
    TaskSessionProjection,
    SessionManagerStats,
)
from linyuanzhe_frontend.contracts.installer_rc import (
    INSTALLER_MANIFEST_ENDPOINT,
    InstallerManifestProjection,
    VersionSlotProjection,
    StartupSelfCheckRecord,
    CrashReportProjection,
    RepairActionRecord,
    installer_rc_policy,
)
from linyuanzhe_frontend.contracts.agent_ui_events import AgentUiEvent, AGENT_UI_CONTRACT_VERSION, agent_ui_policy
from linyuanzhe_frontend.contracts.action_guard import (
    ACTION_GUARD_CONTRACT_VERSION,
    CONFIRMATION_ENDPOINT,
    ActionGuardCard,
    AuditReadonlyCard,
    RollbackReadonlyCard,
    ConfirmationRequestEnvelope,
    action_guard_policy,
    normalize_confirmation_decision,
)
from linyuanzhe_frontend.contracts.streaming_render import EventBuffer, DeltaMerger, VirtualTranscript, STREAM_RENDER_CONTRACT_VERSION, streaming_policy
from linyuanzhe_frontend.contracts.observability import TraceRecord, TraceStats, append_trace_record, observability_policy
from linyuanzhe_frontend.contracts.hook_bus import (
    HOOK_BUS_CONTRACT_VERSION,
    HOOK_STAGE_ON_ERROR,
    HOOK_STAGE_POST_EVENT_APPLY,
    HOOK_STAGE_PRE_CHAT_SUBMIT,
    HOOK_STAGE_PRE_CONFIRMATION_SUBMIT,
    HOOK_STAGE_PRE_CONTROL_REQUEST,
    HOOK_STAGE_PRE_FILE_TRANSFER_REQUEST,
    HOOK_STAGE_PRE_WORKSPACE_AUTHORIZATION_REQUEST,
    HOOK_STAGE_PRE_CONNECTOR_REGISTRATION_REQUEST,
    HOOK_STAGE_PRE_EVENT_APPLY,
    HOOK_STAGE_PRE_FINALIZE,
    HOOK_STAGE_PRE_PROVIDER_SETTINGS_SUBMIT,
    HOOK_STAGE_PRE_SELF_ITERATION_CONFIRM,
    HookBus,
    HookDecision,
    HookStats,
    hook_bus_policy,
)
from linyuanzhe_frontend.contracts.sse_events import (
    CHAT_STREAM_ENDPOINT,
    HEALTH_ENDPOINT,
    PRODUCT_METADATA_ENDPOINT,
    PROVIDER_SETTINGS_ENDPOINT,
    RuntimeSseEvent,
    STATUS_BAR_FIELDS,
    parse_sse_lines,
    sanitize_event_payload,
    validate_terminal_order,
)

SnapshotCallback = Callable[[RuntimeSnapshot], None]
EventCallback = Callable[[RuntimeSseEvent], None]


class SseRuntimeClient:
    """L6.58 official Runtime SSE client with action-guard cards and smooth Agent UI projection.

    The client is a desktop display/submit adapter only. It may contact the
    official Runtime gateway endpoints, consume sanitized SSE/PublicProjection
    events, and send stop/reset/interrupt *requests* to Runtime. It never imports provider
    SDKs, never calls tools/adapters, never writes long-term memory, and never
    applies rollback or self-iteration locally.
    """

    def __init__(self, base_url: str, *, timeout: float = 30.0, max_reconnects: int = 1) -> None:
        cleaned = str(base_url or "").strip().rstrip("/")
        if not cleaned:
            cleaned = "http://127.0.0.1:8787"
        if not urllib.parse.urlparse(cleaned).scheme:
            cleaned = "http://" + cleaned
        self.base_url = cleaned
        self.timeout = float(timeout or 30.0)
        self.max_reconnects = max(0, int(max_reconnects or 0))
        self.endpoint_digest = digest_text(self.base_url, 16)
        self.last_events: List[RuntimeSseEvent] = []
        self.last_agent_ui_events: List[AgentUiEvent] = []
        self._event_buffer = EventBuffer(max_events=512)
        self._delta_merger = DeltaMerger(flush_interval_ms=45, max_chars=1200)
        self._transcript = VirtualTranscript(max_visible_messages=80)
        self.product_identity: Dict[str, Any] = {}
        self.provider_settings: Dict[str, Any] = {}
        self.last_control_result: Dict[str, Any] = {}
        self._active_run_id = ""
        self._active_task_id = ""
        self._last_seq = 0
        self._seen_assistant_final = False
        self._hook_bus = HookBus.default_frontend_bus()
        self._snapshot = RuntimeSnapshot(
            source_kind="runtime_sse",
            runtime_status="未连接",
            connection_status=f"Runtime SSE 待连接：base_url_digest={self.endpoint_digest}",
            current_task_status="DISCONNECTED",
            progress_percent=0,
            current_stage="等待 /health/runtime 或 /chat/stream-events",
            tool_execution_mode="runtime_gateway_only",
            stream_state="idle",
            control_state="ready",
            agent_ui_contract=AGENT_UI_CONTRACT_VERSION,
            stream_render_contract=STREAM_RENDER_CONTRACT_VERSION,
            render_mode="delta_merge_virtual_transcript",
        )
        self._snapshot.trace_records = []
        self._snapshot.trace_stats = TraceStats.from_records([]).to_dict()
        self._snapshot.trace_terminal_order_valid = True
        self._snapshot.trace_export_digest = digest_text(self._snapshot.trace_stats, 16)
        self._sync_hook_projection()
        self._transcript.load(self._snapshot.chat_messages)

    # ------------------------------------------------------------- endpoints
    def _url(self, path: str) -> str:
        if not path.startswith("/"):
            path = "/" + path
        return self.base_url + path

    def _json_request(self, path: str, *, method: str = "GET", payload: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
        data = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(
            self._url(path),
            data=data,
            method=method,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json; charset=utf-8",
                "X-Tiangong-Frontend-Contract": "L6.68",
            },
        )
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            raw = resp.read()
        if not raw:
            return {}
        parsed = json.loads(raw.decode("utf-8", errors="replace"))
        if isinstance(parsed, Mapping):
            return sanitize_event_payload(parsed)
        return {"value": sanitize_event_payload(parsed)}

    # --------------------------------------------------------------- mapping
    def _apply_status_bar(self, mapping: Mapping[str, Any]) -> None:
        for field in STATUS_BAR_FIELDS:
            if field not in mapping:
                continue
            value = mapping[field]
            if field in {"tools_allowed", "latency_ms"}:
                try:
                    setattr(self._snapshot, field, int(value))
                except (TypeError, ValueError):
                    setattr(self._snapshot, field, 0)
            else:
                setattr(self._snapshot, field, safe_text(value, 100))

    def _apply_health(self, data: Mapping[str, Any]) -> None:
        if not data:
            return
        payload = data.get("payload", data)
        if isinstance(payload, Mapping):
            status_bar = payload.get("status_bar") if isinstance(payload.get("status_bar"), Mapping) else payload
            if isinstance(status_bar, Mapping):
                self._apply_status_bar(status_bar)
            self._snapshot.runtime_status = safe_text(payload.get("runtime_status", payload.get("status", "已连接")), 60)
            self._snapshot.connection_status = "Runtime health 已读取"
            self._snapshot.current_task_status = safe_text(payload.get("current_task_status", "READY"), 60)
            self._snapshot.current_stage = safe_text(payload.get("current_stage", "Runtime 已连接，等待任务"), 120)
            self._snapshot.source_kind = "runtime_sse"
            self._sync_derived_projection()

    def _apply_provider_settings(self, data: Mapping[str, Any]) -> None:
        allowed = {
            "provider",
            "model",
            "base_url_digest",
            "base_url_configured",
            "api_key_digest",
            "api_key_configured",
            "timeout",
            "stream",
            "planner_mode",
            "tool_execution_mode",
            "provider_config_state",
            "config_error_code",
            "message",
            "audit_id",
            "requires_restart",
        }
        payload = data.get("payload", data) if isinstance(data, Mapping) else {}
        if not isinstance(payload, Mapping):
            payload = {}
        self.provider_settings = {key: sanitize_event_payload(value) for key, value in payload.items() if key in allowed}
        provider = self.provider_settings.get("provider")
        model = self.provider_settings.get("model")
        if provider or model:
            label = " / ".join([safe_text(x, 50) for x in (provider, model) if x])
            self._snapshot.model_provider = label
            self._snapshot.provider_model = safe_text(model or label, 80)
        if self.provider_settings.get("planner_mode"):
            self._snapshot.planner_mode = safe_text(self.provider_settings.get("planner_mode"), 80)
        if self.provider_settings.get("tool_execution_mode"):
            self._snapshot.tool_execution_mode = safe_text(self.provider_settings.get("tool_execution_mode"), 80)
        if "api_key_configured" in self.provider_settings:
            self._snapshot.provider_api_key_configured = bool(self.provider_settings.get("api_key_configured"))
        if self.provider_settings.get("api_key_digest"):
            self._snapshot.provider_api_key_digest = safe_text(self.provider_settings.get("api_key_digest"), 32)
        if "base_url_configured" in self.provider_settings:
            self._snapshot.provider_base_url_configured = bool(self.provider_settings.get("base_url_configured"))
        if self.provider_settings.get("base_url_digest"):
            self._snapshot.provider_base_url_digest = safe_text(self.provider_settings.get("base_url_digest"), 32)
        if self.provider_settings.get("provider_config_state"):
            self._snapshot.provider_config_state = safe_text(self.provider_settings.get("provider_config_state"), 80)
        if self.provider_settings.get("config_error_code"):
            self._snapshot.provider_config_error_code = safe_text(self.provider_settings.get("config_error_code"), 80)
        if self.provider_settings.get("message"):
            self._snapshot.provider_config_message = safe_text(self.provider_settings.get("message"), 220)
        if self.provider_settings.get("audit_id"):
            self._snapshot.provider_config_audit_id = safe_text(self.provider_settings.get("audit_id"), 80)

    def _apply_product_identity(self, data: Mapping[str, Any]) -> None:
        allowed = {
            "schema",
            "product_name",
            "unique_developer",
            "angel_investor",
            "endpoint",
            "endpoint_digest",
            "endpoint_configured",
            "public",
            "runtime_semantics",
            "frontend_permission",
        }
        self.product_identity = {key: sanitize_event_payload(value) for key, value in data.items() if key in allowed}

    def _apply_connector_registry(self, data: Mapping[str, Any]) -> None:
        payload = data.get("payload", data) if isinstance(data, Mapping) else {}
        if not isinstance(payload, Mapping):
            payload = {}
        registry_payload = payload.get("registry", payload.get("connector_registry_projection", payload))
        if isinstance(registry_payload, Mapping):
            self._snapshot.connector_registry_projection = ConnectorRegistryProjection.from_mapping(registry_payload)
            self._snapshot.connector_registry_state = safe_text(self._snapshot.connector_registry_projection.registry_state, 80)
        manifests = payload.get("connectors", payload.get("connector_manifests", []))
        if isinstance(manifests, list):
            self._snapshot.connector_manifests = [ConnectorManifestProjection.from_mapping(x) for x in manifests if isinstance(x, Mapping)][:40]
        records = payload.get("registration_records", payload.get("connector_registration_records", []))
        if isinstance(records, list):
            self._snapshot.connector_registration_records = [ConnectorRegistrationPublicRecord.from_mapping(x) for x in records if isinstance(x, Mapping)][:40]
        self._snapshot.connector_last_message = safe_text(payload.get("message", "连接器注册表投影已读取"), 220)

    def _apply_session_manager(self, data: Mapping[str, Any]) -> None:
        payload = data.get("payload", data) if isinstance(data, Mapping) else {}
        if not isinstance(payload, Mapping):
            payload = {}
        sessions_payload = payload.get("task_sessions", payload.get("sessions", []))
        sessions: list[TaskSessionProjection] = []
        if isinstance(sessions_payload, list):
            sessions = [TaskSessionProjection.from_mapping(x) for x in sessions_payload if isinstance(x, Mapping)][:80]
        if sessions:
            self._snapshot.task_sessions = sessions
            stats_payload = payload.get("session_stats", payload.get("stats", {}))
            self._snapshot.session_stats = dict(stats_payload) if isinstance(stats_payload, Mapping) else SessionManagerStats.from_sessions(sessions).to_dict()
            self._snapshot.session_filtered_count = len(sessions)
        self._snapshot.session_manager_state = safe_text(payload.get("session_manager_state", payload.get("state", "ready")), 80)
        self._snapshot.session_last_message = safe_text(payload.get("session_last_message", payload.get("message", "任务 Session 投影已读取")), 220)

    def _apply_installer_manifest(self, data: Mapping[str, Any]) -> None:
        payload = data.get("payload", data) if isinstance(data, Mapping) else {}
        if not isinstance(payload, Mapping):
            payload = {}
        manifest_payload = payload.get("installer_manifest", payload)
        if isinstance(manifest_payload, Mapping):
            manifest = InstallerManifestProjection.from_mapping(manifest_payload)
            self._snapshot.installer_manifest = manifest
            self._snapshot.installer_rc_contract = manifest.contract_version
            self._snapshot.installer_stage = safe_text(manifest.package_stage, 80)
            self._snapshot.update_channel = safe_text(manifest.update_channel, 80)
            self._snapshot.startup_self_check_state = safe_text(manifest.startup_self_check_state, 80)
            self._snapshot.version_slots = list(manifest.slots)
            self._snapshot.startup_self_checks = list(manifest.startup_checks)
            self._snapshot.crash_report_records = list(manifest.crash_reports)
            self._snapshot.repair_action_records = list(manifest.repair_actions)
        slots_payload = payload.get("version_slots")
        if isinstance(slots_payload, list):
            self._snapshot.version_slots = [VersionSlotProjection.from_mapping(x) for x in slots_payload if isinstance(x, Mapping)][:40]
        checks_payload = payload.get("startup_self_checks")
        if isinstance(checks_payload, list):
            self._snapshot.startup_self_checks = [StartupSelfCheckRecord.from_mapping(x) for x in checks_payload if isinstance(x, Mapping)][:40]
        crash_payload = payload.get("crash_report_records", payload.get("crash_reports", []))
        if isinstance(crash_payload, list):
            self._snapshot.crash_report_records = [CrashReportProjection.from_mapping(x) for x in crash_payload if isinstance(x, Mapping)][:20]
        repair_payload = payload.get("repair_action_records", payload.get("repair_actions", []))
        if isinstance(repair_payload, list):
            self._snapshot.repair_action_records = [RepairActionRecord.from_mapping(x) for x in repair_payload if isinstance(x, Mapping)][:20]
        self._snapshot.installer_last_message = safe_text(payload.get("installer_last_message", payload.get("message", "安装器 RC 投影已读取")), 220)

    def _sync_hook_projection(self) -> None:
        stats = self._hook_bus.stats()
        self._snapshot.hook_bus_contract = HOOK_BUS_CONTRACT_VERSION
        self._snapshot.hook_enabled = True
        self._snapshot.hook_records = list(self._hook_bus.records)
        self._snapshot.hook_stats = stats.to_dict()
        self._snapshot.hook_last_blocker = safe_text(stats.last_blocker, 220)
        self._snapshot.hook_export_digest = self._hook_bus.export_digest()

    def _evaluate_hook(self, stage: str, context: Mapping[str, Any]) -> HookDecision:
        decision = self._hook_bus.evaluate(stage, context)
        self._sync_hook_projection()
        return decision

    def _apply_hook_block(self, event: RuntimeSseEvent, decision: HookDecision) -> None:
        reason = safe_text(decision.reason, 220)
        self._snapshot.current_task_status = "BLOCKED"
        self._snapshot.stream_state = "error"
        self._snapshot.runtime_status = "hook_blocked"
        self._snapshot.connection_status = f"HookBus blocked {safe_text(event.event, 80)}：{reason}"
        self._snapshot.quality_decision = "blocked_by_hook"
        self._snapshot.quality_allow_continue = False
        if event.event == "quality_gate":
            self._snapshot.gate_status = "A5 blocked_by_hook"
            self._snapshot.quality_gate_status = "A5 blocked_by_hook"
        if reason and reason not in self._snapshot.blocking_reasons:
            self._snapshot.blocking_reasons.append(reason)
        trace_record = TraceRecord(
            seq=int(event.seq or self._last_seq or 0),
            event_type="hook_blocked",
            source_event=safe_text(event.event, 80),
            category="error",
            phase="HookBus",
            status="blocked",
            decision=decision.verdict,
            run_id_digest=digest_text(event.run_id, 16),
            task_id_digest=digest_text(event.task_id, 16),
            message=reason,
            payload_summary={"rule_id": decision.rule_id, "severity": decision.severity},
        )
        self._snapshot.trace_records = append_trace_record(self._snapshot.trace_records, trace_record)
        self._snapshot.trace_stats = TraceStats.from_records(self._snapshot.trace_records).to_dict()
        self._snapshot.trace_terminal_order_valid = bool(self._snapshot.trace_stats.get("terminal_order_valid", True))
        self._snapshot.trace_export_digest = digest_text(self._snapshot.trace_stats, 16)
        self._sync_hook_projection()


    def _upsert_action_guard_card(self, card: ActionGuardCard) -> None:
        cards = list(self._snapshot.action_guard_cards)
        for idx, existing in enumerate(cards):
            if existing.ticket_id and existing.ticket_id == card.ticket_id:
                cards[idx] = card
                self._snapshot.action_guard_cards = cards
                return
            if existing.gate_id and existing.gate_id == card.gate_id:
                cards[idx] = card
                self._snapshot.action_guard_cards = cards
                return
        cards.append(card)
        self._snapshot.action_guard_cards = cards[-20:]

    def _append_audit_readonly_card(self, card: AuditReadonlyCard) -> None:
        cards = [item for item in self._snapshot.audit_readonly_cards if item.audit_id != card.audit_id or not card.audit_id]
        cards.append(card)
        self._snapshot.audit_readonly_cards = cards[-20:]

    def _append_rollback_readonly_card(self, card: RollbackReadonlyCard) -> None:
        cards = [item for item in self._snapshot.rollback_readonly_cards if item.ticket_id != card.ticket_id or not card.ticket_id]
        cards.append(card)
        self._snapshot.rollback_readonly_cards = cards[-20:]



    def _record_agent_ui_event(self, event: RuntimeSseEvent) -> AgentUiEvent:
        ui_event = AgentUiEvent.from_runtime_event(event)
        self.last_agent_ui_events.append(ui_event)
        self._event_buffer.push(ui_event)
        trace_record = TraceRecord.from_mapping(ui_event.to_dict())
        # Preserve Runtime timestamp if present; UI event intentionally stores
        # only a sanitized, digest-only run/task projection.
        if event.timestamp:
            trace_record.timestamp = safe_text(event.timestamp, 80)
        self._snapshot.trace_records = append_trace_record(self._snapshot.trace_records, trace_record)
        self._snapshot.trace_stats = TraceStats.from_records(self._snapshot.trace_records).to_dict()
        self._snapshot.trace_terminal_order_valid = bool(self._snapshot.trace_stats.get("terminal_order_valid", True))
        self._snapshot.trace_export_digest = digest_text(self._snapshot.trace_stats, 16)
        self._snapshot.agent_ui_event_count = len(self.last_agent_ui_events)
        self._snapshot.pending_event_buffer_count = len(self._event_buffer)
        return ui_event

    def _flush_pending_assistant_delta(self, *, force: bool = False) -> None:
        merged = self._delta_merger.flush(force=force)
        if merged:
            self._transcript.append_assistant_delta(merged)
            self._snapshot.chat_messages = self._transcript.visible_messages()
            self._snapshot.visible_message_count = self._transcript.visible_message_count
            self._snapshot.hidden_message_count = self._transcript.hidden_message_count
        self._snapshot.pending_delta_chars = self._delta_merger.pending_chars

    def _step_from_any(self, item: Any, default_status: str = "queued") -> StepSummary:
        if isinstance(item, Mapping):
            return StepSummary.from_mapping({**item, "status": item.get("status") or item.get("state") or default_status})
        return StepSummary(name=safe_text(item, 80), status=default_status, risk_level="A0")

    def _append_or_update_step(self, *, step_id: str = "", tool_name: str = "", status: str = "running", audit_ref: str = "", output_summary: str = "") -> None:
        target_name = safe_text(tool_name or step_id or "runtime_step", 80)
        for idx, step in enumerate(self._snapshot.execution_steps):
            if step.audit_ref and audit_ref and step.audit_ref == audit_ref:
                self._snapshot.execution_steps[idx] = StepSummary(target_name or step.name, status, step.risk_level, audit_ref, output_summary or step.output_summary)
                return
            if step.name == target_name:
                self._snapshot.execution_steps[idx] = StepSummary(step.name, status, step.risk_level, audit_ref or step.audit_ref, output_summary or step.output_summary)
                return
        self._snapshot.execution_steps.append(StepSummary(target_name, status, "A0", audit_ref, output_summary))

    def _apply_event(self, event: RuntimeSseEvent) -> None:
        name = event.event
        payload = event.payload or {}
        pre_decision = self._evaluate_hook(
            HOOK_STAGE_PRE_EVENT_APPLY,
            {
                "event": name,
                "payload": payload,
                "run_id": event.run_id,
                "task_id": event.task_id,
                "seq": event.seq,
                "seen_assistant_final": self._seen_assistant_final,
            },
        )
        if not pre_decision.ok:
            self._apply_hook_block(event, pre_decision)
            self._sync_derived_projection()
            return
        ui_event = self._record_agent_ui_event(event)
        self._snapshot.source_kind = "runtime_sse"
        self._snapshot.stream_state = "streaming"
        if event.seq:
            self._last_seq = max(self._last_seq, int(event.seq))
            self._snapshot.last_event_seq = self._last_seq
        if event.run_id:
            self._active_run_id = event.run_id
            self._snapshot.session_id = event.run_id
            self._snapshot.active_run_id = event.run_id
        if event.task_id:
            self._active_task_id = event.task_id
            self._snapshot.task_snapshot.task_id = event.task_id
            self._snapshot.active_task_id = event.task_id

        if name == "run_started":
            self._snapshot.runtime_status = safe_text(payload.get("runtime_status", "active"), 60)
            self._snapshot.current_task_status = "RUNNING"
            self._snapshot.connection_status = "Runtime SSE 已连接"
            if payload.get("provider_model"):
                self._snapshot.provider_model = safe_text(payload.get("provider_model"), 80)
                self._snapshot.model_provider = self._snapshot.provider_model
            self._snapshot.progress_percent = max(self._snapshot.progress_percent, 5)
        elif name == "planner_started":
            self._snapshot.planner_mode = safe_text(payload.get("planner_mode", self._snapshot.planner_mode), 80)
            self._snapshot.current_stage = "Planner 正在生成计划"
            self._snapshot.progress_percent = max(self._snapshot.progress_percent, 15)
        elif name == "planner_plan":
            raw_steps = payload.get("steps") or []
            if isinstance(raw_steps, str):
                raw_steps = [raw_steps]
            if isinstance(raw_steps, Iterable):
                self._snapshot.execution_steps = [self._step_from_any(item) for item in list(raw_steps)[:50]] or self._snapshot.execution_steps
            self._snapshot.execution_stage = "Plan 已通过 plan_schema normalize"
            self._snapshot.task_snapshot.current_stage = "Plan 已生成"
            self._snapshot.progress_percent = max(self._snapshot.progress_percent, 25)
        elif name == "runtime_state":
            status_bar = payload.get("status_bar") if isinstance(payload.get("status_bar"), Mapping) else payload
            if isinstance(status_bar, Mapping):
                self._apply_status_bar(status_bar)
            self._snapshot.current_stage = safe_text(payload.get("phase", self._snapshot.current_stage), 100)
            if payload.get("status"):
                self._snapshot.current_task_status = safe_text(payload.get("status"), 60)
            if payload.get("progress_percent") is not None:
                try:
                    self._snapshot.progress_percent = max(0, min(100, int(payload.get("progress_percent"))))
                except (TypeError, ValueError):
                    self._snapshot.connection_status = "Runtime progress_percent 非法，已忽略"
        elif name == "quality_gate":
            risk = safe_text(payload.get("risk_level", "A0"), 16)
            decision = safe_text(payload.get("decision", "allowed"), 64)
            guard_card = ActionGuardCard.from_quality_gate_payload(payload)
            self._upsert_action_guard_card(guard_card)
            self._snapshot.action_guard_contract = ACTION_GUARD_CONTRACT_VERSION
            self._snapshot.quality_decision = decision
            self._snapshot.gate_status = f"{risk} {decision}".strip()
            self._snapshot.quality_gate_status = self._snapshot.gate_status
            self._snapshot.quality_allow_continue = decision not in {"blocked", "A5 blocked", "confirmation_required", "requires_confirmation"}
            if guard_card.requires_user_confirmation:
                self._snapshot.pending_confirmation_count = max(self._snapshot.pending_confirmation_count, 1)
                self._snapshot.task_snapshot.waiting_user_confirmation = True
                ticket_id = guard_card.ticket_id or guard_card.gate_id
                if ticket_id and not any(safe_text(item.get("ticket_id", ""), 80) == ticket_id for item in self._snapshot.pending_confirmations):
                    self._snapshot.pending_confirmations.append({
                        "ticket_id": ticket_id,
                        "title": guard_card.title,
                        "risk_level": guard_card.risk_level,
                        "action_summary": guard_card.action_summary,
                        "impact_scope": guard_card.impact_scope,
                        "audit_ref": guard_card.audit_ref,
                        "rollback_ref": guard_card.rollback_ref,
                        "frontend_contract": ACTION_GUARD_CONTRACT_VERSION,
                        "route_to_runtime_only": True,
                    })
            if guard_card.audit_ref:
                self._snapshot.audit_id = guard_card.audit_ref
                self._snapshot.evidence_ref = guard_card.audit_ref
            if guard_card.rollback_ref:
                self._append_rollback_readonly_card(RollbackReadonlyCard.from_payload(payload))
            if risk == "A5" and decision != "allowed":
                self._snapshot.current_task_status = "BLOCKED"
            self._snapshot.progress_percent = max(self._snapshot.progress_percent, 40)
        elif name == "tool_started":
            self._append_or_update_step(step_id=safe_text(payload.get("step_id", ""), 80), tool_name=safe_text(payload.get("tool_name", ""), 80), status="running")
            self._snapshot.progress_percent = max(self._snapshot.progress_percent, 50)
        elif name == "tool_result":
            self._append_or_update_step(
                step_id=safe_text(payload.get("step_id", ""), 80),
                tool_name=safe_text(payload.get("tool_name", ""), 80),
                status=safe_text(payload.get("status", "ok"), 32),
                audit_ref=safe_text(payload.get("audit_ref", ""), 80),
                output_summary=safe_text(payload.get("output_summary", ""), 180),
            )
            self._snapshot.success_count = sum(1 for step in self._snapshot.execution_steps if step.status in {"ok", "succeeded", "success"})
            self._snapshot.blocked_count = sum(1 for step in self._snapshot.execution_steps if step.status in {"blocked", "failed", "timeout"})
            self._snapshot.progress_percent = max(self._snapshot.progress_percent, 60)
        elif name == "audit_event":
            audit_id = safe_text(payload.get("audit_id", payload.get("audit_ref", "")), 80)
            if audit_id:
                self._snapshot.audit_id = audit_id
                self._snapshot.evidence_ref = audit_id
            self._snapshot.audit_count += 1
            self._append_audit_readonly_card(AuditReadonlyCard.from_payload(payload, count=self._snapshot.audit_count))
        elif name in {"rollback_ticket", "rollback_event"}:
            self._append_rollback_readonly_card(RollbackReadonlyCard.from_payload(payload))
            rollback_ref = safe_text(payload.get("rollback_ticket") or payload.get("rollback_ref") or payload.get("ticket_id"), 80)
            if rollback_ref:
                self._snapshot.recovery_ticket_id = rollback_ref
            self._snapshot.recovery_requires_human_confirmation = bool(payload.get("requires_human_confirmation", False))
        elif name == "assistant_delta":
            content = safe_text(payload.get("content", ""), 1200)
            if content:
                self._delta_merger.push(content)
                self._flush_pending_assistant_delta(force=False)
            self._snapshot.current_stage = "Runtime 正在流式输出"
            self._snapshot.chat_messages = self._transcript.visible_messages()
            self._snapshot.visible_message_count = self._transcript.visible_message_count
        elif name == "assistant_final":
            self._seen_assistant_final = True
            self._flush_pending_assistant_delta(force=True)
            content = safe_text(payload.get("content", ""), 1000)
            status = safe_text(payload.get("status", "ok"), 64)
            if content:
                self._transcript.finalize_assistant(content)
                self._snapshot.chat_messages = self._transcript.visible_messages()
                self._snapshot.visible_message_count = self._transcript.visible_message_count
                self._snapshot.hidden_message_count = self._transcript.hidden_message_count
            self._snapshot.current_task_status = "COMPLETED" if status == "ok" else "PARTIAL_OR_FAILED"
            self._snapshot.progress_percent = max(self._snapshot.progress_percent, 90)
        elif name == "run_terminal":
            self._flush_pending_assistant_delta(force=True)
            self._snapshot.stream_state = "completed"
            self._snapshot.connection_status = "Runtime SSE 已收口：assistant_final -> run_terminal"
            self._snapshot.progress_percent = 100 if self._snapshot.current_task_status == "COMPLETED" else self._snapshot.progress_percent
        elif name == "error":
            message = safe_text(payload.get("message", "Runtime SSE error"), 500)
            code = safe_text(payload.get("error_code", "runtime_error"), 80)
            self._snapshot.current_task_status = "PARTIAL_OR_FAILED"
            self._snapshot.runtime_status = "error"
            self._snapshot.stream_state = "error"
            self._snapshot.connection_status = f"Runtime error：{code}"
            self._transcript.finalize_assistant(message, time="错误")
            self._snapshot.chat_messages = self._transcript.visible_messages()
            self._snapshot.visible_message_count = self._transcript.visible_message_count
            self._snapshot.hidden_message_count = self._transcript.hidden_message_count

        post_decision = self._evaluate_hook(
            HOOK_STAGE_POST_EVENT_APPLY,
            {"event": name, "payload": payload, "run_id": event.run_id, "task_id": event.task_id, "seq": event.seq},
        )
        if not post_decision.ok:
            self._apply_hook_block(event, post_decision)
        self._sync_derived_projection()

    def _sync_derived_projection(self) -> None:
        s = self._snapshot
        s.task_snapshot.current_stage = s.current_stage
        s.task_snapshot.current_step = next((step.name for step in s.execution_steps if step.status in {"running", "queued", "confirmation_required"}), s.execution_stage)
        s.task_snapshot.completed_steps = [step.name for step in s.execution_steps if step.status in {"ok", "succeeded", "success"}][:5]
        s.task_snapshot.failed_steps = [step.name for step in s.execution_steps if step.status in {"failed", "blocked", "timeout"}][:5]
        s.task_snapshot.budget_state = f"{s.budget_pool} / {s.budget_used_ratio}"
        s.task_snapshot.tool_state = f"allowed={s.tools_allowed}"
        s.task_snapshot.snapshot_ref = s.audit_id or s.evidence_ref
        s.conversation_guide.intent_summary = f"当前 Runtime 状态：{s.current_task_status}"
        s.conversation_guide.risk_hint = s.gate_status
        if s.action_guard_cards:
            s.conversation_guide.recommended_actions = ["查看行动守卫卡", "提交确认请求", "必要时中断任务"]
            s.conversation_guide.suggested_questions = ["请解释这张行动守卫卡为什么需要确认", "如果拒绝会怎样", "只执行低风险部分"]
            s.pending_confirmation_count = sum(1 for card in s.action_guard_cards if card.requires_user_confirmation and card.status in {"pending_user_confirmation", "display_only"})
        elif s.file_transfer_records and getattr(s.file_transfer_records[-1], "status", "") not in {"ready", "idle"}:
            s.conversation_guide.recommended_actions = ["让临渊者读取附件摘要", "确认文件用途", "必要时中断任务"]
            s.conversation_guide.suggested_questions = ["请基于附件继续分析", "请列出附件中的风险点", "请生成下一步执行计划"]
        else:
            s.conversation_guide.recommended_actions = ["继续对话", "上传附件", "必要时中断任务"]
            s.conversation_guide.suggested_questions = ["下一步", "把当前任务拆成三步", "先给我风险和阻断项"]
        s.pending_event_buffer_count = len(self._event_buffer)
        s.agent_ui_event_count = len(self.last_agent_ui_events)
        s.pending_delta_chars = self._delta_merger.pending_chars
        s.visible_message_count = self._transcript.visible_message_count
        s.hidden_message_count = self._transcript.hidden_message_count
        self._sync_hook_projection()

    def _connection_failure_snapshot(self, reason: str) -> RuntimeSnapshot:
        self._snapshot.runtime_status = "连接失败"
        self._snapshot.connection_status = safe_text(reason, 180)
        self._snapshot.current_task_status = "DISCONNECTED"
        self._snapshot.stream_state = "error"
        self._snapshot.current_stage = "Runtime SSE 连接失败，保持前端可用"
        self._snapshot.source_kind = "runtime_sse_disconnected"
        self._transcript.finalize_assistant(safe_text(reason, 500), time="连接")
        self._snapshot.chat_messages = self._transcript.visible_messages()
        self._evaluate_hook(HOOK_STAGE_ON_ERROR, {"error": reason, "payload": {"message": reason}})
        self._sync_derived_projection()
        return self._snapshot

    def _notify_snapshot(self, callback: Optional[SnapshotCallback]) -> None:
        if callback:
            callback(self._snapshot)

    # ---------------------------------------------------------- public client
    def get_status(self) -> Dict[str, Any]:
        s = self._snapshot
        return {
            "runtime_status": s.runtime_status,
            "model_provider": s.model_provider,
            "planner_mode": s.planner_mode,
            "tool_execution_mode": s.tool_execution_mode,
            "connection_status": s.connection_status,
            "endpoint_digest": self.endpoint_digest,
            "stream_state": s.stream_state,
            "reconnect_attempts": s.reconnect_attempts,
            "control_state": s.control_state,
        }

    def get_tools(self) -> List[Dict[str, Any]]:
        return []

    def get_policy(self) -> Dict[str, Any]:
        return {
            "frontend_mode": "runtime_sse_gateway_only",
            "frontend_contract": "L6.68",
            "no_direct_provider_call": True,
            "no_provider_call": True,
            "no_direct_tool_execution": True,
            "no_tool_execution": True,
            "no_kernel_mutation": True,
            "no_direct_memory_write": True,
            "no_frontend_rollback_apply": True,
            "official_endpoint": CHAT_STREAM_ENDPOINT,
            "control_contract": CONTROL_CONTRACT_VERSION,
            "control_endpoints": [TASK_STOP_ENDPOINT, TASK_RESET_ENDPOINT, TASK_INTERRUPT_ENDPOINT],
            "file_transfer_endpoint": FILE_TRANSFER_ENDPOINT,
            "workspace_policy_endpoint": WORKSPACE_POLICY_ENDPOINT,
            "file_authorization_endpoint": FILE_AUTHORIZATION_ENDPOINT,
            "connector_registry_endpoint": CONNECTOR_REGISTRY_ENDPOINT,
            "connector_register_endpoint": CONNECTOR_REGISTER_ENDPOINT,
            "session_list_endpoint": SESSION_LIST_ENDPOINT,
            "session_resume_endpoint": SESSION_RESUME_ENDPOINT,
            "session_search_endpoint": SESSION_SEARCH_ENDPOINT,
            "installer_manifest_endpoint": INSTALLER_MANIFEST_ENDPOINT,
            "endpoint_digest": self.endpoint_digest,
            "runtime_may_execute_after_quality_gate": True,
            "agent_ui_policy": agent_ui_policy(),
            "streaming_policy": streaming_policy(),
            "observability_policy": observability_policy(),
            "hook_bus_policy": hook_bus_policy(),
            "action_guard_policy": action_guard_policy(),
            "provider_settings_write_policy": provider_settings_write_policy(),
            "connector_registry_policy": connector_registry_policy(),
            "installer_rc_policy": installer_rc_policy(),
        }

    def get_planner_execution(self) -> Dict[str, Any]:
        return {"execution_stage": self._snapshot.execution_stage, "steps": [step.__dict__ for step in self._snapshot.execution_steps]}

    def get_public_projection(self) -> Dict[str, Any]:
        return self._snapshot.to_dict()

    def get_audit_summary(self) -> Dict[str, Any]:
        return {"audit_count": self._snapshot.audit_count, "evidence_ref": self._snapshot.evidence_ref, "audit_id": self._snapshot.audit_id}

    def get_quality_gate(self) -> Dict[str, Any]:
        return {
            "decision": self._snapshot.quality_decision,
            "allow_continue": self._snapshot.quality_allow_continue,
            "allow_package": self._snapshot.quality_allow_package,
            "gate_status": self._snapshot.quality_gate_status,
            "blocking_reasons": self._snapshot.blocking_reasons,
            "action_guard_cards": [card.to_dict() for card in self._snapshot.action_guard_cards],
        }

    def get_memory_summary(self) -> Dict[str, Any]:
        return {"sanitized_summary": self._snapshot.memory_sanitized_summary, "digest": self._snapshot.memory_digest, "evidence_ref": self._snapshot.memory_evidence_ref}

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

    def get_product_identity(self) -> Dict[str, Any]:
        if self.product_identity:
            return dict(self.product_identity)
        return {}

    def get_provider_settings(self) -> Dict[str, Any]:
        if self.provider_settings:
            return dict(self.provider_settings)
        return {}

    def refresh_snapshot(self) -> RuntimeSnapshot:
        try:
            self._apply_health(self._json_request(HEALTH_ENDPOINT))
        except Exception as exc:
            return self._connection_failure_snapshot(f"/health/runtime 读取失败：{safe_text(exc, 160)}")
        try:
            self._apply_product_identity(self._json_request(PRODUCT_METADATA_ENDPOINT))
        except Exception as exc:
            self.product_identity = {"read_error": safe_text(exc, 160)}
        try:
            self._apply_provider_settings(self._json_request(PROVIDER_SETTINGS_ENDPOINT))
        except Exception as exc:
            self.provider_settings = {"read_error": safe_text(exc, 160)}
        try:
            self._apply_connector_registry(self._json_request(CONNECTOR_REGISTRY_ENDPOINT))
        except Exception as exc:
            self._snapshot.connector_last_message = f"连接器注册表读取失败：{safe_text(exc, 160)}"
        try:
            self._apply_session_manager(self._json_request(SESSION_LIST_ENDPOINT))
        except Exception as exc:
            self._snapshot.session_last_message = f"任务 Session 投影读取失败：{safe_text(exc, 160)}"
        try:
            self._apply_installer_manifest(self._json_request(INSTALLER_MANIFEST_ENDPOINT))
        except Exception as exc:
            self._snapshot.installer_last_message = f"安装器 RC 投影读取失败：{safe_text(exc, 160)}"
        self._sync_derived_projection()
        return self._snapshot

    def submit_provider_settings(self, raw: Mapping[str, Any]) -> Dict[str, Any]:
        """Submit write-only Provider settings to Runtime and keep only ack projection.

        The outbound request may contain raw api_key/base_url because Runtime owns
        credential storage. The returned value, self.provider_settings, snapshot,
        and UI status are digest-only and safe to display/report.
        """

        request = ProviderSettingsWriteRequest.from_form(raw)
        self._snapshot.provider_settings_contract = PROVIDER_SETTINGS_WRITE_CONTRACT_VERSION
        runtime_payload = request.to_runtime_payload()
        hook_decision = self._evaluate_hook(HOOK_STAGE_PRE_PROVIDER_SETTINGS_SUBMIT, {"payload": runtime_payload})
        if not hook_decision.ok:
            result = ProviderSettingsWriteResult.from_error(
                f"HookBus blocked provider settings request: {hook_decision.reason}",
                provider=request.provider,
                model=request.model,
            )
        else:
            try:
                data = self._json_request(PROVIDER_SETTINGS_ENDPOINT, method="POST", payload=runtime_payload)
                result = ProviderSettingsWriteResult.from_runtime_response(data)
            except urllib.error.HTTPError as exc:
                body = b""
                try:
                    body = exc.read()
                except Exception:
                    body = b""
                message = f"HTTP {exc.code}"
                if body:
                    try:
                        parsed = json.loads(body.decode("utf-8", errors="replace"))
                        result = ProviderSettingsWriteResult.from_runtime_response(parsed if isinstance(parsed, Mapping) else {})
                        if result.status == "submitted":
                            result = ProviderSettingsWriteResult(
                                status="rejected",
                                provider=request.provider,
                                model=request.model,
                                config_error_code=result.config_error_code or f"http_{exc.code}",
                                message=result.message or message,
                            )
                    except Exception:
                        result = ProviderSettingsWriteResult.from_error(message, provider=request.provider, model=request.model)
                else:
                    result = ProviderSettingsWriteResult.from_error(message, provider=request.provider, model=request.model)
            except Exception as exc:
                result = ProviderSettingsWriteResult.from_error(exc, provider=request.provider, model=request.model)

        public = result.to_dict()
        # Keep local request digests when Runtime omits them, without preserving raw values.
        request_public = request.to_public_dict()
        for key in ("api_key_configured", "api_key_digest", "base_url_configured", "base_url_digest"):
            if not public.get(key):
                public[key] = request_public.get(key)
        if not public.get("provider"):
            public["provider"] = request.provider
        if not public.get("model"):
            public["model"] = request.model

        self.provider_settings = {key: sanitize_event_payload(value) for key, value in public.items()}
        self._snapshot.provider_config_state = safe_text(public.get("status", "submitted"), 80)
        self._snapshot.provider_config_message = safe_text(public.get("message", "Runtime Provider 设置请求已提交"), 220)
        self._snapshot.provider_config_error_code = safe_text(public.get("config_error_code", ""), 80)
        self._snapshot.provider_config_audit_id = safe_text(public.get("audit_id", ""), 80)
        self._snapshot.provider_api_key_configured = bool(public.get("api_key_configured"))
        self._snapshot.provider_api_key_digest = safe_text(public.get("api_key_digest", ""), 32)
        self._snapshot.provider_base_url_configured = bool(public.get("base_url_configured"))
        self._snapshot.provider_base_url_digest = safe_text(public.get("base_url_digest", ""), 32)
        if public.get("provider") or public.get("model"):
            label = " / ".join([safe_text(x, 50) for x in (public.get("provider"), public.get("model")) if x])
            self._snapshot.model_provider = label
            self._snapshot.provider_model = safe_text(public.get("model") or label, 80)
        self._sync_derived_projection()
        return dict(self.provider_settings)

    def _chat_payload(self, safe_message: str, *, resume: bool = False) -> Dict[str, Any]:
        body: Dict[str, Any] = {
            "message": safe_message,
            "user_message": safe_message,
            "frontend_contract": "L6.68",
            "transport": "sse",
            "no_frontend_tool_execution": True,
            "no_frontend_memory_write": True,
            "no_frontend_rollback_apply": True,
        }
        if resume and self._active_run_id:
            body["resume"] = {"run_id": self._active_run_id, "last_seq": self._last_seq}
        hook_decision = self._evaluate_hook(HOOK_STAGE_PRE_CHAT_SUBMIT, {"payload": body, "run_id": self._active_run_id, "task_id": self._active_task_id})
        if not hook_decision.ok:
            raise RuntimeError(f"HookBus blocked chat submit: {hook_decision.reason}")
        return body

    def _open_chat_stream(self, body: Mapping[str, Any]):
        req = urllib.request.Request(
            self._url(CHAT_STREAM_ENDPOINT),
            data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
            method="POST",
            headers={
                "Accept": "text/event-stream, application/json",
                "Content-Type": "application/json; charset=utf-8",
                "Cache-Control": "no-cache",
                "X-Tiangong-Frontend-Contract": "L6.68",
            },
        )
        return urllib.request.urlopen(req, timeout=self.timeout)

    def _consume_response(
        self,
        response: Any,
        events: List[RuntimeSseEvent],
        *,
        on_event: Optional[EventCallback] = None,
        on_snapshot: Optional[SnapshotCallback] = None,
    ) -> None:
        content_type = response.headers.get("Content-Type", "")
        if "text/event-stream" in content_type:
            for event in parse_sse_lines(iter(response.readline, b"")):
                events.append(event)
                self._apply_event(event)
                if on_event:
                    on_event(event)
                self._notify_snapshot(on_snapshot)
            return

        raw = response.read()
        parsed = json.loads(raw.decode("utf-8", errors="replace")) if raw else {}
        if isinstance(parsed, Mapping) and "events" in parsed and isinstance(parsed["events"], list):
            for item in parsed["events"]:
                event = RuntimeSseEvent.from_mapping(item)
                events.append(event)
                self._apply_event(event)
                if on_event:
                    on_event(event)
                self._notify_snapshot(on_snapshot)
        elif isinstance(parsed, Mapping):
            snapshot_data = sanitize_event_payload(parsed.get("snapshot", parsed))
            if isinstance(snapshot_data, Mapping):
                self._snapshot = RuntimeSnapshot.from_mapping({**self._snapshot.to_dict(), **snapshot_data, "source_kind": "runtime_json_response"})
                self._notify_snapshot(on_snapshot)
        else:
            self._snapshot.chat_messages.append(ChatMessage("assistant", "临渊者", "响应", safe_text(parsed, 500)))
            self._notify_snapshot(on_snapshot)

    def submit_user_message(self, text: str) -> RuntimeSnapshot:
        return self.submit_user_message_streaming(text)

    def submit_user_message_streaming(
        self,
        text: str,
        *,
        on_event: Optional[EventCallback] = None,
        on_snapshot: Optional[SnapshotCallback] = None,
        max_reconnects: Optional[int] = None,
    ) -> RuntimeSnapshot:
        safe_message = safe_text(text, 1000)
        self._snapshot.chat_messages.append(ChatMessage("user", "你", "当前", safe_message))
        self._transcript.load(self._snapshot.chat_messages)
        self._delta_merger = DeltaMerger(flush_interval_ms=45, max_chars=1200)
        self._event_buffer = EventBuffer(max_events=512)
        self.last_agent_ui_events = []
        self._snapshot.agent_ui_contract = AGENT_UI_CONTRACT_VERSION
        self._snapshot.stream_render_contract = STREAM_RENDER_CONTRACT_VERSION
        self._snapshot.render_mode = "delta_merge_virtual_transcript"
        self._snapshot.stream_state = "streaming"
        self._snapshot.runtime_status = "active"
        self._snapshot.current_task_status = "RUNNING"
        self._snapshot.current_stage = "Runtime SSE 流式提交中"
        self._snapshot.connection_status = "Runtime SSE 正在连接"
        self._snapshot.reconnect_attempts = 0
        self._snapshot.terminal_order_valid = True
        self._seen_assistant_final = False
        self._snapshot.control_state = "ready"
        self._notify_snapshot(on_snapshot)

        started = time.time()
        events: List[RuntimeSseEvent] = []
        allowed_reconnects = self.max_reconnects if max_reconnects is None else max(0, int(max_reconnects))
        attempt = 0
        resume = False

        while True:
            try:
                with self._open_chat_stream(self._chat_payload(safe_message, resume=resume)) as resp:
                    self._consume_response(resp, events, on_event=on_event, on_snapshot=on_snapshot)
            except urllib.error.HTTPError as exc:
                code = getattr(exc, "code", "http_error")
                return self._connection_failure_snapshot(f"/chat/stream-events HTTP {code}：{safe_text(exc.reason, 120)}")
            except Exception as exc:
                if attempt < allowed_reconnects and self._active_run_id:
                    attempt += 1
                    resume = True
                    self._snapshot.reconnect_attempts = attempt
                    self._snapshot.stream_state = "reconnecting"
                    self._snapshot.connection_status = f"Runtime SSE 断流，正在续接 {attempt}/{allowed_reconnects}"
                    self._notify_snapshot(on_snapshot)
                    continue
                return self._connection_failure_snapshot(f"/chat/stream-events 连接失败：{safe_text(exc, 160)}")

            names = [item.event for item in events]
            if "run_terminal" in names:
                break
            if attempt < allowed_reconnects and self._active_run_id:
                attempt += 1
                resume = True
                self._snapshot.reconnect_attempts = attempt
                self._snapshot.stream_state = "reconnecting"
                self._snapshot.connection_status = f"Runtime SSE 未收到 run_terminal，正在续接 {attempt}/{allowed_reconnects}"
                self._notify_snapshot(on_snapshot)
                continue
            break

        elapsed_ms = int((time.time() - started) * 1000)
        self._snapshot.latency_ms = elapsed_ms
        self._flush_pending_assistant_delta(force=True)
        self.last_events = events
        self._snapshot.terminal_order_valid = validate_terminal_order(events)
        self._evaluate_hook(HOOK_STAGE_PRE_FINALIZE, {"terminal_order_valid": self._snapshot.terminal_order_valid, "payload": {"event_count": len(events)}})
        if not self._snapshot.terminal_order_valid:
            self._snapshot.current_task_status = "PARTIAL_OR_FAILED"
            self._snapshot.stream_state = "error"
            self._snapshot.connection_status = "Runtime SSE 事件顺序异常：缺少 assistant_final -> run_terminal"
        elif "run_terminal" not in [item.event for item in events]:
            self._snapshot.current_task_status = "STREAM_INTERRUPTED"
            self._snapshot.stream_state = "interrupted"
            self._snapshot.connection_status = "Runtime SSE 流未完整收口：未收到 run_terminal"
        elif self._snapshot.stream_state not in {"error"}:
            self._snapshot.stream_state = "completed"
        self._sync_derived_projection()
        self._notify_snapshot(on_snapshot)
        return self._snapshot

    def _control_request(self, path: str, request: RuntimeControlRequest) -> RuntimeSnapshot:
        self._snapshot.control_state = f"{request.action}_requested"
        self._snapshot.current_stage = f"已向 Runtime 提交 {request.action} 请求"
        request_payload = request.to_payload()
        hook_decision = self._evaluate_hook(HOOK_STAGE_PRE_CONTROL_REQUEST, {"payload": request_payload, "run_id": request.run_id, "task_id": request.task_id})
        if not hook_decision.ok:
            self.last_control_result = RuntimeControlResult(
                action=request.action,
                status="blocked_by_hook",
                message=f"HookBus blocked control request: {hook_decision.reason}",
                frontend_only_fallback=True,
            ).__dict__
            self._snapshot.control_state = f"{request.action}_blocked_by_hook"
            self._snapshot.chat_messages.append(ChatMessage("assistant", "临渊者", "控制", self.last_control_result["message"]))
            self._sync_derived_projection()
            return self._snapshot
        try:
            data = self._json_request(path, method="POST", payload=request_payload)
            result = RuntimeControlResult.from_mapping(data, action=request.action)
            self.last_control_result = result.__dict__
            self._snapshot.control_state = f"{request.action}_{result.status}"
            if result.audit_id:
                self._snapshot.audit_id = result.audit_id
                self._snapshot.evidence_ref = result.audit_id
            if result.message:
                self._snapshot.chat_messages.append(ChatMessage("assistant", "临渊者", "控制", result.message))
        except Exception as exc:
            self.last_control_result = RuntimeControlResult(
                action=request.action,
                status="frontend_fallback_recorded",
                message=f"控制请求未到达 Runtime，仅在前端记录：{safe_text(exc, 160)}",
                frontend_only_fallback=True,
            ).__dict__
            self._snapshot.control_state = f"{request.action}_frontend_fallback_recorded"
            self._snapshot.chat_messages.append(ChatMessage("assistant", "临渊者", "控制", self.last_control_result["message"]))
        self._sync_derived_projection()
        return self._snapshot

    def request_task_stop(self, reason: str = "user_requested") -> RuntimeSnapshot:
        return self._control_request(
            TASK_STOP_ENDPOINT,
            RuntimeControlRequest(action="stop", run_id=self._active_run_id, task_id=self._active_task_id, reason=safe_text(reason, 120)),
        )

    def request_task_reset(self, reason: str = "user_requested") -> RuntimeSnapshot:
        return self._control_request(
            TASK_RESET_ENDPOINT,
            RuntimeControlRequest(action="reset", run_id=self._active_run_id, task_id=self._active_task_id, reason=safe_text(reason, 120)),
        )

    def request_task_interrupt(self, reason: str = "user_requested") -> RuntimeSnapshot:
        return self._control_request(
            TASK_INTERRUPT_ENDPOINT,
            RuntimeControlRequest(action="interrupt", run_id=self._active_run_id, task_id=self._active_task_id, reason=safe_text(reason, 120)),
        )

    def request_file_transfer(self, file_path: str, purpose: str = "user_attachment") -> RuntimeSnapshot:
        try:
            request = FileTransferRequest.from_path(file_path, purpose=purpose, run_id=self._active_run_id, task_id=self._active_task_id)
        except Exception as exc:
            record = FileTransferPublicRecord(
                transfer_id="FT-PREPARE-ERROR",
                status="frontend_error",
                message=f"文件传输请求准备失败：{safe_text(exc, 160)}",
                frontend_only_fallback=True,
            )
            self._snapshot.add_file_transfer_record(record)
            self._sync_derived_projection()
            return self._snapshot
        payload = request.to_payload()
        hook_decision = self._evaluate_hook(HOOK_STAGE_PRE_FILE_TRANSFER_REQUEST, {"payload": payload, "run_id": self._active_run_id, "task_id": self._active_task_id})
        if not hook_decision.ok:
            record = FileTransferPublicRecord.from_request_result(
                request,
                status="blocked_by_hook",
                message=f"HookBus 阻断文件传输请求：{hook_decision.reason}",
                transfer_id="FT-BLOCKED",
                frontend_only_fallback=True,
            )
            self._snapshot.add_file_transfer_record(record)
            self._sync_derived_projection()
            return self._snapshot
        try:
            data = self._json_request(FILE_TRANSFER_ENDPOINT, method="POST", payload=payload)
            record = FileTransferPublicRecord.from_mapping(data)
            if not record.file_name:
                record = FileTransferPublicRecord.from_request_result(
                    request,
                    status=record.status or "accepted",
                    message=record.message or "Runtime 已接收文件传输请求；前端未直接执行工具。",
                    transfer_id=record.transfer_id,
                    audit_id=record.audit_id,
                    frontend_only_fallback=record.frontend_only_fallback,
                )
        except Exception as exc:
            record = FileTransferPublicRecord.from_request_result(
                request,
                status="frontend_fallback_recorded",
                message=f"文件传输请求未到达 Runtime，仅在前端记录：{safe_text(exc, 160)}",
                transfer_id="FT-FALLBACK",
                frontend_only_fallback=True,
            )
        self._snapshot.add_file_transfer_record(record)
        if record.audit_id:
            self._snapshot.audit_id = record.audit_id
            self._snapshot.evidence_ref = record.audit_id
        self._sync_derived_projection()
        return self._snapshot

    def request_file_authorization(self, file_path: str, mode: str = "read", scope: str = "user_selected_file", purpose: str = "user_attachment") -> RuntimeSnapshot:
        try:
            request = FileAuthorizationRequest.from_path(
                file_path,
                mode=mode,
                scope=scope,
                purpose=purpose,
                run_id=self._active_run_id,
                task_id=self._active_task_id,
            )
        except Exception as exc:
            record = FileAuthorizationPublicRecord(
                authorization_id="AUTH-PREPARE-ERROR",
                status="frontend_error",
                message=f"文件授权请求准备失败：{safe_text(exc, 160)}",
                frontend_only_fallback=True,
            )
            self._snapshot.add_file_authorization_record(record)
            self._sync_derived_projection()
            return self._snapshot
        payload = request.to_payload()
        hook_decision = self._evaluate_hook(
            HOOK_STAGE_PRE_WORKSPACE_AUTHORIZATION_REQUEST,
            {"payload": payload, "run_id": self._active_run_id, "task_id": self._active_task_id},
        )
        if not hook_decision.ok:
            record = FileAuthorizationPublicRecord.from_request_result(
                request,
                status="blocked_by_hook",
                message=f"HookBus 阻断文件授权请求：{hook_decision.reason}",
                authorization_id="AUTH-BLOCKED",
                frontend_only_fallback=True,
            )
            self._snapshot.add_file_authorization_record(record)
            self._sync_derived_projection()
            return self._snapshot
        try:
            data = self._json_request(FILE_AUTHORIZATION_ENDPOINT, method="POST", payload=payload)
            record = FileAuthorizationPublicRecord.from_mapping(data)
            if not record.file_name:
                record = FileAuthorizationPublicRecord.from_request_result(
                    request,
                    status=record.status or "accepted",
                    message=record.message or "Runtime 已接收文件授权请求；前端未创建工作区或复制文件。",
                    authorization_id=record.authorization_id,
                    audit_id=record.audit_id,
                    runtime_workspace_digest=record.runtime_workspace_digest,
                    frontend_only_fallback=record.frontend_only_fallback,
                )
        except Exception as exc:
            record = FileAuthorizationPublicRecord.from_request_result(
                request,
                status="frontend_fallback_recorded",
                message=f"文件授权请求未到达 Runtime，仅在前端记录：{safe_text(exc, 160)}",
                authorization_id="AUTH-FALLBACK",
                frontend_only_fallback=True,
            )
        self._snapshot.add_file_authorization_record(record)
        if record.audit_id:
            self._snapshot.audit_id = record.audit_id
            self._snapshot.evidence_ref = record.audit_id
        self._sync_derived_projection()
        return self._snapshot


    def request_connector_registration(self, display_name: str, kind: str = "mcp_server", scopes: List[str] | None = None, capabilities: List[str] | None = None) -> RuntimeSnapshot:
        try:
            request = ConnectorRegistrationRequest.build(
                display_name=display_name,
                kind=kind,
                requested_scopes=scopes or ["read_public_metadata"],
                requested_capabilities=capabilities or ["registry_review"],
                source_hint="frontend_manual_request",
                run_id=self._active_run_id,
                task_id=self._active_task_id,
            )
        except Exception as exc:
            record = ConnectorRegistrationPublicRecord(
                request_id="CONN-PREPARE-ERROR",
                status="frontend_error",
                message=f"连接器注册请求准备失败：{safe_text(exc, 160)}",
                frontend_only_fallback=True,
            )
            self._snapshot.add_connector_registration_record(record)
            self._sync_derived_projection()
            return self._snapshot
        payload = request.to_payload()
        hook_decision = self._evaluate_hook(
            HOOK_STAGE_PRE_CONNECTOR_REGISTRATION_REQUEST,
            {"payload": payload, "run_id": self._active_run_id, "task_id": self._active_task_id},
        )
        if not hook_decision.ok:
            record = ConnectorRegistrationPublicRecord.from_request_result(
                request,
                status="blocked_by_hook",
                message=f"HookBus 阻断连接器注册请求：{hook_decision.reason}",
                request_id="CONN-BLOCKED",
                frontend_only_fallback=True,
                quarantined=True,
            )
            self._snapshot.add_connector_registration_record(record)
            self._sync_derived_projection()
            return self._snapshot
        try:
            data = self._json_request(CONNECTOR_REGISTER_ENDPOINT, method="POST", payload=payload)
            record = ConnectorRegistrationPublicRecord.from_mapping(data)
            if not record.display_name:
                record = ConnectorRegistrationPublicRecord.from_request_result(
                    request,
                    status=record.status or "accepted",
                    message=record.message or "Runtime 已接收连接器注册请求；前端未安装或执行连接器。",
                    request_id=record.request_id,
                    audit_id=record.audit_id,
                    frontend_only_fallback=record.frontend_only_fallback,
                    quarantined=record.quarantined,
                )
        except Exception as exc:
            record = ConnectorRegistrationPublicRecord.from_request_result(
                request,
                status="frontend_fallback_recorded",
                message=f"连接器注册请求未到达 Runtime，仅在前端记录：{safe_text(exc, 160)}",
                request_id="CONN-FALLBACK",
                frontend_only_fallback=True,
            )
        self._snapshot.add_connector_registration_record(record)
        if record.audit_id:
            self._snapshot.audit_id = record.audit_id
            self._snapshot.evidence_ref = record.audit_id
        self._sync_derived_projection()
        return self._snapshot

    def request_session_resume(self, session_id_digest: str, reason: str = "user_requested_resume") -> RuntimeSnapshot:
        request = SessionResumeRequest(session_id_digest=safe_text(session_id_digest, 80), reason=safe_text(reason, 120))
        payload = request.to_payload()
        hook_decision = self._evaluate_hook(HOOK_STAGE_PRE_CONTROL_REQUEST, {"payload": payload, "run_id": self._active_run_id, "task_id": self._active_task_id})
        if not hook_decision.ok:
            self._snapshot.record_session_resume_request(session_id_digest, status="blocked_by_hook", message=f"HookBus 阻断 Session 恢复请求：{hook_decision.reason}")
            self._sync_derived_projection()
            return self._snapshot
        try:
            data = self._json_request(SESSION_RESUME_ENDPOINT, method="POST", payload=payload)
            payload_out = data.get("payload", data) if isinstance(data, Mapping) else {}
            status = safe_text(payload_out.get("status", "requested") if isinstance(payload_out, Mapping) else "requested", 80)
            message = safe_text(payload_out.get("message", "Runtime 已接收 Session 恢复请求。") if isinstance(payload_out, Mapping) else "Runtime 已接收 Session 恢复请求。", 220)
            self._snapshot.record_session_resume_request(session_id_digest, status=status, message=message)
            audit_id = safe_text(payload_out.get("audit_id", payload_out.get("audit_ref", "")) if isinstance(payload_out, Mapping) else "", 80)
            if audit_id:
                self._snapshot.audit_id = audit_id
                self._snapshot.evidence_ref = audit_id
        except Exception as exc:
            self._snapshot.record_session_resume_request(session_id_digest, status="frontend_fallback_recorded", message=f"Session 恢复请求未到达 Runtime，仅在前端记录：{safe_text(exc, 160)}")
        self._sync_derived_projection()
        return self._snapshot

    def request_session_search(self, query: str) -> RuntimeSnapshot:
        request = SessionSearchRequest(query=safe_text(query, 120))
        payload = request.to_payload()
        hook_decision = self._evaluate_hook(HOOK_STAGE_PRE_CONTROL_REQUEST, {"payload": payload, "run_id": self._active_run_id, "task_id": self._active_task_id})
        if not hook_decision.ok:
            self._snapshot.session_manager_state = "search_blocked_by_hook"
            self._snapshot.session_last_message = f"HookBus 阻断 Session 搜索请求：{hook_decision.reason}"
            self._sync_derived_projection()
            return self._snapshot
        try:
            data = self._json_request(SESSION_SEARCH_ENDPOINT, method="POST", payload=payload)
            self._apply_session_manager(data)
            self._snapshot.record_session_search(query)
        except Exception:
            self._snapshot.record_session_search(query)
        self._sync_derived_projection()
        return self._snapshot

    def submit_confirmation(self, ticket_id: str, decision: str) -> RuntimeSnapshot:
        envelope = ConfirmationRequestEnvelope.build(
            ticket_id=ticket_id,
            decision=decision,
            run_id=self._active_run_id,
            task_id=self._active_task_id,
        )
        envelope_payload = envelope.to_payload()
        self._snapshot.last_confirmation_request = envelope_payload
        self._snapshot.confirmation_request_state = "requesting_runtime"
        hook_decision = self._evaluate_hook(HOOK_STAGE_PRE_CONFIRMATION_SUBMIT, {"payload": envelope_payload, "ticket_id": envelope.ticket_id, "run_id": envelope.run_id, "task_id": envelope.task_id})
        if not hook_decision.ok:
            self._snapshot.confirmation_request_state = "blocked_by_hook"
            self._snapshot.chat_messages.append(ChatMessage("assistant", "临渊者", "确认", f"HookBus 阻断确认请求：{hook_decision.reason}"))
            self._sync_derived_projection()
            return self._snapshot
        try:
            data = self._json_request(CONFIRMATION_ENDPOINT, method="POST", payload=envelope_payload)
            payload = data.get("payload", data) if isinstance(data, Mapping) else {}
            if not isinstance(payload, Mapping):
                payload = {}
            status = safe_text(payload.get("status", "submitted"), 80)
            audit_id = safe_text(payload.get("audit_id", payload.get("audit_ref", "")), 80)
            self._snapshot.confirmation_request_state = f"runtime_{status}"
            if audit_id:
                self._snapshot.audit_id = audit_id
                self._snapshot.evidence_ref = audit_id
                self._snapshot.audit_count += 1
                self._append_audit_readonly_card(AuditReadonlyCard.from_payload(payload, count=self._snapshot.audit_count))
            normalized = normalize_confirmation_decision(decision)
            for item in self._snapshot.pending_confirmations:
                if safe_text(item.get("ticket_id", ""), 80) == envelope.ticket_id:
                    item["frontend_decision_request"] = normalized
                    item["runtime_status"] = status
                    item["frontend_only"] = False
            for card in self._snapshot.action_guard_cards:
                if safe_text(card.ticket_id, 80) == envelope.ticket_id:
                    object.__setattr__(card, "status", f"runtime_{status}")
            self._snapshot.chat_messages.append(ChatMessage("assistant", "临渊者", "确认", "确认请求已提交 Runtime 网关；等待 QualityGate/Audit 回执，不由前端放行。"))
        except Exception as exc:
            self._snapshot.submit_confirmation(envelope.ticket_id, envelope.decision)
            self._snapshot.confirmation_request_state = "frontend_fallback_recorded"
            self._snapshot.chat_messages.append(ChatMessage("assistant", "临渊者", "确认", f"确认请求未到达 Runtime，仅前端记录请求：{safe_text(exc, 160)}"))
        self._sync_derived_projection()
        return self._snapshot

    def submit_self_iteration_confirmation(self, candidate_id: str, decision: str) -> RuntimeSnapshot:
        payload = {"candidate_id": safe_text(candidate_id, 80), "decision": safe_text(decision, 32), "frontend_contract": ACTION_GUARD_CONTRACT_VERSION, "no_frontend_self_iteration_apply": True}
        hook_decision = self._evaluate_hook(HOOK_STAGE_PRE_SELF_ITERATION_CONFIRM, {"payload": payload})
        if not hook_decision.ok:
            self._snapshot.chat_messages.append(ChatMessage("assistant", "临渊者", "自我迭代", f"HookBus 阻断自我迭代确认请求：{hook_decision.reason}"))
            self._sync_derived_projection()
            return self._snapshot
        try:
            self._json_request(
                "/self-iteration/confirm",
                method="POST",
                payload=payload,
            )
            self._snapshot.chat_messages.append(ChatMessage("assistant", "临渊者", "自我迭代", "自我迭代确认已提交 Runtime 网关；不由前端直接合入。"))
        except Exception as exc:
            self._snapshot.submit_self_iteration_confirmation(candidate_id, decision)
            self._snapshot.chat_messages.append(ChatMessage("assistant", "临渊者", "自我迭代", f"自我迭代确认未到达 Runtime，仅前端记录请求：{safe_text(exc, 160)}"))
        return self._snapshot
