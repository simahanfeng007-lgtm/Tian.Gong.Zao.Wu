from __future__ import annotations

"""L6.66 aggregate release evidence checker."""

import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = Path(os.environ.get("LINYUANZHE_REPORT_DIR") or tempfile.mkdtemp(prefix="linyuanzhe_verify_release_"))


def _public_path(path: Path) -> str:
    try:
        tmp = Path(tempfile.gettempdir()).resolve()
        resolved = path.resolve()
        if resolved == tmp or tmp in resolved.parents:
            return f"<tmp>/{resolved.name}"
    except Exception:
        return path.name
    return path.name


def _exit_result(name: str, expected: set[int] | None = None) -> dict[str, Any]:
    expected = expected or {0}
    p = REPORTS / f"{name}.exit"
    log = REPORTS / f"{name}.log"
    if not p.exists():
        return {"name": name, "returncode": 1, "ok": False, "log": _public_path(log), "reason": "missing exit evidence"}
    try:
        rc = int(p.read_text(encoding="utf-8").strip() or "1")
    except ValueError:
        rc = 1
    return {"name": name, "returncode": rc, "ok": rc in expected, "log": _public_path(log)}


def _json_ok(name: str, path: Path, key: str = "ok") -> dict[str, Any]:
    if not path.exists():
        return {"name": name, "returncode": 1, "ok": False, "log": _public_path(path), "reason": "missing json evidence"}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        ok = bool(payload.get(key))
    except Exception as exc:
        return {"name": name, "returncode": 1, "ok": False, "log": _public_path(path), "reason": str(exc)[:160]}
    return {"name": name, "returncode": 0 if ok else 1, "ok": ok, "log": _public_path(path)}


def _scan_ok(name: str, path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"name": name, "returncode": 1, "ok": False, "log": _public_path(path), "reason": "missing scan report"}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        ok = (
            bool(payload.get("secret_scan", {}).get("ok"))
            and bool(payload.get("provider_sdk_import_scan", {}).get("ok"))
            and bool(payload.get("bare_except_pass_scan", {}).get("ok"))
        )
    except Exception as exc:
        return {"name": name, "returncode": 1, "ok": False, "log": _public_path(path), "reason": str(exc)[:160]}
    return {"name": name, "returncode": 0 if ok else 1, "ok": ok, "log": _public_path(path)}


def main() -> int:
    runtime_present = bool(os.environ.get("LINYUANZHE_RUNTIME_URL", "").strip())
    results: list[dict[str, Any]] = [
        _exit_result("l666_backend_compileall"),
        _exit_result("l666_frontend_scripts_compileall"),
        _exit_result("l666_observability_preflight"),
        _exit_result("l666_hookbus_preflight"),
        _exit_result("l666_file_transfer_interrupt_preflight"),
        _exit_result("l666_workspace_preflight"),
        _exit_result("l666_connector_registry_preflight"),
        _json_ok("l666_rc_preflight_contract_server", REPORTS / "rc_preflight_l666_contract_server.json"),
        _scan_ok("l666_scan", REPORTS / "scan_l659.json"),
    ]
    if runtime_present:
        results.append(_json_ok("l666_real_runtime_unlock", REPORTS / "real_runtime_unlock_l666_verify.json", "ready_for_combine"))
    else:
        results.append(_exit_result("l666_real_runtime_unlock_absent_expected", {2}))
    summary: dict[str, Any] = {
        "contract_version": "tiangong.l6_66.release_verify.v1",
        "checked_at": datetime.now().isoformat(timespec="seconds"),
        "historical_compatibility_only": True,
        "runtime_url_present": runtime_present,
        "results": results,
        "ok": all(item["ok"] for item in results),
        "ready_for_combine": False,
        "note": "L6.66 adds MCP / connector registry governance. Aggregate verifier consumes generated evidence; standalone scripts rerun each preflight.",
    }
    if runtime_present and (REPORTS / "real_runtime_unlock_l666_verify.json").exists():
        try:
            payload = json.loads((REPORTS / "real_runtime_unlock_l666_verify.json").read_text(encoding="utf-8"))
            summary["ready_for_combine"] = bool(payload.get("ready_for_combine"))
        except Exception as exc:
            summary["real_unlock_report_read_error"] = str(exc)[:160]
    out = REPORTS / "validation_summary_l666.json"
    out.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"ok": summary["ok"], "ready_for_combine": summary["ready_for_combine"], "report": _public_path(out)}, ensure_ascii=False, indent=2))
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
