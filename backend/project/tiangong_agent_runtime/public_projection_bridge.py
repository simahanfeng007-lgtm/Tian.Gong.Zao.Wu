"""公共投影桥：只输出安全摘要。"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from typing import Any

from .tool_result import ToolResult


L6_48_DESKTOP_PUBLIC_PROJECTION_SCHEMA = "tiangong.l6_48.desktop_public_projection.v1"
_SENSITIVE_PATTERN = re.compile(
    r"(?i)(api[_-]?key|authorization|bearer\s+|token|secret|password|credential|private[_-]?key)\s*[:=]?\s*[^\s,;]+"
)
_SECRET_VALUE_PATTERN = re.compile(r"(?i)mockkey_[a-z0-9][a-z0-9_\-]{8,}")
_ENDPOINT_PATTERN = re.compile(r"(?i)https?://[^\s,;]+")
_PATH_PATTERN = re.compile(r"(?i)([a-z]:\\\\[^\s]+|/[^\s]+(?:/[^\s]+)+)")


@dataclass(frozen=True)
class RuntimeProjection:
    status: str
    summary: str
    artifacts: list[str] = field(default_factory=list)
    audit_count: int = 0
    chain: dict[str, Any] = field(default_factory=dict)
    pending_confirmations: list[dict[str, Any]] = field(default_factory=list)


@dataclass(frozen=True)
class DesktopDashboardProjection:
    """L6.48 桌面驾驶舱只读公共投影。

    该对象只面向前端展示：任务快照、质量门、审计摘要、对话指引和底部轻量指标。
    它不携带工具调用入口、Provider SDK 参数、长期记忆写入口或自我迭代合入口。
    """

    runtime_status: str
    runtime_summary: str
    task_snapshot: dict[str, Any] = field(default_factory=dict)
    quality_gate: dict[str, Any] = field(default_factory=dict)
    audit_summary: dict[str, Any] = field(default_factory=dict)
    conversation_guide: dict[str, Any] = field(default_factory=dict)
    status_bar: dict[str, Any] = field(default_factory=dict)
    sensitive_digest_refs: list[str] = field(default_factory=list)
    frontend_readonly: bool = True
    projection_only: bool = True
    no_direct_tool_call: bool = True
    no_provider_sdk: bool = True
    no_memory_write: bool = True
    no_self_iteration_merge: bool = True
    no_plain_endpoint: bool = True
    no_plain_token: bool = True

    def __post_init__(self) -> None:
        required_true = (
            self.frontend_readonly,
            self.projection_only,
            self.no_direct_tool_call,
            self.no_provider_sdk,
            self.no_memory_write,
            self.no_self_iteration_merge,
            self.no_plain_endpoint,
            self.no_plain_token,
        )
        if not all(isinstance(item, bool) for item in required_true):
            raise TypeError("DesktopDashboardProjection boundary flags must be bool")
        if not all(required_true):
            raise ValueError("DesktopDashboardProjection must remain read-only public projection")

    def public_dict(self) -> dict[str, Any]:
        payload = {
            "schema": L6_48_DESKTOP_PUBLIC_PROJECTION_SCHEMA,
            "runtime_status": _safe_public_text(self.runtime_status, limit=80),
            "runtime_summary": _safe_public_text(self.runtime_summary, limit=900),
            "task_snapshot": _safe_public_payload(self.task_snapshot),
            "quality_gate": _safe_public_payload(self.quality_gate),
            "audit_summary": _safe_public_payload(self.audit_summary),
            "conversation_guide": _safe_public_payload(self.conversation_guide),
            "status_bar": _safe_public_payload(self.status_bar),
            "sensitive_digest_refs": [_safe_public_text(item, limit=120) for item in self.sensitive_digest_refs[:12]],
            "frontend_readonly": self.frontend_readonly,
            "projection_only": self.projection_only,
            "no_direct_tool_call": self.no_direct_tool_call,
            "no_provider_sdk": self.no_provider_sdk,
            "no_memory_write": self.no_memory_write,
            "no_self_iteration_merge": self.no_self_iteration_merge,
            "no_plain_endpoint": self.no_plain_endpoint,
            "no_plain_token": self.no_plain_token,
        }
        raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)
        if _SECRET_VALUE_PATTERN.search(raw) or _ENDPOINT_PATTERN.search(raw):
            raise ValueError("DesktopDashboardProjection leaked sensitive locator or credential")
        return payload


def build_public_projection(
    results: list[ToolResult],
    audit_count: int,
    chain_summary: Any | None = None,
    pending_confirmations: list[dict[str, Any]] | None = None,
) -> RuntimeProjection:
    pending = pending_confirmations or []
    if not results:
        chain = _chain_to_public_dict(chain_summary)
        return RuntimeProjection(
            status="no_plan",
            summary="未生成可执行计划。",
            audit_count=audit_count,
            chain=chain,
            pending_confirmations=pending,
        )
    status = "ok" if all(result.ok for result in results) else "partial_or_failed"
    lines = [f"- {result.tool_name}: {result.status.value}｜{result.output_summary}" for result in results]
    artifacts: list[str] = []
    for result in results:
        artifacts.extend(result.artifacts)
    chain = _chain_to_public_dict(chain_summary)
    if chain:
        lines.append(
            f"[工作链] executed={chain.get('executed_steps')}/{chain.get('total_steps')} "
            f"stopped_reason={chain.get('stopped_reason')} failures={chain.get('failure_count')}"
        )
    if pending:
        ids = ", ".join(str(item.get("ticket_id")) for item in pending[:5])
        lines.append(f"[待确认] {len(pending)} 个确认票据：{ids}")
    return RuntimeProjection(
        status=status,
        summary="\n".join(lines),
        artifacts=artifacts,
        audit_count=audit_count,
        chain=chain,
        pending_confirmations=pending,
    )


def build_desktop_dashboard_projection(
    projection: RuntimeProjection,
    *,
    task_title: str = "",
    quality_gate: dict[str, Any] | None = None,
    audit_events: list[dict[str, Any]] | None = None,
    context_snapshot: dict[str, Any] | None = None,
    budget_snapshot: dict[str, Any] | None = None,
    conversation_guide: str = "",
) -> DesktopDashboardProjection:
    """构造桌面端只读驾驶舱投影。

    前端应读取该投影，而不是直连工具、Provider SDK、记忆写入或版本槽切换。
    所有 endpoint/token/key/path 类字段在这里降噪为摘要或占位。
    """
    chain = projection.chain or {}
    audit_events = list(audit_events or [])
    context_snapshot = context_snapshot or {}
    budget_snapshot = budget_snapshot or {}
    quality_gate = quality_gate or {}
    task_snapshot = {
        "title": task_title or "当前任务",
        "runtime_status": projection.status,
        "total_steps": chain.get("total_steps", 0),
        "executed_steps": chain.get("executed_steps", 0),
        "failure_count": chain.get("failure_count", 0),
        "stopped_reason": chain.get("stopped_reason", ""),
        "pending_confirmations": len(projection.pending_confirmations),
        "artifact_count": len(projection.artifacts),
    }
    audit_refs = []
    for event in audit_events[-8:]:
        audit_refs.append(
            {
                "event_ref": event.get("event_id") or event.get("audit_ref") or _digest_public(event),
                "tool_name": event.get("tool_name") or event.get("tool") or "runtime_event",
                "status": event.get("status") or event.get("decision") or "recorded",
                "digest": _digest_public(event),
            }
        )
    status_bar = {
        "context": context_snapshot.get("session_records", context_snapshot.get("status", "unknown")),
        "compression": context_snapshot.get("compression", "not_reported"),
        "hit_current": budget_snapshot.get("hit_current", budget_snapshot.get("current_hit", "not_reported")),
        "hit_average": budget_snapshot.get("hit_average", budget_snapshot.get("average_hit", "not_reported")),
        "current_consumption": budget_snapshot.get("current_consumption", budget_snapshot.get("spent", "not_reported")),
        "task_count": budget_snapshot.get("task_count", chain.get("total_steps", 0)),
        "balance": budget_snapshot.get("balance", "not_reported"),
    }
    sensitive_refs = _collect_sensitive_digest_refs(
        {
            "runtime_summary": projection.summary,
            "task_snapshot": task_snapshot,
            "quality_gate": quality_gate,
            "audit_events": audit_events,
            "context_snapshot": context_snapshot,
            "budget_snapshot": budget_snapshot,
            "conversation_guide": conversation_guide,
        }
    )
    return DesktopDashboardProjection(
        runtime_status=projection.status,
        runtime_summary=projection.summary,
        task_snapshot=task_snapshot,
        quality_gate=quality_gate,
        audit_summary={"audit_count": projection.audit_count, "recent_refs": audit_refs},
        conversation_guide={
            "summary": conversation_guide or "等待用户输入。",
            "fixed_chat_input_required": True,
            "home_should_stay_minimal": True,
        },
        status_bar=status_bar,
        sensitive_digest_refs=sensitive_refs,
    )


def _chain_to_public_dict(chain_summary: Any | None) -> dict[str, Any]:
    if chain_summary is None:
        return {}
    checkpoints = []
    for checkpoint in getattr(chain_summary, "checkpoints", [])[:20]:
        checkpoints.append(
            {
                "index": checkpoint.index,
                "step_id": checkpoint.step_id,
                "tool_name": checkpoint.tool_name,
                "status": checkpoint.status,
                "audit_ref": checkpoint.audit_ref,
                "error_code": checkpoint.error_code,
            }
        )
    return {
        "total_steps": getattr(chain_summary, "total_steps", 0),
        "executed_steps": getattr(chain_summary, "executed_steps", 0),
        "failure_count": getattr(chain_summary, "failure_count", 0),
        "stopped_reason": getattr(chain_summary, "stopped_reason", ""),
        "checkpoints": checkpoints,
    }


def _digest_public(payload: Any, *, length: int = 16) -> str:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:length]


def _safe_public_text(value: Any, *, limit: int = 700) -> str:
    text = "" if value is None else str(value)
    text = text.replace("\x00", "").replace("\r", " ").replace("\n", " ").strip()
    text = _SENSITIVE_PATTERN.sub("[redacted-sensitive]", text)
    text = _ENDPOINT_PATTERN.sub(lambda match: f"[redacted-endpoint:{_digest_public(match.group(0), length=12)}]", text)
    text = _PATH_PATTERN.sub("[redacted-path]", text)
    return text[: max(0, int(limit))]


def _safe_public_payload(value: Any, *, limit: int = 700) -> Any:
    if isinstance(value, dict):
        result: dict[str, Any] = {}
        for key, item in list(value.items())[:40]:
            clean_key = _safe_public_text(key, limit=80) or "field"
            lowered = clean_key.lower()
            if any(marker in lowered for marker in ("api_key", "token", "secret", "password", "credential", "base_url", "endpoint")):
                result[f"redacted_field_{_digest_public(clean_key, length=8)}"] = f"[redacted-digest:{_digest_public(item, length=12)}]"
            else:
                result[clean_key] = _safe_public_payload(item, limit=limit)
        return result
    if isinstance(value, (list, tuple)):
        return [_safe_public_payload(item, limit=limit) for item in list(value)[:20]]
    if isinstance(value, (str, int, float, bool)) or value is None:
        if isinstance(value, str):
            return _safe_public_text(value, limit=limit)
        return value
    return _safe_public_text(value, limit=limit)


def _collect_sensitive_digest_refs(payload: Any) -> list[str]:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)
    refs: list[str] = []
    for pattern_name, pattern in (("sensitive", _SENSITIVE_PATTERN), ("endpoint", _ENDPOINT_PATTERN), ("path", _PATH_PATTERN)):
        for match in pattern.finditer(raw):
            ref = f"{pattern_name}:digest:{_digest_public(match.group(0), length=12)}"
            if ref not in refs:
                refs.append(ref)
            if len(refs) >= 12:
                return refs
    return refs
