"""L6 插件建议对象。

建议对象只能表达“希望运行链考虑什么”，不能直接执行工具。真正执行仍必须经
ExecutionSpine → RiskClassifier → PermitGateway → RuntimeToolRegistry → Adapter。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class PlanSuggestion:
    source_plugin: str
    summary: str
    steps: list[dict[str, Any]] = field(default_factory=list)
    confidence: float = 0.0
    direct_execution_requested: bool = False


@dataclass(frozen=True)
class RepairSuggestion:
    source_plugin: str
    summary: str
    target_step_id: str = ""
    proposed_steps: list[dict[str, Any]] = field(default_factory=list)
    confidence: float = 0.0


@dataclass(frozen=True)
class QualityGateSuggestion:
    source_plugin: str
    summary: str
    required_checks: list[str] = field(default_factory=list)
    confidence: float = 0.0


@dataclass(frozen=True)
class HandoffSuggestion:
    source_plugin: str
    summary: str
    handoff_notes: list[str] = field(default_factory=list)
    confidence: float = 0.0
