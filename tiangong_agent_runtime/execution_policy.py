"""执行策略与风险等级。"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class RiskLevel(str, Enum):
    A0 = "A0"
    A1 = "A1"
    A2 = "A2"
    A3 = "A3"
    A4 = "A4"
    A5 = "A5"


class PermitStatus(str, Enum):
    ALLOWED = "allowed"
    CONFIRMATION_REQUIRED = "confirmation_required"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class ExecutionPolicy:
    """默认执行策略：A0-A3 自动，A4 确认，A5 阻断。"""

    auto_execute_levels: frozenset[RiskLevel] = field(
        default_factory=lambda: frozenset({RiskLevel.A0, RiskLevel.A1, RiskLevel.A2, RiskLevel.A3})
    )
    confirmation_levels: frozenset[RiskLevel] = field(default_factory=lambda: frozenset({RiskLevel.A4}))
    blocked_levels: frozenset[RiskLevel] = field(default_factory=lambda: frozenset({RiskLevel.A5}))
    max_output_chars: int = 12_000
    default_timeout_seconds: float = 120.0

    @classmethod
    def default(cls) -> "ExecutionPolicy":
        return cls()
