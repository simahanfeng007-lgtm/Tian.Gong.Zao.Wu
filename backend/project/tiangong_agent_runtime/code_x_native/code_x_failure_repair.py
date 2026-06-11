"""Code-X failure attribution and repair-loop helpers.

Native v2 implementation. Standard library only. No v1 imports, no registry side effect,
no background loop, no automatic patch write. The LLM remains final judge.
"""
from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence


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
        "summary": result.get("summary") or f"{tool} completed with status={status}",
        "r1_next_action_hint": next_action or _hint("handoff_digest", "No next action was provided.", 0.3),
        "r2_execution_protection": {
            "risk_level": "A2",
            "requires_confirmation": False,
            "protected_keys": ["rollback", "handoff", "state_recover", "lease_extend"],
            "a5_hard_block_only": True,
        },
        "evidence": evidence or [],
        "warnings": warnings or [],
        "result": result,
        "created_at_ms": _now_ms(),
    }


def _coerce_log(log_text: str | None = None, command_result: Optional[Mapping[str, Any]] = None) -> str:
    parts: List[str] = []
    if log_text:
        parts.append(str(log_text))
    if command_result:
        for key in ("output_summary", "stdout", "stderr", "summary", "error", "traceback"):
            value = command_result.get(key)
            if value:
                parts.append(str(value))
        data = command_result.get("data")
        if isinstance(data, Mapping):
            for key in ("stdout", "stderr", "output"):
                value = data.get(key)
                if value:
                    parts.append(str(value))
    return "\n".join(parts)


def _evidence_from_patterns(log: str, patterns: Sequence[tuple[str, str]], limit: int = 20) -> List[Dict[str, Any]]:
    evidence: List[Dict[str, Any]] = []
    lines = log.splitlines()
    for i, line in enumerate(lines, 1):
        for kind, pattern in patterns:
            if re.search(pattern, line, re.I):
                evidence.append({"kind": kind, "line": i, "snippet": line[-500:], "score": 0.8})
                break
        if len(evidence) >= limit:
            break
    return evidence


def _classify(log: str) -> Dict[str, Any]:
    low = log.lower()
    categories: List[str] = []
    if re.search(r"syntaxerror|indentationerror|taberror|eof while scanning|invalid syntax", log, re.I):
        categories.append("syntax_error")
    if re.search(r"importerror|modulenotfounderror|cannot import name|no module named", log, re.I):
        categories.append("import_error")
    if re.search(r"package not found|command not found|no such file or directory|npm err|pnpm:|pytest: not found|executable not found", log, re.I):
        categories.append("dependency_or_environment_error")
    if re.search(r"assertionerror|failed|\bFAIL\b|\bERROR\b|expected .* got|assert ", log, re.I):
        categories.append("test_failure")
    if re.search(r"timeout|timed out|deadline exceeded", log, re.I):
        categories.append("timeout_or_flaky")
    if re.search(r"a5|blocked|permission denied|not allowed|forbidden", log, re.I):
        categories.append("policy_or_permission_block")
    if not categories:
        categories.append("unknown_failure")
    primary = categories[0]
    confidence = 0.88 if primary != "unknown_failure" else 0.35
    return {"primary_category": primary, "categories": categories, "confidence": confidence}


def failure_attribution_analyzer(log_text: str | None = None, command_result: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
    log = _coerce_log(log_text, command_result)
    classified = _classify(log)
    evidence = _evidence_from_patterns(log, [
        ("syntax", r"syntaxerror|indentationerror|taberror|invalid syntax"),
        ("import", r"importerror|modulenotfounderror|cannot import name|no module named"),
        ("dependency", r"command not found|package not found|npm err|pytest: not found|no such file"),
        ("test", r"assertionerror|failed|\bFAIL\b|\bERROR\b|expected .* got"),
        ("timeout", r"timeout|timed out|deadline exceeded"),
        ("policy", r"a5|blocked|permission denied|not allowed|forbidden"),
    ])
    next_tool = {
        "syntax_error": "syntax_error_analyzer",
        "import_error": "import_error_analyzer",
        "dependency_or_environment_error": "dependency_error_analyzer",
        "test_failure": "test_failure_analyzer",
        "timeout_or_flaky": "flaky_test_detector",
        "policy_or_permission_block": "handoff_digest",
    }.get(classified["primary_category"], "repair_loop_planner")
    return _envelope(
        "failure_attribution_analyzer",
        "ok",
        {
            "summary": f"Primary failure category: {classified['primary_category']}",
            "log_chars": len(log),
            **classified,
        },
        evidence=evidence,
        next_action=_hint(next_tool, "Route failure to a focused analyzer before patch planning.", classified["confidence"]),
    )


def syntax_error_analyzer(log_text: str | None = None, command_result: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
    log = _coerce_log(log_text, command_result)
    evidence = _evidence_from_patterns(log, [("syntax", r"File \".*\", line \d+|SyntaxError|IndentationError|TabError")])
    file_line_matches = re.findall(r'File "([^"]+)", line (\d+)', log)
    targets = [{"path": p, "line": int(n)} for p, n in file_line_matches]
    return _envelope(
        "syntax_error_analyzer",
        "ok",
        {"summary": f"Detected {len(targets)} syntax target(s).", "targets": targets, "repair_hint": "Inspect target lines and generate minimal syntax patch."},
        evidence=evidence,
        next_action=_hint("symbol_to_line_localizer", "Open exact syntax location before generating edit units.", 0.86),
    )


def import_error_analyzer(log_text: str | None = None, command_result: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
    log = _coerce_log(log_text, command_result)
    missing = re.findall(r"No module named ['\"]([^'\"]+)['\"]", log)
    cannot = re.findall(r"cannot import name ['\"]([^'\"]+)['\"]", log)
    evidence = _evidence_from_patterns(log, [("import", r"ImportError|ModuleNotFoundError|cannot import name|No module named")])
    return _envelope(
        "import_error_analyzer",
        "ok",
        {"summary": "Import failure analyzed.", "missing_modules": missing, "missing_symbols": cannot, "repair_hint": "Check local module names, __init__.py exports, and dependency manifest before changing code."},
        evidence=evidence,
        next_action=_hint("semantic_code_search", "Search missing module/symbol references before patching imports.", 0.82),
    )


def dependency_error_analyzer(log_text: str | None = None, command_result: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
    log = _coerce_log(log_text, command_result)
    markers = []
    for pattern in [r"command not found", r"executable not found", r"No module named ['\"]([^'\"]+)['\"]", r"npm ERR", r"pnpm"]:
        if re.search(pattern, log, re.I):
            markers.append(pattern)
    evidence = _evidence_from_patterns(log, [("dependency", r"command not found|executable not found|No module named|npm ERR|pnpm|No such file")])
    return _envelope(
        "dependency_error_analyzer",
        "ok",
        {"summary": "Dependency/environment failure analyzed.", "markers": markers, "classification": "environment_failure_not_code_failure" if markers else "unknown_dependency_failure", "fallback": "Use static_analyzer / compileall / targeted unit checks when full command is unavailable."},
        evidence=evidence,
        next_action=_hint("fallback_test_strategy", "Choose a lower-friction verifier instead of blocking the chain.", 0.8),
    )


def test_failure_analyzer(log_text: str | None = None, command_result: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
    log = _coerce_log(log_text, command_result)
    failed_tests = re.findall(r"FAILED\s+([^\s]+)", log)
    assertions = _evidence_from_patterns(log, [("assertion", r"AssertionError|assert |expected .* got|E\s+assert")], limit=30)
    return _envelope(
        "test_failure_analyzer",
        "ok",
        {"summary": f"Detected {len(failed_tests)} failed test node(s).", "failed_tests": failed_tests[:30], "repair_hint": "Map failing assertion to production symbol, then generate next patch."},
        evidence=assertions,
        next_action=_hint("test_failure_trace_mapper", "Map test trace to source files before next patch.", 0.83),
    )


def flaky_test_detector(log_text: str | None = None, command_result: Optional[Mapping[str, Any]] = None,
                        repeated_results: Optional[Sequence[Mapping[str, Any]]] = None) -> Dict[str, Any]:
    log = _coerce_log(log_text, command_result)
    timeout = bool(re.search(r"timeout|timed out|deadline exceeded", log, re.I))
    outcomes = [str(item.get("status") or item.get("returncode") or "") for item in (repeated_results or [])]
    inconsistent = len(set(outcomes)) > 1 if outcomes else False
    status = "ok"
    return _envelope(
        "flaky_test_detector",
        status,
        {"summary": "Flaky/timeout heuristic completed.", "timeout_seen": timeout, "inconsistent_repeated_outcomes": inconsistent, "recommended_action": "rerun_targeted" if timeout or inconsistent else "continue_attribution"},
        evidence=_evidence_from_patterns(log, [("timeout", r"timeout|timed out|deadline exceeded")]),
        next_action=_hint("pytest_runner", "Rerun targeted tests once when flaky/timeout is plausible.", 0.65 if (timeout or inconsistent) else 0.45),
    )


def repair_loop_planner(failure_analysis: Mapping[str, Any], loop_count: int = 0, max_loops: int = 3,
                        long_chain: bool = False) -> Dict[str, Any]:
    limit = 6 if long_chain else max_loops
    category = str(failure_analysis.get("primary_category") or failure_analysis.get("category") or "unknown_failure")
    exhausted = loop_count >= limit
    if exhausted:
        next_tool = "handoff_digest"
        reason = "Repair loop limit reached; emit handoff with evidence."
    elif category in {"dependency_or_environment_error", "timeout_or_flaky"}:
        next_tool = "fallback_test_strategy"
        reason = "Environment/flaky failure should downgrade validation before patching."
    elif category == "policy_or_permission_block":
        next_tool = "handoff_digest"
        reason = "Policy block requires LLM/user decision, not automatic repair."
    else:
        next_tool = "next_patch_generator"
        reason = "Failure appears repairable with another candidate patch."
    return _envelope(
        "repair_loop_planner",
        "ok",
        {"summary": f"Repair loop plan: {next_tool}", "loop_count": loop_count, "limit": limit, "exhausted": exhausted, "failure_category": category},
        next_action=_hint(next_tool, reason, 0.82 if not exhausted else 0.95),
    )


def next_patch_generator(repo_root: str | Path, failure_analysis: Mapping[str, Any], target_files: Optional[Sequence[str]] = None) -> Dict[str, Any]:
    root = Path(repo_root).resolve()
    category = str(failure_analysis.get("primary_category") or failure_analysis.get("category") or "unknown_failure")
    proposals: List[Dict[str, Any]] = []
    for rel in list(target_files or [])[:12]:
        proposals.append({
            "path": rel,
            "edit_type": "manual_llm_required",
            "reason": f"Candidate target for {category}; LLM must inspect file and create concrete edit_units.",
        })
    if not proposals:
        proposals.append({
            "path": ".",
            "edit_type": "localize_first",
            "reason": f"No target files provided for {category}; run localization before patch generation.",
        })
    return _envelope(
        "next_patch_generator",
        "ok",
        {"summary": f"Generated {len(proposals)} next-patch proposal(s); no file written.", "repo_root": str(root), "failure_category": category, "proposals": proposals},
        next_action=_hint("edit_unit_planner", "LLM must convert proposal into explicit edit units, then run conflict_detector.", 0.78),
    )
