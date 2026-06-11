
"""
L6.70.2-CodeX R6: 代码定位层旁路候选实现。

边界：
- v2 原生候选工具；不依赖外部项目源码。
- 只读定位，不写 workspace，不注册 Runtime。
- 输出必须能被 R1 next_action_hint 与 R2 执行力保护壳消费。
"""
from __future__ import annotations

import ast
import json
import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

CODE_EXTS = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs",
    ".java", ".go", ".rs", ".c", ".cc", ".cpp", ".h", ".hpp",
    ".cs", ".php", ".rb", ".swift", ".kt", ".kts", ".scala", ".vue",
}
TEST_HINTS = ("test", "tests", "spec", "__tests__")
IGNORE_DIRS = {
    ".git", ".hg", ".svn", "node_modules", "__pycache__", ".pytest_cache",
    ".mypy_cache", ".ruff_cache", ".venv", "venv", "env", "dist", "build",
    "target", "coverage", ".next", ".nuxt", ".cache",
}
TOKEN_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*|[0-9]+|[\u4e00-\u9fff]+")
TRACE_FILE_RE = re.compile(r"(?:File\s+\"(?P<py>[^\"]+)\",\s+line\s+(?P<pyline>\d+))|(?P<plain>[\w./\\-]+\.(?:py|js|jsx|ts|tsx|java|go|rs|cpp|c|h|hpp)):(?P<line>\d+)")
PYTEST_NODE_RE = re.compile(r"(?P<file>[\w./\\-]+\.py)::(?P<test>[A-Za-z_][A-Za-z0-9_]*(?:::?\w+)?)")
ERROR_CLASS_RE = re.compile(r"(?P<error>[A-Za-z_][A-Za-z0-9_]*(?:Error|Exception|Failure))\s*:\s*(?P<msg>.+)")


def _safe_root(root: str | Path) -> Path:
    p = Path(root).expanduser().resolve()
    if not p.exists():
        raise FileNotFoundError(f"workspace root not found: {p}")
    if not p.is_dir():
        raise NotADirectoryError(f"workspace root is not a directory: {p}")
    return p


def _is_ignored(path: Path) -> bool:
    return any(part in IGNORE_DIRS for part in path.parts)


def _rel(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root).as_posix()
    except Exception:
        return path.as_posix()


def _read_text(path: Path, limit_bytes: int = 2_000_000) -> str:
    data = path.read_bytes()[:limit_bytes]
    for enc in ("utf-8", "utf-8-sig", "gb18030", "latin-1"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def _tokens(text: str) -> List[str]:
    return [t.lower() for t in TOKEN_RE.findall(text or "") if len(t) > 1 or t.isdigit()]


def _code_files(root: Path) -> List[Path]:
    files: List[Path] = []
    for path in root.rglob("*"):
        if path.is_file() and path.suffix.lower() in CODE_EXTS and not _is_ignored(path):
            files.append(path)
    return sorted(files)


def _line_snippet(text: str, line_no: int, radius: int = 2) -> str:
    lines = text.splitlines()
    if not lines:
        return ""
    start = max(1, line_no - radius)
    end = min(len(lines), line_no + radius)
    out = []
    for idx in range(start, end + 1):
        prefix = ">" if idx == line_no else " "
        out.append(f"{prefix}{idx}: {lines[idx-1]}")
    return "\n".join(out)


def _best_term_lines(text: str, query_terms: Sequence[str], limit: int = 3) -> List[Dict[str, Any]]:
    lines = text.splitlines()
    ranked = []
    q = set(query_terms)
    for i, line in enumerate(lines, start=1):
        lt = set(_tokens(line))
        score = len(q & lt)
        if score:
            ranked.append({"line": i, "score": score, "snippet": _line_snippet(text, i, 1)})
    ranked.sort(key=lambda x: (-x["score"], x["line"]))
    return ranked[:limit]


@dataclass
class SymbolRecord:
    name: str
    kind: str
    file: str
    line_start: int
    line_end: int
    signature: str
    parent: str = ""


def _extract_python_symbols(root: Path, path: Path, text: str) -> List[SymbolRecord]:
    records: List[SymbolRecord] = []
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return records

    parents: List[str] = []

    class Visitor(ast.NodeVisitor):
        def visit_ClassDef(self, node: ast.ClassDef) -> None:
            parent = ".".join(parents)
            records.append(SymbolRecord(
                name=node.name,
                kind="class",
                file=_rel(root, path),
                line_start=getattr(node, "lineno", 1),
                line_end=getattr(node, "end_lineno", getattr(node, "lineno", 1)),
                signature=f"class {node.name}",
                parent=parent,
            ))
            parents.append(node.name)
            self.generic_visit(node)
            parents.pop()

        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            parent = ".".join(parents)
            args = []
            try:
                args = [a.arg for a in node.args.args]
            except Exception:
                args = []
            records.append(SymbolRecord(
                name=node.name,
                kind="function" if not parent else "method",
                file=_rel(root, path),
                line_start=getattr(node, "lineno", 1),
                line_end=getattr(node, "end_lineno", getattr(node, "lineno", 1)),
                signature=f"def {node.name}({', '.join(args)})",
                parent=parent,
            ))
            parents.append(node.name)
            self.generic_visit(node)
            parents.pop()

        def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
            parent = ".".join(parents)
            args = [a.arg for a in node.args.args]
            records.append(SymbolRecord(
                name=node.name,
                kind="async_function" if not parent else "async_method",
                file=_rel(root, path),
                line_start=getattr(node, "lineno", 1),
                line_end=getattr(node, "end_lineno", getattr(node, "lineno", 1)),
                signature=f"async def {node.name}({', '.join(args)})",
                parent=parent,
            ))
            parents.append(node.name)
            self.generic_visit(node)
            parents.pop()

    Visitor().visit(tree)
    return records


JS_SYMBOL_RE = re.compile(
    r"(?P<kind>class|function|interface|type)\s+(?P<name>[A-Za-z_$][A-Za-z0-9_$]*)|"
    r"(?:export\s+)?(?:const|let|var)\s+(?P<var>[A-Za-z_$][A-Za-z0-9_$]*)\s*=\s*(?:async\s*)?(?:\([^)]*\)|[A-Za-z_$][A-Za-z0-9_$]*)\s*=>|"
    r"(?:export\s+)?(?:async\s+)?function\s+(?P<fname>[A-Za-z_$][A-Za-z0-9_$]*)"
)


def _extract_js_symbols(root: Path, path: Path, text: str) -> List[SymbolRecord]:
    records: List[SymbolRecord] = []
    offsets = []
    pos = 0
    for line_no, line in enumerate(text.splitlines(True), start=1):
        offsets.append((pos, line_no))
        pos += len(line)
    def offset_to_line(offset: int) -> int:
        current = 1
        for start, line_no in offsets:
            if start <= offset:
                current = line_no
            else:
                break
        return current
    for m in JS_SYMBOL_RE.finditer(text):
        name = m.group("name") or m.group("var") or m.group("fname")
        if not name:
            continue
        kind = m.group("kind") or ("function" if m.group("fname") else "constant")
        line = offset_to_line(m.start())
        signature = text.splitlines()[line-1].strip()[:180] if text.splitlines() else name
        records.append(SymbolRecord(name=name, kind=kind, file=_rel(root, path), line_start=line, line_end=line, signature=signature))
    return records


def extract_symbols(root: str | Path, file_path: str | Path | None = None) -> List[Dict[str, Any]]:
    """Extract class/function/module symbols from a workspace or one file."""
    root_p = _safe_root(root)
    paths = [root_p / file_path] if file_path else _code_files(root_p)
    records: List[SymbolRecord] = []
    for path in paths:
        if not path.exists() or path.suffix.lower() not in CODE_EXTS:
            continue
        text = _read_text(path)
        if path.suffix.lower() == ".py":
            records.extend(_extract_python_symbols(root_p, path, text))
        elif path.suffix.lower() in {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"}:
            records.extend(_extract_js_symbols(root_p, path, text))
        else:
            # Generic fallback for languages not yet parsed deeply.
            for i, line in enumerate(text.splitlines(), start=1):
                m = re.search(r"\b(class|function|func|def)\s+([A-Za-z_][A-Za-z0-9_]*)", line)
                if m:
                    records.append(SymbolRecord(m.group(2), m.group(1), _rel(root_p, path), i, i, line.strip()[:180]))
    return [asdict(r) for r in records]


def _build_module_index(root: Path, files: List[Path]) -> Dict[str, str]:
    modules: Dict[str, str] = {}
    for f in files:
        rel = _rel(root, f)
        stem = f.stem
        modules[stem] = rel
        if f.suffix == ".py":
            parts = list(Path(rel).with_suffix("").parts)
            if parts and parts[-1] == "__init__":
                parts.pop()
            if parts:
                modules[".".join(parts)] = rel
                modules[parts[-1]] = rel
        else:
            modules[stem] = rel
    return modules


def _extract_imports(root: Path, path: Path, text: str, module_index: Dict[str, str]) -> List[Dict[str, str]]:
    imports: List[Dict[str, str]] = []
    rel = _rel(root, path)
    if path.suffix.lower() == ".py":
        try:
            tree = ast.parse(text)
        except SyntaxError:
            tree = None
        if tree:
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        name = alias.name
                        target = module_index.get(name) or module_index.get(name.split(".")[-1])
                        if target:
                            imports.append({"source": rel, "target": target, "import": name})
                elif isinstance(node, ast.ImportFrom):
                    mod = node.module or ""
                    candidates = [mod, mod.split(".")[-1]] + [a.name for a in node.names]
                    for cand in candidates:
                        target = module_index.get(cand)
                        if target:
                            imports.append({"source": rel, "target": target, "import": cand})
                            break
    elif path.suffix.lower() in {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"}:
        for m in re.finditer(r"from\s+['\"](?P<mod>[^'\"]+)['\"]|require\(['\"](?P<req>[^'\"]+)['\"]\)", text):
            mod = m.group("mod") or m.group("req") or ""
            name = Path(mod).stem
            target = module_index.get(name)
            if target:
                imports.append({"source": rel, "target": target, "import": mod})
    return imports


def _dependency_edges(root: Path) -> List[Dict[str, str]]:
    files = _code_files(root)
    module_index = _build_module_index(root, files)
    edges: List[Dict[str, str]] = []
    seen = set()
    for path in files:
        text = _read_text(path)
        for e in _extract_imports(root, path, text, module_index):
            key = (e["source"], e["target"], e["import"])
            if e["source"] != e["target"] and key not in seen:
                seen.add(key)
                edges.append(e)
    return edges


def _tool_envelope(tool: str, payload: Dict[str, Any], next_step: str, confidence: str = "medium") -> Dict[str, Any]:
    return {
        "tool": tool,
        "status": "ok",
        "confidence": confidence,
        "payload": payload,
        "next_action_hint": {
            "recommended_next_step": next_step,
            "llm_must_decide": True,
            "planner_is_advisory_only": True,
            "allowed_by_r2_default": True,
        },
    }


def issue_to_file_localizer(root: str | Path, issue_text: str, limit: int = 8) -> Dict[str, Any]:
    """Rank likely files for a bug report, feature request, traceback, or failing test log."""
    root_p = _safe_root(root)
    q_terms = _tokens(issue_text)
    q_counter = Counter(q_terms)
    files = _code_files(root_p)
    symbols = extract_symbols(root_p)
    symbols_by_file: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for s in symbols:
        symbols_by_file[s["file"]].append(s)

    trace_hits: Dict[str, List[int]] = defaultdict(list)
    for m in TRACE_FILE_RE.finditer(issue_text or ""):
        raw = m.group("py") or m.group("plain")
        line = int(m.group("pyline") or m.group("line") or 0)
        if raw:
            norm = raw.replace("\\", "/")
            for f in files:
                rel = _rel(root_p, f)
                if norm.endswith(rel) or rel.endswith(norm) or Path(norm).name == f.name:
                    trace_hits[rel].append(line)

    ranked: List[Dict[str, Any]] = []
    n_files = max(1, len(files))
    doc_freq: Counter[str] = Counter()
    file_terms: Dict[str, Counter[str]] = {}
    for path in files:
        rel = _rel(root_p, path)
        text = _read_text(path)
        terms = Counter(_tokens(rel + "\n" + text[:120_000] + "\n" + " ".join(s["name"] for s in symbols_by_file.get(rel, []))))
        file_terms[rel] = terms
        for t in set(terms):
            doc_freq[t] += 1

    for path in files:
        rel = _rel(root_p, path)
        terms = file_terms[rel]
        matched = sorted(set(q_terms) & set(terms))
        score = 0.0
        for t in matched:
            idf = math.log((n_files + 1) / (doc_freq[t] + 1)) + 1
            score += min(terms[t], 8) * q_counter[t] * idf
        # Path and symbol signal are stronger than body coincidence.
        path_terms = set(_tokens(rel))
        symbol_terms = set(_tokens(" ".join(s["name"] for s in symbols_by_file.get(rel, []))))
        score += 7.0 * len(set(q_terms) & path_terms)
        score += 5.0 * len(set(q_terms) & symbol_terms)
        if trace_hits.get(rel):
            score += 100.0 + 10.0 * len(trace_hits[rel])
        if any(h in rel.lower() for h in TEST_HINTS) and any(t in q_terms for t in ("test", "pytest", "assert", "failure", "failed")):
            score += 6.0
        if score <= 0:
            continue
        text = _read_text(path)
        ranked.append({
            "file": rel,
            "score": round(score, 3),
            "matched_terms": matched[:20],
            "traceback_lines": trace_hits.get(rel, []),
            "symbol_matches": [s for s in symbols_by_file.get(rel, []) if set(_tokens(s["name"])) & set(q_terms)][:8],
            "evidence_snippets": _best_term_lines(text, q_terms, 2),
        })
    ranked.sort(key=lambda x: (-x["score"], x["file"]))
    payload = {"issue_excerpt": (issue_text or "")[:500], "ranked_files": ranked[:limit], "total_candidates": len(ranked)}
    next_step = "open_top_ranked_files_then_call_file_to_symbol_localizer"
    return _tool_envelope("issue_to_file_localizer", payload, next_step, "high" if ranked else "low")


def file_to_symbol_localizer(root: str | Path, file_path: str, query: str = "", limit: int = 20) -> Dict[str, Any]:
    """Rank symbols inside one file; if query is empty, return all symbols in source order."""
    root_p = _safe_root(root)
    symbols = extract_symbols(root_p, file_path)
    q_terms = set(_tokens(query))
    ranked = []
    for s in symbols:
        s_terms = set(_tokens(s["name"] + " " + s["signature"] + " " + s.get("parent", "")))
        score = len(q_terms & s_terms) if q_terms else 1
        if score or not q_terms:
            item = dict(s)
            item["score"] = score
            item["matched_terms"] = sorted(q_terms & s_terms)
            ranked.append(item)
    ranked.sort(key=lambda x: (-x["score"], x["line_start"]))
    return _tool_envelope(
        "file_to_symbol_localizer",
        {"file": file_path, "query": query, "symbols": ranked[:limit], "total_symbols": len(symbols)},
        "call_symbol_to_line_localizer_or_start_patch_plan",
        "high" if ranked else "low",
    )


def symbol_to_line_localizer(root: str | Path, symbol_name: str, file_path: str | None = None, limit: int = 12) -> Dict[str, Any]:
    """Find exact or fuzzy symbol line ranges across the workspace or a file."""
    root_p = _safe_root(root)
    all_symbols = extract_symbols(root_p, file_path)
    q = symbol_name.lower()
    hits = []
    for s in all_symbols:
        name = s["name"].lower()
        if name == q:
            score = 100
        elif q in name or name in q:
            score = 60
        else:
            st = set(_tokens(s["name"] + " " + s["signature"] + " " + s.get("parent", "")))
            qt = set(_tokens(symbol_name))
            score = 20 * len(st & qt)
        if score:
            path = root_p / s["file"]
            text = _read_text(path) if path.exists() else ""
            item = dict(s)
            item["score"] = score
            item["snippet"] = _line_snippet(text, s["line_start"], 2)
            hits.append(item)
    hits.sort(key=lambda x: (-x["score"], x["file"], x["line_start"]))
    return _tool_envelope(
        "symbol_to_line_localizer",
        {"symbol_name": symbol_name, "file_scope": file_path, "hits": hits[:limit], "total_hits": len(hits)},
        "inspect_line_range_then_generate_patch_plan",
        "high" if hits else "low",
    )


def semantic_code_search(root: str | Path, query: str, limit: int = 12) -> Dict[str, Any]:
    """Lexical-semantic search optimized for LLM tool use; no vector DB dependency."""
    root_p = _safe_root(root)
    q_terms = _tokens(query)
    q_set = set(q_terms)
    phrase = (query or "").strip().lower()
    results = []
    for path in _code_files(root_p):
        rel = _rel(root_p, path)
        text = _read_text(path)
        terms = Counter(_tokens(rel + "\n" + text))
        overlap = q_set & set(terms)
        if not overlap and phrase not in text.lower():
            continue
        score = sum(min(terms[t], 8) for t in overlap)
        if phrase and phrase in text.lower():
            score += 25
        if set(_tokens(rel)) & q_set:
            score += 10 * len(set(_tokens(rel)) & q_set)
        snippets = _best_term_lines(text, q_terms, 3)
        if phrase and phrase in text.lower() and not snippets:
            idx = text.lower().find(phrase)
            line_no = text[:idx].count("\n") + 1
            snippets = [{"line": line_no, "score": 25, "snippet": _line_snippet(text, line_no, 1)}]
        results.append({"file": rel, "score": round(float(score), 3), "matched_terms": sorted(overlap)[:20], "snippets": snippets})
    results.sort(key=lambda x: (-x["score"], x["file"]))
    return _tool_envelope(
        "semantic_code_search",
        {"query": query, "results": results[:limit], "total_results": len(results)},
        "call_file_to_symbol_localizer_or_issue_to_file_localizer_for_ranked_file",
        "high" if results else "low",
    )


def graph_code_search(root: str | Path, seed_files: Sequence[str], depth: int = 1, limit: int = 30) -> Dict[str, Any]:
    """Expand from seed files over import/dependency adjacency."""
    root_p = _safe_root(root)
    edges = _dependency_edges(root_p)
    forward: Dict[str, List[Dict[str, str]]] = defaultdict(list)
    reverse: Dict[str, List[Dict[str, str]]] = defaultdict(list)
    for e in edges:
        forward[e["source"]].append(e)
        reverse[e["target"]].append(e)
    normalized = []
    all_files = {_rel(root_p, p) for p in _code_files(root_p)}
    for s in seed_files:
        s2 = str(s).replace("\\", "/")
        matches = [f for f in all_files if f == s2 or f.endswith(s2) or Path(f).name == Path(s2).name]
        normalized.extend(matches or [s2])
    seen = set(normalized)
    frontier = list(normalized)
    related = []
    for d in range(max(0, depth)):
        new_frontier = []
        for f in frontier:
            for e in forward.get(f, []):
                if e["target"] not in seen:
                    seen.add(e["target"]); new_frontier.append(e["target"])
                    related.append({"file": e["target"], "relation": "imported_by_seed", "via": e})
            for e in reverse.get(f, []):
                if e["source"] not in seen:
                    seen.add(e["source"]); new_frontier.append(e["source"])
                    related.append({"file": e["source"], "relation": "dependent_of_seed", "via": e})
        frontier = new_frontier
    return _tool_envelope(
        "graph_code_search",
        {"seed_files": normalized, "depth": depth, "edges_considered": len(edges), "related_files": related[:limit]},
        "inspect_related_files_then_run_affected_area_detector",
        "high" if related else "medium",
    )


def test_failure_trace_mapper(root: str | Path, failure_log: str, limit: int = 20) -> Dict[str, Any]:
    """Map pytest/traceback-like logs to likely source and test files."""
    root_p = _safe_root(root)
    files = {_rel(root_p, p): p for p in _code_files(root_p)}
    implicated: Dict[str, Dict[str, Any]] = {}
    failing_tests = []
    for m in PYTEST_NODE_RE.finditer(failure_log or ""):
        file = m.group("file").replace("\\", "/")
        test = m.group("test")
        matched = [rel for rel in files if rel.endswith(file) or file.endswith(rel)]
        target = matched[0] if matched else file
        failing_tests.append({"file": target, "test": test})
        implicated.setdefault(target, {"file": target, "lines": [], "reasons": []})["reasons"].append("pytest_nodeid")
    for m in TRACE_FILE_RE.finditer(failure_log or ""):
        raw = m.group("py") or m.group("plain")
        line = int(m.group("pyline") or m.group("line") or 0)
        if not raw:
            continue
        norm = raw.replace("\\", "/")
        matched = [rel for rel in files if norm.endswith(rel) or rel.endswith(norm) or Path(norm).name == Path(rel).name]
        target = matched[0] if matched else norm
        rec = implicated.setdefault(target, {"file": target, "lines": [], "reasons": []})
        if line:
            rec["lines"].append(line)
        rec["reasons"].append("traceback")
    error_class = None
    error_message = ""
    for line in (failure_log or "").splitlines():
        m = ERROR_CLASS_RE.search(line.strip())
        if m:
            error_class = m.group("error")
            error_message = m.group("msg")[:300]
            break
    ranked = []
    for rel, rec in implicated.items():
        score = 50 + 10 * len(rec["lines"]) + 5 * len(rec["reasons"])
        if any(h in rel.lower() for h in TEST_HINTS):
            score += 8
        rec["score"] = score
        rec["lines"] = sorted(set(rec["lines"]))
        rec["reasons"] = sorted(set(rec["reasons"]))
        p = files.get(rel)
        if p and rec["lines"]:
            rec["snippets"] = [_line_snippet(_read_text(p), line, 1) for line in rec["lines"][:2]]
        ranked.append(rec)
    ranked.sort(key=lambda x: (-x["score"], x["file"]))
    return _tool_envelope(
        "test_failure_trace_mapper",
        {"error_class": error_class, "error_message": error_message, "failing_tests": failing_tests, "implicated_files": ranked[:limit]},
        "call_failure_attribution_analyzer_in_R9_or_issue_to_file_localizer_now",
        "high" if ranked else "low",
    )


def affected_area_detector(root: str | Path, changed_files: Sequence[str], limit: int = 50) -> Dict[str, Any]:
    """Estimate impacted files/tests from changed source files using dependencies and test naming conventions."""
    root_p = _safe_root(root)
    all_files = {_rel(root_p, p): p for p in _code_files(root_p)}
    normalized = []
    for c in changed_files:
        c2 = str(c).replace("\\", "/")
        matches = [rel for rel in all_files if rel == c2 or rel.endswith(c2) or Path(rel).name == Path(c2).name]
        normalized.extend(matches or [c2])
    normalized = sorted(set(normalized))
    graph = graph_code_search(root_p, normalized, depth=1, limit=limit)["payload"]["related_files"]
    related_tests = []
    changed_names = {Path(f).stem.replace("test_", "") for f in normalized}
    for rel, path in all_files.items():
        low = rel.lower()
        if any(h in low for h in TEST_HINTS):
            tokens = set(_tokens(rel + "\n" + _read_text(path)[:100_000]))
            if tokens & {n.lower() for n in changed_names}:
                related_tests.append({"file": rel, "reason": "test_name_or_import_matches_changed_file"})
    impacted = []
    for f in normalized:
        impacted.append({"file": f, "impact": "direct_changed", "risk": "direct"})
    for item in graph:
        impacted.append({"file": item["file"], "impact": item["relation"], "risk": "medium"})
    for item in related_tests:
        impacted.append({"file": item["file"], "impact": item["reason"], "risk": "test_validation"})
    dedup = []
    seen = set()
    for item in impacted:
        key = (item["file"], item["impact"])
        if key not in seen:
            seen.add(key); dedup.append(item)
    risk_level = "low"
    if len(dedup) > 12 or len(normalized) > 3:
        risk_level = "high"
    elif len(dedup) > 4:
        risk_level = "medium"
    return _tool_envelope(
        "affected_area_detector",
        {"changed_files": normalized, "risk_level": risk_level, "impacted_areas": dedup[:limit], "total_impacted": len(dedup)},
        "use_impacted_areas_to_select_tests_or_prepare_patch_audit",
        "high" if dedup else "low",
    )


R6_TOOL_NAMES = [
    "issue_to_file_localizer",
    "file_to_symbol_localizer",
    "symbol_to_line_localizer",
    "semantic_code_search",
    "graph_code_search",
    "test_failure_trace_mapper",
    "affected_area_detector",
]
