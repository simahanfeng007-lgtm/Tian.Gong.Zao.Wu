"""
Code-X R5 context armor candidate tools.

Scope:
- Pure sidecar utilities for context/rules/log/task/handoff compaction.
- No Runtime registration, no ToolRegistry mutation, no startup side effects.
- No imports from legacy tool packages.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple
import hashlib
import json
import os
import re
from datetime import datetime, timezone

TEXT_EXTENSIONS = {
    ".py", ".ts", ".tsx", ".js", ".jsx", ".json", ".toml", ".yaml", ".yml",
    ".md", ".txt", ".cfg", ".ini", ".css", ".html", ".rs", ".go", ".java",
    ".c", ".h", ".cpp", ".hpp", ".cs", ".sh", ".ps1"
}
IGNORE_DIRS = {".git", "__pycache__", ".pytest_cache", "node_modules", "dist", "build", ".venv", "venv"}
RULE_FILENAMES = ("LINYUANZHE.md", "AGENTS.md", "CLAUDE.md", ".cursorrules")

@dataclass
class ToolEnvelope:
    tool_name: str
    status: str
    summary: str
    artifacts: Dict[str, Any]
    next_action_hint: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _safe_rel(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except Exception:
        return path.as_posix()


def _file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _is_probably_text(path: Path) -> bool:
    if path.suffix.lower() in TEXT_EXTENSIONS:
        return True
    try:
        with path.open("rb") as f:
            sample = f.read(2048)
        return b"\x00" not in sample
    except Exception:
        return False


def _iter_files(root: Path, limit: int = 2000) -> Iterable[Path]:
    count = 0
    for current, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        for name in sorted(files):
            path = Path(current) / name
            if path.is_file():
                yield path
                count += 1
                if count >= limit:
                    return


def generate_linyuanzhe_md(
    repo_root: str | Path,
    project_name: Optional[str] = None,
    stack: Optional[Sequence[str]] = None,
    command_policy: Optional[Dict[str, Any]] = None,
    directory_rules: Optional[Dict[str, str]] = None,
) -> ToolEnvelope:
    """Generate deterministic project instruction text for Code-X sidecar use.

    The function returns content; it does not write into the repository unless a caller explicitly does so.
    """
    root = Path(repo_root)
    name = project_name or root.name
    stack_text = ", ".join(stack or []) or "unknown; detect before build/test"
    policy = command_policy or {
        "default": "A0-A4 allow with audit; A5 require escalation",
        "allowed": ["read/search", "workspace patch", "local tests", "lint", "typecheck", "build", "rollback", "handoff"],
        "blocked_without_confirmation": ["secret exfiltration", "production mutation", "system directory mutation", "mass delete", "destructive shell"],
    }
    directory_rules = directory_rules or {}
    directory_lines = [f"- `{k}`: {v}" for k, v in sorted(directory_rules.items())] or ["- None declared. Use repo map and local files as source of truth."]
    content = f"""# LINYUANZHE.md — Code-X Project Rules

## Project
- Name: {name}
- Stack: {stack_text}
- Generated: {_now_iso()}

## Authority Model
- LLM is the engineering judge and final decision maker.
- Code-X tools are execution exoskeleton components.
- Planner suggests actions only; it must not override the LLM.
- Subagents may research, test, review, or migrate, but must return evidence and may not submit the main patch.

## Execution Defaults
- Read/search, workspace writes, local tests, lint/typecheck/build, rollback, package, and handoff are default-allowed when confined to the workspace.
- A5 operations require escalation: secret leakage, production mutation, destructive shell, system-directory mutation, mass delete, or code exfiltration.
- rollback, handoff, state_recover, and lease_extend must remain available.

## Command Policy
```json
{json.dumps(policy, ensure_ascii=False, indent=2)}
```

## Directory Override Rules
{chr(10).join(directory_lines)}

## Required Code-X Loop
1. Read repo map and project rules.
2. Localize issue to files/symbols.
3. Produce patch plan and edit units.
4. Apply workspace patch with before/after hash.
5. Run available verification.
6. Attribute failures and repair if needed.
7. Roll back or package.
8. Emit handoff digest.
"""
    return ToolEnvelope(
        tool_name="generate_linyuanzhe_md",
        status="ok",
        summary="Generated sidecar project rules content without writing to Runtime or registry.",
        artifacts={"project_name": name, "content": content, "chars": len(content)},
        next_action_hint={"recommend": "project_rules_reader", "reason": "Read active project rules before localization or patch planning."},
    )


def project_rules_reader(repo_root: str | Path, max_chars_per_file: int = 12000) -> ToolEnvelope:
    """Read project-level and directory-level instruction files deterministically."""
    root = Path(repo_root)
    found: List[Dict[str, Any]] = []
    for path in _iter_files(root):
        if path.name in RULE_FILENAMES or path.name.endswith(".rules.md"):
            try:
                text = path.read_text(encoding="utf-8", errors="replace")[:max_chars_per_file]
            except Exception as exc:
                text = f"<unreadable: {exc}>"
            found.append({
                "path": _safe_rel(path, root),
                "scope": _safe_rel(path.parent, root) if path.parent != root else ".",
                "chars": len(text),
                "content": text,
            })
    found.sort(key=lambda item: (item["scope"].count("/"), item["path"]))
    return ToolEnvelope(
        tool_name="project_rules_reader",
        status="ok",
        summary=f"Read {len(found)} project rule file(s).",
        artifacts={"rules": found, "rule_count": len(found)},
        next_action_hint={"recommend": "context_compactor", "reason": "Compact rules with task goal before tool selection."},
    )


def context_compactor(
    sections: Sequence[Dict[str, Any]] | str,
    max_chars: int = 6000,
    preserve_keywords: Optional[Sequence[str]] = None,
) -> ToolEnvelope:
    """Compact mixed context while preserving constraints, files, decisions, errors and next actions."""
    keywords = [k.lower() for k in (preserve_keywords or [
        "must", "禁止", "不得", "必须", "A5", "error", "failed", "traceback", "diff", "patch",
        "test", "next", "handoff", "rollback", "file", "symbol", "decision"
    ])]
    if isinstance(sections, str):
        raw_items = [{"title": "context", "content": sections}]
    else:
        raw_items = list(sections)
    important: List[str] = []
    tail: List[str] = []
    for item in raw_items:
        title = str(item.get("title", "section"))
        content = str(item.get("content", ""))
        lines = content.splitlines()
        picked: List[str] = []
        for line in lines:
            low = line.lower()
            if any(k in low for k in keywords):
                picked.append(line[:500])
        if picked:
            important.append(f"## {title}\n" + "\n".join(picked[:40]))
        if lines:
            tail.append(f"## {title} tail\n" + "\n".join(lines[-12:]))
    compact = "\n\n".join(important + tail)
    if len(compact) > max_chars:
        compact = compact[: max_chars - 160] + "\n\n<TRUNCATED_BY_CONTEXT_COMPACTOR>"
    return ToolEnvelope(
        tool_name="context_compactor",
        status="ok",
        summary=f"Compacted {len(raw_items)} section(s) into {len(compact)} chars.",
        artifacts={"compact_context": compact, "chars": len(compact), "max_chars": max_chars},
        next_action_hint={"recommend": "issue_to_file_localizer", "reason": "Use compact context for localization or patch planning."},
    )


def log_compactor(log_text: str, max_chars: int = 5000) -> ToolEnvelope:
    """Compact command/test/build logs; preserve actionable failure evidence."""
    lines = log_text.splitlines()
    patterns = re.compile(r"(traceback|error|failed|failure|assert|exception|syntaxerror|importerror|modulenotfound|npm ERR|pytest|\bFAIL\b|\bERROR\b)", re.I)
    evidence = [ln[-800:] for ln in lines if patterns.search(ln)]
    failed_tests = [ln.strip() for ln in lines if re.search(r"(FAILED|ERROR)\s+[^\s]+", ln)]
    tail = lines[-60:]
    compact = "\n".join([
        "# Log Compact",
        f"total_lines: {len(lines)}",
        f"evidence_lines: {len(evidence)}",
        "",
        "## Failure Evidence",
        *evidence[:120],
        "",
        "## Failed Tests",
        *failed_tests[:60],
        "",
        "## Tail",
        *tail,
    ])
    if len(compact) > max_chars:
        compact = compact[: max_chars - 120] + "\n<TRUNCATED_BY_LOG_COMPACTOR>"
    status = "failure_evidence_found" if evidence or failed_tests else "ok"
    next_tool = "failure_attribution_analyzer" if evidence or failed_tests else "task_digest"
    return ToolEnvelope(
        tool_name="log_compactor",
        status=status,
        summary=f"Compacted log: {len(lines)} lines, {len(evidence)} evidence lines.",
        artifacts={"compact_log": compact, "failed_tests": failed_tests[:60], "evidence_count": len(evidence)},
        next_action_hint={"recommend": next_tool, "reason": "Use compact failure evidence for attribution, or summarize successful verification."},
    )


def build_baseline_manifest(repo_root: str | Path, limit: int = 2000) -> Dict[str, Dict[str, Any]]:
    """Create a file hash manifest for later changed-files comparison."""
    root = Path(repo_root)
    manifest: Dict[str, Dict[str, Any]] = {}
    for path in _iter_files(root, limit=limit):
        if not _is_probably_text(path):
            continue
        rel = _safe_rel(path, root)
        try:
            manifest[rel] = {"sha256": _file_sha256(path), "size": path.stat().st_size}
        except OSError:
            continue
    return manifest


def changed_files_index(repo_root: str | Path, baseline_manifest: Optional[Dict[str, Dict[str, Any]]] = None) -> ToolEnvelope:
    """Compare current workspace files against an optional baseline manifest."""
    root = Path(repo_root)
    current = build_baseline_manifest(root)
    baseline_manifest = baseline_manifest or {}
    added, modified, deleted, unchanged = [], [], [], []
    for rel, meta in current.items():
        if rel not in baseline_manifest:
            added.append(rel)
        elif baseline_manifest[rel].get("sha256") != meta.get("sha256"):
            modified.append(rel)
        else:
            unchanged.append(rel)
    for rel in baseline_manifest:
        if rel not in current:
            deleted.append(rel)
    result = {
        "added": sorted(added),
        "modified": sorted(modified),
        "deleted": sorted(deleted),
        "unchanged_count": len(unchanged),
        "current_manifest": current,
    }
    next_tool = "patch_manifest_generator" if (added or modified or deleted) else "patch_plan_generator"
    return ToolEnvelope(
        tool_name="changed_files_index",
        status="ok",
        summary=f"Changed files: +{len(added)} ~{len(modified)} -{len(deleted)}.",
        artifacts=result,
        next_action_hint={"recommend": next_tool, "reason": "Create patch manifest if changes exist; otherwise produce or revise patch plan."},
    )


def task_digest(task_state: Dict[str, Any], tool_results: Optional[Sequence[Dict[str, Any]]] = None) -> ToolEnvelope:
    """Create a compact task state digest for long-chain continuation."""
    tool_results = list(tool_results or [])
    lines = [
        "# Code-X Task Digest",
        f"generated: {_now_iso()}",
        f"task_id: {task_state.get('task_id', 'unknown')}",
        f"phase: {task_state.get('phase', 'unknown')}",
        f"goal: {task_state.get('goal', '')}",
        "",
        "## Constraints",
    ]
    for c in task_state.get("constraints", []):
        lines.append(f"- {c}")
    lines += ["", "## Files In Focus"]
    for f in task_state.get("files_in_focus", []):
        lines.append(f"- {f}")
    lines += ["", "## Tool Results"]
    for item in tool_results[-12:]:
        name = item.get("tool_name") or item.get("name") or "tool"
        status = item.get("status", "unknown")
        summary = item.get("summary", "")
        lines.append(f"- {name}: {status} — {summary}")
    blockers = task_state.get("blockers", [])
    lines += ["", "## Blockers"]
    if blockers:
        for b in blockers:
            lines.append(f"- {b}")
    else:
        lines.append("- None recorded.")
    next_hint = task_state.get("next_action_hint") or {"recommend": "tool_result_to_next_action_mapper", "reason": "Select next Code-X action from current task state."}
    lines += ["", "## Next Action Hint", f"```json\n{json.dumps(next_hint, ensure_ascii=False, indent=2)}\n```"]
    digest = "\n".join(lines)
    return ToolEnvelope(
        tool_name="task_digest",
        status="ok",
        summary="Generated compact task digest for continuation.",
        artifacts={"digest_markdown": digest, "task_state": task_state, "tool_result_count": len(tool_results)},
        next_action_hint=next_hint,
    )


def handoff_digest(
    task_digest_markdown: str,
    changed_files: Optional[Dict[str, Any]] = None,
    verification: Optional[Dict[str, Any]] = None,
    next_steps: Optional[Sequence[str]] = None,
) -> ToolEnvelope:
    """Create a handoff summary for restart, review, packaging, or user delivery."""
    changed_files = changed_files or {}
    verification = verification or {}
    next_steps = list(next_steps or [])
    lines = [
        "# Code-X Handoff Digest",
        f"generated: {_now_iso()}",
        "",
        "## Task State",
        task_digest_markdown[:6000],
        "",
        "## Changed Files",
    ]
    for key in ("added", "modified", "deleted"):
        values = changed_files.get(key, []) or []
        lines.append(f"- {key}: {len(values)}")
        for value in values[:40]:
            lines.append(f"  - {value}")
    lines += ["", "## Verification"]
    for key, value in verification.items():
        lines.append(f"- {key}: {value}")
    if not verification:
        lines.append("- Not run or not available.")
    lines += ["", "## Next Steps"]
    if next_steps:
        for step in next_steps:
            lines.append(f"- {step}")
    else:
        lines.append("- Await LLM decision: continue repair, roll back, package, or ask user for missing external dependency.")
    text = "\n".join(lines)
    return ToolEnvelope(
        tool_name="handoff_digest",
        status="ok",
        summary="Generated handoff digest.",
        artifacts={"handoff_markdown": text, "chars": len(text)},
        next_action_hint={"recommend": "delivery_candidate_packager", "reason": "Package successful candidate or preserve handoff for resume."},
    )


def decision_memory(memory_path: str | Path, action: str, record: Optional[Dict[str, Any]] = None, limit: int = 200) -> ToolEnvelope:
    """Append or read local decision memory in JSONL format.

    This is a candidate sidecar file, not global model memory and not Runtime state.
    """
    path = Path(memory_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    records: List[Dict[str, Any]] = []
    if path.exists():
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    if action == "append":
        item = dict(record or {})
        item.setdefault("created_at", _now_iso())
        item.setdefault("kind", "decision")
        records.append(item)
        records = records[-limit:]
        path.write_text("\n".join(json.dumps(r, ensure_ascii=False, sort_keys=True) for r in records) + "\n", encoding="utf-8")
        status = "ok"
        summary = "Appended decision memory record."
    elif action == "read":
        status = "ok"
        summary = f"Read {len(records)} decision memory record(s)."
    else:
        status = "error"
        summary = f"Unsupported action: {action}"
    return ToolEnvelope(
        tool_name="decision_memory",
        status=status,
        summary=summary,
        artifacts={"path": str(path), "records": records[-limit:], "count": len(records)},
        next_action_hint={"recommend": "task_digest", "reason": "Fold relevant decisions into compact task state."},
    )
