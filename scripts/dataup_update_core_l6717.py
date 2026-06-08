from __future__ import annotations

"""DataUp safe updater core for Linyuanzhe FE01 STEP31Q / L6.71.7.

This module is deliberately a standalone helper. The desktop frontend may launch
it, but the frontend itself must not copy files, call Provider SDKs, write
memory, or bypass Runtime/QualityGate. The updater applies only explicit
DataUp packages after manifest validation, path policy checks, rollback-point
creation, and post-update self checks.
"""

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
import zipfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping

SCHEMA = "tiangong.dataup.safe_update.v1"
LATEST_SCHEMA = "tiangong.dataup.latest.v1"
MANIFEST_SCHEMA = "tiangong.dataup.manifest.v1"
VERSION_LABEL = "FE01 STEP31Q / L6.71.7"

GITEE_REPOSITORY = "https://gitee.com/yu-yongxiang1994/natures-craftsmanship"
GITHUB_REPOSITORY = "https://github.com/simahanfeng007-lgtm/Tian.Gong.Zao.Wu"
GITEE_LATEST_URL = GITEE_REPOSITORY + "/raw/main/dataup/latest.json"
GITHUB_LATEST_URL = "https://raw.githubusercontent.com/simahanfeng007-lgtm/Tian.Gong.Zao.Wu/main/dataup/latest.json"

ALLOWED_PREFIXES = (
    "frontend/",
    "desktop/",
    "scripts/",
    "docs/",
    "reports/",
    "launchers/",
    "installer/updater/",
    "installer/startup/",
    "installer/release/",
    "installer/signing/",
    "installer/version_slots/",
    "01_启动入口/",
    "dataup/",
)
ALLOWED_ROOT_FILES = (
    "README",
    "CHANGELOG",
    "目录说明",
    "使用说明",
)
BLOCKED_COMPONENTS = {
    ".git",
    ".ssh",
    "__pycache__",
    "memory",
    "memories",
    "logs",
    "audit_private",
    "credentials",
    "secrets",
    "private_keys",
    "user_data",
    "workspace_private",
}
BLOCKED_FILENAMES = {
    ".env",
    "provider_config.json",
    "model_config.json",
    "id_rsa",
    "id_dsa",
    "id_ecdsa",
    "id_ed25519",
}
SENSITIVE_PATTERNS = (
    re.compile(r"(?i)sk-[A-Za-z0-9_\-]{12,}"),
    re.compile(r"(?i)Bearer\s+[A-Za-z0-9_\-.]{12,}"),
    re.compile(r"(?i)(api[_-]?key|secret|token|password)\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{12,}"),
)


class DataUpError(RuntimeError):
    pass


@dataclass
class FilePlan:
    path: str
    mode: str = "replace"
    sha256: str = ""
    size: int = 0
    source: str = ""
    target_exists: bool = False
    target_digest: str = ""
    action: str = "replace"


@dataclass
class PackagePlan:
    ok: bool
    package_path: str
    manifest_path: str
    package_id: str
    version: str
    target_min_version: str
    channel: str
    risk_level: str
    files: list[FilePlan] = field(default_factory=list)
    blocked: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    source_kind: str = "local_package"
    signature_verified: bool = False
    signature_note: str = "signature slot reserved; no cryptographic verification performed by this stdlib helper"


def _json_dumps(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2, sort_keys=False)


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _safe_text(value: Any, limit: int = 240) -> str:
    text = str(value or "")
    for pat in SENSITIVE_PATTERNS:
        text = pat.sub("<redacted>", text)
    text = text.replace("\r", " ").replace("\n", " ")
    return text[:limit]


def _normalize_rel_path(raw: Any) -> str:
    text = str(raw or "").strip().replace("\\", "/")
    if not text:
        raise DataUpError("empty path")
    pp = PurePosixPath(text)
    if pp.is_absolute():
        raise DataUpError(f"absolute path is forbidden: {_safe_text(text)}")
    parts = [p for p in pp.parts if p not in {"", "."}]
    if not parts or any(p == ".." for p in parts):
        raise DataUpError(f"path traversal is forbidden: {_safe_text(text)}")
    normalized = "/".join(parts)
    if normalized.endswith("/"):
        raise DataUpError(f"directory path is not a file target: {_safe_text(text)}")
    return normalized


def _path_allowed(path: str) -> tuple[bool, str]:
    lower_parts = {p.lower() for p in path.split("/")}
    filename = path.split("/")[-1].lower()
    if lower_parts & BLOCKED_COMPONENTS:
        return False, "blocked directory component"
    if filename in BLOCKED_FILENAMES:
        return False, "blocked filename"
    if any(x in filename for x in ("apikey", "api_key", "secret", "token", "password")):
        return False, "sensitive filename token"
    if path.startswith("backend/") or path.startswith("kernel/") or path.startswith("shell/") or path.startswith("runtime/"):
        return False, "backend/runtime core paths are not writable by DataUp FE updater"
    if path.startswith(ALLOWED_PREFIXES):
        return True, "allowed prefix"
    if "/" not in path and path.startswith(ALLOWED_ROOT_FILES):
        return True, "allowed root documentation file"
    return False, "path is outside DataUp whitelist"


def _find_manifest_member(zf: zipfile.ZipFile) -> str:
    names = [n for n in zf.namelist() if not n.endswith("/")]
    direct = [n for n in names if PurePosixPath(n).name == "dataup_manifest.json"]
    if not direct:
        raise DataUpError("DataUp package missing dataup_manifest.json")
    # Prefer root-level manifest, then shortest path.
    direct.sort(key=lambda n: ("/" in n, len(n)))
    return direct[0]


def _load_manifest(zf: zipfile.ZipFile, member: str) -> dict[str, Any]:
    try:
        raw = zf.read(member)
        data = json.loads(raw.decode("utf-8", errors="replace"))
    except Exception as exc:
        raise DataUpError(f"manifest parse failed: {_safe_text(exc)}") from exc
    if not isinstance(data, dict):
        raise DataUpError("manifest must be a JSON object")
    return data


def _payload_prefix_for_manifest(member: str) -> str:
    parent = str(PurePosixPath(member).parent)
    if parent == ".":
        return "payload/"
    return parent.rstrip("/") + "/payload/"


def _infer_files_from_payload(zf: zipfile.ZipFile, payload_prefix: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for name in zf.namelist():
        if name.endswith("/") or not name.startswith(payload_prefix):
            continue
        rel = name[len(payload_prefix):]
        if not rel:
            continue
        out.append({"path": rel, "mode": "replace"})
    return out


def plan_package(package_path: Path, root: Path, *, source_kind: str = "local_package") -> PackagePlan:
    package_path = package_path.expanduser().resolve()
    root = root.expanduser().resolve()
    if not package_path.exists():
        raise DataUpError(f"package does not exist: {_safe_text(package_path)}")
    if not zipfile.is_zipfile(package_path):
        raise DataUpError("DataUp package must be a zip file")
    with zipfile.ZipFile(package_path, "r") as zf:
        manifest_member = _find_manifest_member(zf)
        manifest = _load_manifest(zf, manifest_member)
        payload_prefix = str(manifest.get("payload_prefix") or _payload_prefix_for_manifest(manifest_member)).replace("\\", "/")
        files_raw = manifest.get("files")
        if not isinstance(files_raw, list) or not files_raw:
            files_raw = _infer_files_from_payload(zf, payload_prefix)
        if not files_raw:
            raise DataUpError("manifest files is empty and payload has no file")
        files: list[FilePlan] = []
        blocked: list[str] = []
        warnings: list[str] = []
        for item in files_raw:
            if not isinstance(item, Mapping):
                blocked.append("invalid file entry")
                continue
            try:
                rel = _normalize_rel_path(item.get("path"))
            except DataUpError as exc:
                blocked.append(str(exc))
                continue
            allowed, reason = _path_allowed(rel)
            if not allowed:
                blocked.append(f"{rel}: {reason}")
                continue
            mode = str(item.get("mode") or "replace").strip().lower()
            if mode not in {"replace", "add", "upsert"}:
                blocked.append(f"{rel}: unsupported mode {mode}")
                continue
            member = str(item.get("source") or (payload_prefix + rel)).replace("\\", "/")
            if member not in zf.namelist():
                blocked.append(f"{rel}: payload member missing")
                continue
            raw = zf.read(member)
            expected = str(item.get("sha256") or "").strip().lower()
            actual = _sha256_bytes(raw)
            if expected and expected != actual:
                blocked.append(f"{rel}: sha256 mismatch")
                continue
            target = root / rel
            target_exists = target.exists()
            target_digest = _sha256_file(target) if target_exists and target.is_file() else ""
            files.append(FilePlan(
                path=rel,
                mode=mode,
                sha256=actual,
                size=len(raw),
                source=member,
                target_exists=target_exists,
                target_digest=target_digest,
                action="replace" if target_exists else "add",
            ))
        risk = str(manifest.get("risk_level") or "A4").strip().upper()
        if risk == "A5":
            blocked.append("risk_level A5 is hard-blocked by DataUp safe updater")
        if not any(n.endswith("dataup_signature.sig") for n in zf.namelist()):
            warnings.append("signature file not present; sha256 manifest validation still applied")
        ok = bool(files) and not blocked
        return PackagePlan(
            ok=ok,
            package_path=str(package_path),
            manifest_path=manifest_member,
            package_id=_safe_text(manifest.get("package_id") or package_path.stem, 120),
            version=_safe_text(manifest.get("version") or "unknown", 80),
            target_min_version=_safe_text(manifest.get("target_min_version") or "unknown", 80),
            channel=_safe_text(manifest.get("channel") or "community", 40),
            risk_level=risk,
            files=files,
            blocked=blocked,
            warnings=warnings,
            source_kind=source_kind,
            signature_verified=False,
        )


def _plan_to_dict(plan: PackagePlan) -> dict[str, Any]:
    return {
        "ok": plan.ok,
        "package_path_digest": _sha256_bytes(plan.package_path.encode("utf-8", errors="ignore"))[:16],
        "manifest_path": plan.manifest_path,
        "package_id": plan.package_id,
        "version": plan.version,
        "target_min_version": plan.target_min_version,
        "channel": plan.channel,
        "risk_level": plan.risk_level,
        "source_kind": plan.source_kind,
        "signature_verified": plan.signature_verified,
        "signature_note": plan.signature_note,
        "file_count": len(plan.files),
        "add_count": len([f for f in plan.files if f.action == "add"]),
        "replace_count": len([f for f in plan.files if f.action == "replace"]),
        "blocked": list(plan.blocked),
        "warnings": list(plan.warnings),
        "files": [
            {
                "path": f.path,
                "mode": f.mode,
                "action": f.action,
                "sha256": f.sha256,
                "size": f.size,
                "target_exists": f.target_exists,
                "target_digest": f.target_digest[:16] if f.target_digest else "",
            }
            for f in plan.files
        ],
    }


def _write_report(root: Path, name: str, payload: dict[str, Any], explicit: Path | None = None) -> Path:
    if explicit is not None:
        out = explicit.expanduser().resolve()
    else:
        out = root / "reports" / name
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(_json_dumps(payload), encoding="utf-8")
    return out


def _download_json(url: str, timeout: float = 10.0) -> dict[str, Any]:
    req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "Linyuanzhe-DataUp/0.1"}, method="GET")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read(1024 * 1024)
    data = json.loads(raw.decode("utf-8", errors="replace")) if raw else {}
    if not isinstance(data, dict):
        raise DataUpError("latest metadata must be object")
    return data


def check_latest(source: str = "auto", *, latest_url: str = "") -> dict[str, Any]:
    candidates: list[tuple[str, str]] = []
    if latest_url:
        candidates.append(("custom", latest_url))
    elif source == "gitee":
        candidates.append(("gitee", GITEE_LATEST_URL))
    elif source == "github":
        candidates.append(("github", GITHUB_LATEST_URL))
    else:
        candidates.extend([("gitee", GITEE_LATEST_URL), ("github", GITHUB_LATEST_URL)])
    attempts = []
    for name, url in candidates:
        try:
            data = _download_json(url)
            data["source_name"] = name
            data["source_url_digest"] = _sha256_bytes(url.encode("utf-8", errors="ignore"))[:16]
            return {"ok": True, "source_name": name, "latest": data, "attempts": attempts}
        except Exception as exc:
            attempts.append({"source_name": name, "ok": False, "error": _safe_text(exc, 180)})
    return {"ok": False, "latest": {}, "attempts": attempts, "error": "all DataUp sources failed"}


def _select_package_url(latest: Mapping[str, Any], source_name: str) -> str:
    keys = []
    if source_name == "gitee":
        keys.extend(["package_url_gitee", "package_url"])
    elif source_name == "github":
        keys.extend(["package_url_github", "package_url"])
    keys.extend(["package_url_gitee", "package_url_github", "package_url"])
    for key in keys:
        val = str(latest.get(key) or "").strip()
        if val:
            return val
    return ""


def download_package_from_latest(latest_result: Mapping[str, Any], dest_dir: Path) -> Path:
    if not latest_result.get("ok"):
        raise DataUpError("latest metadata is not available")
    source_name = str(latest_result.get("source_name") or "auto")
    latest = latest_result.get("latest") if isinstance(latest_result.get("latest"), Mapping) else {}
    assert isinstance(latest, Mapping)
    package_url = _select_package_url(latest, source_name)
    if not package_url:
        raise DataUpError("latest metadata missing package_url")
    package_name = str(latest.get("package_name") or PurePosixPath(package_url).name or "dataup_package.zip")
    package_name = re.sub(r"[^A-Za-z0-9._\-\u4e00-\u9fff]+", "_", package_name)[:180] or "dataup_package.zip"
    dest_dir.mkdir(parents=True, exist_ok=True)
    out = dest_dir / package_name
    req = urllib.request.Request(package_url, headers={"User-Agent": "Linyuanzhe-DataUp/0.1"}, method="GET")
    with urllib.request.urlopen(req, timeout=30) as resp:
        raw = resp.read(128 * 1024 * 1024)
    out.write_bytes(raw)
    expected = str(latest.get("sha256") or "").strip().lower()
    actual = _sha256_file(out)
    if expected and expected != actual:
        try:
            out.unlink()
        except OSError as exc:
            _cleanup_error = _safe_text(exc, 120)
        raise DataUpError("downloaded package sha256 mismatch")
    return out


def _make_backup(root: Path, plan: PackagePlan) -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = root / "backups" / f"dataup_rollback_{stamp}"
    files_dir = backup / "files"
    files_dir.mkdir(parents=True, exist_ok=True)
    records = []
    for item in plan.files:
        target = root / item.path
        if target.exists() and target.is_file():
            dest = files_dir / item.path
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(target, dest)
            records.append({"path": item.path, "existed": True, "sha256": _sha256_file(target)})
        else:
            records.append({"path": item.path, "existed": False, "sha256": ""})
    manifest = {
        "schema": "tiangong.dataup.rollback.v1",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "package_id": plan.package_id,
        "version": plan.version,
        "records": records,
    }
    (backup / "rollback_manifest.json").write_text(_json_dumps(manifest), encoding="utf-8")
    return backup


def rollback(root: Path, backup: Path) -> dict[str, Any]:
    root = root.expanduser().resolve()
    backup = backup.expanduser().resolve()
    manifest_path = backup / "rollback_manifest.json"
    if not manifest_path.exists():
        raise DataUpError("rollback_manifest.json missing")
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    records = data.get("records", []) if isinstance(data, dict) else []
    restored = []
    removed = []
    for rec in records:
        if not isinstance(rec, Mapping):
            continue
        rel = _normalize_rel_path(rec.get("path"))
        target = root / rel
        if rec.get("existed"):
            src = backup / "files" / rel
            if src.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, target)
                restored.append(rel)
        else:
            if target.exists() and target.is_file():
                target.unlink()
                removed.append(rel)
    return {"ok": True, "backup": str(backup), "restored": restored, "removed_new_files": removed}


def _extract_payload_and_apply(package_path: Path, root: Path, plan: PackagePlan) -> None:
    with zipfile.ZipFile(package_path, "r") as zf:
        for item in plan.files:
            raw = zf.read(item.source)
            target = root / item.path
            target.parent.mkdir(parents=True, exist_ok=True)
            tmp = target.with_suffix(target.suffix + ".dataup_tmp")
            tmp.write_bytes(raw)
            os.replace(tmp, target)


def _internal_secret_scan(root: Path) -> tuple[bool, list[str]]:
    hits: list[str] = []
    for base in (root / "frontend", root / "desktop", root / "scripts", root / "docs", root / "01_启动入口"):
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if not path.is_file() or path.stat().st_size > 2 * 1024 * 1024:
                continue
            if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".ico", ".zip", ".pyc"}:
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            for pat in SENSITIVE_PATTERNS:
                if pat.search(text):
                    hits.append(str(path.relative_to(root)))
                    break
    return not hits, hits[:20]


def run_post_checks(root: Path, *, skip_post_checks: bool = False) -> dict[str, Any]:
    if skip_post_checks:
        return {"ok": True, "skipped": True, "checks": []}
    checks: list[dict[str, Any]] = []
    targets = [str(p) for p in ("frontend", "desktop", "scripts") if (root / p).exists()]
    if targets:
        proc = subprocess.run([sys.executable, "-m", "compileall", "-q", *targets], cwd=str(root), text=True, capture_output=True, timeout=180)
        checks.append({"name": "compileall", "ok": proc.returncode == 0, "returncode": proc.returncode, "output_tail": _safe_text((proc.stdout or "") + (proc.stderr or ""), 500)})
    scan_script = root / "scripts" / "scan_l659.py"
    if scan_script.exists():
        proc = subprocess.run([sys.executable, str(scan_script)], cwd=str(root), text=True, capture_output=True, timeout=120)
        checks.append({"name": "scan_l659", "ok": proc.returncode == 0, "returncode": proc.returncode, "output_tail": _safe_text((proc.stdout or "") + (proc.stderr or ""), 500)})
    else:
        ok, hits = _internal_secret_scan(root)
        checks.append({"name": "internal_secret_scan", "ok": ok, "hits": hits})
    preflight = root / "scripts" / "desktop_bundle_preflight_l671.py"
    if preflight.exists() and (root / "backend" / "project" / "run_agent.py").exists():
        proc = subprocess.run([sys.executable, str(preflight)], cwd=str(root), text=True, capture_output=True, timeout=240)
        checks.append({"name": "desktop_bundle_preflight_l671", "ok": proc.returncode == 0, "returncode": proc.returncode, "output_tail": _safe_text((proc.stdout or "") + (proc.stderr or ""), 800)})
    ok_all = all(c.get("ok") for c in checks) if checks else True
    return {"ok": ok_all, "skipped": False, "checks": checks}


def apply_package(package_path: Path, root: Path, *, yes: bool = False, source_kind: str = "local_package", skip_post_checks: bool = False) -> dict[str, Any]:
    root = root.expanduser().resolve()
    plan = plan_package(package_path, root, source_kind=source_kind)
    if not plan.ok:
        return {"ok": False, "stage": "plan", "plan": _plan_to_dict(plan)}
    if not yes:
        return {"ok": False, "stage": "confirmation_required", "message": "apply requires --yes after UI/CLI confirmation", "plan": _plan_to_dict(plan)}
    backup = _make_backup(root, plan)
    try:
        _extract_payload_and_apply(package_path, root, plan)
        post = run_post_checks(root, skip_post_checks=skip_post_checks)
        if not post.get("ok"):
            rb = rollback(root, backup)
            return {"ok": False, "stage": "post_check_failed_rolled_back", "plan": _plan_to_dict(plan), "backup": str(backup), "post_checks": post, "rollback": rb}
        return {"ok": True, "stage": "applied", "plan": _plan_to_dict(plan), "backup": str(backup), "post_checks": post, "restart_required": True}
    except Exception as exc:
        rb = rollback(root, backup)
        return {"ok": False, "stage": "apply_failed_rolled_back", "error": _safe_text(exc, 500), "plan": _plan_to_dict(plan), "backup": str(backup), "rollback": rb}


def _build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Linyuanzhe DataUp safe updater")
    p.add_argument("--root", default=str(Path(__file__).resolve().parents[1]), help="package root")
    p.add_argument("--source", choices=["auto", "gitee", "github"], default="auto")
    p.add_argument("--latest-url", default="")
    p.add_argument("--package", default="", help="local DataUp zip")
    p.add_argument("--check", action="store_true", help="check latest metadata only")
    p.add_argument("--dry-run", action="store_true", help="validate and plan package without applying")
    p.add_argument("--apply", action="store_true", help="apply package after validation and rollback creation")
    p.add_argument("--yes", action="store_true", help="confirmation flag required for apply")
    p.add_argument("--skip-post-checks", action="store_true", help="test-only: skip post checks")
    p.add_argument("--report", default="", help="write JSON report to this path")
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    root = Path(args.root).expanduser().resolve()
    report_path = Path(args.report).expanduser().resolve() if args.report else None
    started = time.time()
    payload: dict[str, Any] = {
        "schema": SCHEMA,
        "version_label": VERSION_LABEL,
        "checked_at": datetime.now().isoformat(timespec="seconds"),
        "root_digest": _sha256_bytes(str(root).encode("utf-8", errors="ignore"))[:16],
        "source_repositories": {"gitee": GITEE_REPOSITORY, "github": GITHUB_REPOSITORY},
    }
    try:
        package = Path(args.package).expanduser().resolve() if args.package else None
        latest_result: dict[str, Any] | None = None
        source_kind = "local_package"
        if args.check or package is None:
            latest_result = check_latest(args.source, latest_url=args.latest_url)
            payload["latest_check"] = latest_result
            source_kind = f"online_{latest_result.get('source_name', args.source)}" if latest_result.get("ok") else "online_unavailable"
            if args.check and not args.apply and not args.dry_run and package is None:
                payload["ok"] = bool(latest_result.get("ok"))
                payload["stage"] = "latest_check"
                out = _write_report(root, "dataup_last_update_report_l6717.json", payload, report_path)
                payload["report"] = str(out)
                print(_json_dumps(payload))
                return 0 if payload["ok"] else 1
        if package is None:
            if latest_result is None or not latest_result.get("ok"):
                raise DataUpError("cannot download package because latest metadata is unavailable")
            with tempfile.TemporaryDirectory(prefix="linyuanzhe_dataup_download_") as td:
                downloaded = download_package_from_latest(latest_result, Path(td))
                if args.apply:
                    result = apply_package(downloaded, root, yes=args.yes, source_kind=source_kind, skip_post_checks=args.skip_post_checks)
                else:
                    plan = plan_package(downloaded, root, source_kind=source_kind)
                    result = {"ok": plan.ok, "stage": "dry_run", "plan": _plan_to_dict(plan)}
                payload.update(result)
        elif args.apply:
            payload.update(apply_package(package, root, yes=args.yes, source_kind=source_kind, skip_post_checks=args.skip_post_checks))
        else:
            plan = plan_package(package, root, source_kind=source_kind)
            payload.update({"ok": plan.ok, "stage": "dry_run", "plan": _plan_to_dict(plan)})
    except Exception as exc:
        payload.update({"ok": False, "stage": "error", "error": _safe_text(exc, 1000)})
    payload["latency_ms"] = int((time.time() - started) * 1000)
    out = _write_report(root, "dataup_last_update_report_l6717.json", payload, report_path)
    payload["report"] = str(out)
    print(_json_dumps(payload))
    return 0 if payload.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
