from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
BACKEND = ROOT / "backend" / "project"
FRONTEND_PARENT = ROOT / "frontend"

CONTRACT_VERSION = "tiangong.l6_60.real_runtime_gate.v1+safe_provider_readonly_l661"
MISSING_RUNTIME_BLOCKER = "real Runtime instance smoke not executed"


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def _env(runtime_url: str) -> dict[str, str]:
    env = os.environ.copy()
    parts = [str(BACKEND), str(FRONTEND_PARENT)]
    if env.get("PYTHONPATH"):
        parts.append(env["PYTHONPATH"])
    env["PYTHONPATH"] = os.pathsep.join(parts)
    if runtime_url:
        # Never print this value. Reports contain digest only.
        env["LINYUANZHE_RUNTIME_URL"] = runtime_url
    return env


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {"json_decode_error": str(exc)}


def _write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _safe_tail(text: str, limit: int = 1800) -> str:
    if not text:
        return ""
    text = text.replace(os.environ.get("LINYUANZHE_RUNTIME_URL", "<empty>"), "<runtime_url_redacted>")
    return text[-limit:]


def _blocked_payload(runtime_url: str, *, allow_missing_real: bool, out: Path) -> dict[str, Any]:
    payload = {
        "contract_version": CONTRACT_VERSION,
        "checked_at": datetime.now().isoformat(timespec="seconds"),
        "runtime_url_visible": "digest_only",
        "runtime_url_digest": _digest(runtime_url) if runtime_url else "",
        "real_runtime_url_present": bool(runtime_url),
        "real_runtime_executed": False,
        "contract_server_used": False,
        "ready_for_combine": False,
        "ok": bool(allow_missing_real),
        "exit_code": 0 if allow_missing_real else 2,
        "merge_blockers": [MISSING_RUNTIME_BLOCKER, "LINYUANZHE_RUNTIME_URL not provided"],
        "next_action": "Start real TiangongWangguan/Runtime, set LINYUANZHE_RUNTIME_URL, then rerun this gate with --require-real.",
        "note": "This is a hard gate. Contract-server regression is intentionally not accepted as a real Runtime smoke result.",
        "report": str(out),
    }
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="FE01 STEP21 / L6.60 real Runtime hard gate")
    parser.add_argument("--runtime-url", default=os.environ.get("LINYUANZHE_RUNTIME_URL", ""), help="真实 Runtime 网关地址；只写 digest，不写明文。")
    parser.add_argument("--require-real", action="store_true", help="没有真实 Runtime 或真实联调未 ready 时返回 2。")
    parser.add_argument("--allow-missing-real", action="store_true", help="允许缺少真实 Runtime 时生成阻断报告但返回 0，用于打包验证。")
    parser.add_argument("--timeout", default=os.environ.get("LINYUANZHE_RUNTIME_TIMEOUT", "8"), help="传递给前端 RC preflight 的超时时间。")
    parser.add_argument("--out", default=str(REPORTS / "real_runtime_gate_l660.json"), help="输出报告 JSON 路径。")
    args = parser.parse_args(argv)

    REPORTS.mkdir(parents=True, exist_ok=True)
    runtime_url = str(args.runtime_url or "").strip()
    out = Path(args.out)

    if not runtime_url:
        payload = _blocked_payload(runtime_url, allow_missing_real=args.allow_missing_real and not args.require_real, out=out)
        _write(out, payload)
        print(json.dumps({"ok": payload["ok"], "ready_for_combine": False, "real_runtime_executed": False, "blockers": payload["merge_blockers"], "report": str(out)}, ensure_ascii=False, indent=2))
        return int(payload["exit_code"])

    rc_out = REPORTS / "rc_preflight_l660_real_runtime.json"
    cmd = [
        sys.executable,
        str(ROOT / "scripts" / "rc_preflight_l659.py"),
        "--require-real",
        "--provider-write-mode",
        os.environ.get("LINYUANZHE_PROVIDER_WRITE_MODE", "read_only"),
        "--out",
        str(rc_out),
    ]
    if args.timeout:
        # The inner preflight reads timeout through the environment.
        pass
    env = _env(runtime_url)
    env["LINYUANZHE_RUNTIME_TIMEOUT"] = str(args.timeout or "8")
    proc = subprocess.run(cmd, cwd=str(ROOT), env=env, text=True, capture_output=True, timeout=max(30, int(float(args.timeout or 8) * 8)))
    rc_payload = _read_json(rc_out)
    blockers = list(rc_payload.get("merge_blockers") or [])
    if rc_payload.get("contract_server_used"):
        blockers.append("contract server was used during real Runtime gate")
    if not rc_payload.get("real_runtime_executed"):
        blockers.append(MISSING_RUNTIME_BLOCKER)

    ready = bool(proc.returncode == 0 and rc_payload.get("ready_for_combine") and rc_payload.get("real_runtime_executed") and not rc_payload.get("contract_server_used") and not blockers)
    payload = {
        "contract_version": CONTRACT_VERSION,
        "checked_at": datetime.now().isoformat(timespec="seconds"),
        "runtime_url_visible": "digest_only",
        "runtime_url_digest": _digest(runtime_url),
        "real_runtime_url_present": True,
        "real_runtime_executed": bool(rc_payload.get("real_runtime_executed")),
        "contract_server_used": bool(rc_payload.get("contract_server_used")),
        "inner_rc_preflight_report": str(rc_out),
        "inner_returncode": proc.returncode,
        "ready_for_combine": ready,
        "ok": ready,
        "merge_blockers": blockers,
        "stdout_tail": _safe_tail(proc.stdout),
        "stderr_tail": _safe_tail(proc.stderr),
        "next_action": "Proceed to installer/RC packaging only after ready_for_combine is true." if ready else "Fix real Runtime endpoint/settings/SSE failures, then rerun --require-real.",
        "note": "Runtime URL is never written in cleartext. Provider credentials remain backend-only.",
        "report": str(out),
    }
    _write(out, payload)
    print(json.dumps({"ok": payload["ok"], "ready_for_combine": payload["ready_for_combine"], "real_runtime_executed": payload["real_runtime_executed"], "blockers": payload["merge_blockers"], "report": str(out)}, ensure_ascii=False, indent=2))
    if ready:
        return 0
    return 2 if args.require_real else 1


if __name__ == "__main__":
    raise SystemExit(main())
