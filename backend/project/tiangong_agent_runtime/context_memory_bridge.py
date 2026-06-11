"""L6.15 上下文/会话/记忆连续性桥。

该桥属于外壳运行层，不写入 tiangong_kernel 主体，不做真实长期记忆持久化。
它只维护当前进程内的安全摘要，供 CLI / planner / report 读取，避免长链任务断片。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from time import time
from typing import Any
from uuid import uuid4
import json

from tiangong_agent_shell.safe_logging import redact_text


SENSITIVE_TOKENS = ("api_key", "secret", "token", "password", "credential", "Authorization", "Bearer ")


def _safe_text(value: Any, *, limit: int = 500) -> str:
    text = str(value or "")
    text = redact_text(text)
    for token in SENSITIVE_TOKENS:
        if token.lower() in text.lower():
            # 不把疑似凭据语义原样带入上下文桥。
            text = text.replace(token, f"{token[:2]}***")
    return text[:limit]


@dataclass(frozen=True)
class ContextMemoryRecord:
    record_id: str
    created_at: float
    kind: str
    user_preview: str
    intent: str
    status: str
    summary: str
    plan_steps: list[str] = field(default_factory=list)
    artifacts: list[str] = field(default_factory=list)
    audit_count: int = 0
    risk_notes: list[str] = field(default_factory=list)

    def public_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "created_at": self.created_at,
            "kind": self.kind,
            "user_preview": self.user_preview,
            "intent": self.intent,
            "status": self.status,
            "summary": self.summary,
            "plan_steps": list(self.plan_steps),
            "artifacts": list(self.artifacts),
            "audit_count": self.audit_count,
            "risk_notes": list(self.risk_notes),
        }


@dataclass(frozen=True)
class ContextSnapshot:
    session_records: int
    recent: list[dict[str, Any]]
    planner_hint: str

    def public_dict(self) -> dict[str, Any]:
        return {
            "session_records": self.session_records,
            "recent": self.recent,
            "planner_hint": self.planner_hint,
        }


class ContextMemoryBridge:
    """当前进程内上下文连续性桥。

    设计边界：
    - 只存安全摘要，不存完整 prompt、API Key、完整文件内容。
    - 默认内存态，不写长期记忆。
    - 导出需要用户显式命令触发。
    """

    def __init__(self, *, max_records: int = 50) -> None:
        self.max_records = max(1, int(max_records))
        self._records: list[ContextMemoryRecord] = []

    @property
    def records(self) -> list[ContextMemoryRecord]:
        return list(self._records)

    def reset(self) -> None:
        self._records.clear()

    def observe_run(self, result: Any) -> ContextMemoryRecord | None:
        user_preview = _safe_text(getattr(getattr(result, "intent", None), "label", ""), limit=120)
        plan = list(getattr(result, "plan", []) or [])
        results = list(getattr(result, "results", []) or [])
        projection = getattr(result, "projection", None)
        status = _safe_text(getattr(projection, "status", "unknown"), limit=80)
        summary = _safe_text(getattr(projection, "summary", ""), limit=500)
        artifacts = [_safe_text(a, limit=240) for a in list(getattr(projection, "artifacts", []) or [])]
        plan_steps = []
        for step in plan:
            tool_name = getattr(step, "tool_name", "unknown")
            reason = getattr(step, "reason", "")
            plan_steps.append(_safe_text(f"{tool_name}: {reason}", limit=200))
        risk_notes = []
        for item in results:
            if not getattr(item, "ok", False):
                risk_notes.append(_safe_text(getattr(item, "output_summary", ""), limit=200))
        intent = _safe_text(getattr(getattr(result, "intent", None), "label", "unknown"), limit=120)
        kind = "model_chat" if any(getattr(step, "tool_name", "") == "model_chat" for step in plan) else "runtime_task"
        record = ContextMemoryRecord(
            record_id=f"ctx_{uuid4().hex[:12]}",
            created_at=time(),
            kind=kind,
            user_preview=user_preview or intent,
            intent=intent,
            status=status,
            summary=summary,
            plan_steps=plan_steps[:20],
            artifacts=artifacts[:20],
            audit_count=int(getattr(projection, "audit_count", 0) or 0),
            risk_notes=risk_notes[:10],
        )
        self._records.append(record)
        if len(self._records) > self.max_records:
            self._records = self._records[-self.max_records :]
        return record

    def public_summary(self, *, limit: int = 8) -> list[dict[str, Any]]:
        return [record.public_dict() for record in self._records[-max(1, limit) :]]

    def build_planner_hint(self, *, limit: int = 5) -> str:
        recent = self._records[-max(1, limit) :]
        if not recent:
            return ""
        lines = ["最近运行上下文摘要（仅安全摘要，不含密钥/完整文件内容）："]
        for record in recent:
            steps = ", ".join(record.plan_steps[:3]) or "无计划步骤"
            artifacts = ", ".join(record.artifacts[:3]) or "无产物"
            lines.append(
                f"- {record.status} | {record.intent} | {record.summary[:160]} | steps={steps} | artifacts={artifacts}"
            )
        return "\n".join(lines)[:2000]

    def snapshot(self, *, limit: int = 8) -> ContextSnapshot:
        return ContextSnapshot(
            session_records=len(self._records),
            recent=self.public_summary(limit=limit),
            planner_hint=self.build_planner_hint(limit=min(limit, 5)),
        )

    def export_json(self, path: str | Path) -> Path:
        target = Path(path).expanduser().resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema": "tiangong.l6_15.context_memory.v1",
            "records": [record.public_dict() for record in self._records],
        }
        target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return target
