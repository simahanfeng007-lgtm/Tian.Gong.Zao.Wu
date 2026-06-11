"""运行报告导出。

L6.13-L6.32 运行报告只导出可公开摘要：计划、结果、审计摘要、长链摘要、
确认票据摘要和 L6.32 Planner 执行主链报告。禁止导出 API Key、完整内部 prompt 或未脱敏凭证。
"""

from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any


def export_runtime_report(result: Any, target: str | Path) -> Path:
    path = Path(target).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    data = runtime_result_to_public_dict(result)
    if path.suffix.lower() == ".md":
        path.write_text(_to_markdown(data), encoding="utf-8")
    else:
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def runtime_result_to_public_dict(result: Any) -> dict[str, Any]:
    return {
        "intent": _safe_dataclass(getattr(result, "intent", None)),
        "plan": [_tool_invocation_to_dict(item) for item in getattr(result, "plan", [])],
        "results": [_tool_result_to_dict(item) for item in getattr(result, "results", [])],
        "projection": _safe_dataclass(getattr(result, "projection", None)),
        "audit_events": list(getattr(result, "audit_events", []) or []),
        # L6.73.0：A5/人工确认票据必须进入 public projection，供前端弹窗；
        # 只导出票据摘要，不导出原始工具参数/敏感正文。
        "pending_confirmations": _json_safe(list(getattr(result, "pending_confirmations", []) or [])),
        "chain_summary": _safe_dataclass(getattr(result, "chain_summary", None)),
        "suggestion_bridge": _safe_dataclass(getattr(result, "suggestion_bridge", None)),
        "planner_execution_report": _safe_public_dict(getattr(result, "planner_execution_report", None)),
        "task_id": getattr(result, "task_id", ""),
        "status": getattr(result, "status", ""),
        "failure_kind": getattr(result, "failure_kind", ""),
        "provider_status": getattr(result, "provider_status", ""),
        "has_executed_tools": bool(getattr(result, "has_executed_tools", False)),
        "plan_repair_attempted": bool(getattr(result, "plan_repair_attempted", False)),
        "deterministic_fallback_used": bool(getattr(result, "deterministic_fallback_used", False)),
        "final_output_contract": getattr(result, "final_output_contract", "execution_report"),
        "user_visible_summary": getattr(result, "user_visible_summary", ""),
        "next_action": getattr(result, "next_action", ""),
        "planner_result": _safe_public_dict(getattr(result, "planner_result", None)),
        "activation_form": _safe_public_dict(getattr(result, "activation_form", None)),
        "task_state_snapshot": _safe_public_dict(getattr(result, "task_state_snapshot", None)),
        "adaptive_work_loop": _safe_public_dict(getattr(result, "adaptive_work_loop", None)),
        "context_window_bundle": _safe_public_dict(getattr(result, "context_window_bundle", None)),
        "skill_playbook_route": _safe_public_dict(getattr(result, "skill_playbook_route", None)),
        "active_model_policy": _safe_public_dict(getattr(result, "active_model_policy", None)),
    }


def _safe_public_dict(value: Any) -> Any:
    if value is None:
        return None
    if hasattr(value, "public_dict"):
        return _json_safe(value.public_dict())
    return _safe_dataclass(value)


def _safe_dataclass(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value):
        return _json_safe(asdict(value))
    if hasattr(value, "to_dict"):
        return _json_safe(value.to_dict())
    return _json_safe(value)


def _tool_invocation_to_dict(invocation: Any) -> dict[str, Any]:
    risk = getattr(invocation, "risk_level", None)
    return {
        "step_id": getattr(invocation, "step_id", ""),
        "tool_name": getattr(invocation, "tool_name", ""),
        "risk_level": getattr(risk, "value", risk) if risk else None,
        "reason": getattr(invocation, "reason", ""),
        "arguments": _json_safe(getattr(invocation, "arguments", {})),
    }


def _tool_result_to_dict(result: Any) -> dict[str, Any]:
    status = getattr(result, "status", "")
    return {
        "step_id": getattr(result, "step_id", ""),
        "tool_name": getattr(result, "tool_name", ""),
        "status": getattr(status, "value", status),
        "output_summary": getattr(result, "output_summary", ""),
        "artifacts": list(getattr(result, "artifacts", []) or []),
        "error_code": getattr(result, "error_code", ""),
        "audit_ref": getattr(result, "audit_ref", ""),
        "data": _json_safe(getattr(result, "data", {})),
    }


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, list | tuple):
        return [_json_safe(v) for v in value]
    if hasattr(value, "value"):
        return value.value
    if isinstance(value, str | int | float | bool) or value is None:
        return value
    return str(value)


def _to_markdown(data: dict[str, Any]) -> str:
    lines = ["# 天工造物 L6.32 运行报告", ""]
    projection = data.get("projection") or {}
    lines.append(f"- status: {projection.get('status', '<unknown>')}")
    lines.append(f"- audit_count: {projection.get('audit_count', 0)}")
    chain = data.get("chain_summary") or {}
    if chain:
        lines.append(f"- chain: {chain.get('executed_steps', 0)}/{chain.get('total_steps', 0)} stopped={chain.get('stopped_reason', '')}")
    planner_execution = data.get("planner_execution_report") or {}
    if planner_execution:
        lines.append(f"- planner_execution: {planner_execution.get('status', '')} executed={planner_execution.get('executed_steps', 0)}/{planner_execution.get('total_steps', 0)}")
    adaptive = data.get("adaptive_work_loop") or {}
    if adaptive:
        lines.append(f"- adaptive_work_loop: {adaptive.get('status', '')} repair_attempted={adaptive.get('repair_attempted', False)} repair_executed={adaptive.get('repair_executed', False)}")
    context_bundle = data.get("context_window_bundle") or {}
    if context_bundle:
        lines.append(f"- context_window: tier={context_bundle.get('model_tier', '')} stage={context_bundle.get('stage', '')} packs={','.join(context_bundle.get('pack_names', []) or [])}")
    playbook = data.get("skill_playbook_route") or {}
    if playbook:
        lines.append(f"- skill_playbook: {playbook.get('playbook_id', '')} phase={playbook.get('current_phase', '')}")
    active_policy = data.get("active_model_policy") or {}
    if active_policy:
        lines.append(f"- active_model_policy: role={active_policy.get('model_role', '')} status={active_policy.get('status', '')} max_steps={active_policy.get('effective_max_steps', '')} prompt_contract={active_policy.get('prompt_contract', '')}")
    lines.extend(["", "## Summary", "", str(projection.get("summary", "")), "", "## Results", ""])
    for item in data.get("results") or []:
        lines.append(f"- {item.get('tool_name')}: {item.get('status')} ｜ {item.get('output_summary')}")
    lines.extend(["", "## Artifacts", ""])
    for artifact in projection.get("artifacts") or []:
        lines.append(f"- {artifact}")
    return "\n".join(lines).rstrip() + "\n"
