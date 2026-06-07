"""审计回放工具。

只基于 AuditEvent 安全摘要重建执行概览，不重放真实工具，不恢复密钥，
不产生任何副作用。
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class AuditReplaySummary:
    total_events: int
    by_tool: dict[str, int] = field(default_factory=dict)
    by_status: dict[str, int] = field(default_factory=dict)
    by_risk: dict[str, int] = field(default_factory=dict)
    artifact_count: int = 0
    error_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_events": self.total_events,
            "by_tool": self.by_tool,
            "by_status": self.by_status,
            "by_risk": self.by_risk,
            "artifact_count": self.artifact_count,
            "error_count": self.error_count,
        }


def replay_audit_events(events: list[dict[str, Any]]) -> AuditReplaySummary:
    return AuditReplaySummary(
        total_events=len(events),
        by_tool=dict(Counter(str(event.get("tool_name") or "") for event in events)),
        by_status=dict(Counter(str(event.get("output_status") or "") for event in events)),
        by_risk=dict(Counter(str(event.get("risk_level") or "") for event in events)),
        artifact_count=sum(len(event.get("artifacts") or []) for event in events),
        error_count=sum(1 for event in events if event.get("error_code")),
    )
