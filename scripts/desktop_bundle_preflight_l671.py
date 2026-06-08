from __future__ import annotations

"""FE01 STEP31F / L6.70.6 desktop all-in-one package preflight."""

import json
import os
import subprocess
import sys
import time
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
BACKEND = ROOT / "backend" / "project"
FRONTEND_PARENT = ROOT / "frontend"
BRIDGE = ROOT / "desktop" / "linyuanzhe_local_runtime_bridge_l671.py"


def _digest_text(value: str) -> str:
    import hashlib
    return hashlib.sha256(value.encode("utf-8", errors="ignore")).hexdigest()[:16]


def _pythonpath() -> str:
    parts = [str(BACKEND), str(FRONTEND_PARENT)]
    current = os.environ.get("PYTHONPATH", "")
    if current:
        parts.append(current)
    return os.pathsep.join(parts)


def _run(name: str, cmd: list[str], *, timeout: int = 120) -> dict[str, Any]:
    REPORTS.mkdir(parents=True, exist_ok=True)
    log = REPORTS / f"{name}.log"
    exit_file = REPORTS / f"{name}.exit"
    started = time.time()
    env = os.environ.copy()
    env["PYTHONPATH"] = _pythonpath()
    try:
        proc = subprocess.run(cmd, cwd=str(ROOT), env=env, text=True, capture_output=True, timeout=timeout)
        output = "\n".join(x for x in (proc.stdout, proc.stderr) if x)
        rc = proc.returncode
    except subprocess.TimeoutExpired as exc:
        output = f"timeout after {timeout}s\n{exc}"
        rc = 124
    log.write_text(output[-20000:], encoding="utf-8")
    exit_file.write_text(str(rc), encoding="utf-8")
    return {"name": name, "ok": rc == 0, "returncode": rc, "latency_ms": int((time.time() - started) * 1000), "log": str(log), "exit": str(exit_file)}


def _compileall() -> dict[str, Any]:
    targets = ["backend/project", "frontend", "scripts", "launchers", "installer", "desktop"]
    cmd = [sys.executable, "-m", "compileall", "-q", *targets]
    return _run("l671_desktop_bundle_compileall", cmd, timeout=180)


def _start_bridge() -> tuple[subprocess.Popen[str], str, list[str]]:
    env = os.environ.copy()
    env["PYTHONPATH"] = _pythonpath()
    cmd = [sys.executable, str(BRIDGE), "--host", "127.0.0.1", "--port", "0", "--backend-mode", "mock", "--timeout", "60"]
    proc = subprocess.Popen(cmd, cwd=str(ROOT), env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=1)
    assert proc.stdout is not None
    lines: list[str] = []
    deadline = time.time() + 20
    url = ""
    while time.time() < deadline:
        line = proc.stdout.readline()
        if line:
            lines.append(line.strip())
            if line.startswith("LINYUANZHE_LOCAL_RUNTIME_URL="):
                url = line.strip().split("=", 1)[1]
                break
        if proc.poll() is not None:
            break
    if not url:
        proc.terminate()
        raise RuntimeError("local desktop bridge did not publish URL: " + " | ".join(lines[-10:]))
    return proc, url, lines


def _stop(proc: subprocess.Popen[str]) -> None:
    if proc.poll() is not None:
        return
    try:
        proc.terminate()
        proc.wait(timeout=5)
    except Exception:
        try:
            proc.kill()
        except Exception as exc:
            _ = exc
            return


def _get_json(url: str, path: str) -> dict[str, Any]:
    req = urllib.request.Request(url + path, headers={"Accept": "application/json"}, method="GET")
    with urllib.request.urlopen(req, timeout=10) as resp:
        raw = resp.read()
        status = int(getattr(resp, "status", 200))
    parsed = json.loads(raw.decode("utf-8", errors="replace")) if raw else {}
    return {"path": path, "ok": 200 <= status < 300, "status": status, "keys": sorted(parsed.keys()) if isinstance(parsed, dict) else [], "payload": parsed}


def _post_sse(url: str, message: str) -> dict[str, Any]:
    body = json.dumps({"message": message, "frontend_contract": "L6.70.6", "no_frontend_tool_execution": True, "no_frontend_memory_write": True, "no_frontend_rollback_apply": True}, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url + "/chat/stream-events", data=body, method="POST", headers={"Accept": "text/event-stream", "Content-Type": "application/json; charset=utf-8"})
    with urllib.request.urlopen(req, timeout=90) as resp:
        raw = resp.read().decode("utf-8", errors="replace")
        status = int(getattr(resp, "status", 200))
    events: list[dict[str, Any]] = []
    for block in raw.split("\n\n"):
        data_lines = []
        for line in block.splitlines():
            if line.startswith("data:"):
                data_lines.append(line[5:].strip())
        if not data_lines:
            continue
        try:
            parsed = json.loads("\n".join(data_lines))
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            events.append(parsed)
    names = [str(item.get("event", "")) for item in events]
    order_ok = "run_terminal" not in names or ("assistant_final" in names and names.index("assistant_final") < names.index("run_terminal"))
    final_event = next((item for item in events if item.get("event") == "assistant_final"), {})
    final_text = str(final_event.get("payload", {}).get("content", "")) if isinstance(final_event.get("payload"), dict) else ""
    return {
        "path": "/chat/stream-events",
        "ok": bool(200 <= status < 300 and order_ok and "run_terminal" in names and final_text.strip()),
        "status": status,
        "events": names,
        "assistant_final_before_run_terminal": order_ok,
        "assistant_final_digest": _digest_text(final_text),
        "assistant_final_length": len(final_text),
    }


def _bridge_probe() -> dict[str, Any]:
    proc = None
    started = time.time()
    try:
        proc, url, lines = _start_bridge()
        read_paths = [
            "/health/runtime",
            "/metadata/product",
            "/settings/provider",
            "/workspace/policy",
            "/connectors/registry",
            "/sessions/list",
            "/installer/manifest",
        ]
        reads = [_get_json(url, path) for path in read_paths]
        chat = _post_sse(url, "桌面一体包自检：请返回一行确认。")
        health_payload = next((r.get("payload", {}) for r in reads if r.get("path") == "/health/runtime"), {})
        runtime_kind = ""
        if isinstance(health_payload, dict):
            inner = health_payload.get("payload", {})
            if isinstance(inner, dict):
                runtime_kind = str(inner.get("runtime_kind", ""))
        return {
            "ok": all(item.get("ok") for item in reads) and chat.get("ok") and runtime_kind == "local_desktop_bridge",
            "latency_ms": int((time.time() - started) * 1000),
            "bridge_url_digest": _digest_text(url),
            "startup_lines": lines[-3:],
            "runtime_kind": runtime_kind,
            "read_endpoint_results": [{k: v for k, v in item.items() if k != "payload"} for item in reads],
            "chat_stream_result": chat,
            "official_real_runtime_smoke_target": False,
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc)[:500], "latency_ms": int((time.time() - started) * 1000)}
    finally:
        if proc is not None:
            _stop(proc)


def main() -> int:
    REPORTS.mkdir(parents=True, exist_ok=True)
    compile_result = _compileall()
    bridge_result = _bridge_probe()
    scan_result = _run("l671_desktop_bundle_scan", [sys.executable, str(ROOT / "scripts" / "scan_l659.py")], timeout=120)
    ok = bool(compile_result.get("ok") and bridge_result.get("ok") and scan_result.get("ok"))
    payload = {
        "contract_version": "tiangong.l6_70_6.desktop_visual_click_preflight.v1",
        "checked_at": datetime.now().isoformat(timespec="seconds"),
        "ok": ok,
        "desktop_all_in_one_ready": ok,
        "frontend_backend_bundled": True,
        "local_desktop_bridge_ready": bool(bridge_result.get("ok")),
        "real_runtime_smoke_passed": False,
        "ready_for_combine": False,
        "final_installer_allowed": False,
        "windows_installer_artifact_emitted": False,
        "runtime_core_mutation": False,
        "compileall": compile_result,
        "local_bridge_probe": bridge_result,
        "scan": scan_result,
        "merge_blockers": ["official real Runtime RC unlock not executed in this desktop all-in-one package"],
        "note": "本报告证明桌面端前端与本地桥接后端可一键启动；它不替代正式 TiangongWangguan/Runtime 真实联调。",
    }
    out = REPORTS / "desktop_bundle_preflight_l671.json"
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"ok": ok, "desktop_all_in_one_ready": ok, "ready_for_combine": False, "report": str(out)}, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
