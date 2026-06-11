"""
L6.70.2-CodeX R10: Worktree / rollback / delivery packaging clean candidate tools.

Scope:
- Candidate-only implementation for checkpointing, rollback planning, restore, and local delivery packaging.
- No Runtime registration, no v2 main-chain modification, no v1 source import/copy.
- Standard library only; git is probed via subprocess only when explicitly requested.

Design principle:
The LLM remains the engineering decision maker. These tools only provide reversible
workspace operations, local artifacts, evidence, and next-action hints.
"""
from __future__ import annotations

import fnmatch
import hashlib
import json
import os
import re
import shutil
import subprocess
import time
import uuid
import zipfile
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

DEFAULT_EXCLUDES = {
    ".git",
    ".codex_snapshots",
    ".codex_delivery",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "node_modules",
    "dist",
    "build",
    ".linyuanzhe",
    "reports",
    ".r21_adapter_smoke_workspace",
    "document_contexts",
    "file_handoffs",
    "model_profiles",
    "prompt_trace",
    "tasks",
}
TEXT_SECRET_PATTERNS = [
    re.compile(r"(?i)(api[_-]?key|secret|token|password)\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{16,}"),
    re.compile(r"A" r"KIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
]
MAX_FILE_BYTES_DEFAULT = 2 * 1024 * 1024


def _now_ms() -> int:
    return int(time.time() * 1000)


def _hint(next_tool: str, reason: str, confidence: float = 0.8, options: Optional[List[str]] = None) -> Dict[str, Any]:
    return {
        "next_tool": next_tool,
        "reason": reason,
        "confidence": confidence,
        "options": options or [],
        "llm_final_decision_required": True,
    }


def _envelope(tool: str, status: str, result: Dict[str, Any], evidence: Optional[List[Dict[str, Any]]] = None,
              next_action: Optional[Dict[str, Any]] = None, warnings: Optional[List[str]] = None,
              risk_level: Optional[str] = None) -> Dict[str, Any]:
    if risk_level is None:
        risk_level = "A4" if status == "blocked" else "A2"
    return {
        "tool_name": tool,
        "status": status,
        "r1_next_action_hint": next_action or _hint("handoff_digest", "No next action was provided.", 0.3),
        "r2_execution_protection": {
            "risk_level": risk_level,
            "requires_confirmation": status == "blocked" and risk_level == "A5",
            "protected_keys": ["rollback", "handoff", "state_recover", "lease_extend"],
            "a5_hard_block_only": True,
        },
        "evidence": evidence or [],
        "warnings": warnings or [],
        "result": result,
    }


def _safe_rel_path(path: str) -> Path:
    if not isinstance(path, str) or not path.strip():
        raise ValueError("path must be a non-empty string")
    normalized = path.replace("\\", "/").strip()
    p = Path(normalized)
    if p.is_absolute():
        raise ValueError(f"absolute path is not allowed: {path}")
    if any(part in ("..", "") for part in p.parts):
        raise ValueError(f"path traversal or empty segment is not allowed: {path}")
    return p


def _root(repo_root: str | Path) -> Path:
    root = Path(repo_root).resolve()
    if not root.exists() or not root.is_dir():
        raise ValueError(f"repo_root must be an existing directory: {repo_root}")
    return root


def _workspace_path(repo_root: str | Path, rel_path: str) -> Path:
    root = _root(repo_root)
    target = (root / _safe_rel_path(rel_path)).resolve()
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"target escapes workspace: {rel_path}") from exc
    return target


def _rel(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> Optional[str]:
    if not path.exists() or not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _is_binary(path: Path, sample_size: int = 4096) -> bool:
    try:
        sample = path.read_bytes()[:sample_size]
    except OSError:
        return True
    return b"\x00" in sample


def _should_exclude(rel_path: str, exclude_dirs: Iterable[str], include_globs: Optional[Sequence[str]] = None,
                    exclude_globs: Optional[Sequence[str]] = None) -> bool:
    parts = Path(rel_path).parts
    if any(part in exclude_dirs for part in parts):
        return True
    if exclude_globs and any(fnmatch.fnmatch(rel_path, pattern) for pattern in exclude_globs):
        return True
    if include_globs:
        return not any(fnmatch.fnmatch(rel_path, pattern) for pattern in include_globs)
    return False


def _iter_files(repo_root: str | Path, include_globs: Optional[Sequence[str]] = None,
                exclude_globs: Optional[Sequence[str]] = None,
                exclude_dirs: Optional[Iterable[str]] = None) -> List[Path]:
    root = _root(repo_root)
    excludes = set(exclude_dirs or DEFAULT_EXCLUDES)
    files: List[Path] = []
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        rel_path = _rel(root, p)
        if _should_exclude(rel_path, excludes, include_globs, exclude_globs) or p.suffix.lower() in {".pyc", ".pyo"} or p.name == ".DS_Store":
            continue
        files.append(p)
    files.sort(key=lambda x: _rel(root, x))
    return files


def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, data: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _copy_file_atomic(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    tmp = dst.with_name(dst.name + f".tmp-{uuid.uuid4().hex}")
    shutil.copy2(src, tmp)
    os.replace(tmp, dst)


def _safe_delete_file(path: Path, root: Path) -> None:
    resolved = path.resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError(f"refusing to delete outside workspace: {path}") from exc
    if resolved.exists() and resolved.is_file():
        resolved.unlink()


def _run_git(repo_root: Path, args: Sequence[str], timeout_seconds: int = 10) -> Dict[str, Any]:
    cmd = ["git", "-C", str(repo_root), *args]
    try:
        completed = subprocess.run(
            cmd,
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
        )
        return {
            "command": " ".join(cmd),
            "exit_code": completed.returncode,
            "stdout": completed.stdout[-4000:],
            "stderr": completed.stderr[-4000:],
        }
    except FileNotFoundError:
        return {"command": " ".join(cmd), "exit_code": 127, "stdout": "", "stderr": "git not found"}
    except subprocess.TimeoutExpired as exc:
        return {"command": " ".join(cmd), "exit_code": 124, "stdout": exc.stdout or "", "stderr": "git command timed out"}


def _scan_secret_text(path: Path) -> List[str]:
    if _is_binary(path):
        return []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")[:200000]
    except OSError:
        return []
    hits: List[str] = []
    for pattern in TEXT_SECRET_PATTERNS:
        if pattern.search(text):
            hits.append(pattern.pattern)
    return hits


def workspace_snapshot(repo_root: str | Path, snapshot_id: Optional[str] = None,
                       include_globs: Optional[Sequence[str]] = None,
                       exclude_globs: Optional[Sequence[str]] = None,
                       max_file_bytes: int = MAX_FILE_BYTES_DEFAULT,
                       snapshot_dir: Optional[str | Path] = None) -> Dict[str, Any]:
    """Create a reversible local snapshot inside the workspace or an explicit snapshot directory."""
    root = _root(repo_root)
    sid = snapshot_id or f"snapshot-{time.strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:8]}"
    base = Path(snapshot_dir).resolve() if snapshot_dir else root / ".codex_snapshots"
    target_root = base / sid
    files_root = target_root / "files"
    manifest_path = target_root / "snapshot_manifest.json"
    if target_root.exists():
        return _envelope(
            "workspace_snapshot",
            "blocked",
            {"snapshot_id": sid, "reason": "snapshot already exists", "manifest_path": str(manifest_path)},
            next_action=_hint("rollback_plan", "Snapshot id collision; choose a new id or inspect existing snapshot.", 0.7),
        )

    entries: List[Dict[str, Any]] = []
    skipped: List[Dict[str, Any]] = []
    for src in _iter_files(root, include_globs=include_globs, exclude_globs=exclude_globs):
        rel_path = _rel(root, src)
        size = src.stat().st_size
        if size > max_file_bytes:
            skipped.append({"path": rel_path, "reason": "file_too_large", "size_bytes": size})
            continue
        dst = files_root / rel_path
        _copy_file_atomic(src, dst)
        entries.append({
            "path": rel_path,
            "existed_at_snapshot": True,
            "size_bytes": size,
            "sha256": _sha256_file(src),
            "snapshot_file": dst.relative_to(target_root).as_posix(),
            "binary": _is_binary(src),
        })

    manifest = {
        "schema": "code_x.workspace_snapshot.v1",
        "snapshot_id": sid,
        "created_at_ms": _now_ms(),
        "repo_root": str(root),
        "snapshot_root": str(target_root),
        "file_count": len(entries),
        "skipped_count": len(skipped),
        "entries": entries,
        "skipped": skipped,
        "r2_policy": {
            "risk_level": "A2",
            "rollback_key_never_lock": True,
            "state_recover_key_never_lock": True,
        },
    }
    _write_json(manifest_path, manifest)
    return _envelope(
        "workspace_snapshot",
        "ok",
        {
            "snapshot_id": sid,
            "snapshot_root": str(target_root),
            "manifest_path": str(manifest_path),
            "file_count": len(entries),
            "skipped_count": len(skipped),
        },
        evidence=[{"kind": "snapshot_manifest", "path": str(manifest_path), "file_count": len(entries)}],
        next_action=_hint("workspace_patch_applier", "Snapshot is ready; LLM may apply a workspace patch or prepare a rollback plan.", 0.85,
                          ["workspace_patch_applier", "rollback_plan", "handoff_digest"]),
    )


def git_worktree_mode(repo_root: str | Path, mode: str = "probe", worktree_dir: Optional[str | Path] = None,
                      branch_name: Optional[str] = None, timeout_seconds: int = 10) -> Dict[str, Any]:
    """Probe or create a git worktree candidate. Creation is explicit and remains local."""
    root = _root(repo_root)
    if mode not in {"probe", "create"}:
        return _envelope(
            "git_worktree_mode",
            "blocked",
            {"reason": "unsupported_mode", "mode": mode, "supported_modes": ["probe", "create"]},
            next_action=_hint("workspace_snapshot", "Use snapshot fallback when worktree mode is not available.", 0.65),
        )
    rev = _run_git(root, ["rev-parse", "--show-toplevel"], timeout_seconds)
    is_git_repo = rev["exit_code"] == 0
    status = _run_git(root, ["status", "--short"], timeout_seconds) if is_git_repo else None
    base_result: Dict[str, Any] = {
        "is_git_repo": is_git_repo,
        "git_probe": rev,
        "worktree_supported": False,
        "fallback": "workspace_snapshot",
    }
    if not is_git_repo:
        return _envelope(
            "git_worktree_mode",
            "ok",
            base_result | {"decision": "snapshot_fallback", "reason": "not_a_git_repository"},
            evidence=[{"kind": "git_probe", "exit_code": rev["exit_code"], "stderr": rev.get("stderr", "")[-300:]}],
            next_action=_hint("workspace_snapshot", "Repository is not git-backed; use workspace snapshot for rollback safety.", 0.9),
        )
    list_result = _run_git(root, ["worktree", "list", "--porcelain"], timeout_seconds)
    base_result.update({
        "worktree_supported": list_result["exit_code"] == 0,
        "worktree_list": list_result,
        "dirty_files": [line for line in (status or {}).get("stdout", "").splitlines() if line.strip()],
    })
    if mode == "probe":
        return _envelope(
            "git_worktree_mode",
            "ok",
            base_result | {"decision": "worktree_available" if base_result["worktree_supported"] else "snapshot_fallback"},
            evidence=[{"kind": "git_worktree_probe", "exit_code": list_result["exit_code"]}],
            next_action=_hint("workspace_snapshot", "Probe complete; take a snapshot before patching or create an isolated worktree if requested.", 0.8,
                              ["workspace_snapshot", "git_worktree_mode", "patch_plan_generator"]),
        )
    if not base_result["worktree_supported"]:
        return _envelope(
            "git_worktree_mode",
            "blocked",
            base_result | {"reason": "git_worktree_not_supported"},
            next_action=_hint("workspace_snapshot", "Worktree creation unavailable; use snapshot fallback.", 0.85),
        )
    if not worktree_dir:
        return _envelope(
            "git_worktree_mode",
            "blocked",
            base_result | {"reason": "worktree_dir_required"},
            next_action=_hint("workspace_snapshot", "Without an explicit worktree path, use snapshot fallback.", 0.7),
        )
    target = Path(worktree_dir).resolve()
    parent = target.parent
    if not parent.exists():
        return _envelope(
            "git_worktree_mode",
            "blocked",
            base_result | {"reason": "worktree_parent_missing", "worktree_dir": str(target)},
            next_action=_hint("workspace_snapshot", "Worktree parent does not exist; use snapshot fallback or create parent manually.", 0.7),
        )
    if target.exists():
        return _envelope(
            "git_worktree_mode",
            "blocked",
            base_result | {"reason": "worktree_dir_already_exists", "worktree_dir": str(target)},
            next_action=_hint("workspace_snapshot", "Worktree target exists; select another path or use snapshot fallback.", 0.7),
        )
    args = ["worktree", "add"]
    if branch_name:
        safe_branch = re.sub(r"[^A-Za-z0-9._/-]", "-", branch_name)[:80]
        args.extend(["-b", safe_branch])
    else:
        args.append("--detach")
    args.extend([str(target), "HEAD"])
    create_result = _run_git(root, args, timeout_seconds)
    status_name = "ok" if create_result["exit_code"] == 0 else "blocked"
    return _envelope(
        "git_worktree_mode",
        status_name,
        base_result | {"decision": "created" if status_name == "ok" else "create_failed", "worktree_dir": str(target), "create_result": create_result},
        evidence=[{"kind": "git_worktree_create", "exit_code": create_result["exit_code"], "stderr": create_result.get("stderr", "")[-500:]}],
        next_action=_hint("workspace_snapshot" if status_name == "blocked" else "patch_plan_generator",
                          "Worktree creation finished; continue with patch planning if successful, otherwise snapshot fallback.", 0.75),
        risk_level="A3",
    )


def rollback_plan(repo_root: str | Path, snapshot_manifest_path: Optional[str | Path] = None,
                  patch_manifest_path: Optional[str | Path] = None,
                  changed_files: Optional[Sequence[str]] = None) -> Dict[str, Any]:
    """Create a dry rollback plan from a snapshot manifest, patch manifest, or explicit changed files."""
    root = _root(repo_root)
    operations: List[Dict[str, Any]] = []
    evidence: List[Dict[str, Any]] = []
    warnings: List[str] = []

    snapshot_manifest: Optional[Dict[str, Any]] = None
    if snapshot_manifest_path:
        smp = Path(snapshot_manifest_path).resolve()
        snapshot_manifest = _load_json(smp)
        evidence.append({"kind": "snapshot_manifest", "path": str(smp)})
        snapshot_root = Path(snapshot_manifest.get("snapshot_root", smp.parent)).resolve()
        entries_by_path = {str(e.get("path")): e for e in snapshot_manifest.get("entries", [])}
        targets = list(changed_files or entries_by_path.keys())
        for rel_path in targets:
            target = _workspace_path(root, rel_path)
            entry = entries_by_path.get(rel_path)
            if entry:
                operations.append({
                    "op": "restore_file",
                    "path": rel_path,
                    "target": str(target),
                    "source": str(snapshot_root / str(entry["snapshot_file"])),
                    "snapshot_sha256": entry.get("sha256"),
                    "current_sha256": _sha256_file(target),
                })
            else:
                operations.append({
                    "op": "delete_untracked_file",
                    "path": rel_path,
                    "target": str(target),
                    "reason": "not_present_in_snapshot_manifest",
                    "current_sha256": _sha256_file(target),
                })
    elif patch_manifest_path:
        pmp = Path(patch_manifest_path).resolve()
        patch_manifest = _load_json(pmp)
        evidence.append({"kind": "patch_manifest", "path": str(pmp)})
        for f in patch_manifest.get("files", []) or patch_manifest.get("changed_files", []):
            rel_path = str(f.get("path") if isinstance(f, Mapping) else f)
            operations.append({
                "op": "restore_from_patch_before_state",
                "path": rel_path,
                "target": str(_workspace_path(root, rel_path)),
                "before_sha256": f.get("before_sha256") if isinstance(f, Mapping) else None,
                "note": "requires before-state content or snapshot for actual restore",
            })
        warnings.append("patch manifest alone may not contain file bodies; restore_checkpoint needs snapshot source for actual restoration")
    elif changed_files:
        for rel_path in changed_files:
            operations.append({
                "op": "manual_review_required",
                "path": str(rel_path).replace("\\", "/"),
                "target": str(_workspace_path(root, str(rel_path))),
                "reason": "changed_files_without_snapshot_or_patch_manifest",
            })
        warnings.append("changed files without snapshot cannot be restored automatically")
    else:
        return _envelope(
            "rollback_plan",
            "blocked",
            {"reason": "no_rollback_source", "operations": []},
            next_action=_hint("workspace_snapshot", "Create a snapshot before patching so rollback can be planned.", 0.9),
        )

    status = "ok" if operations else "blocked"
    return _envelope(
        "rollback_plan",
        status,
        {
            "operation_count": len(operations),
            "operations": operations,
            "requires_llm_final_decision": True,
            "can_restore_automatically": bool(snapshot_manifest and operations),
        },
        evidence=evidence,
        warnings=warnings,
        next_action=_hint("restore_checkpoint" if snapshot_manifest else "handoff_digest",
                          "Rollback plan is ready; LLM decides whether to restore, continue repair, or handoff.", 0.85,
                          ["restore_checkpoint", "repair_loop_planner", "handoff_digest"]),
    )


def restore_checkpoint(repo_root: str | Path, snapshot_manifest_path: str | Path,
                       changed_files: Optional[Sequence[str]] = None,
                       dry_run: bool = True) -> Dict[str, Any]:
    """Restore files from a workspace snapshot manifest. Dry-run is default."""
    root = _root(repo_root)
    smp = Path(snapshot_manifest_path).resolve()
    manifest = _load_json(smp)
    snapshot_root = Path(manifest.get("snapshot_root", smp.parent)).resolve()
    entries_by_path = {str(e.get("path")): e for e in manifest.get("entries", [])}
    targets = list(changed_files or entries_by_path.keys())
    restored: List[Dict[str, Any]] = []
    deleted: List[Dict[str, Any]] = []
    missing_sources: List[Dict[str, Any]] = []

    for rel_path in targets:
        rel_path = str(rel_path).replace("\\", "/")
        target = _workspace_path(root, rel_path)
        entry = entries_by_path.get(rel_path)
        if entry:
            source = snapshot_root / str(entry["snapshot_file"])
            if not source.exists():
                missing_sources.append({"path": rel_path, "source": str(source), "reason": "snapshot_source_missing"})
                continue
            before_restore = _sha256_file(target)
            if not dry_run:
                _copy_file_atomic(source, target)
            restored.append({
                "path": rel_path,
                "source": str(source),
                "target": str(target),
                "before_restore_sha256": before_restore,
                "snapshot_sha256": entry.get("sha256"),
                "after_restore_sha256": _sha256_file(target) if not dry_run else entry.get("sha256"),
                "dry_run": dry_run,
            })
        else:
            before_delete = _sha256_file(target)
            if not dry_run:
                _safe_delete_file(target, root)
            deleted.append({
                "path": rel_path,
                "target": str(target),
                "before_delete_sha256": before_delete,
                "dry_run": dry_run,
                "reason": "not_present_at_snapshot",
            })
    status = "blocked" if missing_sources else "ok"
    return _envelope(
        "restore_checkpoint",
        status,
        {
            "snapshot_id": manifest.get("snapshot_id"),
            "dry_run": dry_run,
            "restored_count": len(restored),
            "deleted_count": len(deleted),
            "missing_source_count": len(missing_sources),
            "restored": restored,
            "deleted": deleted,
            "missing_sources": missing_sources,
        },
        evidence=[{"kind": "snapshot_manifest", "path": str(smp)}],
        next_action=_hint("pytest_runner" if not dry_run and status == "ok" else "rollback_plan",
                          "Restore checkpoint completed or previewed; validate if applied, otherwise review rollback plan.", 0.8,
                          ["pytest_runner", "handoff_digest", "rollback_plan"]),
        risk_level="A3",
    )


def delivery_candidate_packager(repo_root: str | Path, include_paths: Optional[Sequence[str]] = None,
                                package_id: Optional[str] = None,
                                output_dir: Optional[str | Path] = None,
                                include_manifest_note: str = "Code-X local delivery candidate") -> Dict[str, Any]:
    """Create a local delivery candidate directory from explicit files or all safe repo files."""
    root = _root(repo_root)
    pid = package_id or f"delivery-{time.strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:8]}"
    base = Path(output_dir).resolve() if output_dir else root / ".codex_delivery"
    package_root = base / pid
    if package_root.exists():
        return _envelope(
            "delivery_candidate_packager",
            "blocked",
            {"package_id": pid, "reason": "package already exists", "package_root": str(package_root)},
            next_action=_hint("zip_delivery_packager", "Package exists; zip it if it is the intended candidate or choose another package id.", 0.65),
        )

    selected: List[Path] = []
    if include_paths:
        for rel_path in include_paths:
            target = _workspace_path(root, rel_path)
            if target.exists() and target.is_file():
                selected.append(target)
    else:
        selected = _iter_files(root)
    selected = sorted(set(selected), key=lambda x: _rel(root, x))

    packaged: List[Dict[str, Any]] = []
    blocked_secret_hits: List[Dict[str, Any]] = []
    for src in selected:
        rel_path = _rel(root, src)
        secret_hits = _scan_secret_text(src)
        if secret_hits:
            blocked_secret_hits.append({"path": rel_path, "patterns": secret_hits})
            continue
        dst = package_root / "files" / rel_path
        _copy_file_atomic(src, dst)
        packaged.append({
            "path": rel_path,
            "size_bytes": src.stat().st_size,
            "sha256": _sha256_file(src),
            "packaged_as": dst.relative_to(package_root).as_posix(),
        })

    manifest = {
        "schema": "code_x.delivery_candidate.v1",
        "package_id": pid,
        "created_at_ms": _now_ms(),
        "repo_root": str(root),
        "package_root": str(package_root),
        "note": include_manifest_note,
        "file_count": len(packaged),
        "blocked_secret_count": len(blocked_secret_hits),
        "files": packaged,
        "blocked_secret_hits": blocked_secret_hits,
        "llm_final_decision_required": True,
    }
    manifest_path = package_root / "delivery_manifest.json"
    readme_path = package_root / "README.md"
    _write_json(manifest_path, manifest)
    readme_path.write_text(
        f"# {pid}\n\n{include_manifest_note}\n\nFiles: {len(packaged)}\nBlocked secret hits: {len(blocked_secret_hits)}\n",
        encoding="utf-8",
    )
    status = "blocked" if blocked_secret_hits else "ok"
    return _envelope(
        "delivery_candidate_packager",
        status,
        {
            "package_id": pid,
            "package_root": str(package_root),
            "manifest_path": str(manifest_path),
            "file_count": len(packaged),
            "blocked_secret_count": len(blocked_secret_hits),
        },
        evidence=[{"kind": "delivery_manifest", "path": str(manifest_path), "file_count": len(packaged)}],
        next_action=_hint("zip_delivery_packager" if status == "ok" else "handoff_digest",
                          "Delivery candidate staged locally; zip if no secret block, otherwise handoff for review.", 0.85,
                          ["zip_delivery_packager", "handoff_digest"]),
        risk_level="A5" if blocked_secret_hits else "A2",
    )


def zip_delivery_packager(package_root: str | Path, output_zip: Optional[str | Path] = None,
                          overwrite: bool = False) -> Dict[str, Any]:
    """Zip a local delivery candidate directory."""
    root = Path(package_root).resolve()
    if not root.exists() or not root.is_dir():
        return _envelope(
            "zip_delivery_packager",
            "blocked",
            {"reason": "package_root_missing", "package_root": str(root)},
            next_action=_hint("delivery_candidate_packager", "Create a delivery candidate directory before zipping.", 0.9),
        )
    manifest_path = root / "delivery_manifest.json"
    if manifest_path.exists():
        manifest = _load_json(manifest_path)
        if manifest.get("blocked_secret_count", 0):
            return _envelope(
                "zip_delivery_packager",
                "blocked",
                {"reason": "secret_scan_block", "manifest_path": str(manifest_path), "blocked_secret_count": manifest.get("blocked_secret_count")},
                evidence=[{"kind": "delivery_manifest", "path": str(manifest_path)}],
                next_action=_hint("handoff_digest", "Secret scan blocked packaging; LLM should inspect and decide remediation.", 0.9),
                risk_level="A5",
            )
    zip_path = Path(output_zip).resolve() if output_zip else root.with_suffix(".zip")
    if zip_path.exists() and not overwrite:
        return _envelope(
            "zip_delivery_packager",
            "blocked",
            {"reason": "output_zip_exists", "output_zip": str(zip_path)},
            next_action=_hint("handoff_digest", "Zip exists; choose overwrite explicitly or deliver existing artifact.", 0.65),
        )
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    files: List[Dict[str, Any]] = []
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for src in sorted([p for p in root.rglob("*") if p.is_file()], key=lambda x: x.relative_to(root).as_posix()):
            rel_path = src.relative_to(root).as_posix()
            if _should_exclude(rel_path, DEFAULT_EXCLUDES) or src.suffix.lower() in {".pyc", ".pyo"} or src.name == ".DS_Store":
                continue
            zf.write(src, arcname=f"{root.name}/{rel_path}")
            files.append({"path": rel_path, "size_bytes": src.stat().st_size, "sha256": _sha256_file(src)})
    return _envelope(
        "zip_delivery_packager",
        "ok",
        {
            "package_root": str(root),
            "output_zip": str(zip_path),
            "zip_sha256": _sha256_file(zip_path),
            "file_count": len(files),
            "files": files,
        },
        evidence=[{"kind": "zip_artifact", "path": str(zip_path), "sha256": _sha256_file(zip_path)}],
        next_action=_hint("handoff_digest", "Zip delivery artifact is ready; generate handoff summary with changed files and validation status.", 0.9,
                          ["handoff_digest", "delivery_candidate_packager"]),
    )
