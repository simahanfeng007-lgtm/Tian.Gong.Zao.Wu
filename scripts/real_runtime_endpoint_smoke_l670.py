from __future__ import annotations

"""FE01 STEP31 / L6.70 real Runtime endpoint smoke.

This script is intentionally non-mutating by default. It proves read/projection
endpoints against a real Runtime URL and statically validates that frontend
control / file / workspace / connector / session / confirmation operations remain
Runtime-envelope-only. It never prints Runtime URL or provider secrets.
"""

import argparse
import hashlib
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
BACKEND = ROOT / "backend" / "project"
FRONTEND_PARENT = ROOT / "frontend"

# Make bundled frontend contracts importable when called directly.
import sys
for _p in (str(BACKEND), str(FRONTEND_PARENT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from linyuanzhe_frontend.contracts.action_guard import CONFIRMATION_ENDPOINT, ConfirmationRequestEnvelope
from linyuanzhe_frontend.contracts.connectors import CONNECTOR_REGISTER_ENDPOINT, CONNECTOR_REGISTRY_ENDPOINT, ConnectorRegistrationRequest
from linyuanzhe_frontend.contracts.file_transfer import FILE_TRANSFER_ENDPOINT, FileTransferRequest
from linyuanzhe_frontend.contracts.installer_rc import INSTALLER_MANIFEST_ENDPOINT
from linyuanzhe_frontend.contracts.runtime_controls import TASK_INTERRUPT_ENDPOINT, TASK_RESET_ENDPOINT, TASK_STOP_ENDPOINT, RuntimeControlRequest
from linyuanzhe_frontend.contracts.session_manager import SESSION_LIST_ENDPOINT, SESSION_RESUME_ENDPOINT, SESSION_SEARCH_ENDPOINT, SessionResumeRequest, SessionSearchRequest
from linyuanzhe_frontend.contracts.sse_events import HEALTH_ENDPOINT, PRODUCT_METADATA_ENDPOINT, PROVIDER_SETTINGS_ENDPOINT
from linyuanzhe_frontend.contracts.workspace import FILE_AUTHORIZATION_ENDPOINT, WORKSPACE_POLICY_ENDPOINT, FileAuthorizationRequest

CONTRACT_VERSION = "tiangong.l6_70.real_runtime_endpoint_smoke.v1"
MISSING_RUNTIME_BLOCKER = "real Runtime instance smoke not executed"
FORBIDDEN_RESPONSE_KEYS = {"api_key", "authorization", "bearer", "token", "secret", "base_url", "password", "private_key"}
FORBIDDEN_TEXT_MARKERS = ("sk-", "Bearer ", "credential_l658_secret", "provider-write-l658", "api_key=")

READ_ENDPOINTS: tuple[tuple[str, str], ...] = (
    ("core.health", HEALTH_ENDPOINT),
    ("core.product_identity", PRODUCT_METADATA_ENDPOINT),
    ("core.provider_settings_readonly", PROVIDER_SETTINGS_ENDPOINT),
    ("workspace.policy", WORKSPACE_POLICY_ENDPOINT),
    ("connectors.registry", CONNECTOR_REGISTRY_ENDPOINT),
    ("sessions.list", SESSION_LIST_ENDPOINT),
    ("installer.manifest", INSTALLER_MANIFEST_ENDPOINT),
)

REQUEST_ENDPOINTS: tuple[tuple[str, str], ...] = (
    ("chat.stream_events", "/chat/stream-events"),
    ("confirmations.submit", CONFIRMATION_ENDPOINT),
    ("control.stop", TASK_STOP_ENDPOINT),
    ("control.reset", TASK_RESET_ENDPOINT),
    ("control.interrupt", TASK_INTERRUPT_ENDPOINT),
    ("files.transfer", FILE_TRANSFER_ENDPOINT),
    ("workspace.file_authorize", FILE_AUTHORIZATION_ENDPOINT),
    ("connectors.register", CONNECTOR_REGISTER_ENDPOINT),
    ("sessions.resume", SESSION_RESUME_ENDPOINT),
    ("sessions.search", SESSION_SEARCH_ENDPOINT),
)

PROJECTION_POLICIES_WITHOUT_DIRECT_ENDPOINT = (
    "observability.trace_projection_from_sse",
    "hookbus.local_deterministic_guard_projection",
)


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="ignore")).hexdigest()[:16]


def _clean_url(value: str) -> str:
    cleaned = str(value or "").strip().rstrip("/")
    if cleaned and not urllib.parse.urlparse(cleaned).scheme:
        cleaned = "http://" + cleaned
    return cleaned


def _redact(text: Any, runtime_url: str = "", limit: int = 1200) -> str:
    s = str(text or "")
    if runtime_url:
        s = s.replace(runtime_url, "<runtime_url_redacted>")
    s = re.sub(r"https?://[^\s\"'<>]+", "<url_redacted>", s)
    s = re.sub(r"(?i)Bearer\s+[A-Za-z0-9_\-.]{8,}", "Bearer <redacted>", s)
    s = re.sub(r"(?i)sk-[A-Za-z0-9_\-]{8,}", "sk-<redacted>", s)
    return s[-limit:]


def _forbidden_keys(value: Any) -> list[str]:
    hits: set[str] = set()

    def walk(x: Any) -> None:
        if isinstance(x, Mapping):
            for k, v in x.items():
                key = str(k).lower()
                if key in FORBIDDEN_RESPONSE_KEYS:
                    hits.add(key)
                walk(v)
        elif isinstance(x, list):
            for item in x[:100]:
                walk(item)

    walk(value)
    return sorted(hits)


def _json_keys(value: Any) -> list[str]:
    if isinstance(value, Mapping):
        return sorted(str(k) for k in value.keys())[:80]
    if isinstance(value, list):
        return [f"list[{len(value)}]"]
    return []


def _get_json(runtime_url: str, path: str, timeout: float) -> dict[str, Any]:
    started = time.time()
    try:
        req = urllib.request.Request(
            runtime_url + path,
            method="GET",
            headers={
                "Accept": "application/json",
                "X-Tiangong-Frontend-Contract": "L6.70",
                "X-Linyuanzhe-Real-Runtime-Smoke": "read-only",
            },
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read(32768)
            status = int(getattr(resp, "status", 200))
            content_type = resp.headers.get("Content-Type", "")
        parsed: Any = {}
        if raw:
            try:
                parsed = json.loads(raw.decode("utf-8", errors="replace"))
            except json.JSONDecodeError:
                parsed = {"non_json_body_digest": _digest(raw.decode("utf-8", errors="replace"))}
        body_text = json.dumps(parsed, ensure_ascii=False) if isinstance(parsed, (dict, list)) else str(parsed)
        forbidden_keys = _forbidden_keys(parsed)
        forbidden_markers = [m for m in FORBIDDEN_TEXT_MARKERS if m in body_text]
        return {
            "path": path,
            "method": "GET",
            "ok": bool(200 <= status < 300 and not forbidden_keys and not forbidden_markers),
            "status_code": status,
            "latency_ms": int((time.time() - started) * 1000),
            "content_type": _redact(content_type, runtime_url, 160),
            "json_keys": _json_keys(parsed),
            "forbidden_key_hits": forbidden_keys,
            "forbidden_marker_hits": ["<redacted_marker>" for _ in forbidden_markers],
        }
    except urllib.error.HTTPError as exc:
        return {
            "path": path,
            "method": "GET",
            "ok": False,
            "status_code": int(getattr(exc, "code", 0) or 0),
            "latency_ms": int((time.time() - started) * 1000),
            "error": _redact(f"HTTP {getattr(exc, 'code', 'error')}", runtime_url),
        }
    except Exception as exc:
        return {
            "path": path,
            "method": "GET",
            "ok": False,
            "status_code": 0,
            "latency_ms": int((time.time() - started) * 1000),
            "error": _redact(exc, runtime_url),
        }


def _check_payload(name: str, endpoint: str, payload: Mapping[str, Any], required_true: tuple[str, ...]) -> dict[str, Any]:
    missing_or_false = [key for key in required_true if payload.get(key) is not True]
    raw_text = json.dumps(payload, ensure_ascii=False)
    forbidden_markers = [m for m in FORBIDDEN_TEXT_MARKERS if m in raw_text]
    return {
        "name": name,
        "endpoint": endpoint,
        "ok": not missing_or_false and not forbidden_markers,
        "required_true_missing_or_false": missing_or_false,
        "forbidden_marker_hits": ["<redacted_marker>" for _ in forbidden_markers],
        "payload_keys": sorted(str(k) for k in payload.keys())[:60],
    }


def _request_envelope_checks() -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    for action, endpoint in (("stop", TASK_STOP_ENDPOINT), ("reset", TASK_RESET_ENDPOINT), ("interrupt", TASK_INTERRUPT_ENDPOINT)):
        payload = RuntimeControlRequest(action=action, run_id="run_digest_only", task_id="task_digest_only").to_payload()
        checks.append(_check_payload(action, endpoint, payload, ("no_frontend_tool_execution", "no_frontend_memory_write", "no_frontend_rollback_apply")))
    checks.append(_check_payload(
        "file_transfer",
        FILE_TRANSFER_ENDPOINT,
        FileTransferRequest(file_name="placeholder.txt", size_bytes=0, sha256="").to_payload(),
        ("route_to_runtime_only", "no_frontend_tool_execution", "no_frontend_memory_write", "no_frontend_audit_write", "no_frontend_rollback_apply", "no_frontend_path_exposure"),
    ))
    checks.append(_check_payload(
        "workspace_file_authorize",
        FILE_AUTHORIZATION_ENDPOINT,
        FileAuthorizationRequest.from_path("placeholder.txt", mode="read", scope="user_selected_file").to_payload(),
        ("route_to_runtime_only", "no_frontend_workspace_create", "no_frontend_acl_mutation", "no_frontend_file_copy", "no_frontend_memory_write", "no_frontend_audit_write", "no_frontend_rollback_apply", "no_frontend_path_exposure"),
    ))
    checks.append(_check_payload(
        "connector_register",
        CONNECTOR_REGISTER_ENDPOINT,
        ConnectorRegistrationRequest.build(display_name="dry-run connector", requested_scopes=["read_public_metadata"]).to_payload(),
        ("route_to_runtime_only", "no_frontend_connector_install", "no_frontend_connector_execute", "no_frontend_secret_storage", "no_frontend_workspace_bypass", "no_frontend_tool_execution", "no_frontend_memory_write", "no_frontend_audit_write", "no_frontend_rollback_apply", "no_raw_endpoint_display", "no_mcp_market_install", "quality_gate_required", "workspace_authorization_required", "runtime_authority_required"),
    ))
    checks.append(_check_payload(
        "session_resume",
        SESSION_RESUME_ENDPOINT,
        SessionResumeRequest(session_id_digest="session_digest_only").to_payload(),
        ("route_to_runtime_only", "no_frontend_execute", "no_frontend_tool_execution", "no_frontend_memory_write", "no_frontend_audit_write", "no_frontend_rollback_apply"),
    ))
    checks.append(_check_payload(
        "session_search",
        SESSION_SEARCH_ENDPOINT,
        SessionSearchRequest(query="dry-run").to_payload(),
        ("read_only_projection", "no_frontend_execute", "no_frontend_tool_execution", "no_frontend_memory_write", "no_frontend_audit_write", "no_frontend_rollback_apply"),
    ))
    checks.append(_check_payload(
        "confirmation_submit",
        CONFIRMATION_ENDPOINT,
        ConfirmationRequestEnvelope.build(ticket_id="ticket_digest_only", decision="request_changes").to_payload(),
        ("route_to_runtime_only", "no_frontend_execute", "no_frontend_gate_bypass", "no_frontend_audit_write", "no_frontend_rollback_apply"),
    ))
    return checks


def _write(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _blocked(runtime_url: str, out: Path) -> dict[str, Any]:
    return {
        "contract_version": CONTRACT_VERSION,
        "checked_at": datetime.now().isoformat(timespec="seconds"),
        "runtime_url_visible": "digest_only",
        "runtime_url_digest": _digest(runtime_url) if runtime_url else "",
        "real_runtime_url_present": bool(runtime_url),
        "real_runtime_executed": False,
        "read_endpoint_smoke_ok": False,
        "request_envelope_checks_ok": all(item["ok"] for item in _request_envelope_checks()),
        "request_envelope_checks": _request_envelope_checks(),
        "projection_policy_notes": list(PROJECTION_POLICIES_WITHOUT_DIRECT_ENDPOINT),
        "ready_for_combine": False,
        "merge_blockers": [MISSING_RUNTIME_BLOCKER, "LINYUANZHE_RUNTIME_URL not provided"],
        "final_installer_allowed": False,
        "windows_installer_artifact_emitted": False,
        "note": "没有真实 Runtime URL 时，本脚本只产出阻断证据；不使用 contract-server 冒充真实联调。",
        "report": str(out),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="FE01 STEP31 / L6.70 real Runtime endpoint smoke")
    parser.add_argument("--runtime-url", default=os.environ.get("LINYUANZHE_RUNTIME_URL", ""), help="真实 Runtime 地址；报告只写 digest。")
    parser.add_argument("--timeout", type=float, default=float(os.environ.get("LINYUANZHE_RUNTIME_TIMEOUT", "8") or 8), help="HTTP 超时秒数。")
    parser.add_argument("--require-real", action="store_true", help="缺少真实 Runtime 或 endpoint smoke 未通过时返回 2。")
    parser.add_argument("--out", default=str(REPORTS / "real_runtime_endpoint_smoke_l670.json"), help="输出报告 JSON。")
    args = parser.parse_args(argv)

    REPORTS.mkdir(parents=True, exist_ok=True)
    out = Path(args.out)
    runtime_url = _clean_url(args.runtime_url)
    if not runtime_url:
        payload = _blocked(runtime_url, out)
        _write(out, payload)
        print(json.dumps({"ok": False, "ready_for_combine": False, "blockers": payload["merge_blockers"], "report": str(out)}, ensure_ascii=False, indent=2))
        return 2 if args.require_real else 1

    read_results = [{"name": name, **_get_json(runtime_url, path, args.timeout)} for name, path in READ_ENDPOINTS]
    envelope_checks = _request_envelope_checks()
    blockers: list[str] = []
    if not all(item.get("ok") for item in read_results):
        blockers.append("real Runtime read/projection endpoints did not all pass")
    if not all(item.get("ok") for item in envelope_checks):
        blockers.append("frontend request envelope boundary checks failed")

    payload = {
        "contract_version": CONTRACT_VERSION,
        "checked_at": datetime.now().isoformat(timespec="seconds"),
        "runtime_url_visible": "digest_only",
        "runtime_url_digest": _digest(runtime_url),
        "real_runtime_url_present": True,
        "real_runtime_executed": True,
        "read_endpoint_smoke_ok": all(item.get("ok") for item in read_results),
        "read_endpoint_results": read_results,
        "request_endpoint_matrix": [{"name": name, "path": path, "posted_by_default": False, "reason": "non_mutating_l670_smoke; frontend envelope only unless explicit live action exists"} for name, path in REQUEST_ENDPOINTS],
        "request_envelope_checks_ok": all(item.get("ok") for item in envelope_checks),
        "request_envelope_checks": envelope_checks,
        "projection_policy_notes": list(PROJECTION_POLICIES_WITHOUT_DIRECT_ENDPOINT),
        "provider_default_read_only": True,
        "provider_write_mutates_real_runtime": False,
        "ready_for_combine": not blockers,
        "merge_blockers": blockers,
        "final_installer_allowed": False,
        "windows_installer_artifact_emitted": False,
        "note": "本脚本默认不向确认、控制、文件、工作区、连接器、Session 等请求端点提交真实动作；只校验真实只读端点和前端请求信封边界。",
        "report": str(out),
    }
    _write(out, payload)
    print(json.dumps({"ok": not blockers, "ready_for_combine": payload["ready_for_combine"], "blockers": blockers, "report": str(out)}, ensure_ascii=False, indent=2))
    if blockers:
        return 2 if args.require_real else 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
