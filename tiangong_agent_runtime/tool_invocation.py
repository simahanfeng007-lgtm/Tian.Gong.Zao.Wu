"""工具调用计划对象。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from .execution_policy import RiskLevel


@dataclass(frozen=True)
class ToolInvocation:
    tool_name: str
    arguments: dict[str, Any] = field(default_factory=dict)
    step_id: str = field(default_factory=lambda: f"step_{uuid4().hex[:12]}")
    risk_level: RiskLevel | None = None
    reason: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ToolInvocation":
        raw_risk = data.get("risk_level")
        risk = RiskLevel(raw_risk) if raw_risk else None
        return cls(
            tool_name=str(data.get("tool_name") or data.get("kind") or "").strip(),
            arguments=dict(data.get("arguments") or {}),
            step_id=str(data.get("step_id") or f"step_{uuid4().hex[:12]}"),
            risk_level=risk,
            reason=str(data.get("reason") or ""),
        )

    def with_risk(self, risk_level: RiskLevel, reason: str = "") -> "ToolInvocation":
        return ToolInvocation(
            tool_name=self.tool_name,
            arguments=dict(self.arguments),
            step_id=self.step_id,
            risk_level=risk_level,
            reason=reason or self.reason,
        )
