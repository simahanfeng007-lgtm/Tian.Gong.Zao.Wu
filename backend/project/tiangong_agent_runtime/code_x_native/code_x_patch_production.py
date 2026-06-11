
"""
L6.70.2-CodeX R7: Patch production clean candidate tools.

Scope:
- Candidate-only implementation for workspace patch production.
- No Runtime registration, no v2 main-chain modification, no external executor.
- No v1 source import/copy. Standard library only.

Design principle:
The LLM remains the final engineering decision maker. These tools only create,
preview, validate, apply, and manifest patch artifacts inside an explicit
workspace root.
"""
from __future__ import annotations

import difflib
import hashlib
import json
import os
import re
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Optional, Sequence, Tuple

TEXT_ENCODINGS = ("utf-8", "utf-8-sig")
SUPPORTED_EDIT_TYPES = {"replace_text", "replace_range", "append_text", "create_file"}


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
              next_action: Optional[Dict[str, Any]] = None, warnings: Optional[List[str]] = None) -> Dict[str, Any]:
    return {
        "tool_name": tool,
        "status": status,
        "r1_next_action_hint": next_action or _hint("handoff_digest", "No next action was provided.", 0.3),
        "r2_execution_protection": {
            "risk_level": "A2" if status != "blocked" else "A4",
            "requires_confirmation": False,
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


def _workspace_path(repo_root: str | Path, rel_path: str) -> Path:
    root = Path(repo_root).resolve()
    target = (root / _safe_rel_path(rel_path)).resolve()
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"target escapes workspace: {rel_path}") from exc
    return target


def _read_text(path: Path) -> Tuple[str, str]:
    raw = path.read_bytes()
    if b"\x00" in raw[:4096]:
        raise ValueError(f"binary file is not supported: {path}")
    last_error: Optional[Exception] = None
    for enc in TEXT_ENCODINGS:
        try:
            return raw.decode(enc), enc
        except UnicodeDecodeError as exc:
            last_error = exc
    raise ValueError(f"unable to decode text file as utf-8: {path}") from last_error


def _detect_newline(text: str) -> str:
    crlf = text.count("\r\n")
    lf = text.count("\n") - crlf
    if crlf > lf:
        return "\r\n"
    return "\n"


def _write_text_atomic(path: Path, text: str, encoding: str = "utf-8") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + f".tmp-{uuid.uuid4().hex}")
    tmp.write_text(text, encoding=encoding, newline="")
    os.replace(tmp, path)


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> Optional[str]:
    if not path.exists():
        return None
    return _sha256_bytes(path.read_bytes())


def _file_state(repo_root: str | Path, rel_path: str) -> Dict[str, Any]:
    try:
        p = _workspace_path(repo_root, rel_path)
    except ValueError as exc:
        return {"path": rel_path, "valid": False, "error": str(exc)}
    return {
        "path": rel_path,
        "valid": True,
        "exists": p.exists(),
        "is_file": p.is_file() if p.exists() else False,
        "sha256": _sha256_file(p),
        "size_bytes": p.stat().st_size if p.exists() and p.is_file() else None,
    }


def _normalize_edit_unit(repo_root: str | Path, unit: Mapping[str, Any], index: int) -> Dict[str, Any]:
    edit_type = str(unit.get("edit_type", "")).strip()
    if edit_type not in SUPPORTED_EDIT_TYPES:
        raise ValueError(f"unsupported edit_type at #{index}: {edit_type}")
    rel_path = str(unit.get("path", "")).strip()
    target = _workspace_path(repo_root, rel_path)
    before_hash = _sha256_file(target)
    normalized: Dict[str, Any] = {
        "edit_id": str(unit.get("edit_id") or f"edit-{index+1:03d}"),
        "edit_type": edit_type,
        "path": rel_path.replace("\\", "/"),
        "intent": str(unit.get("intent") or "unspecified code edit"),
        "before_sha256": before_hash,
        "requires_existing_file": edit_type in {"replace_text", "replace_range", "append_text"},
        "creates_file": edit_type == "create_file",
    }
    for key in ("find", "replace", "replacement", "content", "text", "start_line", "end_line", "expected_occurrences"):
        if key in unit:
            normalized[key] = unit[key]
    if edit_type == "replace_text":
        if "find" not in normalized or "replace" not in normalized:
            raise ValueError(f"replace_text requires find and replace at #{index}")
        normalized["expected_occurrences"] = int(normalized.get("expected_occurrences", 1))
    elif edit_type == "replace_range":
        normalized["start_line"] = int(normalized.get("start_line", 0))
        normalized["end_line"] = int(normalized.get("end_line", 0))
        if normalized["start_line"] <= 0 or normalized["end_line"] < normalized["start_line"]:
            raise ValueError(f"replace_range requires valid 1-based start_line/end_line at #{index}")
        if "replacement" not in normalized:
            raise ValueError(f"replace_range requires replacement at #{index}")
    elif edit_type == "append_text":
        if "text" not in normalized:
            raise ValueError(f"append_text requires text at #{index}")
    elif edit_type == "create_file":
        if "content" not in normalized:
            raise ValueError(f"create_file requires content at #{index}")
    return normalized


def _apply_unit_to_text(original: str, unit: Mapping[str, Any]) -> str:
    edit_type = unit["edit_type"]
    newline = _detect_newline(original)
    if edit_type == "replace_text":
        find = str(unit["find"])
        replace = str(unit["replace"])
        expected = int(unit.get("expected_occurrences", 1))
        actual = original.count(find)
        if actual != expected:
            raise ValueError(f"replace_text occurrence mismatch for {unit['path']}: expected {expected}, actual {actual}")
        return original.replace(find, replace)
    if edit_type == "replace_range":
        start = int(unit["start_line"])
        end = int(unit["end_line"])
        lines = original.splitlines(keepends=True)
        if end > len(lines):
            raise ValueError(f"replace_range out of range for {unit['path']}: end_line={end}, line_count={len(lines)}")
        replacement = str(unit["replacement"])
        if replacement and not replacement.endswith(("\n", "\r\n")):
            replacement += newline
        repl_lines = replacement.splitlines(keepends=True)
        return "".join(lines[: start - 1] + repl_lines + lines[end:])
    if edit_type == "append_text":
        text = str(unit["text"])
        if original and not original.endswith(("\n", "\r\n")):
            original += newline
        return original + text
    raise ValueError(f"cannot apply edit type to existing text: {edit_type}")


def _simulate_apply(repo_root: str | Path, edit_units: Sequence[Mapping[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Return per-file before/after text without writing."""
    per_file: Dict[str, Dict[str, Any]] = {}
    for unit in edit_units:
        rel = str(unit["path"])
        target = _workspace_path(repo_root, rel)
        if rel not in per_file:
            if unit["edit_type"] == "create_file":
                before_text = ""
                encoding = "utf-8"
                existed_before = target.exists()
            else:
                before_text, encoding = _read_text(target)
                existed_before = True
            per_file[rel] = {
                "before_text": before_text,
                "after_text": before_text,
                "encoding": encoding,
                "existed_before": existed_before,
                "before_sha256": _sha256_file(target),
            }
        if unit["edit_type"] == "create_file":
            if per_file[rel]["after_text"] not in ("", None) or per_file[rel]["existed_before"]:
                raise ValueError(f"create_file target already has content or exists: {rel}")
            per_file[rel]["after_text"] = str(unit["content"])
        else:
            per_file[rel]["after_text"] = _apply_unit_to_text(per_file[rel]["after_text"], unit)
    for rel, state in per_file.items():
        state["after_sha256"] = _sha256_bytes(state["after_text"].encode(state["encoding"] or "utf-8"))
    return per_file


def patch_plan_generator(issue: str, localized_targets: Optional[Sequence[Mapping[str, Any]]] = None,
                         constraints: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
    """Generate an LLM-reviewable patch plan from an issue and localization evidence."""
    targets = list(localized_targets or [])
    plan_id = f"patch-plan-{uuid.uuid4().hex[:12]}"
    phases = [
        {"phase": "confirm_scope", "action": "review localization evidence and constraints", "required": True},
        {"phase": "plan_edit_units", "action": "convert target files/symbols to small edit units", "required": True},
        {"phase": "preview_diff", "action": "generate unified diff before writing", "required": True},
        {"phase": "apply_workspace_patch", "action": "write only inside explicit workspace root", "required": True},
        {"phase": "validate", "action": "run targeted tests/build/lint when available", "required": True},
        {"phase": "repair_or_manifest", "action": "on failure attribute cause; on success create patch manifest", "required": True},
    ]
    edit_candidates = []
    for i, t in enumerate(targets):
        edit_candidates.append({
            "candidate_id": f"candidate-{i+1:03d}",
            "path": t.get("path") or t.get("file") or "UNKNOWN",
            "symbol": t.get("symbol"),
            "line_range": t.get("line_range") or t.get("lines"),
            "reason": t.get("reason") or t.get("evidence") or "localized target from R6",
        })
    result = {
        "plan_id": plan_id,
        "issue_summary": issue.strip()[:1000],
        "constraints": dict(constraints or {}),
        "edit_candidates": edit_candidates,
        "phases": phases,
        "patch_contract": {
            "must_preview_diff_before_apply": True,
            "must_check_conflicts_before_apply": True,
            "must_record_before_after_hash": True,
            "must_emit_manifest": True,
            "workspace_only": True,
            "llm_final_decision_required": True,
        },
    }
    return _envelope(
        "patch_plan_generator",
        "ok",
        result,
        evidence=[{"type": "localized_targets", "count": len(targets)}],
        next_action=_hint("edit_unit_planner", "Patch plan is ready; convert candidate files/symbols into minimal edit units.", 0.88),
    )


def edit_unit_planner(repo_root: str | Path, patch_plan: Mapping[str, Any], proposed_edits: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    """Normalize proposed edits into auditable edit units with before hashes."""
    units: List[Dict[str, Any]] = []
    warnings: List[str] = []
    for i, unit in enumerate(proposed_edits):
        normalized = _normalize_edit_unit(repo_root, unit, i)
        if normalized["before_sha256"] is None and normalized["edit_type"] != "create_file":
            warnings.append(f"target does not exist before edit: {normalized['path']}")
        units.append(normalized)
    result = {
        "plan_id": patch_plan.get("plan_id"),
        "edit_unit_count": len(units),
        "edit_units": units,
        "ordering_rule": "apply in listed order; conflicts must be checked before write",
    }
    status = "ok" if not warnings else "needs_review"
    return _envelope(
        "edit_unit_planner",
        status,
        result,
        evidence=[{"type": "before_hashes", "count": len(units)}],
        warnings=warnings,
        next_action=_hint("conflict_detector", "Edit units are normalized; check file existence, hash, range, and occurrence conflicts before diff/apply.", 0.9),
    )


def conflict_detector(repo_root: str | Path, edit_units: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    """Detect patch conflicts without writing."""
    conflicts: List[Dict[str, Any]] = []
    checked: List[Dict[str, Any]] = []
    try:
        normalized = [_normalize_edit_unit(repo_root, u, i) for i, u in enumerate(edit_units)]
    except Exception as exc:
        return _envelope(
            "conflict_detector",
            "blocked",
            {"can_apply": False, "conflicts": [{"type": "schema_or_path_error", "message": str(exc)}], "checked": []},
            next_action=_hint("edit_unit_planner", "Edit unit schema/path is invalid; revise edit units before patching.", 0.94),
        )

    for unit in normalized:
        rel = unit["path"]
        target = _workspace_path(repo_root, rel)
        state = _file_state(repo_root, rel)
        checked.append(state)
        expected_hash = unit.get("before_sha256")
        current_hash = _sha256_file(target)
        if expected_hash is not None and current_hash != expected_hash:
            conflicts.append({"path": rel, "type": "hash_mismatch", "expected": expected_hash, "actual": current_hash})
            continue
        if unit["edit_type"] == "create_file":
            if target.exists():
                conflicts.append({"path": rel, "type": "target_exists", "message": "create_file target already exists"})
            continue
        if not target.exists() or not target.is_file():
            conflicts.append({"path": rel, "type": "missing_file", "message": "target file does not exist"})
            continue
        try:
            text, _ = _read_text(target)
            if unit["edit_type"] == "replace_text":
                actual = text.count(str(unit["find"]))
                expected = int(unit.get("expected_occurrences", 1))
                if actual != expected:
                    conflicts.append({"path": rel, "type": "occurrence_mismatch", "expected": expected, "actual": actual})
            elif unit["edit_type"] == "replace_range":
                line_count = len(text.splitlines())
                if int(unit["end_line"]) > line_count:
                    conflicts.append({"path": rel, "type": "range_out_of_bounds", "line_count": line_count, "end_line": unit["end_line"]})
        except Exception as exc:
            conflicts.append({"path": rel, "type": "read_or_validate_error", "message": str(exc)})
    can_apply = not conflicts
    return _envelope(
        "conflict_detector",
        "ok" if can_apply else "blocked",
        {"can_apply": can_apply, "conflicts": conflicts, "checked": checked, "edit_unit_count": len(normalized)},
        evidence=[{"type": "conflict_count", "count": len(conflicts)}],
        next_action=_hint("unified_diff_generator" if can_apply else "edit_unit_planner", "No conflicts detected; preview unified diff." if can_apply else "Conflicts detected; revise edit units before applying.", 0.91),
    )


def unified_diff_generator(repo_root: str | Path, edit_units: Sequence[Mapping[str, Any]], context_lines: int = 3) -> Dict[str, Any]:
    """Generate unified diff from edit units without writing."""
    normalized = [_normalize_edit_unit(repo_root, u, i) for i, u in enumerate(edit_units)]
    conflicts = conflict_detector(repo_root, normalized)["result"].get("conflicts", [])
    if conflicts:
        return _envelope(
            "unified_diff_generator",
            "blocked",
            {"diff": "", "conflicts": conflicts, "files": []},
            next_action=_hint("edit_unit_planner", "Diff preview blocked by conflicts; revise edit units.", 0.92),
        )
    per_file = _simulate_apply(repo_root, normalized)
    diff_parts: List[str] = []
    files: List[Dict[str, Any]] = []
    for rel, state in per_file.items():
        before_lines = state["before_text"].splitlines(keepends=True)
        after_lines = state["after_text"].splitlines(keepends=True)
        fromfile = f"a/{rel}" if state["existed_before"] else "/dev/null"
        tofile = f"b/{rel}"
        diff = difflib.unified_diff(before_lines, after_lines, fromfile=fromfile, tofile=tofile, n=context_lines)
        part = "".join(diff)
        diff_parts.append(part)
        files.append({
            "path": rel,
            "existed_before": state["existed_before"],
            "before_sha256": state["before_sha256"],
            "after_sha256": state["after_sha256"],
            "diff_lines": len(part.splitlines()),
        })
    full_diff = "".join(diff_parts)
    return _envelope(
        "unified_diff_generator",
        "ok",
        {"diff": full_diff, "files": files, "edit_unit_count": len(normalized)},
        evidence=[{"type": "diff_files", "count": len(files)}, {"type": "diff_line_count", "count": len(full_diff.splitlines())}],
        next_action=_hint("workspace_patch_applier", "Unified diff is ready; LLM may approve workspace apply if the diff matches intent.", 0.88),
    )


def before_after_hash(repo_root: str | Path, paths: Sequence[str], after_contents: Optional[Mapping[str, str]] = None) -> Dict[str, Any]:
    """Return current before hashes and optional projected after hashes."""
    states: List[Dict[str, Any]] = []
    for rel in paths:
        state = _file_state(repo_root, rel)
        if after_contents and rel in after_contents:
            state["projected_after_sha256"] = _sha256_bytes(after_contents[rel].encode("utf-8"))
        states.append(state)
    return _envelope(
        "before_after_hash",
        "ok",
        {"file_count": len(states), "files": states},
        evidence=[{"type": "hash_file_count", "count": len(states)}],
        next_action=_hint("patch_manifest", "Hashes are captured; record them in a patch manifest after apply or preview.", 0.76),
    )


def patch_manifest(repo_root: str | Path, patch_id: Optional[str], edit_units: Sequence[Mapping[str, Any]],
                   diff: str = "", validation_commands: Optional[Sequence[str]] = None,
                   status: str = "candidate") -> Dict[str, Any]:
    """Write a workspace-local patch manifest under .code_x_patch/manifests."""
    patch_id = patch_id or f"patch-{uuid.uuid4().hex[:12]}"
    normalized = [_normalize_edit_unit(repo_root, u, i) for i, u in enumerate(edit_units)]
    paths = sorted({u["path"] for u in normalized})
    files = []
    for rel in paths:
        files.append(_file_state(repo_root, rel))
    manifest = {
        "schema": "code_x.patch_manifest.v1",
        "r_stage": "R7",
        "patch_id": patch_id,
        "created_at_ms": _now_ms(),
        "status": status,
        "workspace_root_name": Path(repo_root).resolve().name,
        "edit_units": normalized,
        "files": files,
        "diff_line_count": len(diff.splitlines()) if diff else 0,
        "validation_commands": list(validation_commands or []),
        "rollback_note": "R7 records hashes and changed files; full restore_checkpoint is owned by R10.",
        "llm_final_decision_required": True,
    }
    manifest_dir = Path(repo_root).resolve() / ".code_x_patch" / "manifests"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = manifest_dir / f"{patch_id}.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return _envelope(
        "patch_manifest",
        "ok",
        {"patch_id": patch_id, "manifest_path": str(manifest_path), "manifest": manifest},
        evidence=[{"type": "manifest_file", "path": str(manifest_path)}],
        next_action=_hint("pytest_runner", "Patch manifest is ready; move to execution validation in R8 or handoff if validation is unavailable.", 0.78, ["build_runner", "lint_runner", "handoff_digest"]),
    )


def workspace_patch_applier(repo_root: str | Path, edit_units: Sequence[Mapping[str, Any]], dry_run: bool = False,
                            patch_id: Optional[str] = None) -> Dict[str, Any]:
    """Apply edit units inside workspace after conflict check; supports dry run."""
    normalized = [_normalize_edit_unit(repo_root, u, i) for i, u in enumerate(edit_units)]
    conflict_result = conflict_detector(repo_root, normalized)
    conflicts = conflict_result["result"].get("conflicts", [])
    if conflicts:
        return _envelope(
            "workspace_patch_applier",
            "blocked",
            {"applied": False, "dry_run": dry_run, "conflicts": conflicts, "changed_files": []},
            evidence=[{"type": "conflict_count", "count": len(conflicts)}],
            next_action=_hint("edit_unit_planner", "Apply blocked by conflicts; revise edit units or refresh before-hash.", 0.94),
        )
    per_file = _simulate_apply(repo_root, normalized)
    diff_result = unified_diff_generator(repo_root, normalized)
    changed_files: List[Dict[str, Any]] = []
    if not dry_run:
        for rel, state in per_file.items():
            target = _workspace_path(repo_root, rel)
            _write_text_atomic(target, state["after_text"], encoding=state["encoding"] or "utf-8")
            changed_files.append({
                "path": rel,
                "before_sha256": state["before_sha256"],
                "after_sha256": _sha256_file(target),
                "existed_before": state["existed_before"],
            })
        manifest_result = patch_manifest(
            repo_root,
            patch_id or f"patch-{uuid.uuid4().hex[:12]}",
            normalized,
            diff=diff_result["result"].get("diff", ""),
            status="applied",
        )
        manifest_ref = manifest_result["result"]["manifest_path"]
    else:
        for rel, state in per_file.items():
            changed_files.append({
                "path": rel,
                "before_sha256": state["before_sha256"],
                "projected_after_sha256": state["after_sha256"],
                "existed_before": state["existed_before"],
            })
        manifest_ref = None
    return _envelope(
        "workspace_patch_applier",
        "ok",
        {
            "applied": not dry_run,
            "dry_run": dry_run,
            "changed_files": changed_files,
            "manifest_path": manifest_ref,
            "diff": diff_result["result"].get("diff", ""),
        },
        evidence=[{"type": "changed_file_count", "count": len(changed_files)}],
        next_action=_hint("pytest_runner" if not dry_run else "workspace_patch_applier", "Patch applied in workspace; run targeted validation next." if not dry_run else "Dry-run successful; apply patch after LLM approval.", 0.86, ["build_runner", "lint_runner", "typecheck_runner", "patch_manifest"]),
    )
