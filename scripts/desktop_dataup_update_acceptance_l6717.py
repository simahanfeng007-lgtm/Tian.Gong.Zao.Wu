from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _run(cmd: list[str], *, cwd: Path | None = None) -> dict[str, object]:
    proc = subprocess.run(cmd, cwd=str(cwd or ROOT), text=True, capture_output=True, timeout=120)
    return {
        "cmd": [Path(x).name if i == 1 and x.endswith('.py') else x for i, x in enumerate(cmd)],
        "returncode": proc.returncode,
        "ok": proc.returncode == 0,
        "stdout_tail": proc.stdout[-1200:],
        "stderr_tail": proc.stderr[-1200:],
    }


def _make_dataup_package(path: Path, *, bad_path: bool = False) -> None:
    target_rel = "provider_config.json" if bad_path else "frontend/linyuanzhe_frontend/VERSION_FE01.txt"
    payload = b"FE01 STEP31Q / L6.71.7\n"
    manifest = {
        "schema": "tiangong.dataup.manifest.v1",
        "package_id": "acceptance-step31q",
        "version": "FE01 STEP31Q / L6.71.7",
        "target_min_version": "FE01 STEP31P / L6.71.6",
        "channel": "community",
        "risk_level": "A4",
        "payload_prefix": "payload/",
        "files": [
            {"path": target_rel, "sha256": _sha256(payload), "mode": "replace"},
            {"path": "docs/dataup_acceptance_note.txt", "sha256": _sha256(b"ok\n"), "mode": "upsert"},
        ],
    }
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("dataup_manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
        zf.writestr("payload/" + target_rel, payload)
        zf.writestr("payload/docs/dataup_acceptance_note.txt", b"ok\n")


def main() -> int:
    REPORTS.mkdir(parents=True, exist_ok=True)
    checks: dict[str, object] = {}
    with tempfile.TemporaryDirectory(prefix="linyuanzhe_dataup_acceptance_") as td:
        temp = Path(td)
        fake_root = temp / "fake_root"
        (fake_root / "frontend" / "linyuanzhe_frontend").mkdir(parents=True)
        (fake_root / "docs").mkdir(parents=True)
        (fake_root / "reports").mkdir(parents=True)
        (fake_root / "frontend" / "linyuanzhe_frontend" / "VERSION_FE01.txt").write_text("FE01 STEP31P / L6.71.6\n", encoding="utf-8")
        package = temp / "good_dataup.zip"
        bad_package = temp / "bad_dataup.zip"
        _make_dataup_package(package, bad_path=False)
        _make_dataup_package(bad_package, bad_path=True)

        validate = _run([sys.executable, str(ROOT / "scripts" / "dataup_manifest_validate_l6717.py"), "--root", str(fake_root), "--package", str(package)])
        dry_run = _run([sys.executable, str(ROOT / "scripts" / "dataup_update_core_l6717.py"), "--root", str(fake_root), "--package", str(package), "--dry-run"])
        before = (fake_root / "frontend" / "linyuanzhe_frontend" / "VERSION_FE01.txt").read_text(encoding="utf-8")
        apply = _run([sys.executable, str(ROOT / "scripts" / "dataup_update_core_l6717.py"), "--root", str(fake_root), "--package", str(package), "--apply", "--yes", "--skip-post-checks"])
        after = (fake_root / "frontend" / "linyuanzhe_frontend" / "VERSION_FE01.txt").read_text(encoding="utf-8")
        block_bad = _run([sys.executable, str(ROOT / "scripts" / "dataup_update_core_l6717.py"), "--root", str(fake_root), "--package", str(bad_package), "--dry-run"])
        rollback_dirs = list((fake_root / "backups").glob("dataup_rollback_*")) if (fake_root / "backups").exists() else []

        main_window_text = (ROOT / "frontend" / "linyuanzhe_frontend" / "ui" / "main_window.py").read_text(encoding="utf-8")
        entry_files = [
            ROOT / "01_启动入口" / "Windows" / "05_DataUp一键安全更新_L6717.bat",
            ROOT / "01_启动入口" / "Linux" / "05_dataup_safe_update_l6717.sh",
            ROOT / "01_启动入口" / "macOS" / "05_DataUp一键安全更新_L6717.command",
            ROOT / "01_启动入口" / "通用Python" / "DATAUP_SAFE_UPDATE_L6717.py",
        ]
        checks = {
            "manifest_validate_passes": bool(validate["ok"]),
            "dry_run_passes": bool(dry_run["ok"]),
            "dry_run_does_not_mutate": before == "FE01 STEP31P / L6.71.6\n",
            "apply_passes_on_temp_root": bool(apply["ok"]),
            "apply_mutates_only_temp_root": after == "FE01 STEP31Q / L6.71.7\n",
            "rollback_point_created": bool(rollback_dirs),
            "blocked_path_rejected": not bool(block_bad["ok"]),
            "ui_has_dataup_buttons": all(x in main_window_text for x in ("DataUp 社区安全更新", "检查更新", "一键安全更新", "选择本地 DataUp 包")),
            "ui_has_dual_sources": "gitee.com/yu-yongxiang1994/natures-craftsmanship" in main_window_text and "github.com/simahanfeng007-lgtm/Tian.Gong.Zao.Wu" in main_window_text,
            "entry_files_exist": all(p.exists() for p in entry_files),
            "core_script_exists": (ROOT / "scripts" / "dataup_update_core_l6717.py").exists(),
            "helper_exists": (ROOT / "desktop" / "dataup_update_helper_l6717.py").exists(),
        }
        evidence = {"validate": validate, "dry_run": dry_run, "apply": apply, "block_bad": block_bad}

    payload = {
        "schema": "tiangong.fe01.step31q.dataup_update_acceptance.v1",
        "ok": all(bool(v) for v in checks.values()),
        "checks": checks,
        "evidence": evidence,
        "note": "Validates local DataUp manifest, dry-run, rollback-point creation, blocked path rejection, and UI/entry wiring. It does not call Provider SDKs, tools, memory, audit, or official Runtime RC.",
    }
    out = REPORTS / "step31q_dataup_update_acceptance_l6717.json"
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"ok": payload["ok"], "report": str(out)}, ensure_ascii=False, indent=2))
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
