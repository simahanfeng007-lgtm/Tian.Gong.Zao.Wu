from __future__ import annotations

import json
import os
import re
import socket
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from linyuanzhe_frontend.clients.network_policy import NetworkPolicyError, validate_url, urlopen_with_policy
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
from linyuanzhe_frontend.contracts.runtime_snapshot import RuntimeSnapshot, StepSummary, ChatMessage, CHAT_MESSAGE_DISPLAY_LIMIT, CHAT_USER_INPUT_LIMIT, digest_text, safe_chat_text, safe_text
from linyuanzhe_frontend.version_info import FE_RUNTIME_VERSION
from linyuanzhe_frontend.contracts.run_workbench import RUN_WORKBENCH_CONTRACT_VERSION, RunWorkbenchProjection, normalize_run_state, run_state_label, ACTIVE_STATES
from linyuanzhe_frontend.contracts.work_modes import WORK_MODE_CONTRACT_VERSION, sanitize_work_mode_payload, is_casual_chat_message
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
RUN_STATUS_ENDPOINT = "/runs/status"

RAW_TOOL_OUTPUT_PREFIXES = (
    "list_dir", "readfile", "read_file", "writefile", "write_file", "editfile", "edit_file",
    "shell", "run_shell", "cmd", "powershell", "python", "python3", "pytest", "npm", "node",
    "grep", "rg", "cat", "ls", "dir", "mkdir", "zip", "pack", "tool_call", "tool_result", "tool_progress",
)

MAX_PROGRESS_NOTICE_CARDS = 48

STATUS_PROBE_PATTERNS = (
    "咋样", "怎么样", "进度", "到哪", "做到哪", "现在呢", "完成没", "好了没",
    "状态", "status", "progress", "what's up", "how is it going",
)


INTERNAL_CHAT_LEAK_MARKERS = (
    "runstate=", "run_state=", "run_status=", "RuntimeBackendSubprocess",
    "safecommandrunner", "safe_command_runner", "safeCommandRunner",
    "buildshellsystemmount", "build_shell_system_mount", "return_analysis", "return_code",
    "model_output_shape", "plan_schema", "planner_mode", "tool_execution_mode",
    "audit_", "local_envelope", "Runtime 子进程", "原始工具输出",
    "stderr", "stdout", "diagnostic", "debug", "traceback",
    "repaircontext", "adaptiveworkloop", "adaptiveworkloopv1",
    "failedwith_resume", "failed_recoverable",
)

INTERNAL_CHAT_LEAK_PATTERNS = (
    re.compile(r"^\s*[-•*]?\s*(?:工具|Tool)\s*[:：]\s*(?:RuntimeBackendSubprocess|safe_?command_?runner|BuildShellSystemMount)\b", re.IGNORECASE),
    re.compile(r"\b(?:runstate|run_state|run_status|planner_mode|tool_execution_mode)\s*=", re.IGNORECASE),
    re.compile(r"\b(?:safecommandrunner|safe_command_runner|safeCommandRunner|buildshellsystemmount|build_shell_system_mount)\b", re.IGNORECASE),
    re.compile(r"^\s*[-•*]?\s*(?:stdout|stderr|raw_result|raw output|trace|debug|diagnostic)\s*[:：]", re.IGNORECASE),
)

LOCAL_BRIDGE_AUTOREPAIR_WAIT_SECONDS = 12.0
LOCAL_BRIDGE_CONNECT_TIMEOUT_SECONDS = 0.5


def _path_exists(path: Path) -> bool:
    try:
        return path.exists()
    except OSError:
        return False


def _frontend_project_root() -> Path | None:
    env_hint = str(os.environ.get("LINYUANZHE_ROOT_HINT", "") or os.environ.get("LINYUANZHE_DESKTOP_ROOT", "")).strip()
    if env_hint:
        try:
            candidate = Path(env_hint).expanduser().resolve()
            if _path_exists(candidate / "desktop" / "linyuanzhe_local_runtime_bridge_l671.py") and _path_exists(candidate / "frontend" / "linyuanzhe_frontend" / "app.py"):
                return candidate
        except OSError:
            pass
    here = Path(__file__).resolve()
    for candidate in (here.parent.parent.parent.parent, here.parent.parent.parent, Path.cwd()):
        try:
            resolved = candidate.resolve()
        except OSError:
            continue
        if _path_exists(resolved / "desktop" / "linyuanzhe_local_runtime_bridge_l671.py") and _path_exists(resolved / "frontend" / "linyuanzhe_frontend" / "app.py"):
            return resolved
    return None


def _socket_reachable(host: str, port: int, timeout: float = LOCAL_BRIDGE_CONNECT_TIMEOUT_SECONDS) -> bool:
    try:
        with socket.create_connection((host, int(port)), timeout=max(0.1, float(timeout or 0.5))):
            return True
    except OSError:
        return False


def runtime_submission_text(value: Any, max_len: int = 8000) -> str:
    """Text sent to Runtime.

    Display sanitizers intentionally redact local paths.  Runtime submission must
    retain the exact user text so copied file paths such as ``C:\\Users\\...`` or
    ``/Users/...`` do not become ``<redacted>`` before planning/tool routing.
    This function only strips control characters and caps length; it never
    redacts paths or file names.
    """
    text = "" if value is None else str(value)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = "".join(ch for ch in text if ch in "\n\t" or ord(ch) >= 32)
    text = text.strip()
    if len(text) > max_len:
        return text[: max(0, max_len - 1)] + "…"
    return text




_PATH_CANDIDATE_PATTERNS = (
    re.compile(r"[A-Za-z]:\\[^\n\r\t<>|*?]+"),
    re.compile(r"/(?:Users|home|mnt|Volumes|var|tmp)/[^\n\r\t]+"),
)


def extract_host_paths_from_text(value: Any, max_items: int = 12) -> list[str]:
    """Return raw host path candidates without applying display redaction.

    L6.72.49 keeps copied Windows/macOS/Linux paths available to Runtime while
    the UI may still show ``<redacted>``.  The extractor is intentionally
    conservative: it only mirrors likely absolute local paths into metadata and
    never normalizes, resolves, reads, writes, or expands them in the frontend.
    """
    text = runtime_submission_text(value, 8000)
    out: list[str] = []
    seen: set[str] = set()
    for pattern in _PATH_CANDIDATE_PATTERNS:
        for match in pattern.finditer(text):
            candidate = match.group(0).strip().strip('"').strip("'").rstrip("，,。.;；)）]")
            if not candidate or "<redacted>" in candidate.lower():
                continue
            key = candidate.replace("\\", "/").rstrip("/").lower()
            if key in seen:
                continue
            seen.add(key)
            out.append(candidate)
            if len(out) >= max_items:
                return out
    return out


def _raw_runtime_payload_has_redaction_leak(payload: Mapping[str, Any]) -> bool:
    """Detect whether display redaction leaked into raw Runtime fields."""
    raw_keys = {
        "message", "user_message", "raw_user_text", "text_raw",
        "original_user_message", "original_path", "host_path_candidates",
    }

    def walk(value: Any, *, under_raw_key: bool = False) -> bool:
        if isinstance(value, Mapping):
            for key, item in value.items():
                key_is_raw = str(key) in raw_keys
                if walk(item, under_raw_key=under_raw_key or key_is_raw):
                    return True
            return False
        if isinstance(value, (list, tuple, set)):
            return any(walk(item, under_raw_key=under_raw_key) for item in value)
        if under_raw_key and isinstance(value, str):
            return "<redacted>" in value.lower()
        return False

    return walk(payload)

def _is_internal_chat_leak_line(value: Any) -> bool:
    line = str(value or "").strip()
    if not line:
        return False
    lowered = line.lower()
    if any(marker.lower() in lowered for marker in INTERNAL_CHAT_LEAK_MARKERS):
        return True
    return any(pattern.search(line) for pattern in INTERNAL_CHAT_LEAK_PATTERNS)


class SseRuntimeClient:
    """Current Runtime SSE client with action-guard cards and smooth Agent UI projection.

    The client is a desktop display/submit adapter only. It may contact the
    official Runtime gateway endpoints, consume sanitized SSE/PublicProjection
    events, and send stop/reset/interrupt *requests* to Runtime. It never imports provider
    SDKs, never calls tools/adapters, never writes long-term memory, and never
    applies rollback or self-iteration locally.
    """

    def __init__(self, base_url: str, *, timeout: float = 900.0, max_reconnects: int = 3) -> None:
        cleaned = str(base_url or "").strip().rstrip("/")
        if not cleaned:
            cleaned = "http://127.0.0.1:8787"
        if not urllib.parse.urlparse(cleaned).scheme:
            cleaned = "http://" + cleaned
        validate_url(cleaned, allow_loopback_http=True, purpose="runtime_base_url")
        self.base_url = cleaned
        self.timeout = max(60.0, float(timeout or 900.0))
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
        self._active_user_message = ""
        self._last_seq = 0
        self._seen_assistant_final = False
        self._progress_notice_keys: set[str] = set()
        self._last_progress_signature = ""
        self._progress_notice_folded = False
        # L6.72.51：任务流程只在“工作”模式激活。普通聊天不会占用 Run 工作台。
        self._active_task_flow = False
        self._local_bridge_repair_lock = threading.Lock()
        self._local_bridge_repair_attempts = 0
        self._local_bridge_repair_message = ""
        self._managed_bridge_proc: subprocess.Popen[str] | None = None
        self._hook_bus = HookBus.default_frontend_bus()
        self._snapshot = RuntimeSnapshot(
            source_kind="runtime_sse",
            runtime_status="未连接",
            connection_status=f"Runtime SSE 待连接：base_url_digest={self.endpoint_digest}",
            current_task_status="DISCONNECTED",
            progress_percent=0,
            current_stage="等待 /health/runtime 或 /chat/stream-events",
            tool_execution_mode="runtime_governed",
            stream_state="idle",
            control_state="ready",
            agent_ui_contract=AGENT_UI_CONTRACT_VERSION,
            stream_render_contract=STREAM_RENDER_CONTRACT_VERSION,
            render_mode="delta_merge_virtual_transcript",
            stream_activity_label="",
            stream_visual_state="idle",
        )
        self._snapshot.trace_records = []
        self._snapshot.trace_stats = TraceStats.from_records([]).to_dict()
        self._snapshot.trace_terminal_order_valid = True
        self._snapshot.trace_export_digest = digest_text(self._snapshot.trace_stats, 16)
        self._sync_hook_projection()
        self._transcript.load(self._snapshot.chat_messages)

    def _runtime_host_port(self) -> tuple[str, int]:
        parsed = urllib.parse.urlparse(self.base_url)
        host = parsed.hostname or "127.0.0.1"
        port = int(parsed.port or (443 if parsed.scheme == "https" else 80))
        return host, port

    def _is_loopback_runtime(self) -> bool:
        host, _ = self._runtime_host_port()
        return host in {"127.0.0.1", "localhost", "::1", "0.0.0.0"}

    def _autostart_local_bridge_if_needed(self, *, reason: str = "") -> None:
        if not self._is_loopback_runtime():
            return
        host, port = self._runtime_host_port()
        if _socket_reachable(host, port):
            return
        with self._local_bridge_repair_lock:
            if _socket_reachable(host, port):
                return
            if self._managed_bridge_proc is not None and self._managed_bridge_proc.poll() is None:
                deadline = time.time() + 2.0
                while time.time() < deadline:
                    if _socket_reachable(host, port):
                        self._local_bridge_repair_message = f"已重新连接本地桥接：{host}:{port}"
                        return
                    time.sleep(0.1)
            root = _frontend_project_root()
            if root is None:
                self._local_bridge_repair_message = "未找到桌面工程根目录；请从启动入口重新启动。"
                return
            bridge = root / "desktop" / "linyuanzhe_local_runtime_bridge_l671.py"
            if not _path_exists(bridge):
                self._local_bridge_repair_message = f"本地桥接入口缺失：{bridge}"
                return
            env = os.environ.copy()
            existing_pp = str(env.get("PYTHONPATH", "") or "")
            extra_pp = str(root / "frontend")
            env["PYTHONPATH"] = extra_pp if not existing_pp else extra_pp + os.pathsep + existing_pp
            env.setdefault("PYTHONUTF8", "1")
            env.setdefault("PYTHONIOENCODING", "utf-8")
            env["LINYUANZHE_ROOT_HINT"] = str(root)
            backend_mode = str(os.environ.get("LINYUANZHE_BRIDGE_BACKEND_MODE", os.environ.get("LINYUANZHE_BACKEND_MODE", "auto")) or "auto")
            timeout = str(os.environ.get("LINYUANZHE_BACKEND_TIMEOUT", str(int(self.timeout))))
            cmd = [sys.executable, str(bridge), "--host", host, "--port", str(port), "--backend-mode", backend_mode, "--timeout", timeout]
            creationflags = 0
            if os.name == "nt":
                creationflags = int(getattr(subprocess, "CREATE_NO_WINDOW", 0))
            try:
                self._managed_bridge_proc = subprocess.Popen(
                    cmd,
                    cwd=str(root),
                    env=env,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    text=True,
                    creationflags=creationflags,
                )
            except Exception as exc:  # noqa: BLE001 - frontend只做本地自愈提示，不把异常抛给主会话
                self._managed_bridge_proc = None
                self._local_bridge_repair_message = f"本地桥接重启失败：{safe_text(exc, 180)}"
                return
            self._local_bridge_repair_attempts += 1
            deadline = time.time() + LOCAL_BRIDGE_AUTOREPAIR_WAIT_SECONDS
            while time.time() < deadline:
                if _socket_reachable(host, port):
                    self._local_bridge_repair_message = f"检测到本地桥接未运行，已自动拉起：{host}:{port}"
                    return
                if self._managed_bridge_proc.poll() is not None:
                    break
                time.sleep(0.15)
            rc = self._managed_bridge_proc.poll()
            self._local_bridge_repair_message = f"本地桥接未启动成功（exit={rc if rc is not None else 'timeout'}）；请点击重连或重新从启动入口启动。"

    def close(self) -> None:
        proc = self._managed_bridge_proc
        self._managed_bridge_proc = None
        if proc is None:
            return
        try:
            if proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=3)
                except Exception:
                    proc.kill()
        except Exception:
            return

    # ------------------------------------------------------------- endpoints
    def _url(self, path: str) -> str:
        if not path.startswith("/"):
            path = "/" + path
        return self.base_url + path

    def _json_request(self, path: str, *, method: str = "GET", payload: Optional[Mapping[str, Any]] = None, extra_headers: Optional[Mapping[str, str]] = None) -> Dict[str, Any]:
        self._autostart_local_bridge_if_needed(reason=f"json:{path}")
        data = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json; charset=utf-8",
            "X-Tiangong-Frontend-Contract": FE_RUNTIME_VERSION,
        }
        if extra_headers:
            for key, value in extra_headers.items():
                clean_key = safe_text(key, 80)
                if clean_key:
                    headers[clean_key] = safe_text(value, 4096)
        req = urllib.request.Request(
            self._url(path),
            data=data,
            method=method,
            headers=headers,
        )
        with urlopen_with_policy(req, timeout=self.timeout, allow_loopback_http=True, purpose="runtime_json") as resp:
            raw = resp.read()
        if not raw:
            return {}
        parsed = json.loads(raw.decode("utf-8", errors="replace"))
        if isinstance(parsed, Mapping):
            return sanitize_event_payload(parsed)
        return {"value": sanitize_event_payload(parsed)}

    def _apply_run_workbench_status(self, mapping: Mapping[str, Any]) -> None:
        runs = mapping.get("runs") if isinstance(mapping, Mapping) else []
        active_run_id = safe_text(mapping.get("active_run_id", ""), 120) if isinstance(mapping, Mapping) else ""
        target: Mapping[str, Any] = {}
        if isinstance(runs, list) and runs:
            for item in reversed(runs):
                if isinstance(item, Mapping) and (not active_run_id or safe_text(item.get("run_id", ""), 120) == active_run_id):
                    target = item
                    break
            if not target and isinstance(runs[-1], Mapping):
                target = runs[-1]
        state = safe_text(target.get("status", mapping.get("last_run_state", "idle") if isinstance(mapping, Mapping) else "idle"), 40) if target or isinstance(mapping, Mapping) else "idle"
        payload = {
            "frontend_work_mode": target.get("frontend_work_mode", getattr(self._snapshot, "frontend_work_mode", "work")) if target else getattr(self._snapshot, "frontend_work_mode", "work"),
            "planner_mode": target.get("planner_mode", getattr(self._snapshot, "planner_mode", "")) if target else getattr(self._snapshot, "planner_mode", ""),
            "tool_name": target.get("current_tool_name", "") if target else "",
            "status": target.get("current_tool_status", target.get("status", "")) if target else state,
            "diagnostic_summary": target.get("diagnostic_summary", "") if target else "",
            "heartbeat": bool(target.get("heartbeat_count")) if target else False,
            "elapsed_ms": target.get("elapsed_ms", 0) if target else 0,
        }
        mode = safe_text(payload.get("frontend_work_mode"), 40)
        if target and mode not in {"work", "long_chain"}:
            # L6.72.51：任务工作台只展示工作模式；旧 long_chain 作为兼容别名。
            return
        if active_run_id:
            self._snapshot.active_run_id = active_run_id
            self._active_run_id = active_run_id
        if target.get("task_id"):
            self._snapshot.active_task_id = safe_text(target.get("task_id"), 120)
            self._active_task_id = self._snapshot.active_task_id
        self._active_task_flow = True
        self._set_run_workbench_state(state or "idle", event_name="run_status_poll", payload=payload)

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
            "requested_backend_mode",
            "effective_backend_mode",
            "runtime_credential_persisted",
            "runtime_credential_store_digest",
            "provider_readiness",
            "readiness_label",
            "missing_fields",
            "next_action",
            "config_location_hint",
            "config_file_state",
            "config_file_exists",
            "config_path_digest",
            "local_bridge_can_persist",
            "raw_secret_visible_to_frontend",
            "last_provider_check_state",
            "last_provider_error_code",
            "last_provider_error_message",
            "last_provider_next_action",
            "last_provider_elapsed",
            "last_provider_audit_id",
            "provider_hint",
            "model_candidates",
            "base_url_display",
            "persona_name",
            "persona_digest",
            "persona_prompt_digest",
            "host_access_scope",
            "host_access_root_configured",
            "host_access_root_digest",
        }
        payload = data.get("payload", data) if isinstance(data, Mapping) else {}
        if not isinstance(payload, Mapping):
            payload = {}
        safe_payload: Dict[str, Any] = {}
        for key, value in payload.items():
            # Raw ``base_url`` / ``base_url_normalized`` may appear from older
            # Runtime projections. Convert them to the Settings-only display
            # field and do not retain the raw key in frontend state.
            if key in {"base_url", "base_url_normalized"}:
                if "base_url_display" not in safe_payload:
                    safe_payload["base_url_display"] = sanitize_event_payload(value)
                continue
            if key in allowed:
                safe_payload[key] = sanitize_event_payload(value)
        self.provider_settings = safe_payload
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
        if self.provider_settings.get("last_provider_check_state"):
            self._snapshot.last_provider_check_state = safe_text(self.provider_settings.get("last_provider_check_state"), 60)
        if self.provider_settings.get("last_provider_error_code"):
            self._snapshot.last_provider_error_code = safe_text(self.provider_settings.get("last_provider_error_code"), 80)
        if self.provider_settings.get("last_provider_error_message"):
            self._snapshot.last_provider_error_message = safe_text(self.provider_settings.get("last_provider_error_message"), 180)
        if self.provider_settings.get("last_provider_next_action"):
            self._snapshot.last_provider_next_action = safe_text(self.provider_settings.get("last_provider_next_action"), 120)
        if self.provider_settings.get("effective_backend_mode"):
            mode = safe_text(self.provider_settings.get("effective_backend_mode"), 40)
            if self._snapshot.provider_config_message:
                self._snapshot.provider_config_message = safe_text(f"{self._snapshot.provider_config_message}；effective_backend_mode={mode}", 220)

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

    def _normalize_session_stats(self, stats_payload: Mapping[str, Any], sessions: List[TaskSessionProjection]) -> Dict[str, Any]:
        computed = SessionManagerStats.from_sessions(sessions).to_dict()
        out: Dict[str, Any] = dict(computed)
        if isinstance(stats_payload, Mapping):
            aliases = {
                "total_count": "total",
                "running_count": "running",
                "waiting_confirmation_count": "waiting_confirmation",
                "blocked_count": "blocked",
                "recoverable_count": "recoverable",
                "completed_count": "completed",
                "failed_count": "failed",
                "queued_count": "queued",
            }
            for key, value in stats_payload.items():
                normalized_key = aliases.get(str(key), str(key))
                try:
                    out[normalized_key] = int(value)
                except (TypeError, ValueError):
                    out[normalized_key] = value
        for key, value in computed.items():
            if key not in out or out.get(key) in (None, ""):
                out[key] = value
        return out

    def _drop_legacy_mock_sessions(self, sessions: List[TaskSessionProjection]) -> List[TaskSessionProjection]:
        return [
            item for item in sessions
            if not safe_text(getattr(item, "session_id_digest", ""), 80).upper().startswith("SESS-MOCK")
        ]

    def _apply_session_manager(self, data: Mapping[str, Any]) -> None:
        payload = data.get("payload", data) if isinstance(data, Mapping) else {}
        if not isinstance(payload, Mapping):
            payload = {}
        sessions_payload = payload.get("task_sessions", payload.get("sessions", []))
        stats_payload = payload.get("session_stats", payload.get("stats", {}))
        if isinstance(sessions_payload, list):
            sessions = self._drop_legacy_mock_sessions([TaskSessionProjection.from_mapping(x) for x in sessions_payload if isinstance(x, Mapping)][:80])
            # Runtime endpoint is canonical even when it returns an empty list.
            # Keeping the previous list here leaks FE mock rows into the real desktop bridge.
            self._snapshot.task_sessions = sessions
            self._snapshot.session_stats = self._normalize_session_stats(stats_payload if isinstance(stats_payload, Mapping) else {}, sessions)
            self._snapshot.session_filtered_count = len(sessions)
        elif isinstance(stats_payload, Mapping):
            self._snapshot.session_stats = self._normalize_session_stats(stats_payload, list(self._snapshot.task_sessions or []))
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

    def _assistant_label(self) -> str:
        return safe_text(self.provider_settings.get("persona_name", "临渊者"), 32) or "临渊者"

    def _sync_transcript_projection(self) -> None:
        self._snapshot.chat_messages = self._transcript.visible_messages()
        self._snapshot.visible_message_count = self._transcript.visible_message_count
        self._snapshot.hidden_message_count = self._transcript.hidden_message_count

    def _looks_like_mojibake_or_binary_text(self, value: Any) -> bool:
        text = safe_chat_text(value, 4000)
        if not text:
            return False
        sample = text[:4000]
        replacement = sample.count("\ufffd") + sample.count("�")
        box_like = sample.count("□") + sample.count("�")
        controls = sum(1 for ch in sample if ord(ch) < 32 and ch not in "\n\r\t")
        if replacement >= 3 or box_like >= 6 or controls >= 3:
            return True
        if re.search(r"(?:\\x[0-9a-fA-F]{2}){4,}|PK\x03\x04|%PDF-|\x00", sample):
            return True
        printable = sum(1 for ch in sample if ch.isprintable() or ch in "\n\r\t")
        return len(sample) >= 120 and printable / max(1, len(sample)) < 0.86

    def _tool_output_placeholder(self, tool_name: str = "工具") -> str:
        tool = safe_text(tool_name, 40) or "工具"
        return (
            f"{tool} 已返回结果，但原始内容包含不可直接展示的二进制/编码异常片段。\n"
            "主会话已隐藏原始输出，避免乱码污染；诊断/审计仍保留脱敏摘要。\n"
            "如需读取 Office/PDF/图片/未知编码文件，请使用文档解析能力或先转为 UTF-8 文本。"
        )

    def _is_raw_tool_output_line(self, line: str) -> bool:
        stripped = safe_text(line, 1200).strip()
        if not stripped:
            return False
        stripped = stripped.lstrip("-•* ").strip()
        lower = stripped.lower()
        if any(lower.startswith(prefix + ":") for prefix in RAW_TOOL_OUTPUT_PREFIXES):
            return True
        if any(lower.startswith(prefix + " ") and " | " in lower[:160] for prefix in RAW_TOOL_OUTPUT_PREFIXES):
            return True
        if re.match(r"^(?:readfile|read_file|list_dir|shell|python3?|npm|pytest|rg|grep)\s*[:：]\s*(?:ok|failed|error|timeout)\s*[|｜]", lower):
            return True
        if "tool_call_raw" in lower or "return_code" in lower or "return_analysis" in lower:
            return True
        if self._looks_like_mojibake_or_binary_text(stripped):
            return True
        return False

    def _strip_raw_tool_output(self, value: Any) -> str:
        text = safe_chat_text(value, CHAT_MESSAGE_DISPLAY_LIMIT)
        if not text:
            return ""
        raw_tool_line = re.compile(
            r"^\s*[-•*]?\s*(readfile|read_file|list_dir|shell|run_shell|cmd|powershell|python3?|pytest|npm|node|cat|dir|ls|rg|grep)\s*[:：]\s*(?:ok|failed|error|timeout)\s*[|｜]\s*(.*)$",
            re.IGNORECASE,
        )
        kept: list[str] = []
        removed = 0
        hidden_kind = "工具"
        for raw_line in text.splitlines():
            match = raw_tool_line.match(raw_line)
            if match:
                removed += 1
                hidden_kind = match.group(1)
                tail = safe_text(match.group(2), 300)
                if re.search(r"文件不存在|目录不存在|path_not_found|not found", tail, re.IGNORECASE):
                    kept.append("文件读取失败：文件不存在或当前执行范围无法访问。请确认上传交接是否完成，或重新选择文件后再试。")
                elif re.search(r"权限|permission|access is denied", tail, re.IGNORECASE):
                    kept.append("文件读取失败：当前执行范围没有访问权限。请检查电脑访问范围或选择允许访问的目录。")
                continue
            if self._is_raw_tool_output_line(raw_line):
                removed += 1
                continue
            kept.append(raw_line)
        cleaned = safe_chat_text("\n".join(kept).strip(), CHAT_MESSAGE_DISPLAY_LIMIT)
        if self._looks_like_mojibake_or_binary_text(cleaned):
            return self._tool_output_placeholder(hidden_kind)
        if cleaned:
            return cleaned
        if removed:
            return ""
        if self._looks_like_mojibake_or_binary_text(text):
            return self._tool_output_placeholder(hidden_kind)
        return text

    def _progress_bar_text(self, percent: int | float | None, *, width: int = 18) -> str:
        try:
            value = int(percent if percent is not None else getattr(self._snapshot, "progress_percent", 0))
        except (TypeError, ValueError):
            value = 0
        value = max(0, min(100, value))
        filled = max(0, min(width, round(value * width / 100)))
        return "█" * filled + "░" * (width - filled)

    def _short_run_id(self) -> str:
        run_id = safe_text(getattr(self._snapshot, "active_run_id", ""), 80) or safe_text(getattr(self, "_active_run_id", ""), 80)
        if not run_id:
            return ""
        return run_id[:8] + "…" + run_id[-6:] if len(run_id) > 18 else run_id

    def _progress_message(self, title: str, lines: Iterable[str] = (), *, status: str = "进度") -> str:
        """Project long-chain status into a Codex-style chat progress card.

        The card is user-facing summary text only. Raw tool stdout/stderr remains
        in diagnostics/audit and is not dumped into the main conversation.
        """
        percent = max(0, min(100, int(getattr(self._snapshot, "progress_percent", 0) or 0)))
        bar = self._progress_bar_text(percent)
        title_clean = safe_text(title, 80) or "任务进度"
        status_clean = safe_text(status, 40) or "进度"
        body = [
            f"▣ Codex进度｜{title_clean}",
            f"状态：{status_clean} · 进度：{percent}%",
            f"进度条：{bar}",
        ]
        run_short = self._short_run_id()
        if run_short:
            body.append(f"Run：{run_short}")
        current = safe_text(getattr(self._snapshot, "current_stage", ""), 120) or safe_text(getattr(self._snapshot, "execution_stage", ""), 120)
        tool = safe_text(getattr(self._snapshot, "current_tool_name", ""), 80)
        if current:
            body.append(f"当前：{current}")
        if tool:
            body.append(f"工具：{tool}")
        appended = 0
        for item in lines:
            clean = safe_text(item, 260)
            if clean:
                body.append(f"- {clean}")
                appended += 1
        if appended == 0:
            body.append("- 正在同步 Runtime 执行状态。")
        return safe_chat_text("\n".join(body), 3600)

    def _append_progress_notice(self, key: str, title: str, lines: Iterable[str] = (), *, force: bool = False) -> None:
        if not bool(getattr(self, "_active_task_flow", False)):
            return
        safe_key = safe_text(key, 160)
        text = self._progress_message(title, lines)
        signature = digest_text((safe_key, text), 16)
        if not force and (safe_key in self._progress_notice_keys or signature == self._last_progress_signature):
            return
        # L6.72.54：工作流进度只进任务工作台/状态栏，不再写入聊天 transcript。
        # 会话区只保留用户与主脑自然语言、必要确认和最终简明结论。
        if not force and len(self._progress_notice_keys) >= MAX_PROGRESS_NOTICE_CARDS:
            if not bool(getattr(self, "_progress_notice_folded", False)):
                self._progress_notice_folded = True
                folded = self._progress_message(
                    "长链进度已自动折叠",
                    [
                        f"已路由 {MAX_PROGRESS_NOTICE_CARDS} 条关键进度到任务工作台。",
                        "后续高频工具事件继续进入任务工作台、状态栏和审计，不写入主会话。",
                        "最终简明结论仍可进入会话区。",
                    ],
                    status="折叠",
                )
                self._progress_notice_keys.add("progress_notice_folded")
                self._last_progress_signature = digest_text(("progress_notice_folded", folded), 16)
                self._snapshot.run_diagnostic_summary = safe_text(folded, 900)
                self._snapshot.current_stage = "长链进度已折叠到任务工作台"
                self._sync_derived_projection()
            return
        self._progress_notice_keys.add(safe_key)
        self._last_progress_signature = signature
        self._snapshot.run_diagnostic_summary = safe_text(text, 900)
        self._snapshot.current_stage = safe_text(title, 120) or self._snapshot.current_stage
        self._sync_derived_projection()

    def _summarize_plan_steps(self, raw_steps: Any, limit: int = 8) -> list[str]:
        if isinstance(raw_steps, str):
            raw_items: list[Any] = [raw_steps]
        elif isinstance(raw_steps, Iterable):
            raw_items = list(raw_steps)
        else:
            raw_items = []
        lines: list[str] = []
        for index, item in enumerate(raw_items[:limit], start=1):
            if isinstance(item, Mapping):
                name = safe_text(item.get("name") or item.get("title") or item.get("step") or item.get("tool_name") or f"步骤 {index}", 100)
                detail = safe_text(item.get("goal") or item.get("summary") or item.get("description") or item.get("output_summary") or "", 140)
                lines.append(f"{index}. {name}" + (f"：{detail}" if detail else ""))
            else:
                lines.append(f"{index}. {safe_text(item, 180)}")
        if len(raw_items) > limit:
            lines.append(f"其余 {len(raw_items) - limit} 个步骤已进入任务工作台。")
        return lines

    def _tool_display_name(self, payload: Mapping[str, Any]) -> str:
        return safe_text(payload.get("tool_name") or payload.get("step_name") or payload.get("step_id") or "工具步骤", 80)

    def _format_status_probe_reply(self) -> str:
        s = self._snapshot
        run_id = safe_text(getattr(s, "active_run_id", ""), 80) or "无"
        if len(run_id) > 18:
            run_id = run_id[:8] + "…" + run_id[-6:]
        current = safe_text(getattr(s, "current_stage", ""), 120) or safe_text(getattr(s, "execution_stage", ""), 120) or "等待 Runtime 状态"
        tool = safe_text(getattr(s, "current_tool_name", ""), 80) or "暂无工具事件"
        event = safe_text(getattr(s, "run_last_event", ""), 80) or "无"
        lines = [
            f"Run：{run_id}",
            f"状态：{safe_text(getattr(s, 'run_status_label', ''), 40) or safe_text(getattr(s, 'current_task_status', ''), 40)}",
            f"进度：{int(getattr(s, 'progress_percent', 0) or 0)}%",
            f"当前阶段：{current}",
            f"当前工具：{tool}",
            f"最近事件：{event}",
            f"成功/阻断：{int(getattr(s, 'success_count', 0) or 0)} / {int(getattr(s, 'blocked_count', 0) or 0)}",
        ]
        if int(getattr(s, "pending_confirmation_count", 0) or 0) > 0 or safe_text(getattr(s, "waiting_approval_ticket_id", ""), 80):
            lines.append("等待审批：有权限/质量门确认项，请看弹窗或质量门详情。")
        running_steps = [step for step in list(getattr(s, "execution_steps", []) or []) if safe_text(getattr(step, "status", ""), 32) in {"running", "queued", "confirmation_required"}]
        if running_steps:
            lines.append("当前步骤：" + "；".join(safe_text(getattr(step, "name", ""), 80) for step in running_steps[:3]))
        next_plan = safe_text(getattr(getattr(s, "task_snapshot", None), "next_plan", ""), 160)
        if next_plan:
            lines.append(f"下一步：{next_plan}")
        return self._progress_message("当前任务状态", lines, status="状态")

    def _is_status_probe_message(self, text: str) -> bool:
        clean = safe_text(text, 120).lower().strip(" ?？。！!，,")
        if not clean:
            return False
        if len(clean) > 40 and not any(word in clean for word in ("进度", "状态", "status", "progress")):
            return False
        return any(word.lower() in clean for word in STATUS_PROBE_PATTERNS)

    def try_handle_status_probe(self, text: str) -> Optional[RuntimeSnapshot]:
        if not self._is_status_probe_message(text):
            return None
        safe_message = safe_chat_text(text, CHAT_USER_INPUT_LIMIT).strip()
        if not safe_message:
            return None
        self._transcript.append_message(ChatMessage("user", "你", time.strftime("%H:%M:%S"), safe_message))
        if not bool(getattr(self, "_active_task_flow", False)):
            reply = "当前没有运行中的工作任务。聊天不会触发任务工作台；需要真实执行请切换到工作模式。"
        else:
            reply = self._format_status_probe_reply()
        self._transcript.append_message(ChatMessage("assistant", self._assistant_label(), "状态", reply))
        self._sync_transcript_projection()
        self._snapshot.stream_state = safe_text(getattr(self._snapshot, "stream_state", "idle"), 40) or "idle"
        self._snapshot.stream_activity_label = safe_text(getattr(self._snapshot, "stream_activity_label", ""), 80)
        return self._snapshot

    def _clean_assistant_visible_content(self, value: Any, *, final: bool = False) -> str:
        raw_text = safe_chat_text(value, CHAT_MESSAGE_DISPLAY_LIMIT if final else 1600)
        casual = is_casual_chat_message(self._active_user_message)
        internal_markers = (
            "return_analysis", "return_code", "User message appears incomplete", "Awaiting complete task description",
            "runstate=", "safecommandrunner", "safe_command_runner", "RuntimeBackendSubprocess",
        )
        if casual and any(marker.lower() in raw_text.lower() for marker in internal_markers):
            # The user is chatting; raw runtime diagnostics are not a valid chat answer.
            # Let final fallback produce a natural visible response.
            return "刚刚有内部诊断信息被挡在显示层了。现在按普通聊天继续。" if final else ""
        text = self._strip_raw_tool_output(raw_text)
        text = safe_chat_text(text, CHAT_MESSAGE_DISPLAY_LIMIT if final else 1600)
        if not text:
            return "在。" if final and casual else ""
        cleaned_lines: list[str] = []
        removed_internal = 0
        for line in text.splitlines():
            stripped = line.strip()
            if _is_internal_chat_leak_line(stripped):
                removed_internal += 1
                continue
            stripped2 = re.sub(
                r"^[-•]?\s*(?:return_analysis|return_code|model_chat)\s*[:：]\s*(?:ok|pass|success|succeeded)?\s*[|｜:：-]?\s*",
                "",
                stripped,
                flags=re.IGNORECASE,
            )
            if not stripped2:
                continue
            if any(marker.lower() in stripped2.lower() for marker in ("Runtime is live and ready", "Affective state:", "Lifecycle, memory", "Awaiting user directive")):
                removed_internal += 1
                continue
            cleaned_lines.append(stripped2 if stripped2 != stripped else line)
        cleaned = safe_chat_text("\n".join(cleaned_lines).strip(), CHAT_MESSAGE_DISPLAY_LIMIT if final else 1600)
        if not cleaned and final:
            if casual or removed_internal:
                return "刚刚有内部诊断信息被挡在显示层了。现在按普通聊天继续。"
            return "已收到。"
        return cleaned

    def _flush_pending_assistant_delta(self, *, force: bool = False) -> None:
        merged = self._delta_merger.flush(force=force)
        if merged:
            self._transcript.append_assistant_delta(merged, label=self._assistant_label())
            self._sync_transcript_projection()
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

    def _payload_requests_task_flow(self, payload: Optional[Mapping[str, Any]]) -> bool:
        if not isinstance(payload, Mapping):
            return False
        # L6.73.1：前端 work 只请求 ActivationForm，不代表已经进入工具/长链状态。
        # 任务工作台只在后端明确返回 run_started/long_chain，或前端显式要求 task_flow 时打开，
        # 避免“你是谁/普通聊天”在沙盘/工作模式下误显示工具执行中。
        if bool(payload.get("task_flow_requested")):
            return True
        if bool(payload.get("long_chain_requested")):
            return True
        if isinstance(payload.get("work_mode"), Mapping):
            work_mode = payload.get("work_mode") or {}
            if bool(work_mode.get("task_flow_requested")) or bool(work_mode.get("long_chain_requested")):
                return True
        return False

    def _display_channel_from_payload(self, payload: Optional[Mapping[str, Any]], event: RuntimeSseEvent | None = None) -> str:
        channel = safe_text(getattr(event, "display_channel", "") if event is not None else "", 40)
        if channel:
            return channel
        if isinstance(payload, Mapping):
            return safe_text(payload.get("display_channel", ""), 40)
        return ""

    def _event_visibility_from_payload(self, payload: Optional[Mapping[str, Any]], event: RuntimeSseEvent | None = None) -> str:
        visibility = safe_text(getattr(event, "visibility", "") if event is not None else "", 40)
        if visibility:
            return visibility
        if isinstance(payload, Mapping):
            return safe_text(payload.get("visibility", ""), 40)
        return ""

    def _event_kind_from_payload(self, payload: Optional[Mapping[str, Any]], event: RuntimeSseEvent | None = None) -> str:
        kind = safe_text(getattr(event, "event_kind", "") if event is not None else "", 40)
        if kind:
            return kind
        if isinstance(payload, Mapping):
            return safe_text(payload.get("event_kind", ""), 40)
        return ""

    def _event_requests_task_flow(self, name: str, payload: Optional[Mapping[str, Any]], event: RuntimeSseEvent | None = None) -> bool:
        """Return whether an event should occupy RunWorkbench / tamockkey_flow UI.

        L6.73.x: ``status`` channel alone is not enough. Plain chat streams may
        finish with ``run_terminal`` without run_id/task_id. Such events must not
        open or complete the workbench unless a task identity, explicit tamockkey_flow
        flag, existing active flow, or run_started event is present.
        """
        display_channel = self._display_channel_from_payload(payload, event)
        has_identity = bool(
            (event is not None and (safe_text(getattr(event, "run_id", ""), 80) or safe_text(getattr(event, "task_id", ""), 80)))
            or (isinstance(payload, Mapping) and (safe_text(payload.get("run_id", ""), 80) or safe_text(payload.get("task_id", ""), 80)))
        )
        active = bool(getattr(self, "_active_task_flow", False))
        payload_requests = self._payload_requests_task_flow(payload)
        if display_channel == "conversation":
            return False
        if display_channel == "workbench":
            return True
        if payload_requests:
            return True
        if name == "run_started":
            return True
        if display_channel in {"status", "silent_audit"}:
            return bool(has_identity or active)
        task_events = {
            "run_started", "run_accepted", "planner_started", "planner_plan", "execution_report", "runtime_state", "heartbeat",
            "quality_gate", "approval_required", "tool_started", "tool_progress", "tool_result",
            "rollback_ticket", "rollback_event", "run_terminal",
        }
        return bool(active and name in task_events)

    def _is_runtime_success_status(self, status: Any) -> bool:
        clean = safe_text(status, 80).lower().replace("-", "_")
        return clean in {
            "ok", "completed", "success", "succeeded", "done",
            "completed_pass", "completed_with_warnings", "deterministic_fallback",
        }

    def _set_run_workbench_state(self, state: str, *, event_name: str = "", payload: Optional[Mapping[str, Any]] = None) -> None:
        payload = payload or {}
        normalized = normalize_run_state(state)
        s = self._snapshot
        s.run_workbench_contract = RUN_WORKBENCH_CONTRACT_VERSION
        s.run_workbench_state = normalized
        s.run_status_label = run_state_label(normalized)
        s.frontend_work_mode = safe_text(payload.get("frontend_work_mode", getattr(s, "frontend_work_mode", "work")), 40)
        if event_name:
            s.run_last_event = safe_text(event_name, 80)
        if payload.get("timestamp"):
            s.run_last_event_at = safe_text(payload.get("timestamp"), 80)
        if payload.get("tool_name") or payload.get("step_id"):
            s.current_tool_name = safe_text(payload.get("tool_name") or payload.get("step_id"), 80)
        if payload.get("status"):
            s.current_tool_status = safe_text(payload.get("status"), 80)
        ticket = safe_text(payload.get("ticket_id") or payload.get("gate_id") or payload.get("approval_id") or "", 80)
        if ticket:
            s.waiting_approval_ticket_id = ticket
        if payload.get("heartbeat") or event_name == "heartbeat":
            s.run_heartbeat_count += 1
            try:
                s.run_heartbeat_age_ms = int(payload.get("elapsed_ms", s.run_heartbeat_age_ms) or 0)
            except (TypeError, ValueError):
                pass
        if payload.get("diagnostic_summary") or payload.get("message"):
            s.run_diagnostic_summary = safe_text(payload.get("diagnostic_summary") or payload.get("message"), 260)
        s.run_stop_available = normalized in ACTIVE_STATES
        s.run_resume_available = normalized in {"reconnecting", "recoverable"}
        s.run_reconnect_available = normalized in {"reconnecting", "recoverable", "failed"}
        s.frontend_executes_tools = False
        s.run_workbench = RunWorkbenchProjection.from_mapping({
            "state": s.run_workbench_state,
            "label": s.run_status_label,
            "run_id": s.active_run_id,
            "task_id": s.active_task_id,
            "frontend_work_mode": s.frontend_work_mode,
            "planner_mode": s.planner_mode,
            "current_tool_name": s.current_tool_name,
            "current_tool_status": s.current_tool_status,
            "waiting_ticket_id": s.waiting_approval_ticket_id,
            "heartbeat_count": s.run_heartbeat_count,
            "heartbeat_age_ms": s.run_heartbeat_age_ms,
            "last_event": s.run_last_event,
            "last_event_at": s.run_last_event_at,
            "diagnostic_summary": s.run_diagnostic_summary,
            "reconnect_available": s.run_reconnect_available,
            "resume_available": s.run_resume_available,
            "stop_available": s.run_stop_available,
        })

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
        display_channel = self._display_channel_from_payload(payload, event)
        visibility = self._event_visibility_from_payload(payload, event)
        event_kind = self._event_kind_from_payload(payload, event)
        conversation_event = display_channel == "conversation" or (not display_channel and name in {"assistant_delta", "assistant_final"})
        task_flow_event = self._event_requests_task_flow(name, payload, event)
        if task_flow_event:
            self._active_task_flow = True
        if event.seq:
            self._last_seq = max(self._last_seq, int(event.seq))
            self._snapshot.last_event_seq = self._last_seq
        if event.run_id and task_flow_event:
            self._active_run_id = event.run_id
            self._snapshot.session_id = event.run_id
            self._snapshot.active_run_id = event.run_id
        if event.task_id and task_flow_event:
            self._active_task_id = event.task_id
            self._snapshot.task_snapshot.task_id = event.task_id
            self._snapshot.active_task_id = event.task_id
        wb_payload = dict(payload)
        if event.timestamp:
            wb_payload.setdefault("timestamp", event.timestamp)

        if name in {"provider_settings", "provider_settings_snapshot", "provider_settings_public"}:
            # Provider settings can arrive either through the explicit REST
            # endpoint or through a runtime SSE projection. Apply the same
            # allowlist/sanitization path in both cases so legacy raw
            # ``base_url`` is converted to ``base_url_display`` and secrets
            # never enter frontend public state.
            self._apply_provider_settings(payload)
            self._sync_derived_projection()
            return

        if name == "run_started":
            if task_flow_event:
                self._set_run_workbench_state("submitting", event_name=name, payload=wb_payload)
            self._snapshot.runtime_status = safe_text(payload.get("runtime_status", "active"), 60)
            self._snapshot.current_task_status = "RUNNING" if task_flow_event else "CHATTING"
            self._snapshot.connection_status = "Runtime SSE 已连接"
            self._snapshot.stream_state = "thinking"
            self._snapshot.stream_visual_state = "thinking"
            self._snapshot.stream_activity_label = "正在思考"
            if payload.get("provider_model"):
                self._snapshot.provider_model = safe_text(payload.get("provider_model"), 80)
                self._snapshot.model_provider = self._snapshot.provider_model
            if payload.get("tool_execution_mode"):
                self._snapshot.tool_execution_mode = safe_text(payload.get("tool_execution_mode"), 80)
                self.provider_settings["tool_execution_mode"] = self._snapshot.tool_execution_mode
            if payload.get("persona_name"):
                self.provider_settings["persona_name"] = safe_text(payload.get("persona_name"), 32)
            self._snapshot.progress_percent = max(self._snapshot.progress_percent, 5)
            self._append_progress_notice(
                f"run_started:{self._snapshot.active_run_id or event.seq}",
                "工作任务已启动",
                ["Runtime 已接收任务流。", f"模式：{safe_text(getattr(self._snapshot, 'frontend_work_mode', ''), 40) or 'work'}", "后续步骤会持续写入任务工作台，不写入会话区。"],
            )
        elif name == "run_accepted":
            if not task_flow_event:
                return
            self._set_run_workbench_state("accepted", event_name=name, payload=wb_payload)
            self._snapshot.current_stage = safe_text(payload.get("phase", "Runtime 已接收任务"), 100)
            self._snapshot.connection_status = "Runtime 已接收任务，进入任务工作台"
            self._snapshot.progress_percent = max(self._snapshot.progress_percent, 8)
            self._append_progress_notice(
                f"run_accepted:{self._snapshot.active_run_id or event.seq}",
                "任务已进入执行链",
                [self._snapshot.current_stage, "前端只展示状态；真实执行仍由 Runtime / Planner / ToolMode / QualityGate 裁决。"],
            )
        elif name == "planner_started":
            if not task_flow_event:
                return
            self._set_run_workbench_state("planning", event_name=name, payload=wb_payload)
            self._snapshot.planner_mode = safe_text(payload.get("planner_mode", self._snapshot.planner_mode), 80)
            self._snapshot.current_stage = "Planner 正在生成计划"
            self._snapshot.stream_state = "thinking"
            self._snapshot.stream_visual_state = "thinking"
            self._snapshot.stream_activity_label = "正在思考"
            self._snapshot.progress_percent = max(self._snapshot.progress_percent, 15)
            self._append_progress_notice(
                f"planner_started:{self._snapshot.active_run_id or event.seq}",
                "正在拆解任务计划",
                ["Planner 正在把用户目标拆成可执行步骤。", f"Planner 模式：{self._snapshot.planner_mode or '默认'}"],
            )
        elif name == "planner_plan":
            if not task_flow_event:
                return
            self._set_run_workbench_state("planning", event_name=name, payload=wb_payload)
            raw_steps = payload.get("steps") or []
            if isinstance(raw_steps, str):
                raw_steps = [raw_steps]
            if isinstance(raw_steps, Iterable):
                self._snapshot.execution_steps = [self._step_from_any(item) for item in list(raw_steps)[:50]] or self._snapshot.execution_steps
            self._snapshot.execution_stage = "Plan 已通过 plan_schema normalize"
            self._snapshot.task_snapshot.current_stage = "Plan 已生成"
            self._snapshot.progress_percent = max(self._snapshot.progress_percent, 25)
            plan_lines = self._summarize_plan_steps(raw_steps)
            self._append_progress_notice(
                f"planner_plan:{self._snapshot.active_run_id or event.seq}:{digest_text(plan_lines, 8)}",
                "执行计划已生成",
                plan_lines or ["Plan 已生成，等待工具链接续执行。"],
            )
        elif name in {"runtime_state", "heartbeat"}:
            if not task_flow_event:
                return
            self._set_run_workbench_state("tool_running", event_name=name, payload=wb_payload)
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
        elif name in {"quality_gate", "approval_required"}:
            if not task_flow_event:
                return
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
                self._set_run_workbench_state("waiting_approval", event_name=name, payload=wb_payload)
                self._snapshot.pending_confirmation_count = max(self._snapshot.pending_confirmation_count, 1)
                self._snapshot.task_snapshot.waiting_user_confirmation = True
                ticket_id = guard_card.ticket_id or guard_card.gate_id
                if ticket_id and not any(safe_text(item.get("ticket_id", ""), 80) == ticket_id for item in self._snapshot.pending_confirmations):
                    self._append_progress_notice(
                        f"approval_required:{ticket_id}",
                        "等待用户审批",
                        [f"风险等级：{guard_card.risk_level}", guard_card.action_summary or guard_card.title, "请在审批弹窗或质量门详情中决定。"],
                    )
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
            elif not guard_card.requires_user_confirmation:
                self._set_run_workbench_state("accepted", event_name=name, payload=wb_payload)
            self._snapshot.progress_percent = max(self._snapshot.progress_percent, 40)
        elif name in {"tool_started", "tool_progress"}:
            if not task_flow_event:
                return
            self._set_run_workbench_state("tool_running", event_name=name, payload=wb_payload)
            tool_name = self._tool_display_name(payload)
            self._append_or_update_step(step_id=safe_text(payload.get("step_id", ""), 80), tool_name=safe_text(payload.get("tool_name", ""), 80), status="running")
            detail = safe_text(payload.get("message") or payload.get("phase") or payload.get("input_summary") or payload.get("path_hint") or "正在执行工具步骤", 220)
            progress_kind = "tool_progress" if name == "tool_progress" else "tool_started"
            progress_title = "步骤进展" if name == "tool_progress" else "正在执行步骤"
            progress_key_tail = digest_text(detail, 8) if name == "tool_progress" else tool_name
            self._append_progress_notice(
                f"{progress_kind}:{self._snapshot.active_run_id or event.seq}:{tool_name}:{progress_key_tail}",
                progress_title,
                [f"工具/步骤：{tool_name}", detail],
            )
            self._snapshot.progress_percent = max(self._snapshot.progress_percent, 50)
        elif name == "tool_result":
            if not task_flow_event:
                return
            self._set_run_workbench_state("tool_running", event_name=name, payload=wb_payload)
            self._append_or_update_step(
                step_id=safe_text(payload.get("step_id", ""), 80),
                tool_name=safe_text(payload.get("tool_name", ""), 80),
                status=safe_text(payload.get("status", "ok"), 32),
                audit_ref=safe_text(payload.get("audit_ref", ""), 80),
                output_summary=safe_text(payload.get("output_summary", ""), 180),
            )
            self._snapshot.success_count = sum(1 for step in self._snapshot.execution_steps if step.status in {"ok", "succeeded", "success"})
            self._snapshot.blocked_count = sum(1 for step in self._snapshot.execution_steps if step.status in {"blocked", "failed", "timeout"})
            result_status = safe_text(payload.get("status", "ok"), 32)
            summary = safe_text(payload.get("output_summary") or payload.get("summary") or payload.get("message") or "工具步骤已返回结果；原始输出在诊断/审计中查看。", 240)
            self._append_progress_notice(
                f"tool_result:{self._snapshot.active_run_id or event.seq}:{self._tool_display_name(payload)}:{result_status}",
                "步骤已返回",
                [f"工具/步骤：{self._tool_display_name(payload)}", f"状态：{result_status}", summary],
            )
            self._snapshot.progress_percent = max(self._snapshot.progress_percent, 60)
        elif name == "audit_event":
            audit_id = safe_text(payload.get("audit_id", payload.get("audit_ref", "")), 80)
            if audit_id:
                self._snapshot.audit_id = audit_id
                self._snapshot.evidence_ref = audit_id
            self._snapshot.audit_count += 1
            self._append_audit_readonly_card(AuditReadonlyCard.from_payload(payload, count=self._snapshot.audit_count))
        elif name in {"rollback_ticket", "rollback_event"}:
            if not task_flow_event:
                return
            self._append_rollback_readonly_card(RollbackReadonlyCard.from_payload(payload))
            rollback_ref = safe_text(payload.get("rollback_ticket") or payload.get("rollback_ref") or payload.get("ticket_id"), 80)
            if rollback_ref:
                self._snapshot.recovery_ticket_id = rollback_ref
            self._snapshot.recovery_requires_human_confirmation = bool(payload.get("requires_human_confirmation", False))
        elif name == "assistant_delta":
            if task_flow_event:
                self._set_run_workbench_state("streaming", event_name=name, payload=wb_payload)
            if payload.get("label"):
                self.provider_settings["persona_name"] = safe_text(payload.get("label"), 32)
            content = self._clean_assistant_visible_content(payload.get("content", ""), final=False)
            if content and conversation_event:
                self._delta_merger.push(content)
                self._flush_pending_assistant_delta(force=False)
            elif content:
                self._snapshot.run_diagnostic_summary = safe_text(content, 900)
            self._snapshot.stream_state = "streaming"
            self._snapshot.stream_visual_state = "streaming"
            self._snapshot.stream_activity_label = "正在输出"
            self._snapshot.current_stage = "Runtime 正在流式输出"
        elif name == "assistant_final":
            if task_flow_event:
                self._set_run_workbench_state("streaming", event_name=name, payload=wb_payload)
            self._seen_assistant_final = True
            self._flush_pending_assistant_delta(force=True)
            content = self._clean_assistant_visible_content(payload.get("content", ""), final=True)
            status = safe_text(payload.get("status", "ok"), 64)
            if content and conversation_event:
                self._transcript.finalize_assistant(content, label=self._assistant_label())
                self._snapshot.chat_messages = self._transcript.visible_messages()
                self._snapshot.visible_message_count = self._transcript.visible_message_count
                self._snapshot.hidden_message_count = self._transcript.hidden_message_count
            elif content:
                self._snapshot.run_diagnostic_summary = safe_text(content, 900)
            self._snapshot.current_task_status = ("COMPLETED" if task_flow_event else "READY") if self._is_runtime_success_status(status) else "PARTIAL_OR_FAILED"
            if task_flow_event:
                self._snapshot.progress_percent = max(self._snapshot.progress_percent, 90)
        elif name == "run_terminal":
            self._flush_pending_assistant_delta(force=True)
            terminal_status = safe_text(payload.get("status", "ok"), 64)
            if task_flow_event:
                terminal_state = normalize_run_state(terminal_status)
                if self._is_runtime_success_status(terminal_status):
                    self._set_run_workbench_state("completed", event_name=name, payload=wb_payload)
                elif terminal_state == "recoverable":
                    self._set_run_workbench_state("recoverable", event_name=name, payload=wb_payload)
                elif terminal_status in {"cancelled", "stopped", "interrupted"} or terminal_state == "cancelled":
                    self._set_run_workbench_state("cancelled", event_name=name, payload=wb_payload)
                else:
                    self._set_run_workbench_state("failed", event_name=name, payload=wb_payload)
            if self._is_runtime_success_status(terminal_status) and self._snapshot.current_task_status not in {"PARTIAL_OR_FAILED", "BLOCKED"}:
                self._snapshot.current_task_status = "COMPLETED" if task_flow_event else "READY"
            if task_flow_event:
                self._append_progress_notice(
                    f"run_terminal:{self._snapshot.active_run_id or event.seq}:{terminal_status}",
                    "任务已收口",
                    [f"终态：{terminal_status}", f"成功步骤：{self._snapshot.success_count}", f"阻断/失败：{self._snapshot.blocked_count}", "原始工具输出已从主会话隐藏，可通过诊断查看。"],
                    force=True,
                )
            self._snapshot.stream_state = "completed"
            self._snapshot.stream_visual_state = "completed"
            self._snapshot.stream_activity_label = "已完成"
            self._snapshot.current_stage = "Runtime SSE 已收口"
            self._snapshot.execution_stage = "任务已完成" if self._snapshot.current_task_status == "COMPLETED" else "任务已收口，需检查异常"
            self._snapshot.connection_status = "Runtime SSE 已收口：assistant_final -> run_terminal"
            self._snapshot.progress_percent = 100 if self._snapshot.current_task_status == "COMPLETED" else self._snapshot.progress_percent
        elif name == "error":
            if task_flow_event:
                self._set_run_workbench_state("failed", event_name=name, payload=wb_payload)
            message = safe_text(payload.get("message", "Runtime SSE error"), 500)
            code = safe_text(payload.get("error_code", "runtime_error"), 80)
            self._snapshot.current_task_status = "PARTIAL_OR_FAILED"
            self._snapshot.runtime_status = "error"
            self._snapshot.stream_state = "error"
            self._snapshot.stream_visual_state = "error"
            self._snapshot.stream_activity_label = "已停止"
            self._snapshot.connection_status = f"Runtime error：{code}"
            self._append_progress_notice(
                f"error:{self._snapshot.active_run_id or event.seq}:{code}",
                "执行出现异常",
                [f"错误码：{code}", message, "可点击重连/诊断继续排查。"],
                force=True,
            )
            if conversation_event and event_kind == "error_summary":
                self._transcript.finalize_assistant(message, time="错误")
                self._sync_transcript_projection()
            else:
                self._snapshot.run_diagnostic_summary = safe_text(message, 900)
                self._sync_derived_projection()

        post_decision = self._evaluate_hook(
            HOOK_STAGE_POST_EVENT_APPLY,
            {"event": name, "payload": payload, "run_id": event.run_id, "task_id": event.task_id, "seq": event.seq},
        )
        if not post_decision.ok:
            self._apply_hook_block(event, post_decision)
        self._sync_derived_projection()

    def _runtime_session_status(self) -> str:
        status = safe_text(self._snapshot.current_task_status, 60).upper()
        if status in {"COMPLETED", "DONE", "SUCCESS"}:
            return "completed"
        if status in {"RUNNING", "STREAMING"}:
            return "running"
        if status in {"BLOCKED", "A5_BLOCKED"}:
            return "blocked"
        if status in {"PARTIAL_OR_FAILED", "STREAM_INTERRUPTED", "ERROR", "FAILED"}:
            return "recoverable"
        if status in {"DISCONNECTED"}:
            return "paused"
        if status in {"READY", "IDLE"}:
            return "queued"
        return status.lower() if status else "queued"

    def _sync_active_session_projection(self) -> None:
        s = self._snapshot
        if not (self._active_run_id or s.active_run_id or self._active_task_id or s.active_task_id):
            s.session_stats = self._normalize_session_stats({}, list(s.task_sessions or []))
            return
        run_id = self._active_run_id or s.active_run_id or s.session_id
        task_id = self._active_task_id or s.active_task_id or s.task_snapshot.task_id
        session_digest = digest_text(run_id or task_id or s.session_id, 16)
        status = self._runtime_session_status()
        waiting = bool(s.pending_confirmation_count > 0 or s.task_snapshot.waiting_user_confirmation)
        blocked = status == "blocked" or bool(s.blocked_count > 0 and not s.quality_allow_continue)
        recoverable = status in {"recoverable", "failed", "paused", "blocked"} or bool(s.recovery_resume_plan_count > 0 or s.recovery_ticket_id)
        title = safe_text(self._active_user_message or s.task_snapshot.current_stage or s.current_stage or "当前任务", 120)
        active = status == "running"
        projected = TaskSessionProjection(
            session_id_digest=session_digest,
            title=title or "当前任务",
            status=status,
            current_stage=safe_text(s.task_snapshot.current_stage or s.current_stage, 140),
            progress_percent=s.progress_percent,
            waiting_confirmation=waiting,
            blocked=blocked,
            recoverable=recoverable,
            active=active,
            last_updated="当前",
            run_id_digest=digest_text(run_id, 16),
            task_id_digest=digest_text(task_id, 16),
            audit_id=s.audit_id or s.evidence_ref,
            tags=["runtime_projection", s.stream_state],
            message="当前任务由 Runtime SSE 投影；前端只显示和提交请求。",
        )
        existing = self._drop_legacy_mock_sessions(list(s.task_sessions or []))
        replaced = False
        updated: List[TaskSessionProjection] = []
        for item in existing:
            if safe_text(getattr(item, "session_id_digest", ""), 80) == session_digest:
                updated.append(projected)
                replaced = True
            else:
                updated.append(item)
        if not replaced:
            updated.insert(0, projected)
        s.task_sessions = updated[:80]
        s.session_stats = self._normalize_session_stats({}, s.task_sessions)
        s.session_filtered_count = len(s.task_sessions)

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
        pending_from_cards = sum(1 for card in s.action_guard_cards if card.requires_user_confirmation and card.status in {"pending_user_confirmation", "display_only"})
        pending_from_tickets = len([item for item in (s.pending_confirmations or []) if not safe_text(item.get("runtime_status", item.get("frontend_decision_request", item.get("frontend_decision", ""))), 80)])
        s.pending_confirmation_count = max(pending_from_cards, pending_from_tickets)
        s.task_snapshot.waiting_user_confirmation = bool(s.pending_confirmation_count > 0)
        if pending_from_cards:
            s.conversation_guide.recommended_actions = ["查看行动守卫卡", "提交确认请求", "必要时中断任务"]
            s.conversation_guide.suggested_questions = ["请解释这张行动守卫卡为什么需要确认", "如果拒绝会怎样", "只执行低风险部分"]
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
        s.task_sessions = self._drop_legacy_mock_sessions(list(s.task_sessions or []))
        self._sync_active_session_projection()
        self._sync_hook_projection()

    def _connection_failure_snapshot(self, reason: str) -> RuntimeSnapshot:
        timeout_hint = ""
        if "timed out" in str(reason).lower() or "timeout" in str(reason).lower() or "超时" in str(reason):
            timeout_hint = "；可能是后端长任务未及时发送 heartbeat，请检查桥接心跳或提高运行时空闲超时"
        repair_hint = safe_text(self._local_bridge_repair_message, 180)
        diagnostic = safe_text(str(reason) + timeout_hint + (("；" + repair_hint) if repair_hint else ""), 320)
        task_flow_active = bool(getattr(self, "_active_task_flow", False))
        self._snapshot.runtime_status = "连接失败"
        self._snapshot.connection_status = diagnostic
        self._snapshot.current_task_status = "DISCONNECTED" if task_flow_active else "CHATTING"
        self._snapshot.stream_state = "error"
        self._snapshot.stream_visual_state = "error"
        self._snapshot.stream_activity_label = "连接未完成"
        self._snapshot.source_kind = "runtime_sse_disconnected"
        self._snapshot.run_diagnostic_summary = diagnostic
        if task_flow_active:
            self._snapshot.current_stage = "Runtime SSE 工作连接失败；任务状态进入可恢复诊断"
            self._set_run_workbench_state("recoverable", event_name="connection_failure", payload={"diagnostic_summary": diagnostic})
            visible = "工作任务连接未完成，诊断已放入任务详情区；可重试、续接或中断。"
        else:
            # L6.72.49：普通聊天失败不得生成 run/task 工作台，也不得把
            # /chat/stream-events、stdout/stderr、Provider 诊断原文塞入主会话。
            self._snapshot.current_stage = "普通聊天连接未完成；未触发工作任务"
            self._snapshot.run_workbench_state = "idle"
            self._snapshot.run_status_label = "待机"
            self._snapshot.active_run_id = ""
            self._snapshot.active_task_id = ""
            self._snapshot.current_tool_name = ""
            self._snapshot.current_tool_status = ""
            visible = "我这边没有拿到模型回复。普通聊天未触发工作任务，诊断已进入状态栏。"
        self._transcript.finalize_assistant(visible, time="连接")
        self._snapshot.chat_messages = self._transcript.visible_messages()
        self._evaluate_hook(HOOK_STAGE_ON_ERROR, {"error": diagnostic, "payload": {"message": diagnostic, "task_flow_active": task_flow_active}})
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

    def clear_local_transcript(self) -> RuntimeSnapshot:
        """Clear only the desktop-visible transcript cache.

        This does not delete Runtime audit records, task sessions, memory, or
        rollback state. It prevents the old UI transcript from being reloaded
        after the user clicks 清屏 and then sends a new message.
        """
        self._snapshot.chat_messages = []
        self._snapshot.visible_message_count = 0
        self._snapshot.hidden_message_count = 0
        self._snapshot.pending_delta_chars = 0
        self._snapshot.stream_state = "idle"
        self._snapshot.stream_visual_state = "idle"
        self._snapshot.stream_activity_label = ""
        self._delta_merger.flush(force=True)
        self._transcript.clear()
        try:
            data = self._json_request("/conversation/clear", method="POST", payload={"reason": "frontend_clear_local_transcript"})
            if isinstance(data, Mapping) and data.get("message"):
                self._snapshot.control_state = safe_text(data.get("message"), 120)
        except Exception:
            # 兼容旧 Runtime：旧服务没有 /conversation/clear 时，仍至少清前端转录。
            pass
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
            self._apply_run_workbench_status(self._json_request(RUN_STATUS_ENDPOINT))
        except Exception as exc:
            self._snapshot.run_diagnostic_summary = f"Run 工作台状态读取失败：{safe_text(exc, 160)}"
        try:
            self._apply_installer_manifest(self._json_request(INSTALLER_MANIFEST_ENDPOINT))
        except Exception as exc:
            self._snapshot.installer_last_message = f"安装器 RC 投影读取失败：{safe_text(exc, 160)}"
        self._sync_derived_projection()
        return self._snapshot

    def get_run_status(self) -> RuntimeSnapshot:
        try:
            self._apply_run_workbench_status(self._json_request(RUN_STATUS_ENDPOINT))
        except Exception as exc:
            return self._connection_failure_snapshot(f"/runs/status 读取失败：{safe_text(exc, 160)}")
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
        for key in ("api_key_configured", "api_key_digest", "base_url_configured", "base_url_digest", "base_url_display", "tool_execution_mode", "persona_name", "persona_digest", "soul_style_contract", "style_source", "non_soul_style_influence_allowed", "host_access_scope", "host_access_root_configured", "host_access_root_digest"):
            if not public.get(key):
                public[key] = request_public.get(key)
        if not public.get("provider"):
            public["provider"] = request.provider
        if not public.get("model"):
            public["model"] = request.model
        if request.base_url_configured and not public.get("base_url_display"):
            # L6.73.2: Base URL is not a credential. Keep it visible in Settings;
            # API Key remains masked/digest-only.
            public["base_url_display"] = request.base_url

        self.provider_settings = {
            key: sanitize_event_payload(value)
            for key, value in public.items()
            if key not in {"api_key", "base_url", "base_url_normalized", "authorization", "bearer", "token", "secret", "endpoint"}
        }
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
        if public.get("tool_execution_mode"):
            self._snapshot.tool_execution_mode = safe_text(public.get("tool_execution_mode"), 80)
        self._sync_derived_projection()
        return dict(self.provider_settings)

    def _chat_payload(self, runtime_message: str, *, resume: bool = False, work_mode_payload: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
        work_payload = sanitize_work_mode_payload(work_mode_payload or {})
        task_flow_requested = self._payload_requests_task_flow(work_payload)
        requested_tool_mode = safe_text(work_payload.get("tool_mode_requested") or self.provider_settings.get("tool_execution_mode", self._snapshot.tool_execution_mode), 80)
        if not task_flow_requested:
            requested_tool_mode = "disabled"
        elif requested_tool_mode in {"enabled", "enable", "tools", "tool"}:
            requested_tool_mode = "runtime_governed"
        path_candidates = extract_host_paths_from_text(runtime_message)
        body: Dict[str, Any] = {
            "message": runtime_message,
            "user_message": runtime_message,
            "raw_user_text": runtime_message,
            "text_raw": runtime_message,
            "original_user_message": runtime_message,
            "original_path": path_candidates[0] if path_candidates else "",
            "host_path_candidates": path_candidates,
            "message_display": safe_chat_text(runtime_message, 1000),
            "runtime_payload_redaction_guard": "path_redaction_leak_block_v1",
            "frontend_contract": FE_RUNTIME_VERSION,
            "transport": "sse",
            "no_frontend_tool_execution": True,
            "no_frontend_memory_write": True,
            "no_frontend_rollback_apply": True,
            "tool_execution_mode": requested_tool_mode,
            "persona_name": safe_text(self.provider_settings.get("persona_name", "临渊者"), 32),
            "style_source": "soul_only",
            "non_soul_style_influence_allowed": False,
            "work_mode_contract": WORK_MODE_CONTRACT_VERSION,
            "frontend_work_mode": safe_text(work_payload.get("mode", "chat"), 40),
            "work_mode": work_payload,
            "planner_allowed": bool(work_payload.get("planner_allowed", False)),
            "tools_requested": bool(work_payload.get("tools_requested", False)),
            "activation_requested": bool(work_payload.get("activation_requested", False)),
            "long_chain_requested": bool(work_payload.get("long_chain_requested", False)),
            "quality_gate_required": bool(work_payload.get("quality_gate_required", False)),
        }
        if resume and self._active_run_id:
            body["resume"] = {"run_id": self._active_run_id, "last_seq": self._last_seq}
        if _raw_runtime_payload_has_redaction_leak(body):
            raise RuntimeError("path_redaction_leak_detected: <redacted> reached raw Runtime payload")
        hook_decision = self._evaluate_hook(HOOK_STAGE_PRE_CHAT_SUBMIT, {"payload": body, "run_id": self._active_run_id, "task_id": self._active_task_id})
        if not hook_decision.ok:
            raise RuntimeError(f"HookBus blocked chat submit: {hook_decision.reason}")
        return body

    def _open_chat_stream(self, body: Mapping[str, Any]):
        self._autostart_local_bridge_if_needed(reason="chat_stream")
        req = urllib.request.Request(
            self._url(CHAT_STREAM_ENDPOINT),
            data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
            method="POST",
            headers={
                "Accept": "text/event-stream, application/json",
                "Content-Type": "application/json; charset=utf-8",
                "Cache-Control": "no-cache",
                "X-Tiangong-Frontend-Contract": FE_RUNTIME_VERSION,
            },
        )
        return urlopen_with_policy(req, timeout=self.timeout, allow_loopback_http=True, purpose="runtime_sse")

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
            self._snapshot.append_assistant_notice_once("响应", safe_text(parsed, 500), "runtime_json_response", safe_text(parsed, 180), window=20)
            self._notify_snapshot(on_snapshot)

    def submit_user_message(self, text: str) -> RuntimeSnapshot:
        return self.submit_user_message_streaming(text)

    def submit_user_message_streaming(
        self,
        text: str,
        *,
        on_event: Optional[EventCallback] = None,
        on_snapshot: Optional[SnapshotCallback] = None,
        work_mode_payload: Optional[Mapping[str, Any]] = None,
        max_reconnects: Optional[int] = None,
    ) -> RuntimeSnapshot:
        runtime_message = runtime_submission_text(text, 8000)
        safe_message = safe_chat_text(runtime_message, 1000)
        work_payload = sanitize_work_mode_payload(work_mode_payload or {})
        task_flow_requested = self._payload_requests_task_flow(work_payload)
        self._active_task_flow = bool(task_flow_requested)
        if not task_flow_requested:
            self._active_run_id = ""
            self._active_task_id = ""
            self._snapshot.active_run_id = ""
            self._snapshot.active_task_id = ""
        self._active_user_message = runtime_message
        self._snapshot.frontend_work_mode = safe_text(work_payload.get("mode", "chat"), 40)
        self._snapshot.chat_messages.append(ChatMessage("user", "你", time.strftime("%H:%M:%S"), safe_message))
        self._transcript.load(self._snapshot.chat_messages)
        self._delta_merger = DeltaMerger(flush_interval_ms=45, max_chars=1200)
        self._event_buffer = EventBuffer(max_events=512)
        self.last_agent_ui_events = []
        self._snapshot.agent_ui_contract = AGENT_UI_CONTRACT_VERSION
        self._snapshot.stream_render_contract = STREAM_RENDER_CONTRACT_VERSION
        self._snapshot.render_mode = "delta_merge_virtual_transcript"
        self._snapshot.pending_confirmation_count = 0
        self._snapshot.pending_confirmations = []
        self._snapshot.action_guard_cards = []
        self._snapshot.task_snapshot.waiting_user_confirmation = False
        self._snapshot.stream_state = "thinking"
        self._snapshot.stream_visual_state = "thinking"
        self._snapshot.stream_activity_label = "正在思考"
        self._snapshot.runtime_status = "active"
        self._snapshot.current_task_status = "RUNNING" if task_flow_requested else "CHATTING"
        self._snapshot.current_stage = "Runtime SSE 工作提交中" if task_flow_requested else "普通聊天流式提交中"
        self._snapshot.connection_status = "Runtime SSE 正在连接"
        self._snapshot.reconnect_attempts = 0
        self._snapshot.terminal_order_valid = True
        self._seen_assistant_final = False
        self._snapshot.control_state = "ready"
        if task_flow_requested:
            self._set_run_workbench_state("submitting", event_name="frontend_submit", payload={"frontend_work_mode": "work", "diagnostic_summary": "工作任务已从桌面端提交；等待 Runtime 接收。"})
        else:
            self._snapshot.run_workbench_state = "idle"
            self._snapshot.run_status_label = "待机"
            self._snapshot.current_tool_name = ""
            self._snapshot.current_tool_status = ""
        self._notify_snapshot(on_snapshot)

        started = time.time()
        events: List[RuntimeSseEvent] = []
        allowed_reconnects = self.max_reconnects if max_reconnects is None else max(0, int(max_reconnects))
        attempt = 0
        resume = False

        while True:
            try:
                with self._open_chat_stream(self._chat_payload(runtime_message, resume=resume, work_mode_payload=work_payload)) as resp:
                    self._consume_response(resp, events, on_event=on_event, on_snapshot=on_snapshot)
            except urllib.error.HTTPError as exc:
                code = getattr(exc, "code", "http_error")
                return self._connection_failure_snapshot(f"/chat/stream-events HTTP {code}：{safe_text(exc.reason, 120)}")
            except Exception as exc:
                if task_flow_requested and attempt < allowed_reconnects and self._active_run_id:
                    attempt += 1
                    resume = True
                    self._snapshot.reconnect_attempts = attempt
                    self._snapshot.stream_state = "reconnecting"
                    self._snapshot.stream_visual_state = "reconnecting"
                    self._snapshot.stream_activity_label = "断线续接中"
                    self._set_run_workbench_state("reconnecting", event_name="frontend_reconnect", payload={"diagnostic_summary": f"Runtime SSE 断流，正在续接 {attempt}/{allowed_reconnects}"})
                    self._snapshot.connection_status = f"Runtime SSE 断流，正在续接 {attempt}/{allowed_reconnects}"
                    self._notify_snapshot(on_snapshot)
                    continue
                return self._connection_failure_snapshot(f"/chat/stream-events 连接失败：{safe_text(exc, 160)}")

            names = [item.event for item in events]
            if "run_terminal" in names:
                break
            if task_flow_requested and attempt < allowed_reconnects and self._active_run_id:
                attempt += 1
                resume = True
                self._snapshot.reconnect_attempts = attempt
                self._snapshot.stream_state = "reconnecting"
                self._snapshot.stream_visual_state = "reconnecting"
                self._snapshot.stream_activity_label = "断线续接中"
                self._set_run_workbench_state("reconnecting", event_name="frontend_reconnect", payload={"diagnostic_summary": f"未收到 run_terminal，正在续接 {attempt}/{allowed_reconnects}"})
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
            self._snapshot.stream_visual_state = "error"
            self._snapshot.stream_activity_label = "已停止"
            self._snapshot.connection_status = "Runtime SSE 事件顺序异常：缺少 assistant_final -> run_terminal"
        elif "run_terminal" not in [item.event for item in events]:
            self._snapshot.current_task_status = "STREAM_INTERRUPTED"
            self._snapshot.stream_state = "interrupted"
            self._snapshot.stream_visual_state = "interrupted"
            self._snapshot.stream_activity_label = "已停止"
            self._snapshot.connection_status = "Runtime SSE 流未完整收口：未收到 run_terminal"
        elif self._snapshot.stream_state not in {"error"}:
            self._snapshot.stream_state = "completed"
            self._snapshot.stream_visual_state = "completed"
            self._snapshot.stream_activity_label = "已完成"
        if task_flow_requested:
            try:
                self._apply_session_manager(self._json_request(SESSION_LIST_ENDPOINT))
            except Exception as exc:
                self._snapshot.session_last_message = f"任务 Session 收口刷新失败：{safe_text(exc, 160)}"
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
            self._snapshot.append_assistant_notice_once("控制", self.last_control_result["message"], "控制", self.last_control_result["message"], window=20)
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
                self._snapshot.append_assistant_notice_once("控制", result.message, "控制", result.message, window=20)
        except Exception as exc:
            self.last_control_result = RuntimeControlResult(
                action=request.action,
                status="frontend_fallback_recorded",
                message=f"控制请求未到达 Runtime，仅在前端记录：{safe_text(exc, 160)}",
                frontend_only_fallback=True,
            ).__dict__
            self._snapshot.control_state = f"{request.action}_frontend_fallback_recorded"
            self._snapshot.append_assistant_notice_once("控制", self.last_control_result["message"], "控制", self.last_control_result["message"], window=20)
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
            data = self._json_request(FILE_TRANSFER_ENDPOINT, method="POST", payload=payload, extra_headers=request.to_private_runtime_headers())
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
        safe_session = safe_text(session_id_digest, 80)
        if safe_session.upper().startswith("SESS-MOCK"):
            self._snapshot.record_session_resume_request(safe_session, status="mock_session_discarded", message="已清理旧版演示 Session；未向 Runtime 提交恢复请求。")
            self._sync_derived_projection()
            return self._snapshot
        request = SessionResumeRequest(session_id_digest=safe_session, reason=safe_text(reason, 120))
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
            self._snapshot.append_chat_message_once(
                ChatMessage("assistant", "临渊者", "确认", f"HookBus 阻断确认请求：{hook_decision.reason}"),
                "HookBus 阻断确认请求",
                safe_text(hook_decision.reason, 160),
                window=20,
            )
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
            self._snapshot.append_chat_message_once(
                ChatMessage("assistant", "临渊者", "确认", "确认请求已提交 Runtime 网关；等待 QualityGate/Audit 回执，不由前端放行。"),
                "确认请求已提交 Runtime 网关",
                window=20,
            )
        except Exception as exc:
            self._snapshot.submit_confirmation(envelope.ticket_id, envelope.decision)
            self._snapshot.confirmation_request_state = "frontend_fallback_recorded"
            fallback_message = f"确认请求未到达 Runtime，仅前端记录请求：{safe_text(exc, 160)}"
            self._snapshot.append_chat_message_once(
                ChatMessage("assistant", "临渊者", "确认", fallback_message),
                "确认请求未到达 Runtime",
                safe_text(exc, 160),
                window=20,
            )
        self._sync_derived_projection()
        return self._snapshot


    def run_startup_self_check(self) -> RuntimeSnapshot:
        try:
            data = self._json_request("/installer/startup/self-check", method="GET")
            payload = data.get("payload", data) if isinstance(data, Mapping) else {}
            if not isinstance(payload, Mapping):
                payload = {}
            raw_checks = payload.get("startup_self_checks", payload.get("checks", []))
            checks = [StartupSelfCheckRecord.from_mapping(x) for x in raw_checks if isinstance(x, Mapping)][:40] if isinstance(raw_checks, list) else []
            status = safe_text(payload.get("status", "pass" if payload.get("ok", False) else "warn"), 80)
            self._snapshot.record_installer_self_check_result(checks, status=status)
        except Exception as exc:
            self._snapshot.record_installer_self_check_result(
                [StartupSelfCheckRecord(check_id="startup_self_check_http", name="启动自检请求", status="fail", message=f"自检请求失败：{safe_text(exc, 160)}")],
                status="frontend_request_failed",
            )
        self._sync_derived_projection()
        return self._snapshot

    def submit_self_iteration_confirmation(self, candidate_id: str, decision: str) -> RuntimeSnapshot:
        payload = {"candidate_id": safe_text(candidate_id, 80), "decision": safe_text(decision, 32), "frontend_contract": ACTION_GUARD_CONTRACT_VERSION, "no_frontend_self_iteration_apply": True}
        hook_decision = self._evaluate_hook(HOOK_STAGE_PRE_SELF_ITERATION_CONFIRM, {"payload": payload})
        if not hook_decision.ok:
            self._snapshot.append_chat_message_once(
                ChatMessage("assistant", "临渊者", "自我迭代", f"HookBus 阻断自我迭代确认请求：{hook_decision.reason}"),
                "HookBus 阻断自我迭代确认请求",
                safe_text(hook_decision.reason, 160),
                window=20,
            )
            self._sync_derived_projection()
            return self._snapshot
        last_error = ""
        for endpoint in ("/self-iteration/confirm", "/self_iteration/confirm", "/self-iteration/confirm/request"):
            try:
                data = self._json_request(endpoint, method="POST", payload=payload)
                payload_out = data.get("payload", data) if isinstance(data, Mapping) else {}
                status = safe_text(payload_out.get("status", "accepted") if isinstance(payload_out, Mapping) else "accepted", 80)
                self._snapshot.submit_self_iteration_confirmation(candidate_id, decision, runtime_submitted=True, runtime_status=status)
                self._sync_derived_projection()
                return self._snapshot
            except Exception as exc:
                last_error = safe_text(exc, 160)
                continue
        self._snapshot.submit_self_iteration_confirmation(candidate_id, decision)
        fallback_message = f"自我迭代确认未到达 Runtime，仅前端记录请求：{last_error}"
        self._snapshot.append_chat_message_once(
            ChatMessage("assistant", "临渊者", "自我迭代", fallback_message),
            "自我迭代确认未到达 Runtime",
            last_error,
            window=20,
        )
        self._sync_derived_projection()
        return self._snapshot
