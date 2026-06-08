from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BRIDGE = ROOT / "desktop" / "linyuanzhe_local_runtime_bridge_l671.py"
REPORT = ROOT / "reports" / "desktop_step31d_regression_l6704.json"
URL_RE = re.compile(r"LINYUANZHE_LOCAL_RUNTIME_URL=(http://[^\s]+)")


def _pythonpath() -> str:
    parts = [str(ROOT / "backend" / "project"), str(ROOT / "frontend")]
    current = os.environ.get("PYTHONPATH", "")
    if current:
        parts.append(current)
    return os.pathsep.join(parts)


def _json_request(base: str, path: str, *, method: str = "GET", payload: dict | None = None) -> dict:
    data = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        base + path,
        data=data,
        method=method,
        headers={"Accept": "application/json", "Content-Type": "application/json; charset=utf-8"},
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        raw = resp.read()
    return json.loads(raw.decode("utf-8")) if raw else {}


def _start_bridge() -> tuple[subprocess.Popen[str], str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = _pythonpath()
    cmd = [sys.executable, str(BRIDGE), "--host", "127.0.0.1", "--port", "0", "--backend-mode", "mock", "--timeout", "30"]
    proc = subprocess.Popen(cmd, cwd=str(ROOT), env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=1)
    assert proc.stdout is not None
    deadline = time.time() + 15
    seen: list[str] = []
    while time.time() < deadline:
        line = proc.stdout.readline()
        if line:
            seen.append(line.rstrip())
            m = URL_RE.search(line)
            if m:
                return proc, m.group(1)
        if proc.poll() is not None:
            break
    proc.kill()
    raise RuntimeError("bridge did not start: " + "\\n".join(seen[-20:]))


def main() -> int:
    sys.path.insert(0, str(ROOT / "frontend"))
    from linyuanzhe_frontend.clients.sse_runtime_client import SseRuntimeClient

    proc, base = _start_bridge()
    results: dict[str, object] = {"base_url": base}
    try:
        health = _json_request(base, "/health/runtime")
        results["health_status"] = health.get("payload", {}).get("status")

        self_iter = _json_request(base, "/self-iteration/confirm", method="POST", payload={"candidate_id": "ITER-FE01-0001", "decision": "confirmed"})
        results["self_iteration_status"] = self_iter.get("status")

        conn = _json_request(base, "/connectors/register/request", method="POST", payload={"display_name": "本地 MCP 候选连接器", "kind": "mcp_server", "requested_scopes": ["read_public_metadata"]})
        results["connector_status"] = conn.get("status")
        registry = _json_request(base, "/connectors/registry")
        results["connector_count"] = registry.get("connector_registry_projection", {}).get("connector_count")

        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as fh:
            fh.write("临渊者 STEP31D file handoff smoke test")
            temp_path = Path(fh.name)
        file_req = _json_request(
            base,
            "/files/transfer/request",
            method="POST",
            payload={
                "file_name": temp_path.name,
                "size_bytes": temp_path.stat().st_size,
                "sha256": "abc123",
                "mime_type": "text/plain",
                "purpose": "user_attachment",
                "runtime_handoff_path": str(temp_path),
            },
        )
        results["file_transfer_status"] = file_req.get("status")

        auth_req = _json_request(
            base,
            "/workspace/file/authorize",
            method="POST",
            payload={"file_name": "output.txt", "mode": "write", "scope": "workspace_outbox", "purpose": "workspace_output_write", "local_path_digest": "digest_only"},
        )
        results["file_auth_status"] = auth_req.get("status")
        results["file_auth_mode"] = auth_req.get("mode")
        results["file_auth_scope"] = auth_req.get("scope")

        check = _json_request(base, "/installer/startup/self-check")
        results["startup_check_ok"] = check.get("ok")
        results["startup_check_count"] = len(check.get("checks", []))

        sessions = _json_request(base, "/sessions/list")
        results["mock_session_leaked_http"] = any("SESS-MOCK" in json.dumps(item, ensure_ascii=False) for item in sessions.get("task_sessions", []))

        client = SseRuntimeClient(base, timeout=10, max_reconnects=0)
        snap = client.refresh_snapshot()
        results["client_refresh_status"] = snap.runtime_status
        snap = client.request_session_resume("SESS-MOCK-FAILED")
        results["client_mock_session_state"] = snap.session_manager_state
        results["client_mock_session_leaked"] = any("SESS-MOCK" in getattr(x, "session_id_digest", "") for x in snap.task_sessions)
        snap = client.submit_self_iteration_confirmation("ITER-FE01-0001", "confirmed")
        results["client_self_iteration_tail"] = snap.chat_messages[-1].text if snap.chat_messages else ""
        snap = client.run_startup_self_check()
        results["client_startup_state"] = snap.startup_self_check_state

        ok = (
            results["health_status"] == "ok"
            and results["self_iteration_status"] == "accepted"
            and results["connector_status"] == "accepted"
            and int(results["connector_count"] or 0) >= 1
            and results["file_transfer_status"] == "accepted"
            and results["file_auth_status"] == "accepted"
            and results["file_auth_mode"] == "write"
            and results["file_auth_scope"] == "workspace_outbox"
            and results["startup_check_ok"] is True
            and results["mock_session_leaked_http"] is False
            and results["client_mock_session_state"] == "mock_session_discarded"
            and results["client_mock_session_leaked"] is False
            and "HTTP Error 404" not in str(results["client_self_iteration_tail"])
            and results["client_startup_state"] in {"pass", "accepted", "ok"}
        )
        results["ok"] = bool(ok)
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        REPORT.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(results, ensure_ascii=False, indent=2))
        return 0 if ok else 1
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except Exception:
            proc.kill()


if __name__ == "__main__":
    raise SystemExit(main())
