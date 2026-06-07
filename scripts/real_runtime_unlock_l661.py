from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
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

CONTRACT_VERSION = "tiangong.l6_61.real_runtime_unlock.v1"
MISSING_RUNTIME_BLOCKER = "real Runtime instance smoke not executed"
REQUIRED_READ_ENDPOINTS = ("/health/runtime", "/metadata/product", "/settings/provider")
FORBIDDEN_RESPONSE_KEYS = {"api_key", "authorization", "bearer", "token", "secret", "base_url"}
FORBIDDEN_TEXT_MARKERS = ("sk-", "Bearer ", "credential_l658_secret", "provider-write-l658")


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


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


def _safe_json_keys(value: Any) -> list[str]:
    if isinstance(value, Mapping):
        return sorted(str(k) for k in value.keys())[:80]
    return []


def _has_forbidden_key(value: Any) -> list[str]:
    hits: set[str] = set()
    def walk(x: Any) -> None:
        if isinstance(x, Mapping):
            for k, v in x.items():
                ks = str(k).lower()
                if ks in FORBIDDEN_RESPONSE_KEYS:
                    hits.add(ks)
                walk(v)
        elif isinstance(x, list):
            for item in x[:50]:
                walk(item)
    walk(value)
    return sorted(hits)


def _request_json(runtime_url: str, path: str, *, timeout: float) -> dict[str, Any]:
    url = runtime_url + path
    started = time.time()
    try:
        req = urllib.request.Request(
            url,
            method="GET",
            headers={
                "Accept": "application/json",
                "X-Tiangong-Frontend-Contract": "L6.61",
                "X-Linyuanzhe-Real-Runtime-Unlock": "read-only",
            },
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read(8192)
            status = int(getattr(resp, "status", 200))
            content_type = resp.headers.get("Content-Type", "")
        parsed: Any = {}
        if raw:
            try:
                parsed = json.loads(raw.decode("utf-8", errors="replace"))
            except json.JSONDecodeError:
                parsed = {"non_json_body_digest": _digest(raw.decode("utf-8", errors="replace"))}
        body_text = json.dumps(parsed, ensure_ascii=False) if isinstance(parsed, (dict, list)) else str(parsed)
        forbidden_keys = _has_forbidden_key(parsed) if path == "/settings/provider" else []
        forbidden_markers = [m for m in FORBIDDEN_TEXT_MARKERS if m in body_text]
        return {
            "path": path,
            "method": "GET",
            "ok": 200 <= status < 300 and not forbidden_keys and not forbidden_markers,
            "status_code": status,
            "latency_ms": int((time.time() - started) * 1000),
            "content_type": _redact(content_type, runtime_url, 160),
            "json_keys": _safe_json_keys(parsed),
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


def _env(runtime_url: str, provider_write_mode: str) -> dict[str, str]:
    env = os.environ.copy()
    parts = [str(BACKEND), str(FRONTEND_PARENT)]
    if env.get("PYTHONPATH"):
        parts.append(env["PYTHONPATH"])
    env["PYTHONPATH"] = os.pathsep.join(parts)
    env["LINYUANZHE_RUNTIME_URL"] = runtime_url
    env["LINYUANZHE_PROVIDER_WRITE_MODE"] = provider_write_mode
    return env


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"read_error": _redact(exc)}


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
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
        "direct_read_probe_ok": False,
        "l660_gate_ok": False,
        "ready_for_combine": False,
        "provider_write_mode": "not_started",
        "confirmation_submit_probe": "not_mutated_without_pending_confirmation",
        "merge_blockers": [MISSING_RUNTIME_BLOCKER, "LINYUANZHE_RUNTIME_URL not provided"],
        "next_action": "启动真实 TiangongWangguan/Runtime，设置真实 Runtime 地址后重新运行本脚本。",
        "report": str(out),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="FE01 STEP22 / L6.61 true Runtime unlock gate")
    parser.add_argument("--runtime-url", default=os.environ.get("LINYUANZHE_RUNTIME_URL", ""), help="真实 Runtime 地址；报告只写 digest。")
    parser.add_argument("--require-real", action="store_true", help="缺少真实 Runtime 或未解阻时返回非零。")
    parser.add_argument("--timeout", type=float, default=float(os.environ.get("LINYUANZHE_RUNTIME_TIMEOUT", "8") or 8), help="HTTP/SSE 超时秒数。")
    parser.add_argument("--provider-write-mode", choices=["read_only", "smoke"], default=os.environ.get("LINYUANZHE_PROVIDER_WRITE_MODE", "read_only"), help="真实 Runtime 默认只读探测；smoke 才提交 Provider 写入。")
    parser.add_argument("--out", default=str(REPORTS / "real_runtime_unlock_l661.json"), help="输出报告 JSON。")
    args = parser.parse_args(argv)

    REPORTS.mkdir(parents=True, exist_ok=True)
    out = Path(args.out)
    runtime_url = _clean_url(args.runtime_url)
    if not runtime_url:
        payload = _blocked(runtime_url, out)
        _write_json(out, payload)
        print(json.dumps({"ok": False, "ready_for_combine": False, "blockers": payload["merge_blockers"], "report": str(out)}, ensure_ascii=False, indent=2))
        return 2 if args.require_real else 1

    direct = [_request_json(runtime_url, path, timeout=args.timeout) for path in REQUIRED_READ_ENDPOINTS]
    direct_ok = bool(direct) and all(item.get("ok") for item in direct)

    gate_report = REPORTS / "real_runtime_gate_l661_via_l660.json"
    cmd = [sys.executable, str(ROOT / "scripts" / "real_runtime_gate_l660.py"), "--require-real", "--out", str(gate_report)]
    env = _env(runtime_url, args.provider_write_mode)
    proc = subprocess.run(
        cmd,
        cwd=str(ROOT),
        env=env,
        text=True,
        capture_output=True,
        timeout=max(45, int(args.timeout * 10)),
    )
    gate_payload = _read_json(gate_report)
    gate_ready = bool(proc.returncode == 0 and gate_payload.get("ready_for_combine"))

    blockers: list[str] = []
    if not direct_ok:
        blockers.append("real Runtime read endpoints did not all pass")
    blockers.extend(str(x) for x in gate_payload.get("merge_blockers", []) if str(x) not in blockers)
    if proc.returncode != 0 and not blockers:
        blockers.append("real Runtime gate returned non-zero")
    ready = bool(direct_ok and gate_ready and not blockers)
    payload = {
        "contract_version": CONTRACT_VERSION,
        "checked_at": datetime.now().isoformat(timespec="seconds"),
        "runtime_url_visible": "digest_only",
        "runtime_url_digest": _digest(runtime_url),
        "real_runtime_url_present": True,
        "real_runtime_executed": bool(gate_payload.get("real_runtime_executed")),
        "direct_read_probe_ok": direct_ok,
        "direct_read_probes": direct,
        "l660_gate_ok": gate_ready,
        "l660_gate_returncode": proc.returncode,
        "l660_gate_report": str(gate_report),
        "provider_write_mode": args.provider_write_mode,
        "provider_write_mutates_real_runtime": args.provider_write_mode == "smoke",
        "confirmation_submit_probe": "skipped_non_mutating; endpoint remains request-only via frontend contract",
        "ready_for_combine": ready,
        "merge_blockers": blockers,
        "stdout_tail": _redact(proc.stdout, runtime_url),
        "stderr_tail": _redact(proc.stderr, runtime_url),
        "next_action": "进入安装器 RC 前置结构。" if ready else "按 blockers 修复真实 Runtime 地址、端点契约、SSE 顺序或 Provider 投影后重跑。",
        "note": "L6.61 默认不向真实 Runtime 写入 Provider 配置；只有 provider-write-mode=smoke 才会提交写入烟测。",
        "report": str(out),
    }
    _write_json(out, payload)
    print(json.dumps({"ok": ready, "ready_for_combine": ready, "real_runtime_executed": payload["real_runtime_executed"], "blockers": blockers, "report": str(out)}, ensure_ascii=False, indent=2))
    if ready:
        return 0
    return 2 if args.require_real else 1


if __name__ == "__main__":
    raise SystemExit(main())
