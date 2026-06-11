"""审计桥：记录每步安全摘要。"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from time import time
from typing import Any
from uuid import uuid4

from tiangong_agent_shell.safe_logging import sanitize_mapping

from .execution_policy import PermitStatus, RiskLevel
from .tool_invocation import ToolInvocation
from .tool_result import ToolResult


@dataclass(frozen=True)
class AuditEvent:
    audit_id: str
    timestamp: float
    step_id: str
    tool_name: str
    risk_level: str
    permit_status: str
    output_status: str
    input_summary: dict[str, Any] = field(default_factory=dict)
    output_summary: str = ""
    artifacts: list[str] = field(default_factory=list)
    error_code: str = ""


class AuditBridge:
    def __init__(self) -> None:
        self.events: list[AuditEvent] = []

    def record(
        self,
        invocation: ToolInvocation,
        *,
        risk_level: RiskLevel,
        permit_status: PermitStatus,
        result: ToolResult,
    ) -> str:
        audit_id = f"audit_{uuid4().hex[:12]}"
        event = AuditEvent(
            audit_id=audit_id,
            timestamp=time(),
            step_id=invocation.step_id,
            tool_name=invocation.tool_name,
            risk_level=risk_level.value,
            permit_status=permit_status.value,
            output_status=result.status.value,
            input_summary=sanitize_mapping(invocation.arguments),
            output_summary=result.output_summary,
            artifacts=list(result.artifacts),
            error_code=result.error_code,
        )
        self.events.append(event)
        return audit_id


    def export_jsonl(self, path: str | Path) -> Path:
        """导出审计 JSONL。只写安全摘要，不包含密钥明文。"""
        target = Path(path).expanduser().resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("w", encoding="utf-8") as fh:
            for event in self.events:
                fh.write(json.dumps(asdict(event), ensure_ascii=False, sort_keys=True) + "\n")
        return target

    @staticmethod
    def load_jsonl(path: str | Path) -> list[dict[str, Any]]:
        """读取审计 JSONL 为安全摘要列表；不触发任何真实执行。"""
        source = Path(path).expanduser().resolve()
        events: list[dict[str, Any]] = []
        if not source.exists():
            return events
        with source.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                data = json.loads(line)
                if isinstance(data, dict):
                    events.append(data)
        return events

    def recent_summary(self, limit: int = 20) -> list[dict[str, Any]]:
        return [asdict(event) for event in self.events[-limit:]]
