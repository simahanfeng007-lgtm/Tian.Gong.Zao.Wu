"""L2 状态边界对象，只记录边界结果事实，不做风险评分、权限裁决或替代执行。"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.decision import Decision
from tiangong_kernel.l0_primitives.identity import TypedRef
from tiangong_kernel.l0_primitives.risk import RiskView
from tiangong_kernel.l1_ports.envelope import PortBoundaryContext


class L2BoundaryStatusKind(str, Enum):
    """L2 边界状态枚举；只表达已知边界结果，不触发裁决。"""

    UNKNOWN = "unknown"
    PASSED = "passed"
    BLOCKED = "blocked"
    DEGRADED = "degraded"
    NEEDS_CONFIRMATION = "needs_confirmation"
    NEEDS_VALIDATION = "needs_validation"
    NEEDS_ROLLBACK_READY = "needs_rollback_ready"


@dataclass(frozen=True, slots=True)
class L2StateBoundary:
    """L2 状态边界事实。

    作用：记录端口边界上下文、风险视图、裁决事实、替代路径和证据引用。
    边界：不做真实评分，不发起确认，不执行替代路径，只保存边界结果。
    """

    status: L2BoundaryStatusKind = L2BoundaryStatusKind.UNKNOWN
    boundary_context: PortBoundaryContext | None = None
    risk_view: RiskView | None = None
    decision: Decision | None = None
    alternative_paths: tuple[str, ...] = field(default_factory=tuple)
    violation_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("L2StateBoundary.schema_version cannot be empty")
