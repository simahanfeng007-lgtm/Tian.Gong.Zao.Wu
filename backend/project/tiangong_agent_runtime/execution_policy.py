"""执行策略与风险等级。

L6.72 起，A0-A4 不再只靠固定集合判断，而是先通过 BioDynamicState
计算执行倾向；A5 仍保持硬边界，避免把不可逆高危行为交给漂移公式。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .biodynamic_policy_core import BioDynamicState, clamp01, dynamic_threshold


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


_RISK_BASE_LOAD: dict[RiskLevel, float] = {
    RiskLevel.A0: 0.05,
    RiskLevel.A1: 0.12,
    RiskLevel.A2: 0.24,
    RiskLevel.A3: 0.42,
    RiskLevel.A4: 0.66,
    RiskLevel.A5: 1.00,
}

_RISK_BASE_THRESHOLD: dict[RiskLevel, float] = {
    RiskLevel.A0: 0.18,
    RiskLevel.A1: 0.26,
    RiskLevel.A2: 0.34,
    RiskLevel.A3: 0.46,
    RiskLevel.A4: 0.62,
    RiskLevel.A5: 0.98,
}


@dataclass(frozen=True)
class ExecutionPolicy:
    """执行力优先策略：A0-A4 默认放行，A5 硬阻断。"""

    auto_execute_levels: frozenset[RiskLevel] = field(
        default_factory=lambda: frozenset({RiskLevel.A0, RiskLevel.A1, RiskLevel.A2, RiskLevel.A3, RiskLevel.A4})
    )
    confirmation_levels: frozenset[RiskLevel] = field(default_factory=lambda: frozenset())
    blocked_levels: frozenset[RiskLevel] = field(default_factory=lambda: frozenset({RiskLevel.A5}))
    max_output_chars: int = 12_000
    default_timeout_seconds: float = 120.0
    execution_drive_bias: float = 0.74
    rollback_recovery_bias: float = 0.72
    confirmation_margin: float = 0.08

    def __post_init__(self) -> None:
        for field_name in ("execution_drive_bias", "rollback_recovery_bias", "confirmation_margin"):
            clamp01(getattr(self, field_name))
        if isinstance(self.max_output_chars, bool) or not isinstance(self.max_output_chars, int) or self.max_output_chars <= 0:
            raise ValueError("ExecutionPolicy.max_output_chars must be positive int")
        if isinstance(self.default_timeout_seconds, bool) or not isinstance(self.default_timeout_seconds, (int, float)) or self.default_timeout_seconds <= 0:
            raise ValueError("ExecutionPolicy.default_timeout_seconds must be positive number")

    @classmethod
    def default(cls) -> "ExecutionPolicy":
        return cls()

    def biodynamic_state_for(
        self,
        risk_level: RiskLevel | str,
        *,
        evidence: float = 0.72,
        user_intent: float = 0.70,
        resource_pressure: float = 0.0,
        failure_pressure: float = 0.0,
        uncertainty_pressure: float = 0.0,
        reversibility: float = 0.72,
    ) -> BioDynamicState:
        level = RiskLevel(risk_level)
        base_load = _RISK_BASE_LOAD[level]
        return BioDynamicState(
            evidence=evidence,
            drive=self.execution_drive_bias,
            user_intent=user_intent,
            resource_pressure=max(base_load, clamp01(resource_pressure)),
            failure_pressure=clamp01(failure_pressure),
            uncertainty_pressure=clamp01(uncertainty_pressure),
            privacy_pressure=0.0,
            pollution_pressure=0.0,
            conflict_pressure=base_load if level is RiskLevel.A4 else 0.0,
            fatigue=0.0,
            recovery=self.rollback_recovery_bias,
            reversibility=reversibility,
            inertia=base_load,
        )

    def dynamic_status(
        self,
        risk_level: RiskLevel | str,
        *,
        evidence: float = 0.72,
        user_intent: float = 0.70,
        resource_pressure: float = 0.0,
        failure_pressure: float = 0.0,
        uncertainty_pressure: float = 0.0,
        reversibility: float = 0.72,
    ) -> PermitStatus:
        """L6.72.39 执行力优先裁决：A5 才硬拦，A0-A4 默认放行。

        BioDynamicState 仍可用于审计和状态解释，但不再把 A0-A4 降级成确认等待。
        这保留 Runtime/QualityGate/Audit 链路，同时删除对代码编辑能力影响最大的
        非 A5 摩擦。
        """
        level = RiskLevel(risk_level)
        if level is RiskLevel.A5 or level in self.blocked_levels:
            return PermitStatus.BLOCKED
        return PermitStatus.ALLOWED
