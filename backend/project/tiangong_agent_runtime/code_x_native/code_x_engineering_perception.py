"""L6.70.2-CodeX R4 engineering perception candidate tools.

Design boundary:
- Candidate-only implementation; not registered into Runtime.
- No v1 imports, no v1 source copying, no runtime patching, no background loop.
- Read-only workspace scanning. It never writes to the scanned repository.
- LLM remains final decision maker; these tools return evidence and next_action_hint only.

The module intentionally uses only Python standard library to keep the candidate portable.
"""
from __future__ import annotations

import ast
import fnmatch
import hashlib
import json
import os
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

IGNORE_DIRS = {
    ".git",
    ".hg",
    ".svn",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    "venv",
    "env",
    "node_modules",
    "dist",
    "build",
    "target",
    "out",
    ".next",
    ".turbo",
    ".cache",
}

SOURCE_EXTS = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".go", ".rs", ".c", ".cc", ".cpp",
    ".h", ".hpp", ".cs", ".php", ".rb", ".swift", ".kt", ".kts", ".scala", ".sh",
}
TEST_HINTS = ("test", "tests", "spec", "__tests__")
CONFIG_NAMES = {
    "pyproject.toml", "setup.py", "setup.cfg", "requirements.txt", "requirements-dev.txt",
    "Pipfile", "poetry.lock", "package.json", "pnpm-lock.yaml", "yarn.lock", "package-lock.json",
    "tsconfig.json", "vite.config.js", "vite.config.ts", "next.config.js", "next.config.mjs",
    "webpack.config.js", "rollup.config.js", "eslint.config.js", ".eslintrc", ".eslintrc.json",
    "ruff.toml", ".ruff.toml", "mypy.ini", ".pre-commit-config.yaml", "Dockerfile",
    "docker-compose.yml", "compose.yml", "Makefile", "tox.ini", "pytest.ini", "CODEOWNERS",
}
DOC_EXTS = {".md", ".rst", ".txt", ".adoc"}
ARTIFACT_EXTS = {".pyc", ".pyo", ".class", ".o", ".so", ".dll", ".exe", ".zip", ".tar", ".gz", ".whl"}
TEXT_PARSE_MAX_BYTES = 1_200_000

SAFE_BLOCKED_ROOT_NAMES = {
    "", "/", "/bin", "/sbin", "/etc", "/usr", "/var", "/opt", "/System", "/Library",
    "C:\\", "C:\\Windows", "C:\\Program Files", "C:\\Program Files (x86)",
}


@dataclass(frozen=True)
class EvidenceRef:
    kind: str
    path: str
    line: Optional[int] = None
    note: str = ""


@dataclass(frozen=True)
class NextActionHint:
    recommended_next: str
    reason: str
    alternatives: Tuple[str, ...] = ()
    stop_reason: Optional[str] = None


def _stable_hash(payload: Any) -> str:
    data = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(data).hexdigest()[:16]


def _envelope(tool_id: str, task_id: str, status: str, summary: str, artifacts: Dict[str, Any],
              evidence: Optional[List[EvidenceRef]] = None,
              next_action: str = "continue_read",
              reason: str = "工程感知结果已生成，建议继续定位或生成补丁计划。",
              alternatives: Tuple[str, ...] = ("localize_issue", "plan_patch", "handoff"),
              blocker_type: Optional[str] = None) -> Dict[str, Any]:
    ev = [asdict(e) for e in (evidence or [])]
    return {
        "tool_id": tool_id,
        "task_id": task_id,
        "status": status,
        "summary": summary,
        "evidence": ev,
        "artifacts": artifacts,
        "changed_files": [],
        "risk_report": {"risk_level": "A1", "mode": "read_only", "blocker_type": blocker_type},
        "audit_event": {
            "decision_owner": "LLM",
            "planner_role": "advisor_only",
            "subagent_role": "evidence_only",
            "output_hash": _stable_hash({"summary": summary, "artifacts": artifacts, "evidence": ev}),
        },
        "next_action_hint": asdict(NextActionHint(next_action, reason, alternatives, blocker_type)),
    }


def _resolve_workspace(workspace_root: str | os.PathLike[str]) -> Path:
    root = Path(workspace_root).expanduser().resolve()
    root_str = str(root)
    if root_str in SAFE_BLOCKED_ROOT_NAMES:
        raise ValueError(f"blocked workspace root: {root_str}")
    if not root.exists() or not root.is_dir():
        raise FileNotFoundError(f"workspace root not found or not directory: {root_str}")
    return root


def _rel(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def _is_ignored_dir(name: str) -> bool:
    return name in IGNORE_DIRS or name.startswith(".mypy_cache")


def _walk_files(root: Path, max_files: int = 5000) -> List[Path]:
    files: List[Path] = []
    for current, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if not _is_ignored_dir(d)]
        for name in sorted(filenames):
            path = Path(current) / name
            files.append(path)
            if len(files) >= max_files:
                return files
    return files


def _safe_read_text(path: Path, max_bytes: int = TEXT_PARSE_MAX_BYTES) -> Optional[str]:
    try:
        if path.stat().st_size > max_bytes:
            return None
        raw = path.read_bytes()
        try:
            return raw.decode("utf-8")
        except UnicodeDecodeError:
            return raw.decode("utf-8", errors="replace")
    except OSError:
        return None


def _line_of_text(text: str, pattern: str) -> Optional[int]:
    for idx, line in enumerate(text.splitlines(), 1):
        if pattern in line:
            return idx
    return None


def _classify_file(root: Path, path: Path) -> str:
    rel = _rel(root, path).lower()
    name = path.name
    ext = path.suffix.lower()
    parts = set(Path(rel).parts)
    if name in CONFIG_NAMES or name.lower() in {n.lower() for n in CONFIG_NAMES}:
        return "config"
    if ext in ARTIFACT_EXTS:
        return "artifact"
    if ext in DOC_EXTS:
        return "doc"
    if any(h in parts for h in TEST_HINTS) or path.name.startswith("test_") or path.name.endswith("_test.py") or ".spec." in path.name or ".test." in path.name:
        return "test"
    if ext in SOURCE_EXTS:
        return "source"
    return "other"


def file_tree_scan(workspace_root: str, task_id: str = "r4-demo", max_files: int = 5000) -> Dict[str, Any]:
    """Scan files and classify them. Read-only."""
    try:
        root = _resolve_workspace(workspace_root)
        files = _walk_files(root, max_files=max_files)
        entries: List[Dict[str, Any]] = []
        counts = Counter()
        ext_counts = Counter()
        for path in files:
            try:
                st = path.stat()
            except OSError:
                continue
            kind = _classify_file(root, path)
            counts[kind] += 1
            ext_counts[path.suffix.lower() or "[no_ext]"] += 1
            entries.append({
                "path": _rel(root, path),
                "kind": kind,
                "extension": path.suffix.lower(),
                "size_bytes": st.st_size,
            })
        truncated = len(files) >= max_files
        artifacts = {
            "workspace_root": str(root),
            "file_count": len(entries),
            "truncated": truncated,
            "counts_by_kind": dict(counts),
            "counts_by_extension": dict(ext_counts.most_common(40)),
            "files": entries,
            "ignored_dirs": sorted(IGNORE_DIRS),
        }
        status = "partial" if truncated else "success"
        return _envelope(
            "code_x.file_tree_scan", task_id, status,
            f"扫描 {len(entries)} 个文件，源码 {counts.get('source', 0)}，测试 {counts.get('test', 0)}，配置 {counts.get('config', 0)}。",
            artifacts,
            evidence=[EvidenceRef("workspace", ".", note="file tree scanned")],
            next_action="continue_read",
            reason="文件树已分类，建议继续 repo_map 或 symbol_index。",
            alternatives=("repo_map", "symbol_index", "localize_issue"),
        )
    except Exception as exc:  # candidate boundary: return structured failure, do not raise into Runtime
        return _envelope("code_x.file_tree_scan", task_id, "blocked", f"文件树扫描阻断：{exc}", {}, [], "handoff", "扫描失败，建议交接阻断原因。", ("state_recover",), type(exc).__name__)


def _module_name_from_path(root: Path, path: Path) -> str:
    rel = path.relative_to(root).with_suffix("").as_posix()
    rel = rel.replace("/", ".")
    for prefix in ("src.", "lib."):
        if rel.startswith(prefix):
            return rel[len(prefix):]
    return rel


def _parse_python_symbols(root: Path, path: Path, text: str) -> Tuple[List[Dict[str, Any]], List[str], List[EvidenceRef]]:
    symbols: List[Dict[str, Any]] = []
    imports: List[str] = []
    evidence: List[EvidenceRef] = []
    try:
        tree = ast.parse(text, filename=str(path))
    except SyntaxError as exc:
        evidence.append(EvidenceRef("parse_error", _rel(root, path), exc.lineno, f"SyntaxError: {exc.msg}"))
        return symbols, imports, evidence
    module = _module_name_from_path(root, path)
    symbols.append({"kind": "module", "name": module, "path": _rel(root, path), "line": 1})
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            symbols.append({"kind": "function", "name": node.name, "qualified_name": f"{module}.{node.name}", "path": _rel(root, path), "line": node.lineno})
            evidence.append(EvidenceRef("symbol", _rel(root, path), node.lineno, f"function {node.name}"))
        elif isinstance(node, ast.ClassDef):
            symbols.append({"kind": "class", "name": node.name, "qualified_name": f"{module}.{node.name}", "path": _rel(root, path), "line": node.lineno})
            evidence.append(EvidenceRef("symbol", _rel(root, path), node.lineno, f"class {node.name}"))
        elif isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)
    return symbols, sorted(set(imports)), evidence


def _parse_js_ts_symbols(root: Path, path: Path, text: str) -> Tuple[List[Dict[str, Any]], List[str], List[EvidenceRef]]:
    symbols: List[Dict[str, Any]] = []
    imports: List[str] = []
    evidence: List[EvidenceRef] = []
    rel = _rel(root, path)
    patterns = [
        ("function", re.compile(r"\b(?:export\s+)?(?:async\s+)?function\s+([A-Za-z_$][\w$]*)")),
        ("class", re.compile(r"\b(?:export\s+)?class\s+([A-Za-z_$][\w$]*)")),
        ("const_function", re.compile(r"\b(?:export\s+)?const\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?\(")),
    ]
    import_re = re.compile(r"(?:import\s+.*?\s+from\s+['\"]([^'\"]+)['\"]|require\(['\"]([^'\"]+)['\"]\))")
    for idx, line in enumerate(text.splitlines(), 1):
        for m in import_re.finditer(line):
            imports.append(m.group(1) or m.group(2))
        for kind, pattern in patterns:
            for m in pattern.finditer(line):
                name = m.group(1)
                symbols.append({"kind": kind, "name": name, "qualified_name": f"{rel}:{name}", "path": rel, "line": idx})
                evidence.append(EvidenceRef("symbol", rel, idx, f"{kind} {name}"))
    return symbols, sorted(set(imports)), evidence


def symbol_index(workspace_root: str, task_id: str = "r4-demo", max_files: int = 5000) -> Dict[str, Any]:
    """Build a lightweight symbol index for Python and JS/TS family files."""
    try:
        root = _resolve_workspace(workspace_root)
        symbols: List[Dict[str, Any]] = []
        imports_by_file: Dict[str, List[str]] = {}
        evidence: List[EvidenceRef] = []
        parse_errors: List[Dict[str, Any]] = []
        for path in _walk_files(root, max_files=max_files):
            ext = path.suffix.lower()
            if ext not in {".py", ".js", ".jsx", ".ts", ".tsx"}:
                continue
            text = _safe_read_text(path)
            if text is None:
                continue
            if ext == ".py":
                syms, imports, ev = _parse_python_symbols(root, path, text)
                for item in ev:
                    if item.kind == "parse_error":
                        parse_errors.append(asdict(item))
                symbols.extend(syms)
                imports_by_file[_rel(root, path)] = imports
                evidence.extend(ev[:20])
            else:
                syms, imports, ev = _parse_js_ts_symbols(root, path, text)
                symbols.extend(syms)
                imports_by_file[_rel(root, path)] = imports
                evidence.extend(ev[:20])
        counts = Counter(s["kind"] for s in symbols)
        artifacts = {
            "symbol_count": len(symbols),
            "counts_by_kind": dict(counts),
            "symbols": symbols,
            "imports_by_file": imports_by_file,
            "parse_errors": parse_errors,
        }
        status = "partial" if parse_errors else "success"
        return _envelope(
            "code_x.symbol_index", task_id, status,
            f"建立 {len(symbols)} 个符号索引，parse_errors={len(parse_errors)}。",
            artifacts,
            evidence=evidence[:50],
            next_action="localize_issue",
            reason="符号索引已生成，建议继续依赖图/调用图或定位修改点。",
            alternatives=("dependency_graph", "call_graph", "affected_area_detector", "plan_patch"),
        )
    except Exception as exc:
        return _envelope("code_x.symbol_index", task_id, "blocked", f"符号索引阻断：{exc}", {}, [], "handoff", "索引失败，建议交接阻断原因。", ("state_recover",), type(exc).__name__)


def dependency_graph(workspace_root: str, task_id: str = "r4-demo", max_files: int = 5000) -> Dict[str, Any]:
    """Construct file-level import/dependency graph. Best-effort and read-only."""
    try:
        root = _resolve_workspace(workspace_root)
        idx = symbol_index(str(root), task_id, max_files=max_files)["artifacts"]
        module_to_file: Dict[str, str] = {}
        for sym in idx.get("symbols", []):
            if sym.get("kind") == "module":
                module_to_file[sym["name"]] = sym["path"]
        edges: List[Dict[str, str]] = []
        external = defaultdict(list)
        for file_path, imports in idx.get("imports_by_file", {}).items():
            for imp in imports:
                target = None
                # Exact and prefix mapping for Python packages.
                if imp in module_to_file:
                    target = module_to_file[imp]
                else:
                    head = imp.split(".")[0]
                    for mod, mod_file in module_to_file.items():
                        if mod == head or mod.startswith(head + "."):
                            target = mod_file
                            break
                # JS/TS relative import mapping.
                if target is None and imp.startswith("."):
                    base = (root / file_path).parent
                    candidate_base = (base / imp).resolve()
                    for suffix in ("", ".js", ".jsx", ".ts", ".tsx", "/index.js", "/index.ts", ".py"):
                        cand = Path(str(candidate_base) + suffix)
                        if cand.exists() and cand.is_file() and root in cand.parents:
                            target = _rel(root, cand)
                            break
                if target:
                    edges.append({"from": file_path, "to": target, "import": imp, "scope": "internal"})
                else:
                    external[file_path].append(imp)
        artifacts = {
            "internal_edge_count": len(edges),
            "internal_edges": edges,
            "external_imports_by_file": dict(external),
        }
        return _envelope(
            "code_x.dependency_graph", task_id, "success",
            f"生成依赖图：内部边 {len(edges)}，外部依赖文件 {len(external)}。",
            artifacts,
            evidence=[EvidenceRef("dependency_edge", e["from"], note=f"imports {e['to']}") for e in edges[:50]],
            next_action="localize_issue",
            reason="依赖图已生成，建议结合 issue/test failure 计算影响范围。",
            alternatives=("affected_area_detector", "test_map", "plan_patch"),
        )
    except Exception as exc:
        return _envelope("code_x.dependency_graph", task_id, "blocked", f"依赖图阻断：{exc}", {}, [], "handoff", "依赖图失败，建议交接阻断原因。", ("state_recover",), type(exc).__name__)


class _CallVisitor(ast.NodeVisitor):
    def __init__(self, root: Path, path: Path, module: str) -> None:
        self.root = root
        self.path = path
        self.module = module
        self.scope_stack: List[str] = []
        self.calls: List[Dict[str, Any]] = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> Any:
        self.scope_stack.append(node.name)
        self.generic_visit(node)
        self.scope_stack.pop()

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> Any:
        self.visit_FunctionDef(node)  # type: ignore[arg-type]

    def visit_Call(self, node: ast.Call) -> Any:
        if self.scope_stack:
            callee = self._callee_name(node.func)
            if callee:
                self.calls.append({
                    "from": f"{self.module}.{'.'.join(self.scope_stack)}",
                    "to": callee,
                    "path": _rel(self.root, self.path),
                    "line": getattr(node, "lineno", None),
                })
        self.generic_visit(node)

    def _callee_name(self, node: ast.AST) -> Optional[str]:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            base = self._callee_name(node.value)
            return f"{base}.{node.attr}" if base else node.attr
        return None


def call_graph(workspace_root: str, task_id: str = "r4-demo", max_files: int = 5000) -> Dict[str, Any]:
    """Build best-effort Python call graph. JS/TS support is intentionally deferred."""
    try:
        root = _resolve_workspace(workspace_root)
        calls: List[Dict[str, Any]] = []
        parse_errors: List[Dict[str, Any]] = []
        for path in _walk_files(root, max_files=max_files):
            if path.suffix.lower() != ".py":
                continue
            text = _safe_read_text(path)
            if text is None:
                continue
            try:
                tree = ast.parse(text, filename=str(path))
            except SyntaxError as exc:
                parse_errors.append({"path": _rel(root, path), "line": exc.lineno, "msg": exc.msg})
                continue
            visitor = _CallVisitor(root, path, _module_name_from_path(root, path))
            visitor.visit(tree)
            calls.extend(visitor.calls)
        artifacts = {"call_edge_count": len(calls), "call_edges": calls, "parse_errors": parse_errors}
        status = "partial" if parse_errors else "success"
        return _envelope(
            "code_x.call_graph", task_id, status,
            f"生成 Python 调用图：调用边 {len(calls)}，parse_errors={len(parse_errors)}。",
            artifacts,
            evidence=[EvidenceRef("call_edge", c["path"], c.get("line"), f"{c['from']} -> {c['to']}") for c in calls[:50]],
            next_action="localize_issue",
            reason="调用图已生成，建议结合符号索引计算修改影响范围。",
            alternatives=("affected_area_detector", "test_map", "plan_patch"),
        )
    except Exception as exc:
        return _envelope("code_x.call_graph", task_id, "blocked", f"调用图阻断：{exc}", {}, [], "handoff", "调用图失败，建议交接阻断原因。", ("state_recover",), type(exc).__name__)


def test_map(workspace_root: str, task_id: str = "r4-demo", max_files: int = 5000) -> Dict[str, Any]:
    """Map test files to probable source files via naming and imports."""
    try:
        root = _resolve_workspace(workspace_root)
        scan = file_tree_scan(str(root), task_id, max_files=max_files)["artifacts"]
        source_files = {f["path"] for f in scan.get("files", []) if f.get("kind") == "source"}
        test_files = [f["path"] for f in scan.get("files", []) if f.get("kind") == "test"]
        dep = dependency_graph(str(root), task_id, max_files=max_files)["artifacts"]
        dep_edges = dep.get("internal_edges", [])
        edges: List[Dict[str, Any]] = []
        for test in test_files:
            stem = Path(test).stem
            normalized = re.sub(r"^(test_|spec_)", "", stem)
            normalized = re.sub(r"(_test|_spec)$", "", normalized)
            for src in source_files:
                if Path(src).stem == normalized:
                    edges.append({"test": test, "source": src, "reason": "name_match"})
            for e in dep_edges:
                if e["from"] == test:
                    edges.append({"test": test, "source": e["to"], "reason": f"imports {e['import']}"})
        artifacts = {
            "test_file_count": len(test_files),
            "source_file_count": len(source_files),
            "test_to_source_edges": edges,
            "orphan_tests": sorted(set(test_files) - {e["test"] for e in edges}),
        }
        return _envelope(
            "code_x.test_map", task_id, "success",
            f"生成测试映射：测试文件 {len(test_files)}，映射边 {len(edges)}。",
            artifacts,
            evidence=[EvidenceRef("test_map", e["test"], note=f"covers {e['source']} via {e['reason']}") for e in edges[:50]],
            next_action="plan_patch",
            reason="测试映射已生成，建议后续 patch 前选择最小验证命令。",
            alternatives=("localize_issue", "pytest_runner", "fallback_test_strategy"),
        )
    except Exception as exc:
        return _envelope("code_x.test_map", task_id, "blocked", f"测试映射阻断：{exc}", {}, [], "handoff", "测试映射失败，建议交接阻断原因。", ("state_recover",), type(exc).__name__)


def entrypoint_detector(workspace_root: str, task_id: str = "r4-demo", max_files: int = 5000) -> Dict[str, Any]:
    """Detect probable application and script entrypoints."""
    try:
        root = _resolve_workspace(workspace_root)
        entries: List[Dict[str, Any]] = []
        evidence: List[EvidenceRef] = []
        for path in _walk_files(root, max_files=max_files):
            rel = _rel(root, path)
            name = path.name
            if name in {"main.py", "app.py", "manage.py", "server.py", "cli.py"}:
                entries.append({"path": rel, "kind": "filename_convention", "confidence": 0.72})
                evidence.append(EvidenceRef("entrypoint", rel, note="filename convention"))
            if path.suffix.lower() == ".py":
                text = _safe_read_text(path)
                if text and "if __name__" in text and "__main__" in text:
                    line = _line_of_text(text, "__main__")
                    entries.append({"path": rel, "kind": "python_main_guard", "line": line, "confidence": 0.9})
                    evidence.append(EvidenceRef("entrypoint", rel, line, "python __main__ guard"))
            if name == "package.json":
                text = _safe_read_text(path)
                if text:
                    try:
                        pkg = json.loads(text)
                        for key, command in pkg.get("scripts", {}).items():
                            entries.append({"path": rel, "kind": "package_json_script", "script": key, "command": command, "confidence": 0.8})
                            evidence.append(EvidenceRef("entrypoint", rel, note=f"script {key}"))
                    except json.JSONDecodeError:
                        evidence.append(EvidenceRef("parse_error", rel, note="invalid package.json"))
        artifacts = {"entrypoints": entries, "entrypoint_count": len(entries)}
        return _envelope(
            "code_x.entrypoint_detector", task_id, "success",
            f"检测入口 {len(entries)} 个。",
            artifacts,
            evidence=evidence[:50],
            next_action="continue_read",
            reason="入口已识别，建议结合 stack_detector 与 command_capability_probe 选择验证命令。",
            alternatives=("stack_detector", "environment_probe", "plan_patch"),
        )
    except Exception as exc:
        return _envelope("code_x.entrypoint_detector", task_id, "blocked", f"入口检测阻断：{exc}", {}, [], "handoff", "入口检测失败，建议交接阻断原因。", ("state_recover",), type(exc).__name__)


def config_detector(workspace_root: str, task_id: str = "r4-demo", max_files: int = 5000) -> Dict[str, Any]:
    """Detect project configuration files and classify their toolchain purpose."""
    try:
        root = _resolve_workspace(workspace_root)
        configs: List[Dict[str, Any]] = []
        for path in _walk_files(root, max_files=max_files):
            name = path.name
            lower = name.lower()
            if name in CONFIG_NAMES or lower in {n.lower() for n in CONFIG_NAMES}:
                purpose = "general"
                if name in {"pyproject.toml", "setup.py", "setup.cfg", "requirements.txt", "pytest.ini", "tox.ini", "ruff.toml", "mypy.ini"}:
                    purpose = "python"
                elif name in {"package.json", "pnpm-lock.yaml", "yarn.lock", "package-lock.json", "tsconfig.json", "vite.config.js", "vite.config.ts", "next.config.js", "webpack.config.js"}:
                    purpose = "node"
                elif name in {"Dockerfile", "docker-compose.yml", "compose.yml"}:
                    purpose = "container"
                elif name == "CODEOWNERS":
                    purpose = "ownership"
                configs.append({"path": _rel(root, path), "name": name, "purpose": purpose})
        artifacts = {"config_count": len(configs), "configs": configs}
        return _envelope(
            "code_x.config_detector", task_id, "success",
            f"检测配置文件 {len(configs)} 个。",
            artifacts,
            evidence=[EvidenceRef("config", c["path"], note=c["purpose"]) for c in configs[:50]],
            next_action="continue_read",
            reason="配置已识别，建议继续 stack_detector 或 validation command 规划。",
            alternatives=("stack_detector", "command_capability_probe", "test_map"),
        )
    except Exception as exc:
        return _envelope("code_x.config_detector", task_id, "blocked", f"配置检测阻断：{exc}", {}, [], "handoff", "配置检测失败，建议交接阻断原因。", ("state_recover",), type(exc).__name__)


def stack_detector(workspace_root: str, task_id: str = "r4-demo", max_files: int = 5000) -> Dict[str, Any]:
    """Infer language/runtime/test stacks from files and config."""
    try:
        root = _resolve_workspace(workspace_root)
        scan = file_tree_scan(str(root), task_id, max_files=max_files)["artifacts"]
        configs = config_detector(str(root), task_id, max_files=max_files)["artifacts"].get("configs", [])
        ext_counts = scan.get("counts_by_extension", {})
        stacks: List[Dict[str, Any]] = []
        def add(name: str, confidence: float, evidence_note: str) -> None:
            stacks.append({"stack": name, "confidence": confidence, "evidence": evidence_note})
        if ext_counts.get(".py"):
            add("python", 0.7, f"{ext_counts.get('.py')} .py files")
        if any(c["name"] in {"pyproject.toml", "requirements.txt", "pytest.ini"} for c in configs):
            add("python-packaging-or-pytest", 0.86, "python config detected")
        if ext_counts.get(".js") or ext_counts.get(".ts") or ext_counts.get(".tsx") or ext_counts.get(".jsx"):
            add("node-js-ts", 0.7, "JS/TS extensions detected")
        if any(c["name"] == "package.json" for c in configs):
            add("npm-compatible", 0.88, "package.json detected")
        if any(c["name"].startswith("vite.config") for c in configs):
            add("vite", 0.82, "vite config detected")
        if any(c["name"].startswith("next.config") for c in configs):
            add("nextjs", 0.82, "next config detected")
        if any(c["name"] == "Dockerfile" for c in configs):
            add("docker", 0.78, "Dockerfile detected")
        artifacts = {"stacks": stacks, "stack_count": len(stacks)}
        return _envelope(
            "code_x.stack_detector", task_id, "success",
            f"推断技术栈 {len(stacks)} 个。",
            artifacts,
            evidence=[EvidenceRef("stack", ".", note=f"{s['stack']}:{s['confidence']}") for s in stacks[:50]],
            next_action="plan_patch",
            reason="技术栈已识别，建议进入命令能力探测或定位/补丁计划。",
            alternatives=("command_capability_probe", "localize_issue", "plan_patch"),
        )
    except Exception as exc:
        return _envelope("code_x.stack_detector", task_id, "blocked", f"技术栈检测阻断：{exc}", {}, [], "handoff", "技术栈检测失败，建议交接阻断原因。", ("state_recover",), type(exc).__name__)


def code_owner_detector(workspace_root: str, task_id: str = "r4-demo", max_files: int = 5000) -> Dict[str, Any]:
    """Parse CODEOWNERS-like rules when present. Does not contact remote services."""
    try:
        root = _resolve_workspace(workspace_root)
        candidates = [root / "CODEOWNERS", root / ".github" / "CODEOWNERS", root / "docs" / "CODEOWNERS"]
        rules: List[Dict[str, Any]] = []
        evidence: List[EvidenceRef] = []
        for path in candidates:
            if not path.exists():
                continue
            text = _safe_read_text(path)
            if text is None:
                continue
            for idx, line in enumerate(text.splitlines(), 1):
                stripped = line.strip()
                if not stripped or stripped.startswith("#"):
                    continue
                parts = stripped.split()
                if len(parts) >= 2:
                    rules.append({"path": _rel(root, path), "line": idx, "pattern": parts[0], "owners": parts[1:]})
                    evidence.append(EvidenceRef("code_owner", _rel(root, path), idx, stripped))
        artifacts = {"owner_rule_count": len(rules), "owner_rules": rules}
        status = "success" if rules else "no_op"
        return _envelope(
            "code_x.code_owner_detector", task_id, status,
            f"检测 CODEOWNERS 规则 {len(rules)} 条。",
            artifacts,
            evidence=evidence[:50],
            next_action="continue_read",
            reason="代码归属规则已读取或不存在；建议结合审查/迁移子代理使用。",
            alternatives=("review_subagent", "security_review_subagent", "handoff"),
        )
    except Exception as exc:
        return _envelope("code_x.code_owner_detector", task_id, "blocked", f"代码归属检测阻断：{exc}", {}, [], "handoff", "代码归属检测失败，建议交接阻断原因。", ("state_recover",), type(exc).__name__)


def repo_map(workspace_root: str, task_id: str = "r4-demo", max_files: int = 5000) -> Dict[str, Any]:
    """Generate a compressed repository map assembled from R4 perception tools."""
    try:
        root = _resolve_workspace(workspace_root)
        scan = file_tree_scan(str(root), task_id, max_files=max_files)["artifacts"]
        cfg = config_detector(str(root), task_id, max_files=max_files)["artifacts"]
        stacks = stack_detector(str(root), task_id, max_files=max_files)["artifacts"]
        entries = entrypoint_detector(str(root), task_id, max_files=max_files)["artifacts"]
        tests = test_map(str(root), task_id, max_files=max_files)["artifacts"]
        owners = code_owner_detector(str(root), task_id, max_files=max_files)["artifacts"]
        top_dirs = Counter()
        for f in scan.get("files", []):
            parts = Path(f["path"]).parts
            top_dirs[parts[0] if parts else "."] += 1
        artifacts = {
            "workspace_root": str(root),
            "file_count": scan.get("file_count", 0),
            "counts_by_kind": scan.get("counts_by_kind", {}),
            "counts_by_extension": scan.get("counts_by_extension", {}),
            "top_dirs": dict(top_dirs.most_common(20)),
            "configs": cfg.get("configs", []),
            "stacks": stacks.get("stacks", []),
            "entrypoints": entries.get("entrypoints", []),
            "test_map_summary": {
                "test_file_count": tests.get("test_file_count", 0),
                "test_to_source_edges": tests.get("test_to_source_edges", []),
            },
            "owner_rules": owners.get("owner_rules", []),
            "repo_map_contract": {
                "purpose": "compressed_context_for_llm",
                "max_detail_policy": "summarize counts; use file/symbol tools for detail",
                "next_stage": "R5 context armor or R6 localization",
            },
        }
        return _envelope(
            "code_x.repo_map", task_id, "success",
            f"生成 repo_map：文件 {artifacts['file_count']}，技术栈 {len(artifacts['stacks'])}，入口 {len(artifacts['entrypoints'])}，测试映射 {len(artifacts['test_map_summary']['test_to_source_edges'])}。",
            artifacts,
            evidence=[EvidenceRef("repo_map", ".", note="compressed repository map generated")],
            next_action="localize_issue",
            reason="repo_map 已压缩，可进入问题定位或上下文装甲生成。",
            alternatives=("context_compactor", "symbol_index", "issue_to_file_localizer", "plan_patch"),
        )
    except Exception as exc:
        return _envelope("code_x.repo_map", task_id, "blocked", f"repo_map 阻断：{exc}", {}, [], "handoff", "repo_map 失败，建议交接阻断原因。", ("state_recover",), type(exc).__name__)


TOOL_TABLE = {
    "file_tree_scan": file_tree_scan,
    "repo_map": repo_map,
    "symbol_index": symbol_index,
    "dependency_graph": dependency_graph,
    "call_graph": call_graph,
    "test_map": test_map,
    "entrypoint_detector": entrypoint_detector,
    "config_detector": config_detector,
    "stack_detector": stack_detector,
    "code_owner_detector": code_owner_detector,
}


def main(argv: Optional[List[str]] = None) -> int:
    """Small CLI for candidate validation only.

    Usage:
        python code_x_engineering_perception.py <tool> <workspace_root> [task_id]
    """
    import sys
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) < 2 or args[0] not in TOOL_TABLE:
        print("Usage: python code_x_engineering_perception.py <tool> <workspace_root> [task_id]", file=sys.stderr)
        print("Tools: " + ", ".join(sorted(TOOL_TABLE)), file=sys.stderr)
        return 2
    tool_name, workspace_root = args[0], args[1]
    task_id = args[2] if len(args) > 2 else "r4-cli"
    result = TOOL_TABLE[tool_name](workspace_root, task_id)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("status") in {"success", "partial", "no_op"} else 1


if __name__ == "__main__":  # pragma: no cover - CLI only
    raise SystemExit(main())
