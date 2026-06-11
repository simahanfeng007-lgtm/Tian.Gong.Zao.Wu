"""L1 端口生命周期声明。

本模块只定义端口生命周期状态、状态迁移说明与生命周期边界。
它不启动资源、不停止资源、不恢复资源。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef


class PortLifecycleState(str, Enum):
    """端口生命周期状态枚举；只表达状态事实。"""

    UNKNOWN = "unknown"
    DECLARED = "declared"
    READY = "ready"
    DEGRADED = "degraded"
    SUSPENDED = "suspended"
    RETIRED = "retired"


@dataclass(frozen=True, slots=True)
class PortLifecycleTransition:
    """端口生命周期迁移声明。

    作用：说明允许从一个声明性状态转向另一个声明性状态。
    边界：不执行迁移，不操作外部资源。
    """

    from_state: PortLifecycleState
    to_state: PortLifecycleState
    reason: str = ""
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("PortLifecycleTransition.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class PortLifecycleBoundary:
    """端口生命周期边界。

    作用：说明生命周期声明覆盖哪些状态，不覆盖哪些资源行为。
    边界：不启动、不停止、不恢复真实资源。
    """

    declared_scope: str
    excluded_scope: str = ""
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.declared_scope:
            raise ValueError("PortLifecycleBoundary.declared_scope cannot be empty")
        if not self.schema_version:
            raise ValueError("PortLifecycleBoundary.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class PortLifecycleDeclaration:
    """端口生命周期声明。

    作用：表达端口当前生命周期状态、可声明迁移和边界范围。
    边界：不驱动生命周期，不创建后台任务，不修改资源状态。
    """

    state: PortLifecycleState = PortLifecycleState.UNKNOWN
    transitions: tuple[PortLifecycleTransition, ...] = field(default_factory=tuple)
    boundary: PortLifecycleBoundary | None = None
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("PortLifecycleDeclaration.schema_version cannot be empty")
