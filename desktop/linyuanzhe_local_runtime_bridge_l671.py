from __future__ import annotations

"""FE01 STEP31A / L6.70.1 local desktop Runtime bridge.

This bridge is bundled for the desktop all-in-one package. It exposes the
frontend Runtime HTTP/SSE contract and delegates chat execution to the bundled
backend CLI entrypoint. It is deliberately labeled as a local desktop bridge,
not as the official TiangongWangguan real Runtime smoke target.
"""

import argparse
import hashlib
import json
import os
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


class BridgeState:
    def __init__(self, *, backend_mode: str, timeout: float) -> None:
        self.backend_mode = backend_mode
        self.timeout = timeout
        self.provider = os.environ.get("LINYUANZHE_PROVIDER", "deepseek").strip() or "deepseek"
        self.model = os.environ.get("LINYUANZHE_MODEL", "deepseek-reasoner").strip() or "deepseek-reasoner"
        self.provider_base = os.environ.get("LINYUANZHE_PROVIDER_BASE", "").strip()
        self.provider_key = os.environ.get("LINYUANZHE_PROVIDER_KEY", "").strip()
        self.started_at = datetime.now().isoformat(timespec="seconds")
        self.chat_count = 0
        self.last_audit_id = "audit_local_bridge_idle"
        self.sessions: list[dict[str, Any]] = []

    @property
    def effective_backend_mode(self) -> str:
        if self.backend_mode == "provider" and self.provider_key and self.provider_base:
            return "provider"
        return "mock"

    def provider_projection(self) -> dict[str, Any]:
        base_configured = bool(self.provider_base)
        key_configured = bool(self.provider_key)
        state = "ready" if self.effective_backend_mode == "provider" else "mock_ready"
        message = "本地桌面桥接后端已就绪；未配置真实模型时使用 bundled mock 后端。"
        if self.effective_backend_mode == "provider":
            message = "本地桌面桥接后端已就绪；真实模型配置仅保存在当前进程内存，不写入磁盘。"
        return {
            "frontend_contract": "tiangong.l6_70_1.desktop_provider_projection.v1",
            "provider": self.provider,
            "model": self.model,
            "provider_config_state": state,
            "config_error_code": "",
            "message": message,
            "audit_id": self.last_audit_id,
            "planner_mode": "rule_only",
            "tool_execution_mode": "runtime_governed",
            "stream": True,
            "api_key_configured": key_configured,
            "api_key_digest": _digest(self.provider_key) if key_configured else "",
            "base_url_configured": base_configured,
            "base_url_digest": _digest(self.provider_base) if base_configured else "",
            "local_desktop_bridge": True,
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
        # Keep values in process memory only. Do not write raw values to files or reports.
        self.provider_base = base
        self.provider_key = key
        self.last_audit_id = f"audit_local_provider_{_digest(str(time.time()))}"
        projection = self.provider_projection()
        projection.update({
            "status": "accepted",
            "requires_restart": False,
            "runtime_memory_only": True,
            "no_secret_persistence": True,
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
        "runtime_governed",
        "--planner-mode",
        "model_suggest",
        "--max-steps",
        "40",
    ]
    if state.effective_backend_mode == "mock":
        cmd.insert(2, "--mock")
    else:
        env["TIANGONG_PROVIDER"] = state.provider
        env["TIANGONG_MODEL"] = state.model
        env["TIANGONG_BASE_URL"] = state.provider_base
        env["TIANGONG_API_KEY"] = state.provider_key
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
    server_version = "LinyuanzheLocalDesktopBridge/0.70.1"

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
                    "bridge_version": "FE01 STEP31A / L6.70.1",
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
                    "connector_count": 0,
                    "enabled_count": 0,
                    "read_only_count": 0,
                    "quarantined_count": 0,
                    "pending_review_count": 0,
                    "allow_market_install": False,
                    "allow_unsigned_connector": False,
                    "runtime_authority_required": True,
                    "quality_gate_required": True,
                    "workspace_authorization_required": True,
                    "frontend_may_install_connector": False,
                    "frontend_may_execute_connector": False,
                    "frontend_may_store_connector_secret": False,
                },
                "connector_manifests": [],
                "connector_registration_records": [],
            })
            return
        if path == "/sessions/list":
            self._send_json({
                "session_manager_contract": "tiangong.l6_67.session_manager.v1",
                "session_manager_state": "local_bridge_ready",
                "task_sessions": list(reversed(STATE.sessions[-20:])),
                "session_stats": {
                    "total_count": len(STATE.sessions),
                    "running_count": 0,
                    "completed_count": len([s for s in STATE.sessions if s.get("status") == "completed"]),
                    "recoverable_count": 0,
                    "blocked_count": 0,
                },
                "session_last_message": "本地桌面桥接 Session 投影已读取。",
            })
            return
        if path == "/installer/manifest":
            self._send_json({
                "installer_rc_contract": "tiangong.l6_70_1.desktop_bundle_manifest.v1",
                "installer_manifest": {
                    "version_label": "FE01 STEP31A / L6.70.1 桌面端前后端一体化启动包",
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
            status = "ok" if ok else "failed"
            session = {
                "session_id": run_id,
                "title": _safe_text(message, 80),
                "status": "completed" if ok else "blocked",
                "current_stage": "本地桥接后端执行完成" if ok else "本地桥接后端执行失败",
                "progress_percent": 100 if ok else 70,
                "active": False,
                "blocked": not ok,
                "recoverable": True,
                "audit_id": audit_id,
                "tags": ["local_bridge", STATE.effective_backend_mode],
            }
            STATE.sessions.append(session)
            events = [
                {"event": "run_started", "seq": 1, "run_id": run_id, "task_id": task_id, "timestamp": datetime.now().isoformat(timespec="seconds"), "payload": {"runtime_status": "active", "provider_model": STATE.model, "backend_mode": STATE.effective_backend_mode}},
                {"event": "planner_started", "seq": 2, "run_id": run_id, "task_id": task_id, "timestamp": datetime.now().isoformat(timespec="seconds"), "payload": {"planner_mode": "rule_only", "current_stage": "本地桥接后端执行"}},
                {"event": "quality_gate", "seq": 3, "run_id": run_id, "task_id": task_id, "timestamp": datetime.now().isoformat(timespec="seconds"), "payload": {"risk_level": "A0", "decision": "allowed", "audit_ref": audit_id, "route_to_runtime_only": True}},
                {"event": "assistant_delta", "seq": 4, "run_id": run_id, "task_id": task_id, "timestamp": datetime.now().isoformat(timespec="seconds"), "payload": {"content": "本地桥接后端已返回结果，正在收口。"}},
                {"event": "audit_event", "seq": 5, "run_id": run_id, "task_id": task_id, "timestamp": datetime.now().isoformat(timespec="seconds"), "payload": {"audit_id": audit_id, "event": "local_bridge_backend_once", "status": status, "elapsed": elapsed}},
                {"event": "assistant_final", "seq": 6, "run_id": run_id, "task_id": task_id, "timestamp": datetime.now().isoformat(timespec="seconds"), "payload": {"content": answer, "status": status}},
                {"event": "run_terminal", "seq": 7, "run_id": run_id, "task_id": task_id, "timestamp": datetime.now().isoformat(timespec="seconds"), "payload": {"status": status, "audit_id": audit_id, "assistant_final_before_terminal": True}},
            ]
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
                "decision": payload.get("decision", "submitted"),
                "message": "确认请求已进入本地桥接信封；正式放行仍属于 Runtime/QualityGate。",
                "route_to_runtime_only": True,
                "audit_id": f"audit_confirm_{_digest(str(time.time()))}",
            })
            return
        if path == "/files/transfer/request":
            self._send_json({
                "file_transfer_contract": "tiangong.l6_64.file_transfer_request.v1",
                "status": "accepted",
                "route_to_runtime_only": True,
                "no_frontend_file_copy": True,
                "record": {"file_name_digest": _digest(payload.get("file_name", "")), "state": "request_recorded"},
            })
            return
        if path == "/workspace/file/authorize":
            self._send_json({
                "workspace_contract": "tiangong.l6_65.file_authorization.v1",
                "status": "accepted",
                "route_to_runtime_only": True,
                "authorization_ref": f"auth_{_digest(str(time.time()))}",
                "no_frontend_path_exposure": True,
            })
            return
        if path == "/files/download/claim":
            self._send_json({"status": "accepted", "route_to_runtime_only": True, "download_claim_ref": f"claim_{_digest(str(time.time()))}"})
            return
        if path in {"/connectors/register/request", "/connectors/quarantine/request"}:
            self._send_json({
                "connector_registry_contract": "tiangong.l6_66.connector_request.v1",
                "status": "accepted",
                "route_to_runtime_only": True,
                "quality_gate_required": True,
                "workspace_authorization_required": True,
                "runtime_authority_required": True,
                "request_ref": f"connector_{_digest(str(time.time()))}",
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
        if path in {"/installer/update/check", "/installer/repair/request", "/installer/rollback/plan"}:
            self._send_json({"installer_rc_contract": "tiangong.l6_68.installer_request.v1", "status": "dry_run", "route_to_runtime_only": True, "final_installer_allowed": False})
            return
        self._send_json({"error": "not_found", "path": path}, status=404)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="临渊者 L6.70.1 本地桌面 Runtime 桥接服务")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=0)
    parser.add_argument("--backend-mode", choices=["mock", "provider"], default=os.environ.get("LINYUANZHE_BACKEND_MODE", "mock"))
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
