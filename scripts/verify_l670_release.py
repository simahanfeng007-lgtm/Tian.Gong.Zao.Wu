from __future__ import annotations

"""FE01 STEP68 / L6.73.8 compatibility wrapper for historical L6.70 evidence."""

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


def _json_ok(name: str, path: Path, key: str = "ok", expected: bool = True) -> dict[str, Any]:
    if not path.exists():
        return {"name": name, "returncode": 1, "ok": False, "log": _public_path(path), "reason": "missing json evidence"}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        value = bool(payload.get(key))
        ok = value is expected
    except Exception as exc:
        return {"name": name, "returncode": 1, "ok": False, "log": _public_path(path), "reason": str(exc)[:160]}
    return {"name": name, "returncode": 0 if ok else 1, "ok": ok, "log": _public_path(path), "key": key, "value": value}


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
        counts = {
            "secret_hits": int(payload.get("secret_scan", {}).get("hit_count", -1)),
            "provider_sdk_import_hits": int(payload.get("provider_sdk_import_scan", {}).get("hit_count", -1)),
            "bare_except_pass_hits": int(payload.get("bare_except_pass_scan", {}).get("hit_count", -1)),
        }
    except Exception as exc:
        return {"name": name, "returncode": 1, "ok": False, "log": _public_path(path), "reason": str(exc)[:160]}
    return {"name": name, "returncode": 0 if ok else 1, "ok": ok, "log": _public_path(path), "counts": counts}


def _blockers_from(path: Path) -> list[str]:
    if not path.exists():
        return [f"missing report: {path.name}"]
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return [str(x) for x in payload.get("merge_blockers", [])]
    except Exception as exc:
        return [f"report read failed: {path.name}: {str(exc)[:120]}"]


def main() -> int:
    runtime_present = bool(os.environ.get("LINYUANZHE_RUNTIME_URL", "").strip())
    results: list[dict[str, Any]] = [
        _exit_result("l670_backend_compileall"),
        _exit_result("l670_frontend_scripts_launchers_installer_compileall"),
        _exit_result("l670_observability_preflight"),
        _exit_result("l670_hookbus_preflight"),
        _exit_result("l670_file_transfer_interrupt_preflight"),
        _exit_result("l670_workspace_preflight"),
        _exit_result("l670_connector_registry_preflight"),
        _exit_result("l670_session_manager_preflight"),
        _exit_result("l670_installer_rc_preflight"),
        _exit_result("l670_package_builder_preflight"),
        _exit_result("l670_rc_preflight_contract_server"),
        _json_ok("l670_rc_preflight_contract_server_json", REPORTS / "rc_preflight_l670_contract_server.json"),
        _scan_ok("l670_scan", REPORTS / "scan_l659.json"),
    ]
    if runtime_present:
        results.extend([
            _exit_result("l670_real_runtime_unlock"),
            _exit_result("l670_real_runtime_endpoint_smoke"),
            _json_ok("l670_real_runtime_unlock_json", REPORTS / "real_runtime_unlock_l670.json", "ready_for_combine"),
            _json_ok("l670_real_runtime_endpoint_smoke_json", REPORTS / "real_runtime_endpoint_smoke_l670.json", "ready_for_combine"),
        ])
    else:
        results.extend([
            _exit_result("l670_real_runtime_unlock_absent_expected", {2}),
            _exit_result("l670_real_runtime_endpoint_smoke_absent_expected", {2}),
            _json_ok("l670_real_runtime_unlock_blocked_json", REPORTS / "real_runtime_unlock_l670.json", "ready_for_combine", expected=False),
            _json_ok("l670_real_runtime_endpoint_smoke_blocked_json", REPORTS / "real_runtime_endpoint_smoke_l670.json", "ready_for_combine", expected=False),
        ])

    ready = False
    if runtime_present:
        ready = bool(
            all(item["ok"] for item in results)
            and json.loads((REPORTS / "real_runtime_unlock_l670.json").read_text(encoding="utf-8")).get("ready_for_combine")
            and json.loads((REPORTS / "real_runtime_endpoint_smoke_l670.json").read_text(encoding="utf-8")).get("ready_for_combine")
        )

    blockers: list[str] = []
    for p in (REPORTS / "real_runtime_unlock_l670.json", REPORTS / "real_runtime_endpoint_smoke_l670.json"):
        for item in _blockers_from(p):
            if item not in blockers:
                blockers.append(item)
    if not runtime_present and "LINYUANZHE_RUNTIME_URL not provided" not in blockers:
        blockers.append("LINYUANZHE_RUNTIME_URL not provided")

    summary: dict[str, Any] = {
        "contract_version": "tiangong.l6_70.release_verify.v1",
        "checked_at": datetime.now().isoformat(timespec="seconds"),
        "historical_compatibility_only": True,
        "runtime_url_present": runtime_present,
        "results": results,
        "ok": all(item["ok"] for item in results),
        "ready_for_combine": ready,
        "real_runtime_smoke_passed": ready,
        "final_installer_allowed": False,
        "windows_installer_artifact_emitted": False,
        "runtime_core_mutation": False,
        "merge_blockers": blockers,
        "note": "L6.70 is only unblocked when real Runtime unlock and endpoint smoke both pass. Contract-server evidence remains regression-only.",
    }
    out = REPORTS / "validation_summary_l670.json"
    out.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"ok": summary["ok"], "ready_for_combine": summary["ready_for_combine"], "blockers": blockers, "report": _public_path(out)}, ensure_ascii=False, indent=2))
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
