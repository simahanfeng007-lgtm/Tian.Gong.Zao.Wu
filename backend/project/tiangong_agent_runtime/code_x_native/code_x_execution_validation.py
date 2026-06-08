"""
L6.70.2-CodeX R8: execution validation clean candidate tools.

Scope:
- Candidate-only implementation for local validation of workspace changes.
- No Runtime registration, no v2 main-chain modification, no external provider.
- No legacy module import/copy. Standard library only.

Design principle:
The LLM remains the final engineering decision maker. These tools only probe,
run bounded commands, collect evidence, classify environment gaps, and return
next-action hints for the LLM's repair/rollback/handoff decision.
"""
from __future__ import annotations

import ast
import json
import os
import platform
import py_compile
import re
import shlex
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

DEFAULT_TIMEOUT_SEC = 30
DEFAULT_MAX_OUTPUT_CHARS = 12000
SAFE_VERSION_FLAGS = {
    "python": ["--version"],
    "python3": ["--version"],
    "pytest": ["--version"],
    "node": ["--version"],
    "npm": ["--version"],
    "pnpm": ["--version"],
    "ruff": ["--version"],
    "mypy": ["--version"],
    "pyright": ["--version"],
    "tsc": ["--version"],
    "eslint": ["--version"],
}
PROJECT_MARKERS = [
    "pyproject.toml", "setup.py", "setup.cfg", "requirements.txt", "tox.ini",
    "package.json", "pnpm-lock.yaml", "package-lock.json", "yarn.lock",
    "tsconfig.json", "vite.config.ts", "webpack.config.js", "Cargo.toml",
    "go.mod", "pom.xml", "build.gradle", ".git",
]
A5_BLOCK_TOKENS = {
    "rm", "rmdir", "del", "erase", "format", "shutdown", "reboot", "halt", "mkfs",
    "diskpart", "reg", "takeown", "icacls", "chmod", "chown", "dd", "curl", "wget",
    "scp", "sftp", "ssh", "nc", "netcat", "powershell", "pwsh",
}
A5_DANGEROUS_PATTERNS = [
    re.compile(r"\brm\s+-[^\n]*r[^\n]*f\b", re.I),
    re.compile(r"\bdel\s+/[sq]\b", re.I),
    re.compile(r"\bRemove-Item\b.*\b-Recurse\b", re.I),
    re.compile(r"\bmkfs\b", re.I),
    re.compile(r"\bdd\s+.*\bof=", re.I),
    re.compile(r"\b(shutdown|reboot|halt)\b", re.I),
    re.compile(r"[;&|`$<>]"),
]
TEXT_SUFFIXES = {".py", ".js", ".ts", ".tsx", ".jsx", ".json", ".toml", ".yaml", ".yml", ".md", ".txt"}
SKIP_DIRS = {".git", ".venv", "venv", "node_modules", "dist", "build", "__pycache__", ".pytest_cache", ".mypy_cache"}


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
              risk_level: str = "A2") -> Dict[str, Any]:
    return {
        "tool_name": tool,
        "status": status,
        "r1_next_action_hint": next_action or _hint("handoff_digest", "No next action was provided.", 0.3),
        "r2_execution_protection": {
            "risk_level": "A5" if status == "blocked" else risk_level,
            "requires_confirmation": status == "blocked",
            "protected_keys": ["rollback", "handoff", "state_recover", "lease_extend"],
            "a5_hard_block_only": True,
        },
        "evidence": evidence or [],
        "warnings": warnings or [],
        "result": result,
    }


def _safe_repo_root(repo_root: str | Path) -> Path:
    root = Path(repo_root).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        raise ValueError(f"repo_root must be an existing directory: {repo_root}")
    return root


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


def _workspace_path(repo_root: str | Path, rel_path: str = ".") -> Path:
    root = _safe_repo_root(repo_root)
    target = (root / _safe_rel_path(rel_path)).resolve() if rel_path not in ("", ".") else root
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"target escapes workspace: {rel_path}") from exc
    return target


def _truncate(text: str, limit: int = DEFAULT_MAX_OUTPUT_CHARS) -> Tuple[str, bool]:
    if len(text) <= limit:
        return text, False
    head = text[: max(limit // 2, 1)]
    tail = text[-max(limit // 2, 1):]
    return head + "\n...[truncated]...\n" + tail, True


def _parse_command(command: str | Sequence[str]) -> List[str]:
    if isinstance(command, str):
        if not command.strip():
            raise ValueError("command cannot be empty")
        return shlex.split(command, posix=os.name != "nt")
    if not command:
        raise ValueError("command cannot be empty")
    return [str(x) for x in command]


def _command_string(args: Sequence[str]) -> str:
    return " ".join(shlex.quote(str(x)) for x in args)


def _classify_command_risk(args: Sequence[str]) -> Dict[str, Any]:
    cmd_text = _command_string(args)
    executable = Path(str(args[0])).name.lower() if args else ""
    reasons: List[str] = []
    for pattern in A5_DANGEROUS_PATTERNS:
        if pattern.search(cmd_text):
            reasons.append(f"dangerous shell/destructive pattern: {pattern.pattern}")
    if executable in A5_BLOCK_TOKENS:
        reasons.append(f"blocked executable: {executable}")
    if executable in {"pip", "pip3", "python", "python3"} and any(str(a).lower() == "install" for a in args[1:]):
        reasons.append("dependency installation is not part of R8 default validation")
    risk = "A5" if reasons else "A2"
    return {"risk_level": risk, "blocked": bool(reasons), "reasons": reasons, "command": cmd_text}


def _find_project_markers(root: Path) -> List[str]:
    found: List[str] = []
    for marker in PROJECT_MARKERS:
        if (root / marker).exists():
            found.append(marker)
    return sorted(found)


def _walk_files(root: Path, suffixes: Optional[Iterable[str]] = None) -> List[Path]:
    suffix_set = {s.lower() for s in suffixes} if suffixes else None
    files: List[Path] = []
    for p in root.rglob("*"):
        if any(part in SKIP_DIRS for part in p.relative_to(root).parts):
            continue
        if not p.is_file():
            continue
        if suffix_set is not None and p.suffix.lower() not in suffix_set:
            continue
        files.append(p)
    return sorted(files)


def environment_probe(repo_root: str | Path) -> Dict[str, Any]:
    """Inspect local validation environment without modifying the workspace."""
    root = _safe_repo_root(repo_root)
    commands = {name: shutil.which(name) for name in sorted(SAFE_VERSION_FLAGS)}
    project_markers = _find_project_markers(root)
    python_files = _walk_files(root, {".py"})
    node_files = _walk_files(root, {".js", ".jsx", ".ts", ".tsx"})
    result = {
        "repo_root": str(root),
        "platform": platform.platform(),
        "python_executable": sys.executable,
        "python_version": sys.version.split()[0],
        "cwd": os.getcwd(),
        "project_markers": project_markers,
        "available_commands": {k: v for k, v in commands.items() if v},
        "missing_commands": [k for k, v in commands.items() if not v],
        "file_counts": {
            "python": len(python_files),
            "node_like": len(node_files),
            "total_text_candidate": len(_walk_files(root, TEXT_SUFFIXES)),
        },
        "detected_stack": {
            "python": any(m in project_markers for m in ["pyproject.toml", "requirements.txt", "setup.py", "setup.cfg"]),
            "node": "package.json" in project_markers,
            "typescript": "tsconfig.json" in project_markers or any(p.suffix.lower() in {".ts", ".tsx"} for p in node_files),
            "git": ".git" in project_markers,
        },
    }
    next_tool = "command_capability_probe" if result["available_commands"] else "fallback_test_strategy"
    return _envelope(
        "environment_probe", "ok", result,
        evidence=[{"kind": "project_markers", "items": project_markers[:20]}],
        next_action=_hint(next_tool, "Environment is mapped; probe validation commands before running tests.", 0.86),
        risk_level="A0",
    )


def command_capability_probe(repo_root: str | Path, commands: Optional[Sequence[str]] = None,
                             run_versions: bool = True, timeout_sec: int = 5) -> Dict[str, Any]:
    """Check whether validation commands exist and optionally collect side-effect-free versions."""
    root = _safe_repo_root(repo_root)
    names = list(commands or SAFE_VERSION_FLAGS.keys())
    capabilities: List[Dict[str, Any]] = []
    for name in names:
        exe = shutil.which(name)
        item: Dict[str, Any] = {"command": name, "available": bool(exe), "path": exe, "version": None, "probe_error": None}
        if exe and run_versions and name in SAFE_VERSION_FLAGS:
            try:
                proc = subprocess.run([exe] + SAFE_VERSION_FLAGS[name], cwd=str(root), capture_output=True, text=True,
                                      timeout=timeout_sec, shell=False)
                version_text = (proc.stdout or proc.stderr or "").strip().splitlines()
                item["version"] = version_text[0] if version_text else None
                item["version_exit_code"] = proc.returncode
            except Exception as exc:  # noqa: BLE001 - evidence collection must not crash the chain
                item["probe_error"] = str(exc)
        capabilities.append(item)
    result = {
        "repo_root": str(root),
        "capabilities": capabilities,
        "available": [c["command"] for c in capabilities if c["available"]],
        "missing": [c["command"] for c in capabilities if not c["available"]],
    }
    return _envelope(
        "command_capability_probe", "ok", result,
        evidence=[{"kind": "capability", "command": c["command"], "available": c["available"]} for c in capabilities],
        next_action=_hint("static_analyzer", "Capabilities are known; run static analysis before expensive test/build commands.", 0.84),
        risk_level="A0",
    )


def safe_command_runner(repo_root: str | Path, command: str | Sequence[str], cwd: str = ".",
                        timeout_sec: int = DEFAULT_TIMEOUT_SEC, max_output_chars: int = DEFAULT_MAX_OUTPUT_CHARS,
                        allowed_return_codes: Optional[Sequence[int]] = None,
                        env_overrides: Optional[Mapping[str, str]] = None) -> Dict[str, Any]:
    """Run a bounded, non-shell command inside workspace and capture stdout/stderr."""
    root = _safe_repo_root(repo_root)
    workdir = _workspace_path(root, cwd)
    args = _parse_command(command)
    risk = _classify_command_risk(args)
    if risk["blocked"]:
        return _envelope(
            "safe_command_runner", "blocked",
            {"command": risk["command"], "blocked_reasons": risk["reasons"], "cwd": str(workdir)},
            evidence=[{"kind": "risk", "risk_level": "A5", "reason": r} for r in risk["reasons"]],
            next_action=_hint("handoff_digest", "Command was A5-blocked; the LLM must choose a safer validation or request confirmation.", 0.94),
            risk_level="A5",
        )
    exe = args[0]
    resolved = exe if Path(exe).is_absolute() and Path(exe).exists() else shutil.which(exe)
    if not resolved:
        return _envelope(
            "safe_command_runner", "environment_missing",
            {"command": risk["command"], "missing_executable": exe, "cwd": str(workdir)},
            evidence=[{"kind": "missing_executable", "command": exe}],
            next_action=_hint("fallback_test_strategy", "Executable is missing; generate a fallback validation strategy.", 0.88),
            risk_level="A1",
        )
    env = os.environ.copy()
    if env_overrides:
        for key, value in env_overrides.items():
            if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", str(key)):
                raise ValueError(f"invalid environment variable name: {key}")
            env[str(key)] = str(value)
    started = time.monotonic()
    try:
        proc = subprocess.run(args, cwd=str(workdir), capture_output=True, text=True, timeout=timeout_sec,
                              shell=False, env=env)
        duration_ms = int((time.monotonic() - started) * 1000)
        stdout, stdout_truncated = _truncate(proc.stdout or "", max_output_chars)
        stderr, stderr_truncated = _truncate(proc.stderr or "", max_output_chars)
        allowed = list(allowed_return_codes) if allowed_return_codes is not None else [0]
        status = "ok" if proc.returncode in allowed else "failed"
        next_tool = "handoff_digest" if status == "ok" else "failure_attribution_analyzer"
        reason = "Command succeeded; summarize validation evidence." if status == "ok" else "Command failed; attribute failure before another patch."
        return _envelope(
            "safe_command_runner", status,
            {
                "command": risk["command"],
                "cwd": str(workdir),
                "exit_code": proc.returncode,
                "duration_ms": duration_ms,
                "stdout": stdout,
                "stderr": stderr,
                "stdout_truncated": stdout_truncated,
                "stderr_truncated": stderr_truncated,
                "timeout_sec": timeout_sec,
            },
            evidence=[{"kind": "command_result", "exit_code": proc.returncode, "duration_ms": duration_ms}],
            next_action=_hint(next_tool, reason, 0.86),
            risk_level="A2",
        )
    except subprocess.TimeoutExpired as exc:
        stdout, stdout_truncated = _truncate(exc.stdout or "", max_output_chars) if isinstance(exc.stdout, str) else ("", False)
        stderr, stderr_truncated = _truncate(exc.stderr or "", max_output_chars) if isinstance(exc.stderr, str) else ("", False)
        return _envelope(
            "safe_command_runner", "timeout",
            {"command": risk["command"], "cwd": str(workdir), "timeout_sec": timeout_sec, "stdout": stdout,
             "stderr": stderr, "stdout_truncated": stdout_truncated, "stderr_truncated": stderr_truncated},
            evidence=[{"kind": "timeout", "timeout_sec": timeout_sec}],
            next_action=_hint("failure_attribution_analyzer", "Command timed out; decide whether to narrow test scope or inspect hang cause.", 0.82),
            risk_level="A2",
        )


def static_analyzer(repo_root: str | Path, paths: Optional[Sequence[str]] = None) -> Dict[str, Any]:
    """Run side-effect-free static checks. Python files are syntax-compiled."""
    root = _safe_repo_root(repo_root)
    if paths:
        targets: List[Path] = []
        for rel in paths:
            p = _workspace_path(root, rel)
            if p.is_dir():
                targets.extend(_walk_files(p, {".py"}))
            elif p.is_file() and p.suffix.lower() == ".py":
                targets.append(p)
    else:
        targets = _walk_files(root, {".py"})
    issues: List[Dict[str, Any]] = []
    analyzed: List[str] = []
    for file_path in sorted(set(targets)):
        rel = str(file_path.relative_to(root)).replace("\\", "/")
        analyzed.append(rel)
        try:
            source = file_path.read_text(encoding="utf-8")
            ast.parse(source, filename=rel)
            py_compile.compile(str(file_path), doraise=True, quiet=2)
        except SyntaxError as exc:
            issues.append({"path": rel, "type": "syntax_error", "line": exc.lineno, "offset": exc.offset, "message": exc.msg})
        except py_compile.PyCompileError as exc:
            issues.append({"path": rel, "type": "compile_error", "message": str(exc)})
        except UnicodeDecodeError as exc:
            issues.append({"path": rel, "type": "decode_error", "message": str(exc)})
        except Exception as exc:  # noqa: BLE001 - static analyzer must report and continue
            issues.append({"path": rel, "type": "static_check_error", "message": str(exc)})
    status = "ok" if not issues else "failed"
    next_tool = "pytest_runner" if status == "ok" else "failure_attribution_analyzer"
    reason = "Static analysis passed; run targeted tests." if status == "ok" else "Static analysis failed; attribute syntax/compile errors."
    return _envelope(
        "static_analyzer", status,
        {"repo_root": str(root), "analyzed_files": analyzed, "issue_count": len(issues), "issues": issues},
        evidence=[{"kind": "static_issue", **issue} for issue in issues[:20]],
        next_action=_hint(next_tool, reason, 0.9 if status == "ok" else 0.93),
        risk_level="A1",
    )


def pytest_runner(repo_root: str | Path, test_path: Optional[str] = None,
                  extra_args: Optional[Sequence[str]] = None, timeout_sec: int = 60) -> Dict[str, Any]:
    root = _safe_repo_root(repo_root)
    args = [sys.executable, "-m", "pytest", "-q"]
    if test_path:
        args.append(str(_safe_rel_path(test_path)))
    if extra_args:
        args.extend(str(x) for x in extra_args)
    result = safe_command_runner(root, args, timeout_sec=timeout_sec)
    result["tool_name"] = "pytest_runner"
    result["result"]["runner"] = "pytest"
    if result["status"] == "ok":
        result["r1_next_action_hint"] = _hint("handoff_digest", "Pytest passed; package validation evidence or continue with lint/typecheck if required.", 0.86,
                                             ["lint_runner", "typecheck_runner", "delivery_candidate_packager"])
    elif result["status"] == "environment_missing":
        result["r1_next_action_hint"] = _hint("fallback_test_strategy", "Pytest is unavailable; use compile/static fallback and report environment gap.", 0.88)
    else:
        result["r1_next_action_hint"] = _hint("failure_attribution_analyzer", "Pytest failed; map failures to files before another patch.", 0.9)
    return result


def npm_test_runner(repo_root: str | Path, timeout_sec: int = 120) -> Dict[str, Any]:
    root = _safe_repo_root(repo_root)
    package_json = root / "package.json"
    if not package_json.exists():
        return _envelope(
            "npm_test_runner", "skipped",
            {"reason": "package.json not found", "repo_root": str(root)},
            evidence=[{"kind": "missing_project_marker", "marker": "package.json"}],
            next_action=_hint("fallback_test_strategy", "No Node test marker; choose Python/static fallback or handoff environment gap.", 0.74),
            risk_level="A1",
        )
    result = safe_command_runner(root, ["npm", "test"], timeout_sec=timeout_sec)
    result["tool_name"] = "npm_test_runner"
    result["result"]["runner"] = "npm test"
    if result["status"] == "ok":
        result["r1_next_action_hint"] = _hint("handoff_digest", "npm test passed; summarize validation evidence.", 0.86)
    else:
        result["r1_next_action_hint"] = _hint("failure_attribution_analyzer", "npm test did not pass; classify environment/dependency/test failure.", 0.86)
    return result


def build_runner(repo_root: str | Path, build_command: Optional[str | Sequence[str]] = None, timeout_sec: int = 120) -> Dict[str, Any]:
    root = _safe_repo_root(repo_root)
    if build_command:
        result = safe_command_runner(root, build_command, timeout_sec=timeout_sec)
        result["tool_name"] = "build_runner"
        result["result"]["runner"] = "custom_build"
        return result
    if (root / "package.json").exists():
        try:
            data = json.loads((root / "package.json").read_text(encoding="utf-8"))
            scripts = data.get("scripts", {}) if isinstance(data, dict) else {}
        except Exception:
            scripts = {}
        if "build" in scripts:
            result = safe_command_runner(root, ["npm", "run", "build"], timeout_sec=timeout_sec)
            result["tool_name"] = "build_runner"
            result["result"]["runner"] = "npm run build"
            return result
    if any((root / marker).exists() for marker in ["pyproject.toml", "setup.py", "requirements.txt"]):
        result = static_analyzer(root)
        result["tool_name"] = "build_runner"
        result["result"]["runner"] = "python_static_build_fallback"
        result["r1_next_action_hint"] = _hint("pytest_runner" if result["status"] == "ok" else "failure_attribution_analyzer",
                                             "Python build fallback used compile/static checks; continue based on result.", 0.78)
        return result
    return _envelope(
        "build_runner", "skipped",
        {"reason": "no build marker detected", "repo_root": str(root)},
        evidence=[{"kind": "build_marker", "found": False}],
        next_action=_hint("fallback_test_strategy", "No build command detected; create fallback validation plan.", 0.76),
        risk_level="A1",
    )


def lint_runner(repo_root: str | Path, lint_command: Optional[str | Sequence[str]] = None, timeout_sec: int = 120) -> Dict[str, Any]:
    root = _safe_repo_root(repo_root)
    if lint_command:
        result = safe_command_runner(root, lint_command, timeout_sec=timeout_sec)
        result["tool_name"] = "lint_runner"
        result["result"]["runner"] = "custom_lint"
        return result
    if shutil.which("ruff"):
        result = safe_command_runner(root, ["ruff", "check", "."], timeout_sec=timeout_sec)
        result["tool_name"] = "lint_runner"
        result["result"]["runner"] = "ruff check ."
        return result
    if (root / "package.json").exists() and shutil.which("npm"):
        try:
            data = json.loads((root / "package.json").read_text(encoding="utf-8"))
            scripts = data.get("scripts", {}) if isinstance(data, dict) else {}
        except Exception:
            scripts = {}
        if "lint" in scripts:
            result = safe_command_runner(root, ["npm", "run", "lint"], timeout_sec=timeout_sec)
            result["tool_name"] = "lint_runner"
            result["result"]["runner"] = "npm run lint"
            return result
    return _envelope(
        "lint_runner", "skipped",
        {"reason": "no lint command available", "repo_root": str(root)},
        evidence=[{"kind": "lint_capability", "available": False}],
        next_action=_hint("typecheck_runner", "Lint unavailable; try typecheck or static analyzer fallback.", 0.7,
                          ["static_analyzer", "handoff_digest"]),
        risk_level="A1",
    )


def typecheck_runner(repo_root: str | Path, typecheck_command: Optional[str | Sequence[str]] = None,
                     timeout_sec: int = 120) -> Dict[str, Any]:
    root = _safe_repo_root(repo_root)
    if typecheck_command:
        result = safe_command_runner(root, typecheck_command, timeout_sec=timeout_sec)
        result["tool_name"] = "typecheck_runner"
        result["result"]["runner"] = "custom_typecheck"
        return result
    if shutil.which("mypy"):
        result = safe_command_runner(root, ["mypy", "."], timeout_sec=timeout_sec)
        result["tool_name"] = "typecheck_runner"
        result["result"]["runner"] = "mypy ."
        return result
    if shutil.which("pyright"):
        result = safe_command_runner(root, ["pyright"], timeout_sec=timeout_sec)
        result["tool_name"] = "typecheck_runner"
        result["result"]["runner"] = "pyright"
        return result
    if shutil.which("tsc") and (root / "tsconfig.json").exists():
        result = safe_command_runner(root, ["tsc", "--noEmit"], timeout_sec=timeout_sec)
        result["tool_name"] = "typecheck_runner"
        result["result"]["runner"] = "tsc --noEmit"
        return result
    return _envelope(
        "typecheck_runner", "skipped",
        {"reason": "no typecheck command available", "repo_root": str(root)},
        evidence=[{"kind": "typecheck_capability", "available": False}],
        next_action=_hint("static_analyzer", "Typecheck unavailable; use static analyzer fallback and report environment gap.", 0.75,
                          ["fallback_test_strategy", "handoff_digest"]),
        risk_level="A1",
    )


def fallback_test_strategy(repo_root: str | Path, previous_results: Optional[Sequence[Mapping[str, Any]]] = None) -> Dict[str, Any]:
    """Generate an LLM-readable fallback strategy when normal validation cannot run."""
    root = _safe_repo_root(repo_root)
    markers = _find_project_markers(root)
    python_files = _walk_files(root, {".py"})
    package_json = root / "package.json"
    steps: List[Dict[str, Any]] = []
    if python_files:
        steps.append({
            "step": "python_static_compile",
            "tool": "static_analyzer",
            "reason": "Python files exist; syntax/compile checks are side-effect-free and available through stdlib.",
            "minimum_evidence": ["analyzed_files", "issues"],
        })
        if shutil.which("pytest") or True:
            steps.append({
                "step": "targeted_pytest_if_available",
                "tool": "pytest_runner",
                "reason": "Use python -m pytest when test files or pytest config exist.",
                "condition": "tests/ exists or pytest.ini/pyproject pytest config exists",
            })
    if package_json.exists():
        steps.append({
            "step": "node_script_probe",
            "tool": "npm_test_runner/build_runner/lint_runner",
            "reason": "package.json exists; run scripts only if npm is available and scripts are defined.",
            "condition": "npm available",
        })
    if not steps:
        steps.append({
            "step": "manual_evidence_review",
            "tool": "handoff_digest",
            "reason": "No executable project markers found; handoff should state that validation is structurally unavailable.",
        })
    status_inputs = [str(x.get("status", "unknown")) for x in (previous_results or []) if isinstance(x, Mapping)]
    result = {
        "repo_root": str(root),
        "project_markers": markers,
        "fallback_steps": steps,
        "previous_statuses": status_inputs,
        "minimum_handoff_fields": [
            "commands_attempted", "commands_skipped", "environment_gaps", "static_results",
            "test_results", "known_unvalidated_risks", "recommended_next_action",
        ],
    }
    return _envelope(
        "fallback_test_strategy", "ok", result,
        evidence=[{"kind": "fallback_step", "step": step["step"], "tool": step["tool"]} for step in steps],
        next_action=_hint("handoff_digest", "Fallback strategy is ready; the LLM should run feasible checks or disclose validation gaps.", 0.82,
                          ["static_analyzer", "pytest_runner", "handoff_digest"]),
        risk_level="A0",
    )


__all__ = [
    "environment_probe",
    "command_capability_probe",
    "safe_command_runner",
    "python_quality_runner",
    "pytest_runner",
    "npm_test_runner",
    "build_runner",
    "lint_runner",
    "typecheck_runner",
    "static_analyzer",
    "fallback_test_strategy",
]


def python_quality_runner(repo_root: str | Path, timeout_sec: int = 60) -> Dict[str, Any]:
    """Run the Python validation stack available without installing dependencies."""
    static_result = static_analyzer(repo_root)
    if static_result["status"] != "ok":
        static_result["tool_name"] = "python_quality_runner"
        static_result["r1_next_action_hint"] = _hint("failure_attribution_analyzer", "Python static quality check failed; repair syntax/compile errors first.", 0.9)
        return static_result
    root = _safe_repo_root(repo_root)
    has_tests = (root / "tests").exists() or any(p.name.startswith("test_") for p in _walk_files(root, {".py"}))
    if has_tests:
        result = pytest_runner(root, timeout_sec=timeout_sec)
        result["tool_name"] = "python_quality_runner"
        result["result"]["static_analyzer"] = static_result["result"]
        return result
    return _envelope(
        "python_quality_runner", "ok",
        {"static_analyzer": static_result["result"], "pytest": "skipped_no_tests"},
        evidence=static_result.get("evidence", []),
        next_action=_hint("handoff_digest", "Python static checks passed but no tests were detected; disclose validation scope.", 0.78),
        risk_level="A1",
    )
