
"""
L6.70.2-CodeX R11: subagent parallel layer clean candidate tools.

Scope:
- Candidate-only subagent specs and evidence-return helpers.
- Subagents perform research, test design, review, migration analysis, and visual checklist generation.
- Subagents DO NOT write workspace files, apply patches, commit, register Runtime tools, or replace the LLM.

Design principle:
LLM = main brain and final engineering decision maker.
Subagents = bounded reconnaissance/review assistants that return evidence + summary only.
"""
from __future__ import annotations

import ast
import fnmatch
import json
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

DEFAULT_EXCLUDES = {
    ".git", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache",
    "node_modules", "dist", "build", ".codex_snapshots", ".codex_delivery",
}
TEXT_EXTENSIONS = {
    ".py", ".pyi", ".js", ".jsx", ".ts", ".tsx", ".vue", ".svelte",
    ".html", ".css", ".scss", ".sass", ".md", ".toml", ".json", ".yaml", ".yml",
}
SOURCE_EXTENSIONS = {".py", ".js", ".jsx", ".ts", ".tsx", ".vue", ".svelte"}
FRONTEND_EXTENSIONS = {".jsx", ".tsx", ".vue", ".svelte", ".html", ".css", ".scss", ".sass"}
TEST_PATTERNS = ["test_*.py", "*_test.py", "*.spec.ts", "*.test.ts", "*.spec.tsx", "*.test.tsx", "*.spec.js", "*.test.js"]

SECRET_PATTERNS = [
    ("generic_secret_assignment", re.compile(r"(?i)(api[_-]?key|secret|token|password)\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{16,}")),
    ("aws_access_key", re.compile(r"A" r"KIA[0-9A-Z]{16}")),
    ("private_key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----")),
]
SECURITY_PATTERNS = [
    ("dynamic_eval", re.compile(r"\b(eval|exec)\s*\("), "A4"),
    ("shell_true", re.compile(r"shell\s*=\s*True"), "A4"),
    ("os_system", re.compile(r"\bos\.system\s*\("), "A4"),
    ("pickle_loads", re.compile(r"\bpickle\.(loads|load)\s*\("), "A4"),
    ("yaml_load_without_safe", re.compile(r"\byaml\.load\s*\("), "A4"),
    ("verify_false", re.compile(r"verify\s*=\s*False"), "A4"),
    ("destructive_command_literal", re.compile(r"(?i)\b(rm\s+-rf|del\s+/s|format\s+[a-z]:|drop\s+table)\b"), "A5"),
]


def _now_ms() -> int:
    return int(time.time() * 1000)


def _root(repo_root: str | Path) -> Path:
    root = Path(repo_root).resolve()
    if not root.exists() or not root.is_dir():
        raise ValueError(f"repo_root must be an existing directory: {repo_root}")
    return root


def _rel(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


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
    root = _root(repo_root)
    target = (root / _safe_rel_path(rel_path)).resolve()
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"target escapes workspace: {rel_path}") from exc
    return target


def _should_exclude(rel_path: str, exclude_dirs: Iterable[str] = DEFAULT_EXCLUDES) -> bool:
    parts = Path(rel_path).parts
    return any(part in exclude_dirs for part in parts)


def _is_text_candidate(path: Path) -> bool:
    return path.suffix.lower() in TEXT_EXTENSIONS


def _read_text(path: Path, max_chars: int = 160_000) -> str:
    data = path.read_bytes()
    if b"\x00" in data[:4096]:
        return ""
    return data.decode("utf-8", errors="ignore")[:max_chars]


def _iter_text_files(repo_root: str | Path, include_globs: Optional[Sequence[str]] = None) -> List[Path]:
    root = _root(repo_root)
    out: List[Path] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rel = _rel(root, path)
        if _should_exclude(rel):
            continue
        if include_globs and not any(fnmatch.fnmatch(rel, pat) for pat in include_globs):
            continue
        if _is_text_candidate(path):
            out.append(path)
    return sorted(out, key=lambda p: _rel(root, p))


def _line_evidence(root: Path, path: Path, line_no: int, snippet: str, kind: str, score: float = 0.5) -> Dict[str, Any]:
    return {
        "kind": kind,
        "file": _rel(root, path),
        "line": line_no,
        "snippet": snippet.strip()[:240],
        "score": round(float(score), 4),
    }


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
              risk_level: str = "A1") -> Dict[str, Any]:
    return {
        "tool_name": tool,
        "status": status,
        "agent_role": "bounded_subagent",
        "llm_is_final_decider": True,
        "subagent_limits": {
            "may_write_workspace": False,
            "may_apply_patch": False,
            "may_commit": False,
            "may_register_runtime": False,
            "must_return_evidence": True,
        },
        "r1_next_action_hint": next_action or _hint("handoff_digest", "No next action was provided.", 0.3),
        "r2_execution_protection": {
            "risk_level": risk_level,
            "requires_confirmation": risk_level == "A5",
            "a5_hard_block_only": True,
            "protected_keys": ["rollback", "handoff", "state_recover", "lease_extend"],
        },
        "evidence": evidence or [],
        "warnings": warnings or [],
        "result": result,
    }


def _tokenize_query(query: str) -> List[str]:
    return [tok.lower() for tok in re.findall(r"[A-Za-z_][A-Za-z0-9_]*|[\u4e00-\u9fff]{2,}|\d+", query or "") if len(tok) >= 2]


def _file_score(rel: str, text: str, tokens: Sequence[str]) -> Tuple[float, List[Tuple[int, str, str]]]:
    lowered = text.lower()
    score = 0.0
    hits: List[Tuple[int, str, str]] = []
    lines = text.splitlines()
    rel_lower = rel.lower()
    for tok in tokens:
        if tok in rel_lower:
            score += 5.0
            hits.append((1, tok, f"path contains {tok}"))
        count = lowered.count(tok)
        if count:
            score += min(count, 8) * 1.5
            for idx, line in enumerate(lines, start=1):
                if tok in line.lower():
                    hits.append((idx, tok, line))
                    break
    if "/tests/" in f"/{rel_lower}" or rel_lower.startswith("tests/"):
        score += 0.25
    return score, hits


def _python_defs(path: Path) -> List[Dict[str, Any]]:
    text = _read_text(path)
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return []
    out: List[Dict[str, Any]] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            out.append({
                "name": node.name,
                "kind": "class" if isinstance(node, ast.ClassDef) else "function",
                "line": getattr(node, "lineno", 1),
                "end_line": getattr(node, "end_lineno", getattr(node, "lineno", 1)),
            })
    out.sort(key=lambda x: (x["line"], x["name"]))
    return out


def _js_like_defs(text: str) -> List[Dict[str, Any]]:
    defs: List[Dict[str, Any]] = []
    patterns = [
        ("function", re.compile(r"\bfunction\s+([A-Za-z_$][\w$]*)\s*\(")),
        ("class", re.compile(r"\bclass\s+([A-Za-z_$][\w$]*)\b")),
        ("function", re.compile(r"\b(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>")),
        ("function", re.compile(r"\bexport\s+(?:default\s+)?function\s+([A-Za-z_$][\w$]*)\s*\(")),
    ]
    for idx, line in enumerate(text.splitlines(), start=1):
        for kind, pattern in patterns:
            m = pattern.search(line)
            if m:
                defs.append({"name": m.group(1), "kind": kind, "line": idx, "end_line": idx})
    return defs


def _source_defs(path: Path) -> List[Dict[str, Any]]:
    if path.suffix.lower() == ".py":
        return _python_defs(path)
    if path.suffix.lower() in {".js", ".jsx", ".ts", ".tsx", ".vue", ".svelte"}:
        return _js_like_defs(_read_text(path))
    return []


def _is_test_file(path: Path) -> bool:
    name = path.name
    rel = path.as_posix().lower()
    return any(fnmatch.fnmatch(name, pat) for pat in TEST_PATTERNS) or "/test" in rel or rel.startswith("test")


def _resolve_target_files(root: Path, target_files: Optional[Sequence[str]]) -> List[Path]:
    if not target_files:
        return [p for p in _iter_text_files(root) if p.suffix.lower() in SOURCE_EXTENSIONS]
    out: List[Path] = []
    for rel in target_files:
        p = _workspace_path(root, rel)
        if p.exists() and p.is_file() and _is_text_candidate(p):
            out.append(p)
    return out


def code_research_subagent(repo_root: str | Path, query: str, max_files: int = 12) -> Dict[str, Any]:
    """Return ranked files and evidence for a code question or issue description. Read-only."""
    root = _root(repo_root)
    tokens = _tokenize_query(query)
    if not tokens:
        return _envelope(
            "code_research_subagent", "needs_input",
            {"query": query, "ranked_files": [], "summary": "No searchable tokens were found in query."},
            next_action=_hint("task_digest", "Ask LLM/user to clarify the issue before dispatching subagents.", 0.55),
        )
    ranked: List[Dict[str, Any]] = []
    evidence: List[Dict[str, Any]] = []
    for path in _iter_text_files(root):
        text = _read_text(path)
        rel = _rel(root, path)
        score, hits = _file_score(rel, text, tokens)
        if score <= 0:
            continue
        defs = _source_defs(path)[:12]
        ranked.append({"file": rel, "score": round(score, 4), "matched_tokens": sorted({h[1] for h in hits}), "symbols": defs})
        for line_no, token, line in hits[:2]:
            evidence.append(_line_evidence(root, path, line_no, line, f"query_hit:{token}", min(score / 20, 1.0)))
    ranked.sort(key=lambda item: item["score"], reverse=True)
    ranked = ranked[:max_files]
    selected = {item["file"] for item in ranked}
    evidence = [ev for ev in evidence if ev["file"] in selected][:max_files * 2]
    status = "ok" if ranked else "no_match"
    summary = f"Found {len(ranked)} candidate files for query tokens {tokens}." if ranked else "No candidate files matched query tokens."
    return _envelope(
        "code_research_subagent", status,
        {"query": query, "tokens": tokens, "ranked_files": ranked, "summary": summary},
        evidence=evidence,
        next_action=_hint("issue_to_file_localizer", "Use ranked evidence to confirm files, then localize symbols/lines before planning edits.", 0.86,
                          ["file_to_symbol_localizer", "symbol_to_line_localizer", "patch_plan_generator"]),
    )


def test_design_subagent(repo_root: str | Path, target_files: Optional[Sequence[str]] = None,
                         issue: str = "", max_cases_per_file: int = 5) -> Dict[str, Any]:
    """Suggest test cases and map existing tests. Read-only; no test files are written."""
    root = _root(repo_root)
    sources = _resolve_target_files(root, target_files)
    tests = [p for p in _iter_text_files(root) if _is_test_file(p)]
    evidence: List[Dict[str, Any]] = []
    proposals: List[Dict[str, Any]] = []
    existing = []
    for test in tests[:30]:
        text = _read_text(test)
        defs = _source_defs(test)
        existing.append({"file": _rel(root, test), "test_symbols": defs[:20]})
        for d in defs[:2]:
            evidence.append(_line_evidence(root, test, d["line"], d["name"], "existing_test_symbol", 0.7))
    for src in sources[:20]:
        defs = [d for d in _source_defs(src) if not d["name"].startswith("_")]
        if not defs:
            continue
        cases = []
        for d in defs[:max_cases_per_file]:
            lname = d["name"].lower()
            if any(word in lname for word in ["parse", "load", "read"]):
                cases.append({"symbol": d["name"], "case": "valid input, malformed input, missing file/path, encoding edge case"})
            elif any(word in lname for word in ["add", "calc", "compute", "sum", "divide"]):
                cases.append({"symbol": d["name"], "case": "normal numeric path, zero/empty boundary, negative or invalid input"})
            elif any(word in lname for word in ["auth", "token", "secret"]):
                cases.append({"symbol": d["name"], "case": "authorized, unauthorized, expired credential, secret redaction"})
            else:
                cases.append({"symbol": d["name"], "case": "happy path, boundary path, invalid input, regression from issue"})
            evidence.append(_line_evidence(root, src, d["line"], d["name"], "source_symbol_for_test_design", 0.66))
        proposals.append({"target_file": _rel(root, src), "proposed_cases": cases})
    summary = f"Mapped {len(existing)} existing test files and proposed tests for {len(proposals)} source files."
    return _envelope(
        "test_design_subagent", "ok" if proposals or existing else "no_targets",
        {"issue": issue, "existing_tests": existing, "test_proposals": proposals, "summary": summary},
        evidence=evidence[:60],
        next_action=_hint("generated_test_runner", "LLM may convert selected proposals into tests, then run the validation layer.", 0.78,
                          ["pytest_runner", "npm_test_runner", "fallback_test_strategy"]),
    )


def _diff_added_lines(diff_text: str) -> List[Tuple[int, str]]:
    out: List[Tuple[int, str]] = []
    current_line = 0
    for raw in diff_text.splitlines():
        if raw.startswith("@@"):
            m = re.search(r"\+(\d+)", raw)
            current_line = int(m.group(1)) if m else current_line
            continue
        if raw.startswith("+") and not raw.startswith("+++"): 
            out.append((current_line, raw[1:]))
            current_line += 1
        elif not raw.startswith("-"):
            current_line += 1
    return out


def _review_text_for_smells(text: str, path: Path, root: Path) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    findings: List[Dict[str, Any]] = []
    evidence: List[Dict[str, Any]] = []
    smell_patterns = [
        ("bare_except", re.compile(r"\bexcept\s*:\s*(?:#.*)?$"), "Use a specific exception type or re-raise with context."),
        ("silent_pass", re.compile(r"\bpass\s*(?:#.*)?$"), "Verify that pass is intentional and not hiding an unfinished branch."),
        ("debug_print", re.compile(r"\bprint\s*\("), "Consider structured logging or remove debug output before delivery."),
        ("todo_leftover", re.compile(r"(?i)\bTODO\b|\bFIXME\b"), "Track TODO/FIXME explicitly before handoff."),
        ("broad_exception", re.compile(r"except\s+Exception\b"), "Broad exception handling needs evidence or narrowing."),
    ]
    for idx, line in enumerate(text.splitlines(), start=1):
        for name, pattern, message in smell_patterns:
            if pattern.search(line):
                finding = {"file": _rel(root, path), "line": idx, "kind": name, "severity": "medium", "message": message}
                findings.append(finding)
                evidence.append(_line_evidence(root, path, idx, line, name, 0.7))
    if path.suffix.lower() == ".py":
        try:
            tree = ast.parse(text)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    end = getattr(node, "end_lineno", node.lineno)
                    length = end - node.lineno + 1
                    if length > 80:
                        findings.append({"file": _rel(root, path), "line": node.lineno, "kind": "long_function", "severity": "medium", "message": f"Function {node.name} is {length} lines."})
                        evidence.append(_line_evidence(root, path, node.lineno, node.name, "long_function", 0.6))
        except SyntaxError as exc:
            findings.append({"file": _rel(root, path), "line": exc.lineno or 1, "kind": "syntax_parse_failed", "severity": "high", "message": str(exc)})
    return findings, evidence


def review_subagent(repo_root: str | Path, changed_files: Optional[Sequence[str]] = None,
                    diff_text: str = "") -> Dict[str, Any]:
    """Review changed files or diff for maintainability risks. Read-only."""
    root = _root(repo_root)
    files = _resolve_target_files(root, changed_files)
    if not changed_files and diff_text:
        files = []
    findings: List[Dict[str, Any]] = []
    evidence: List[Dict[str, Any]] = []
    for path in files[:40]:
        f, ev = _review_text_for_smells(_read_text(path), path, root)
        findings.extend(f)
        evidence.extend(ev)
    if diff_text:
        for line_no, line in _diff_added_lines(diff_text):
            for name, pattern, msg in [
                ("diff_debug_print", re.compile(r"\bprint\s*\("), "New debug print in diff."),
                ("diff_todo", re.compile(r"(?i)TODO|FIXME"), "New TODO/FIXME in diff."),
                ("diff_bare_except", re.compile(r"\bexcept\s*:\s*$"), "New bare except in diff."),
            ]:
                if pattern.search(line):
                    findings.append({"file": "<diff>", "line": line_no, "kind": name, "severity": "medium", "message": msg})
                    evidence.append({"kind": name, "file": "<diff>", "line": line_no, "snippet": line[:240], "score": 0.7})
    status = "needs_attention" if findings else "ok"
    return _envelope(
        "review_subagent", status,
        {"findings": findings, "summary": f"Review found {len(findings)} maintainability findings."},
        evidence=evidence[:80],
        next_action=_hint("patch_audit_hook" if findings else "pytest_runner", "LLM should decide whether to revise patch or proceed to validation.", 0.76,
                          ["next_patch_generator", "pytest_runner", "handoff_digest"]),
    )


def security_review_subagent(repo_root: str | Path, changed_files: Optional[Sequence[str]] = None,
                             diff_text: str = "") -> Dict[str, Any]:
    """Scan changed files/diff for secrets and risky code patterns. Read-only."""
    root = _root(repo_root)
    files = _resolve_target_files(root, changed_files) if changed_files else _iter_text_files(root)
    findings: List[Dict[str, Any]] = []
    evidence: List[Dict[str, Any]] = []
    highest = "A1"

    def bump(level: str) -> None:
        nonlocal highest
        order = {"A0": 0, "A1": 1, "A2": 2, "A3": 3, "A4": 4, "A5": 5}
        if order[level] > order[highest]:
            highest = level

    for path in files[:80]:
        text = _read_text(path)
        for idx, line in enumerate(text.splitlines(), start=1):
            for name, pattern in SECRET_PATTERNS:
                if pattern.search(line):
                    findings.append({"file": _rel(root, path), "line": idx, "kind": name, "severity": "critical", "risk_level": "A5", "message": "Potential secret material detected; do not package or externalize."})
                    evidence.append(_line_evidence(root, path, idx, "<redacted potential secret>", name, 0.98))
                    bump("A5")
            for name, pattern, risk in SECURITY_PATTERNS:
                if pattern.search(line):
                    findings.append({"file": _rel(root, path), "line": idx, "kind": name, "severity": "high" if risk == "A5" else "medium", "risk_level": risk, "message": "Risky code pattern requires LLM review."})
                    evidence.append(_line_evidence(root, path, idx, line, name, 0.82))
                    bump(risk)
    if diff_text:
        for line_no, line in _diff_added_lines(diff_text):
            for name, pattern in SECRET_PATTERNS:
                if pattern.search(line):
                    findings.append({"file": "<diff>", "line": line_no, "kind": name, "severity": "critical", "risk_level": "A5", "message": "Potential secret introduced in diff."})
                    evidence.append({"kind": name, "file": "<diff>", "line": line_no, "snippet": "<redacted potential secret>", "score": 0.98})
                    bump("A5")
            for name, pattern, risk in SECURITY_PATTERNS:
                if pattern.search(line):
                    findings.append({"file": "<diff>", "line": line_no, "kind": name, "severity": "high" if risk == "A5" else "medium", "risk_level": risk, "message": "Risky pattern introduced in diff."})
                    evidence.append({"kind": name, "file": "<diff>", "line": line_no, "snippet": line[:240], "score": 0.82})
                    bump(risk)
    status = "blocked" if highest == "A5" else ("needs_attention" if findings else "ok")
    return _envelope(
        "security_review_subagent", status,
        {"findings": findings, "highest_risk_level": highest, "summary": f"Security scan found {len(findings)} findings; highest risk {highest}."},
        evidence=evidence[:100],
        next_action=_hint("secret_scan_hook" if highest == "A5" else "review_subagent", "LLM must block/export-redact A5 findings, otherwise decide whether to revise or continue validation.", 0.9,
                          ["next_patch_generator", "delivery_candidate_packager", "handoff_digest"]),
        risk_level=highest,
    )


def refactor_review_subagent(repo_root: str | Path, target_files: Optional[Sequence[str]] = None) -> Dict[str, Any]:
    """Find refactor opportunities without performing refactor edits."""
    root = _root(repo_root)
    files = _resolve_target_files(root, target_files)
    findings: List[Dict[str, Any]] = []
    evidence: List[Dict[str, Any]] = []
    import_lines_seen: Dict[str, List[Tuple[str, int]]] = {}
    for path in files[:80]:
        text = _read_text(path)
        lines = text.splitlines()
        if len(lines) > 500:
            findings.append({"file": _rel(root, path), "line": 1, "kind": "large_file", "severity": "medium", "message": f"File has {len(lines)} lines; consider split only if change scope justifies it."})
            evidence.append(_line_evidence(root, path, 1, f"{len(lines)} lines", "large_file", 0.55))
        if path.suffix.lower() == ".py":
            for idx, line in enumerate(lines, start=1):
                if line.startswith("import ") or line.startswith("from "):
                    import_lines_seen.setdefault(line.strip(), []).append((_rel(root, path), idx))
            for d in _python_defs(path):
                length = d.get("end_line", d["line"]) - d["line"] + 1
                if length > 60:
                    findings.append({"file": _rel(root, path), "line": d["line"], "kind": "long_symbol", "severity": "medium", "message": f"{d['kind']} {d['name']} spans {length} lines."})
                    evidence.append(_line_evidence(root, path, d["line"], d["name"], "long_symbol", 0.62))
        duplicate_blocks = {}
        for idx, line in enumerate(lines, start=1):
            key = line.strip()
            if len(key) >= 48 and not key.startswith("#"):
                duplicate_blocks.setdefault(key, []).append(idx)
        for key, idxs in list(duplicate_blocks.items())[:20]:
            if len(idxs) >= 3:
                findings.append({"file": _rel(root, path), "line": idxs[0], "kind": "repeated_line", "severity": "low", "message": "Repeated non-trivial line may indicate extractable helper."})
                evidence.append(_line_evidence(root, path, idxs[0], key, "repeated_line", 0.45))
    for imp, locations in import_lines_seen.items():
        fileset = {loc[0] for loc in locations}
        if len(fileset) >= 4:
            findings.append({"file": "<repo>", "line": 1, "kind": "common_import_cluster", "severity": "low", "message": f"Import appears in {len(fileset)} files: {imp}"})
    status = "needs_attention" if findings else "ok"
    return _envelope(
        "refactor_review_subagent", status,
        {"findings": findings, "summary": f"Refactor review found {len(findings)} opportunities. These are advisory only."},
        evidence=evidence[:80],
        next_action=_hint("edit_unit_planner" if findings else "handoff_digest", "LLM may turn selected advisory findings into explicit edit units, or defer them to avoid scope creep.", 0.72,
                          ["patch_plan_generator", "review_subagent"]),
    )


def migration_subagent(repo_root: str | Path, migration_goal: str,
                       target_patterns: Optional[Sequence[str]] = None) -> Dict[str, Any]:
    """Map files and steps for a migration goal. Does not edit files."""
    root = _root(repo_root)
    tokens = _tokenize_query(migration_goal)
    include_globs = target_patterns
    candidates: List[Dict[str, Any]] = []
    evidence: List[Dict[str, Any]] = []
    deprecated_markers = [
        ("python_unittest_to_pytest", re.compile(r"\bunittest\b|self\.assert")),
        ("typing_optional_old", re.compile(r"\bOptional\[|\bUnion\[")),
        ("react_class_component", re.compile(r"extends\s+React\.Component|componentDidMount|componentWillUnmount")),
        ("commonjs_to_esm", re.compile(r"\brequire\s*\(|module\.exports")),
        ("legacy_todo", re.compile(r"(?i)\blegacy\b|\bdeprecated\b|\bTODO migrate\b")),
    ]
    for path in _iter_text_files(root, include_globs=include_globs):
        text = _read_text(path)
        rel = _rel(root, path)
        score, hits = _file_score(rel, text, tokens)
        markers = []
        for name, pattern in deprecated_markers:
            for idx, line in enumerate(text.splitlines(), start=1):
                if pattern.search(line):
                    markers.append({"marker": name, "line": idx})
                    evidence.append(_line_evidence(root, path, idx, line, name, 0.7))
                    break
        if score > 0 or markers:
            candidates.append({"file": rel, "score": round(score + len(markers) * 2, 4), "markers": markers[:8]})
    candidates.sort(key=lambda x: x["score"], reverse=True)
    phases = [
        "inventory affected files and decide exact migration scope",
        "write compatibility tests before edits",
        "migrate one small cluster and validate",
        "run full test/build/lint/typecheck suite",
        "handoff with changed files and known residual risks",
    ]
    return _envelope(
        "migration_subagent", "ok" if candidates else "no_targets",
        {"migration_goal": migration_goal, "candidate_files": candidates[:40], "migration_phases": phases, "summary": f"Mapped {len(candidates)} candidate migration files."},
        evidence=evidence[:100],
        next_action=_hint("patch_plan_generator" if candidates else "code_research_subagent", "LLM should confirm migration scope before any patch is generated.", 0.75,
                          ["test_design_subagent", "edit_unit_planner", "pytest_runner"]),
    )


def frontend_visual_subagent(repo_root: str | Path, changed_files: Optional[Sequence[str]] = None) -> Dict[str, Any]:
    """Produce a frontend visual/accessibility checklist from source files. No screenshots; no writes."""
    root = _root(repo_root)
    if changed_files:
        files = [p for p in _resolve_target_files(root, changed_files) if p.suffix.lower() in FRONTEND_EXTENSIONS]
    else:
        files = [p for p in _iter_text_files(root) if p.suffix.lower() in FRONTEND_EXTENSIONS]
    findings: List[Dict[str, Any]] = []
    evidence: List[Dict[str, Any]] = []
    checks = {
        "has_fixed_or_sticky_input": False,
        "has_responsive_viewport": False,
        "has_overflow_guard": False,
        "has_accessibility_labels": False,
        "has_loading_or_disabled_state": False,
    }
    for path in files[:80]:
        text = _read_text(path)
        for idx, line in enumerate(text.splitlines(), start=1):
            low = line.lower()
            rel = _rel(root, path)
            if "position: fixed" in low or "position: sticky" in low or "fixed bottom" in low or "sticky bottom" in low:
                checks["has_fixed_or_sticky_input"] = True
                evidence.append(_line_evidence(root, path, idx, line, "fixed_or_sticky_input", 0.78))
            if "@media" in low or "min-width" in low or "max-width" in low or "viewport" in low:
                checks["has_responsive_viewport"] = True
                evidence.append(_line_evidence(root, path, idx, line, "responsive_rule", 0.72))
            if "overflow" in low or "min-h-0" in low or "height: 100" in low:
                checks["has_overflow_guard"] = True
                evidence.append(_line_evidence(root, path, idx, line, "overflow_guard", 0.68))
            if "aria-" in low or "role=" in low or "alt=" in low:
                checks["has_accessibility_labels"] = True
                evidence.append(_line_evidence(root, path, idx, line, "accessibility_marker", 0.72))
            if "loading" in low or "disabled" in low or "isloading" in line:
                checks["has_loading_or_disabled_state"] = True
                evidence.append(_line_evidence(root, path, idx, line, "loading_or_disabled_state", 0.66))
        if path.suffix.lower() in {".jsx", ".tsx", ".vue", ".svelte", ".html"}:
            if "input" in text.lower() and not ("aria-" in text.lower() or "label" in text.lower()):
                findings.append({"file": rel, "line": 1, "kind": "input_without_obvious_accessibility_label", "severity": "medium", "message": "Input-like UI detected without obvious label/aria marker."})
            if "overflow" not in text.lower() and "chat" in text.lower():
                findings.append({"file": rel, "line": 1, "kind": "chat_layout_overflow_not_obvious", "severity": "low", "message": "Chat layout should confirm scroll container and fixed input behavior."})
    missing = [name for name, ok in checks.items() if not ok]
    for name in missing:
        findings.append({"file": "<frontend>", "line": 1, "kind": f"missing_{name}", "severity": "medium", "message": f"No obvious evidence for {name}. Verify manually or via desktop shell."})
    status = "needs_attention" if findings else "ok"
    return _envelope(
        "frontend_visual_subagent", status,
        {"checked_files": [_rel(root, p) for p in files], "visual_checks": checks, "findings": findings, "summary": f"Visual checklist found {len(findings)} attention items across {len(files)} frontend files."},
        evidence=evidence[:100],
        next_action=_hint("frontend_visual_fixture" if findings else "handoff_digest", "LLM should decide whether to run visual fixture/screenshot checks after code validation.", 0.74,
                          ["review_subagent", "build_runner", "handoff_digest"]),
    )


SUBAGENT_REGISTRY = {
    "code_research_subagent": code_research_subagent,
    "test_design_subagent": test_design_subagent,
    "review_subagent": review_subagent,
    "security_review_subagent": security_review_subagent,
    "refactor_review_subagent": refactor_review_subagent,
    "migration_subagent": migration_subagent,
    "frontend_visual_subagent": frontend_visual_subagent,
}

# pytest sees names prefixed with test_ in imported namespaces. These are tools, not tests.
test_design_subagent.__test__ = False


def subagent_pack_manifest() -> Dict[str, Any]:
    """Return candidate registry metadata without Runtime registration side effects."""
    return _envelope(
        "subagent_pack_manifest", "ok",
        {
            "candidate_package": "subagents.code_research_pack",
            "subagents": sorted(SUBAGENT_REGISTRY.keys()),
            "runtime_registration": False,
            "side_effects": "none",
            "authority_model": "LLM final decision; subagents return evidence only",
        },
        next_action=_hint("abilitypackage_orchestration", "R12 may repackage these contracts into candidate ToolPackage/AbilityPackage metadata.", 0.82),
    )
