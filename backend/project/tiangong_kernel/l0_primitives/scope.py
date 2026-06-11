"""L0 范围与边界事实原语，只表达 scope、boundary 与范围层级；不做权限裁决或沙箱隔离。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .identity import RefId, TypedRef


class ScopeKind(str, Enum):
    """ScopeKind 的 L0 枚举，只表达稳定事实，不实现上层算法或真实执行。"""
    GLOBAL = "global"
    WORKSPACE = "workspace"
    SESSION = "session"
    RUN = "run"
    STEP = "step"
    ACTOR = "actor"
    RESOURCE = "resource"
    ENVIRONMENT = "environment"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class ScopeRef:
    """ScopeRef 的 L0 不可变事实对象，只表达稳定事实，不实现上层算法或真实执行。"""
    value: RefId
    kind: ScopeKind = ScopeKind.UNKNOWN
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("ScopeRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class BoundaryRef:
    """BoundaryRef 的 L0 不可变事实对象，只表达稳定事实，不实现上层算法或真实执行。"""
    value: RefId
    boundary_type: str = "unknown"
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.boundary_type:
            raise ValueError("BoundaryRef.boundary_type cannot be empty")
        if not self.schema_version:
            raise ValueError("BoundaryRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ScopeBoundary:
    """ScopeBoundary 的 L0 不可变事实对象，只表达稳定事实，不实现上层算法或真实执行。"""
    boundary_ref: BoundaryRef
    scope_ref: ScopeRef
    label: str = ""
    related_refs: tuple[TypedRef, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class CoreScope:
    """CoreScope 的 L0 不可变事实对象，只表达稳定事实，不实现上层算法或真实执行。"""
    scope_ref: ScopeRef
    kind: ScopeKind
    parent_scope_ref: ScopeRef | None = None
    boundary_refs: tuple[BoundaryRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("CoreScope.schema_version cannot be empty")
