"""统一工具结果。"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ToolResultStatus(str, Enum):
    OK = "ok"
    FAILED = "failed"
    BLOCKED = "blocked"
    CONFIRMATION_REQUIRED = "confirmation_required"
    SKIPPED = "skipped"
    TIMEOUT = "timeout"


@dataclass(frozen=True)
class ToolResult:
    step_id: str
    tool_name: str
    status: ToolResultStatus
    output_summary: str = ""
    data: dict[str, Any] = field(default_factory=dict)
    artifacts: list[str] = field(default_factory=list)
    error_code: str = ""
    audit_ref: str = ""

    @property
    def ok(self) -> bool:
        return self.status is ToolResultStatus.OK
