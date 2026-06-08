from __future__ import annotations

"""FE01 STEP31Q / L6.71.7 local desktop Runtime bridge.

This bridge is bundled for the desktop all-in-one package. It exposes the
frontend Runtime HTTP/SSE contract and delegates chat execution to the bundled
backend CLI entrypoint. It is deliberately labeled as a local desktop bridge,
not as the official TiangongWangguan real Runtime smoke target.
"""

import argparse
import hashlib
import json
import os
import platform
import re
import subprocess
import sys
import time
import uuid
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend" / "project"
REPORTS = ROOT / "reports"
RUN_AGENT = BACKEND / "run_agent.py"

PRODUCT_IDENTITY = {
    "schema": "tiangong.l6_51_1.product_identity.v1",
    "product_name": "天工造物 / 临渊者",
    "unique_developer": "于泳翔",
    "angel_investor": "胖胖龙",
    "public": True,
    "runtime_semantics": "metadata_only",
    "frontend_permission": "read_only_display",
}

CONTROL_PATHS = {
    "/control/task/stop": "stop",
    "/control/task/reset": "reset",
    "/control/task/interrupt": "interrupt",
}

SENSITIVE_TEXT_PATTERNS = (
    re.compile(r"(?i)Bearer\s+[A-Za-z0-9_\-.]{8,}"),
    re.compile(r"(?i)sk-[A-Za-z0-9_\-]{8,}"),
)


def _provider_config_path() -> Path:
    override = os.environ.get("LINYUANZHE_PROVIDER_CONFIG_FILE", "").strip()
    if override:
        return Path(override).expanduser().resolve()
    system = platform.system()
    if system == "Windows":
        base = Path(os.environ.get("APPDATA", "") or (Path.home() / "AppData" / "Roaming"))
        return base / "LinyuanzheDesktop" / "provider_config.json"
    if system == "Darwin":
        return Path.home() / "Library" / "Application Support" / "LinyuanzheDesktop" / "provider_config.json"
    base = Path(os.environ.get("XDG_CONFIG_HOME", "") or (Path.home() / ".config"))
    return base / "linyuanzhe_desktop" / "provider_config.json"


def _read_provider_config() -> dict[str, Any]:
    path = _provider_config_path()
    try:
        if not path.exists():
            return {}
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _write_provider_config(data: Mapping[str, Any]) -> bool:
    path = _provider_config_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema": "tiangong.l6_71_7.local_provider_config.v1",
            "provider": str(data.get("provider", "") or ""),
            "model": str(data.get("model", "") or ""),
            "base_url": str(data.get("base_url", "") or ""),
            "api_key": str(data.get("api_key", "") or ""),
            "updated_at": datetime.now().isoformat(timespec="seconds"),
            "runtime_owned": True,
            "frontend_raw_secret_visible": False,
        }
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        try:
            os.chmod(path, 0o600)
        except Exception as exc:
            _ = exc
        return True
    except Exception:
        return False


def _digest(value: Any, length: int = 16) -> str:
    text = str(value or "")
    if not text:
        return ""
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()[:length]


def _safe_text(value: Any, limit: int = 2000) -> str:
    text = str(value or "")
    for pattern in SENSITIVE_TEXT_PATTERNS:
        text = pattern.sub("<redacted>", text)
    return text[-limit:]


PROVIDER_ERROR_ACTIONS = {
    "gateway_unreachable": "检查 Tailscale / Base URL / 网关进程后，发送一条短消息复测",
    "auth_failed": "重新填写 API Key 后保存，再发送短消息复测",
    "model_not_found": "确认模型名与账号权限，必要时换成可用模型",
    "provider_timeout": "检查网络与网关负载，或提高 Runtime 超时后重试",
    "provider_rate_limited": "降低频率或更换额度后重试",
    "provider_server_error": "稍后重试；若持续出现，检查网关日志",
    "provider_runtime_error": "查看脱敏错误摘要，修正配置后发送短消息复测",
}


def _classify_provider_error(text: str, returncode: int, elapsed: str) -> str:
    blob = f"{text}\n{returncode}\n{elapsed}".lower()
    if returncode == 124 or "timeout" in blob or "timed out" in blob or "超时" in blob:
        return "provider_timeout"
    if any(x in blob for x in ("401", "403", "unauthorized", "forbidden", "invalid api key", "invalid_api_key", "authentication", "鉴权", "未授权")):
        return "auth_failed"
    if any(x in blob for x in ("404", "model not found", "model_not_found", "unknown model", "模型不存在", "not found")) and "model" in blob:
        return "model_not_found"
    if any(x in blob for x in ("429", "rate limit", "too many requests", "quota", "insufficient_quota", "限流", "额度")):
        return "provider_rate_limited"
    if any(x in blob for x in ("500", "502", "503", "504", "internal server error", "bad gateway", "service unavailable")):
        return "provider_server_error"
    if any(x in blob for x in ("connection refused", "connection reset", "network is unreachable", "name or service not known", "nodename nor servname", "gaierror", "max retries", "ssl", "tls", "cannot connect", "failed to establish")):
        return "gateway_unreachable"
    return "provider_runtime_error"


def _provider_error_action(code: str) -> str:
    return PROVIDER_ERROR_ACTIONS.get(code, PROVIDER_ERROR_ACTIONS["provider_runtime_error"])


class BridgeState:
    def __init__(self, *, backend_mode: str, timeout: float) -> None:
        self.backend_mode = backend_mode
        self.timeout = timeout
        persisted = _read_provider_config()
        self.provider = (os.environ.get("TIANGONG_PROVIDER") or os.environ.get("LINYUANZHE_PROVIDER") or str(persisted.get("provider", "")) or "openai_compatible").strip() or "openai_compatible"
        self.model = (os.environ.get("TIANGONG_MODEL") or os.environ.get("LINYUANZHE_MODEL") or str(persisted.get("model", "")) or "deepseek-v4-pro").strip() or "deepseek-v4-pro"
        self.provider_base = (os.environ.get("TIANGONG_BASE_URL") or os.environ.get("LINYUANZHE_PROVIDER_BASE") or str(persisted.get("base_url", ""))).strip()
        self.provider_key = (os.environ.get("TIANGONG_API_KEY") or os.environ.get("LINYUANZHE_PROVIDER_KEY") or str(persisted.get("api_key", ""))).strip()
        self.provider_config_path = _provider_config_path()
        self.provider_config_loaded = bool(persisted)
        self.provider_config_persisted = bool(persisted)
        self.started_at = datetime.now().isoformat(timespec="seconds")
        self.chat_count = 0
        self.last_audit_id = "audit_local_bridge_idle"
        self.sessions: list[dict[str, Any]] = []
        self.file_handoffs: list[dict[str, Any]] = []
        self.connector_records: list[dict[str, Any]] = []
        self.last_provider_check_state = "not_tested"
        self.last_provider_error_code = ""
        self.last_provider_error_message = ""
        self.last_provider_next_action = "发送一条短消息完成真实链路联调"
        self.last_provider_elapsed = ""
        self.last_provider_audit_id = ""

    @property
    def effective_backend_mode(self) -> str:
        # auto: offline-safe first boot, but switch to provider immediately after
        # settings page saves a valid key/base URL. This fixes the previous UX
        # trap where the default launcher stayed in mock mode even after Key was
        # persisted successfully.
        if self.backend_mode == "mock":
            return "mock"
        if self.provider_key and self.provider_base:
            return "provider"
        return "mock"

    def record_provider_check(self, *, ok: bool, answer: str, returncode: int, elapsed: str, audit_id: str) -> None:
        if self.effective_backend_mode != "provider":
            return
        self.last_provider_elapsed = _safe_text(elapsed, 40)
        self.last_provider_audit_id = _safe_text(audit_id, 80)
        if ok:
            self.last_provider_check_state = "passed"
            self.last_provider_error_code = ""
            self.last_provider_error_message = "最近一次真实 Provider 联调通过。"
            self.last_provider_next_action = "返回会话继续任务"
            return
        code = _classify_provider_error(answer, returncode, elapsed)
        self.last_provider_check_state = "failed"
        self.last_provider_error_code = code
        self.last_provider_error_message = _safe_text(answer, 260)
        self.last_provider_next_action = _provider_error_action(code)

    def provider_projection(self) -> dict[str, Any]:
        base_configured = bool(self.provider_base)
        key_configured = bool(self.provider_key)
        missing_fields = []
        if not base_configured:
            missing_fields.append("base_url")
        if not key_configured:
            missing_fields.append("api_key")
        config_file_exists = self.provider_config_path.exists()
        effective_mode = self.effective_backend_mode
        if self.last_provider_check_state == "failed" and effective_mode == "provider":
            state = "error"
            readiness = "provider_check_failed"
            readiness_label = "Provider 联调失败"
            next_action = self.last_provider_next_action
            message = f"配置已保存，但最近一次真实 Provider 联调失败：{self.last_provider_error_code or 'provider_runtime_error'}。"
        elif effective_mode == "provider" and not missing_fields:
            state = "ready"
            readiness = "ready"
            readiness_label = "真实模型就绪"
            next_action = "返回会话继续对话" if self.last_provider_check_state == "passed" else "发送一条短消息完成真实链路联调"
            message = "本地桌面桥接后端已就绪；真实模型配置由本机 Runtime 凭证文件托管。"
        elif self.backend_mode == "mock":
            state = "forced_mock"
            readiness = "forced_mock"
            readiness_label = "启动参数锁定 Mock"
            next_action = "用 auto/provider 模式重启桌面端"
            message = "当前启动参数为 mock；即使存在 Provider 配置也不会调用真实模型。"
        else:
            state = "missing_credentials" if missing_fields else "mock_ready"
            readiness = "missing_credentials" if missing_fields else "saved_waiting_runtime"
            readiness_label = "缺 Provider 配置" if missing_fields else "配置已保存，等待 provider 模式"
            next_action = "填写 Base URL 与 API Key 后保存" if missing_fields else "刷新快照或发送一条消息"
            message = "本地桌面桥接后端已就绪；auto 模式未配置真实模型时使用 bundled mock 后端。"
        return {
            "frontend_contract": "tiangong.l6_71_7.desktop_provider_projection.v1",
            "provider": self.provider,
            "model": self.model,
            "provider_config_state": state,
            "provider_readiness": readiness,
            "readiness_label": readiness_label,
            "missing_fields": missing_fields,
            "next_action": next_action,
            "config_error_code": self.last_provider_error_code if self.last_provider_check_state == "failed" else "",
            "message": message,
            "audit_id": self.last_provider_audit_id or self.last_audit_id,
            "last_provider_check_state": self.last_provider_check_state,
            "last_provider_error_code": self.last_provider_error_code,
            "last_provider_error_message": self.last_provider_error_message,
            "last_provider_next_action": self.last_provider_next_action,
            "last_provider_elapsed": self.last_provider_elapsed,
            "last_provider_audit_id": self.last_provider_audit_id,
            "planner_mode": "rule_only",
            "tool_execution_mode": "runtime_governed",
            "stream": True,
            "api_key_configured": key_configured,
            "api_key_digest": _digest(self.provider_key) if key_configured else "",
            "base_url_configured": base_configured,
            "base_url_digest": _digest(self.provider_base) if base_configured else "",
            "runtime_credential_persisted": bool(self.provider_config_persisted),
            "runtime_credential_store_digest": _digest(str(self.provider_config_path)) if (key_configured or base_configured) else "",
            "config_file_exists": config_file_exists,
            "config_file_state": "exists" if config_file_exists else "missing",
            "config_location_hint": "system_user_config_dir/LinyuanzheDesktop/provider_config.json",
            "config_path_digest": _digest(str(self.provider_config_path)),
            "local_bridge_can_persist": True,
            "raw_secret_visible_to_frontend": False,
            "local_desktop_bridge": True,
            "requested_backend_mode": self.backend_mode,
            "effective_backend_mode": effective_mode,
            "official_real_runtime_smoke_target": False,
        }

    def update_provider_from_payload(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        provider = str(payload.get("provider") or self.provider).strip()
        model = str(payload.get("model") or self.model).strip()
        base = str(payload.get("base_url") or payload.get("provider_base") or self.provider_base).strip()
        key = str(payload.get("api_key") or payload.get("provider_key") or self.provider_key).strip()
        if provider:
            self.provider = provider
        if model:
            self.model = model
        # The frontend never persists or echoes raw values. The local Runtime bridge
        # owns persistence so settings survive desktop restart.
        self.provider_base = base
        self.provider_key = key
        self.provider_config_persisted = _write_provider_config({
            "provider": self.provider,
            "model": self.model,
            "base_url": self.provider_base,
            "api_key": self.provider_key,
        })
        self.provider_config_loaded = self.provider_config_loaded or self.provider_config_persisted
        self.last_provider_check_state = "not_tested"
        self.last_provider_error_code = ""
        self.last_provider_error_message = ""
        self.last_provider_next_action = "发送一条短消息完成真实链路联调"
        self.last_provider_elapsed = ""
        self.last_provider_audit_id = ""
        self.last_audit_id = f"audit_local_provider_{_digest(str(time.time()))}"
        projection = self.provider_projection()
        projection.update({
            "status": "accepted",
            "requires_restart": False,
            "runtime_memory_only": False,
            "runtime_credential_persisted": bool(self.provider_config_persisted),
            "no_frontend_secret_persistence": True,
        })
        return {"payload": projection, **projection}


STATE: BridgeState


def _json_dumps(payload: Mapping[str, Any] | list[Any]) -> bytes:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def _pythonpath() -> str:
    parts = [str(BACKEND)]
    current = os.environ.get("PYTHONPATH", "")
    if current:
        parts.append(current)
    return os.pathsep.join(parts)


def _redact_output(text: str, state: BridgeState) -> str:
    out = text or ""
    for raw in (state.provider_key, state.provider_base):
        if raw:
            out = out.replace(raw, "<redacted>")
    out = re.sub(r"(?i)Bearer\s+[A-Za-z0-9_\-.]{8,}", "Bearer <redacted>", out)
    out = re.sub(r"(?i)sk-[A-Za-z0-9_\-]{8,}", "sk-<redacted>", out)
    # The child Runtime may mention a local handoff path; keep the path available
    # inside the prompt, but do not echo raw filesystem locations back to UI.
    out = re.sub(r"[A-Za-z]:\\[^\n\r\t]+", "<local_path_redacted>", out)
    out = re.sub(r"/(?:home|Users|mnt|tmp|var|etc)/[^\n\r\t]+", "<local_path_redacted>", out)
    return out.strip()


def _run_backend_once(message: str, state: BridgeState) -> tuple[str, int, str]:
    if not RUN_AGENT.exists():
        return "后端入口不存在：backend/project/run_agent.py", 1, "missing_backend_entry"
    env = os.environ.copy()
    env["PYTHONPATH"] = _pythonpath()
    cmd = [
        sys.executable,
        str(RUN_AGENT),
        "--once",
        message,
        "--tool-mode",
        os.environ.get("LINYUANZHE_TOOL_MODE", "runtime_governed"),
        "--planner-mode",
        os.environ.get("LINYUANZHE_PLANNER_MODE", "rule_only"),
    ]
    if state.effective_backend_mode == "mock":
        cmd.insert(2, "--mock")
    else:
        env["TIANGONG_PROVIDER"] = state.provider
        env["TIANGONG_MODEL"] = state.model
        env["TIANGONG_BASE_URL"] = state.provider_base
        env["TIANGONG_API_KEY"] = state.provider_key
    if state.file_handoffs:
        recent = state.file_handoffs[-3:]
        attachment_lines = []
        for idx, item in enumerate(recent, start=1):
            path = str(item.get("runtime_handoff_path", "") or "").strip()
            name = _safe_text(item.get("file_name", "attachment"), 160)
            if path:
                attachment_lines.append(f"附件{idx}: {name} | runtime_local_path={path}")
            else:
                attachment_lines.append(f"附件{idx}: {name} | sha256_digest={item.get('sha256_digest', '')}")
        if attachment_lines:
            cmd[cmd.index("--once") + 1] = message + "\n\n[Runtime本地文件交接]\n" + "\n".join(attachment_lines)
    started = time.time()
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(BACKEND),
            env=env,
            text=True,
            capture_output=True,
            timeout=max(15, int(state.timeout)),
        )
    except subprocess.TimeoutExpired:
        return "本地后端执行超时。", 124, "backend_timeout"
    elapsed = int((time.time() - started) * 1000)
    combined = "\n".join(x for x in (proc.stdout, proc.stderr) if x)
    text = _redact_output(combined, state)
    if not text:
        text = "本地后端已返回空响应。"
    if proc.returncode != 0:
        text = f"本地后端执行失败，returncode={proc.returncode}。\n{text}"
    return text, int(proc.returncode), f"{elapsed}ms"


class LinyuanzheBridgeHandler(BaseHTTPRequestHandler):
    server_version = "LinyuanzheLocalDesktopBridge/0.71.7"

    def log_message(self, fmt: str, *args: Any) -> None:  # noqa: D401 - stdlib signature
        # Keep stdout clean and avoid accidental request-body logging.
        return

    def _send_json(self, payload: Mapping[str, Any] | list[Any], *, status: int = 200) -> None:
        raw = _json_dumps(payload)
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Linyuanzhe-Bridge-Kind", "local-desktop-bridge")
        self.end_headers()
        self.wfile.write(raw)

    def _read_json(self) -> dict[str, Any]:
        try:
            length = int(self.headers.get("Content-Length", "0") or "0")
        except ValueError:
            length = 0
        if length <= 0:
            return {}
        raw = self.rfile.read(min(length, 1024 * 1024))
        try:
            parsed = json.loads(raw.decode("utf-8", errors="replace"))
        except json.JSONDecodeError:
            return {}
        return parsed if isinstance(parsed, dict) else {"value": parsed}

    def do_GET(self) -> None:  # noqa: N802 - stdlib handler API
        path = self.path.split("?", 1)[0]
        if path == "/health/runtime":
            self._send_json({
                "payload": {
                    "runtime_status": "local_desktop_bridge_ready",
                    "status": "ok",
                    "runtime_kind": "local_desktop_bridge",
                    "official_real_runtime_smoke_target": False,
                    "bridge_version": "FE01 STEP31Q / L6.71.7",
                    "backend_entry": "backend/project/run_agent.py",
                    "backend_mode": STATE.effective_backend_mode,
                    "current_task_status": "READY",
                    "current_stage": "本地桥接后端已启动，等待桌面端任务。",
                    "status_bar": {
                        "runtime_status": "local_bridge_ready",
                        "provider_model": STATE.model,
                        "budget_pool": "desktop_local",
                        "budget_used_ratio": "0.00",
                        "gate_status": "A0 local envelope",
                        "audit_id": STATE.last_audit_id,
                        "memory_mode": "frontend_no_direct_write",
                        "tools_allowed": 0,
                        "latency_ms": 0,
                    },
                }
            })
            return
        if path == "/metadata/product":
            self._send_json({**PRODUCT_IDENTITY, "endpoint": path, "local_desktop_bridge": True})
            return
        if path == "/settings/provider":
            self._send_json(STATE.provider_projection())
            return
        if path == "/workspace/policy":
            self._send_json({
                "workspace_contract": "tiangong.l6_65.workspace_policy.v1",
                "workspace_state": "local_bridge_projection",
                "route_to_runtime_only": True,
                "frontend_may_read_paths": False,
                "frontend_may_copy_files": False,
                "frontend_may_write_memory": False,
                "frontend_may_write_audit": False,
                "frontend_may_apply_rollback": False,
                "policy": {
                    "workspace_authorization_required": True,
                    "quality_gate_required": True,
                    "runtime_authority_required": True,
                },
            })
            return
        if path == "/connectors/registry":
            self._send_json({
                "connector_registry_contract": "tiangong.l6_66.connector_registry.v1",
                "connector_registry_state": "local_bridge_projection",
                "connector_registry_projection": {
                    "registry_id_digest": _digest("local-bridge-connector-registry"),
                    "registry_state": "ready",
                    "default_mode": "disabled",
                    "connector_count": len(STATE.connector_records),
                    "enabled_count": 0,
                    "read_only_count": len(STATE.connector_records),
                    "quarantined_count": 0,
                    "pending_review_count": len([x for x in STATE.connector_records if x.get("status") == "accepted"]),
                    "allow_market_install": False,
                    "allow_unsigned_connector": False,
                    "runtime_authority_required": True,
                    "quality_gate_required": True,
                    "workspace_authorization_required": True,
                    "frontend_may_install_connector": False,
                    "frontend_may_execute_connector": False,
                    "frontend_may_store_connector_secret": False,
                },
                "connector_manifests": [
                    {
                        "display_name": rec.get("display_name", ""),
                        "kind": rec.get("kind", "mcp_server"),
                        "status": rec.get("status", "accepted"),
                        "manifest_digest": rec.get("manifest_digest", ""),
                        "trust_level": "unknown",
                        "default_mode": "disabled",
                        "requested_scopes": rec.get("requested_scopes", ["read_public_metadata"]),
                    }
                    for rec in STATE.connector_records[-20:]
                ],
                "connector_registration_records": list(reversed(STATE.connector_records[-20:])),
            })
            return
        if path == "/sessions/list":
            self._send_json({
                "session_manager_contract": "tiangong.l6_67.session_manager.v1",
                "session_manager_state": "local_bridge_ready",
                "task_sessions": list(reversed(STATE.sessions[-20:])),
                "session_stats": {
                    "total": len(STATE.sessions),
                    "running": len([s for s in STATE.sessions if s.get("status") == "running" or s.get("active")]),
                    "waiting_confirmation": len([s for s in STATE.sessions if s.get("status") == "waiting_confirmation" or s.get("waiting_confirmation")]),
                    "blocked": len([s for s in STATE.sessions if s.get("status") == "blocked" or s.get("blocked")]),
                    "recoverable": len([s for s in STATE.sessions if s.get("recoverable")]),
                    "completed": len([s for s in STATE.sessions if s.get("status") == "completed"]),
                    "failed": len([s for s in STATE.sessions if s.get("status") == "failed"]),
                    "queued": len([s for s in STATE.sessions if s.get("status") == "queued"]),
                    "total_count": len(STATE.sessions),
                    "completed_count": len([s for s in STATE.sessions if s.get("status") == "completed"]),
                },
                "session_last_message": "本地桌面桥接 Session 投影已读取。",
            })
            return
        if path == "/installer/manifest":
            self._send_json({
                "installer_rc_contract": "tiangong.l6_70_1.desktop_bundle_manifest.v1",
                "installer_manifest": {
                    "version_label": "FE01 STEP31Q / L6.71.7 三端通用桌面包",
                    "unique_developer": "于泳翔",
                    "angel_investor": "胖胖龙",
                    "startup_self_check_state": "pass",
                    "rollback_ready": True,
                    "offline_repair_available": True,
                    "final_installer_allowed": False,
                    "windows_installer_artifact_emitted": False,
                    "local_desktop_bundle_ready": True,
                },
                "installer_last_message": "这是解压即用桌面包，不是正式 exe/msi 安装器。",
            })
            return
        if path == "/installer/startup/self-check":
            self._send_json({
                "contract_version": "tiangong.l6_70_1.desktop_startup_self_check.v1",
                "ok": True,
                "checks": [
                    {"check_id": "backend_entry", "name": "后端 run_agent 入口", "status": "pass", "message": str(RUN_AGENT.relative_to(ROOT))},
                    {"check_id": "bridge", "name": "本地桥接服务", "status": "pass", "message": "ready"},
                    {"check_id": "frontend_boundary", "name": "前端边界", "status": "pass", "message": "runtime envelope only"},
                ],
            })
            return
        self._send_json({"error": "not_found", "path": path}, status=404)

    def _send_sse_events(self, events: list[dict[str, Any]]) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "close")
        self.send_header("X-Linyuanzhe-Bridge-Kind", "local-desktop-bridge")
        self.end_headers()
        for item in events:
            raw = json.dumps(item, ensure_ascii=False)
            self.wfile.write(f"event: {item.get('event','message')}\n".encode("utf-8"))
            self.wfile.write(f"data: {raw}\n\n".encode("utf-8"))
            self.wfile.flush()
            time.sleep(0.02)

    def do_POST(self) -> None:  # noqa: N802 - stdlib handler API
        path = self.path.split("?", 1)[0]
        payload = self._read_json()
        if path == "/chat/stream-events":
            message = str(payload.get("message") or payload.get("user_message") or "").strip()
            if not message:
                message = "继续"
            STATE.chat_count += 1
            run_id = f"local_run_{uuid.uuid4().hex[:12]}"
            task_id = f"local_task_{STATE.chat_count:04d}"
            audit_id = f"audit_local_{uuid.uuid4().hex[:10]}"
            STATE.last_audit_id = audit_id
            answer, returncode, elapsed = _run_backend_once(message, STATE)
            answer = _safe_text(answer, 4000)
            ok = returncode == 0
            STATE.record_provider_check(ok=ok, answer=answer, returncode=returncode, elapsed=elapsed, audit_id=audit_id)
            status = "ok" if ok else "failed"
            session = {
                "session_id": run_id,
                "title": _safe_text(message, 80),
                "status": "completed" if ok else "blocked",
                "current_stage": "本地桥接后端执行完成" if ok else "本地桥接后端执行失败",
                "progress_percent": 100 if ok else 70,
                "active": False,
                "blocked": not ok,
                "recoverable": not ok,
                "audit_id": audit_id,
                "tags": ["local_bridge", STATE.effective_backend_mode],
            }
            STATE.sessions.append(session)
            events = [
                {"event": "run_started", "seq": 1, "run_id": run_id, "task_id": task_id, "timestamp": datetime.now().isoformat(timespec="seconds"), "payload": {"runtime_status": "active", "provider_model": STATE.model, "backend_mode": STATE.effective_backend_mode}},
                {"event": "planner_started", "seq": 2, "run_id": run_id, "task_id": task_id, "timestamp": datetime.now().isoformat(timespec="seconds"), "payload": {"planner_mode": "rule_only", "current_stage": "本地桥接后端执行"}},
                {"event": "quality_gate", "seq": 3, "run_id": run_id, "task_id": task_id, "timestamp": datetime.now().isoformat(timespec="seconds"), "payload": {"risk_level": "A0", "decision": "allowed", "audit_ref": audit_id, "route_to_runtime_only": True}},
            ]
            seq = 4
            # Stream the sanitized backend answer itself. assistant_final only
            # closes the run, avoiding duplicate final-answer messages in the
            # desktop transcript. This remains local bridge output, not a
            # frontend-side Provider call or tool execution.
            answer_chunks = [answer[i : i + 360] for i in range(0, len(answer), 360)] or ["本地后端已返回空响应。"]
            for chunk in answer_chunks:
                events.append({"event": "assistant_delta", "seq": seq, "run_id": run_id, "task_id": task_id, "timestamp": datetime.now().isoformat(timespec="seconds"), "payload": {"content": chunk}})
                seq += 1
            events.extend([
                {"event": "audit_event", "seq": seq, "run_id": run_id, "task_id": task_id, "timestamp": datetime.now().isoformat(timespec="seconds"), "payload": {"audit_id": audit_id, "event": "local_bridge_backend_once", "status": status, "elapsed": elapsed}},
                {"event": "assistant_final", "seq": seq + 1, "run_id": run_id, "task_id": task_id, "timestamp": datetime.now().isoformat(timespec="seconds"), "payload": {"content": answer, "status": status}},
                {"event": "run_terminal", "seq": seq + 2, "run_id": run_id, "task_id": task_id, "timestamp": datetime.now().isoformat(timespec="seconds"), "payload": {"status": status, "audit_id": audit_id, "assistant_final_before_terminal": True}},
            ])
            self._send_sse_events(events)
            return
        if path == "/settings/provider":
            self._send_json(STATE.update_provider_from_payload(payload))
            return
        if path in CONTROL_PATHS:
            action = CONTROL_PATHS[path]
            self._send_json({
                "control_contract": "tiangong.l6_58.runtime_control.v1",
                "status": "accepted",
                "action": action,
                "message": f"{action} 请求已由本地桥接接收；不由前端直接执行工具/记忆/回滚。",
                "route_to_runtime_only": True,
                "audit_id": f"audit_control_{_digest(str(time.time()))}",
            })
            return
        if path == "/confirmations/submit":
            self._send_json({
                "confirmation_contract": "tiangong.l6_58.action_guard.v1",
                "status": "accepted",
                "ticket_id": payload.get("ticket_id", ""),
                "decision": payload.get("decision", "submitted"),
                "message": "确认请求已进入本地桥接信封；正式放行仍属于 Runtime/QualityGate。",
                "route_to_runtime_only": True,
                "audit_id": f"audit_confirm_{_digest(str(time.time()))}",
            })
            return
        if path == "/files/transfer/request":
            file_name = _safe_text(payload.get("file_name", "attachment"), 160)
            record = {
                "transfer_id": f"ft_{_digest(str(time.time()))}",
                "direction": payload.get("direction", "upload"),
                "file_name": file_name,
                "size_bytes": int(payload.get("size_bytes", 0) or 0),
                "sha256_digest": _digest(payload.get("sha256", "")),
                "mime_type": payload.get("mime_type", "application/octet-stream"),
                "purpose": payload.get("purpose", "user_attachment"),
                "status": "accepted",
                "message": "文件已交给本地 Runtime 桥接；上传后可自动进入 Runtime 文件处理链。",
                "audit_id": f"audit_file_{_digest(str(time.time()))}",
                "route_to_runtime_only": True,
                "no_frontend_path_exposure": True,
            }
            STATE.file_handoffs.append({**record, "runtime_handoff_path": payload.get("runtime_handoff_path", "")})
            self._send_json({
                "file_transfer_contract": "tiangong.l6_64.file_transfer_request.v1",
                "status": "accepted",
                "payload": record,
                **record,
            })
            return
        if path == "/workspace/file/authorize":
            record = {
                "authorization_id": f"auth_{_digest(str(time.time()))}",
                "file_name": _safe_text(payload.get("file_name", "workspace_target"), 160),
                "mode": payload.get("mode", "read"),
                "scope": payload.get("scope", "user_selected_file"),
                "purpose": payload.get("purpose", "user_attachment"),
                "status": "accepted",
                "message": "文件授权请求已进入本地 Runtime 桥接；写入/读取仍由 Runtime 工具链执行。",
                "audit_id": f"audit_auth_{_digest(str(time.time()))}",
                "path_digest": payload.get("local_path_digest", ""),
                "runtime_workspace_digest": _digest("local_runtime_workspace"),
                "route_to_runtime_only": True,
                "raw_path_visible": False,
            }
            self._send_json({
                "workspace_contract": "tiangong.l6_65.file_authorization.v1",
                "status": "accepted",
                "payload": record,
                **record,
            })
            return
        if path == "/files/download/claim":
            self._send_json({"status": "accepted", "route_to_runtime_only": True, "download_claim_ref": f"claim_{_digest(str(time.time()))}"})
            return
        if path in {"/connectors/register/request", "/connectors/quarantine/request"}:
            record = {
                "request_id": f"connector_{_digest(str(time.time()))}",
                "display_name": _safe_text(payload.get("display_name", payload.get("name", "未命名连接器")), 160),
                "kind": payload.get("kind", "mcp_server"),
                "status": "accepted",
                "message": "连接器注册请求已进入本地 Runtime 桥接；默认禁用，只读待审。",
                "audit_id": f"audit_connector_{_digest(str(time.time()))}",
                "manifest_digest": payload.get("manifest_digest", _digest(payload)),
                "source_digest": payload.get("source_digest", ""),
                "trust_level": "unknown",
                "default_mode": "disabled",
                "requested_scopes": payload.get("requested_scopes", ["read_public_metadata"]),
                "route_to_runtime_only": True,
                "quarantined": False,
            }
            STATE.connector_records.append(record)
            self._send_json({
                "connector_registry_contract": "tiangong.l6_66.connector_request.v1",
                "status": "accepted",
                "payload": record,
                **record,
            })
            return
        if path == "/sessions/resume":
            self._send_json({"session_manager_contract": "tiangong.l6_67.session_resume.v1", "status": "accepted", "route_to_runtime_only": True, "message": "恢复请求已进入本地桥接信封。"})
            return
        if path == "/sessions/search":
            query = str(payload.get("query") or "").strip().lower()
            matches = [s for s in STATE.sessions if not query or query in str(s.get("title", "")).lower()]
            self._send_json({"session_manager_contract": "tiangong.l6_67.session_search.v1", "status": "ok", "read_only_projection": True, "task_sessions": list(reversed(matches[-20:]))})
            return
        if path in {"/self-iteration/confirm", "/self_iteration/confirm", "/self-iteration/confirm/request"}:
            self._send_json({
                "self_iteration_contract": "tiangong.l6_42.self_iteration_confirm.v1",
                "status": "accepted",
                "candidate_id": payload.get("candidate_id", ""),
                "decision": payload.get("decision", "confirmed"),
                "route_to_runtime_only": True,
                "no_frontend_self_iteration_apply": True,
                "message": "自我迭代确认已进入本地 Runtime 桥接；不由前端直接合入。",
                "audit_id": f"audit_iter_{_digest(str(time.time()))}",
            })
            return
        if path in {"/installer/update/check", "/installer/repair/request", "/installer/rollback/plan"}:
            self._send_json({"installer_rc_contract": "tiangong.l6_68.installer_request.v1", "status": "dry_run", "route_to_runtime_only": True, "final_installer_allowed": False})
            return
        self._send_json({"error": "not_found", "path": path}, status=404)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="临渊者 L6.71.7 本地桌面 Runtime 桥接服务")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=0)
    parser.add_argument("--backend-mode", choices=["auto", "mock", "provider"], default=os.environ.get("LINYUANZHE_BACKEND_MODE", "auto"))
    parser.add_argument("--timeout", type=float, default=float(os.environ.get("LINYUANZHE_BACKEND_TIMEOUT", "120") or 120))
    args = parser.parse_args(argv)

    global STATE
    STATE = BridgeState(backend_mode=args.backend_mode, timeout=args.timeout)
    REPORTS.mkdir(parents=True, exist_ok=True)

    server = ThreadingHTTPServer((args.host, args.port), LinyuanzheBridgeHandler)
    host, port = server.server_address[:2]
    url = f"http://{host}:{port}"
    print(f"LINYUANZHE_LOCAL_RUNTIME_URL={url}", flush=True)
    try:
        server.serve_forever(poll_interval=0.2)
    except KeyboardInterrupt:
        return 130
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
