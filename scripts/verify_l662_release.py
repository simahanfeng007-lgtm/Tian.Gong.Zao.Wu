from __future__ import annotations

"""FE01 STEP68 / L6.73.8 quick compatibility verifier for historical L662 release evidence.

The original historical verifier re-ran heavy compile/preflight chains and could
hang in CI or create __pycache__ inside a clean delivery tree. This wrapper keeps
the public entry point, but makes the default path deterministic, read-only for
the package, and explicit about compatibility-only scope.
"""

import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = Path(os.environ.get("LINYUANZHE_REPORT_DIR") or tempfile.mkdtemp(prefix="linyuanzhe_verify_l662_"))
CONTRACT_VERSION = "tiangong.l6_62.release_verify.quick_compat.v2"


def _public_path(path: Path) -> str:
    try:
        tmp = Path(tempfile.gettempdir()).resolve()
        resolved = path.resolve()
        if resolved == tmp or tmp in resolved.parents:
            return f"<tmp>/{resolved.name}"
    except Exception:
        pass
    return path.name


def _path_check(name: str, rel: str, kind: str = "file") -> dict[str, Any]:
    path = ROOT / rel
    if kind == "dir":
        ok = path.is_dir()
    else:
        ok = path.is_file()
    return {"name": name, "path": rel.replace("\\", "/"), "ok": bool(ok), "kind": kind}


def main() -> int:
    REPORTS.mkdir(parents=True, exist_ok=True)
    checks = [
        _path_check("backend_runtime_entry", "backend/project/run_agent.py"),
        _path_check("frontend_package", "frontend/linyuanzhe_frontend", "dir"),
        _path_check("rc_launcher", "launchers/start_linyuanzhe_rc.py"),
        _path_check("version_product", "VERSION_PRODUCT.txt"),
    ]
    ok = all(item["ok"] for item in checks)
    summary: dict[str, Any] = {
        "contract_version": CONTRACT_VERSION,
        "checked_at": datetime.now().isoformat(timespec="seconds"),
        "historical_compatibility_only": True,
        "status": "PASS" if ok else "FAIL",
        "ok": ok,
        "ready_for_combine": False,
        "skipped_heavy_steps": True,
        "skip_reason": "Historical L662 compile/preflight chain is superseded by the current L6.73.8 verifier; default mode is package-read-only and CI-safe.",
        "pycache_policy": "no compileall; no package-tree pycache generation",
        "report_dir_policy": "temporary unless LINYUANZHE_REPORT_DIR is explicitly set",
        "checks": checks,
        "note": "L6.62 observability preflight is not rerun by default to avoid CI hangs.",
    }
    out = REPORTS / "validation_summary_l662.json"
    out.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"ok": ok, "status": summary["status"], "historical_compatibility_only": True, "report": _public_path(out)}, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
