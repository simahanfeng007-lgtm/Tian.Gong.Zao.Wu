"""L1 端口边界说明。

本模块定义端口能做什么、不能做什么、越界时如何解释以及可替代路径。
边界说明只负责表达，不负责复杂裁决、审批、风险评分或真实资源控制。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef


class BoundarySeverity(str, Enum):
    """边界严重度枚举；只表达越界程度。"""

    UNKNOWN = "unknown"
    INFO = "info"
    WARNING = "warning"
    BLOCKING = "blocking"
    FATAL = "fatal"


@dataclass(frozen=True, slots=True)
class BoundaryHint:
    """边界提示。

    作用：说明越界原因、可替代路径和调用方可理解的修正方向。
    边界：不执行替代路径，不生成新计划。
    """

    reason: str
    suggested_fix: str = ""
    alternative_paths: tuple[str, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.reason:
            raise ValueError("BoundaryHint.reason cannot be empty")
        if not self.schema_version:
            raise ValueError("BoundaryHint.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class BoundaryRule:
    """边界规则声明。

    作用：以文字和引用形式表达端口允许、禁止或需要说明的边界。
    边界：不执行规则匹配，不做动态评分。
    """

    rule_id: str
    description: str
    severity: BoundarySeverity = BoundarySeverity.WARNING
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    hint: BoundaryHint | None = None
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.rule_id:
            raise ValueError("BoundaryRule.rule_id cannot be empty")
        if not self.description:
            raise ValueError("BoundaryRule.description cannot be empty")
        if not self.schema_version:
            raise ValueError("BoundaryRule.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class BoundaryViolation:
    """边界越界事实。

    作用：记录某次调用被认为越界的规则、严重度和解释。
    边界：不决定是否继续，不发起审批，不做恢复动作。
    """

    rule_id: str
    severity: BoundarySeverity = BoundarySeverity.BLOCKING
    hint: BoundaryHint | None = None
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.rule_id:
            raise ValueError("BoundaryViolation.rule_id cannot be empty")
        if not self.schema_version:
            raise ValueError("BoundaryViolation.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class PortBoundary:
    """端口边界说明。

    作用：声明端口的适用范围、明确禁止事项、边界提示与证据引用。
    边界：只做说明，不做权限裁决、风险评分或真实资源拦截。
    """

    summary: str
    allowed_scopes: tuple[str, ...] = field(default_factory=tuple)
    forbidden_scopes: tuple[str, ...] = field(default_factory=tuple)
    rules: tuple[BoundaryRule, ...] = field(default_factory=tuple)
    default_hint: BoundaryHint | None = None
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.summary:
            raise ValueError("PortBoundary.summary cannot be empty")
        if not self.schema_version:
            raise ValueError("PortBoundary.schema_version cannot be empty")
