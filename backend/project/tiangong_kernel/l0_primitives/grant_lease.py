"""L0 授予与租约事实原语，只表达授权窗口、授予引用与租约状态；不签发真实权限、不续租执行。
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .identity import RefId, TypedRef
from .time import TemporalWindow


class GrantKind(str, Enum):
    """GrantKind 的 L0 枚举，只表达稳定事实，不实现上层算法或真实执行。"""
    USER = "user"
    SYSTEM = "system"
    POLICY = "policy"
    CONTRACT = "contract"
    DELEGATED = "delegated"
    EMERGENCY = "emergency"
    UNKNOWN = "unknown"


class LeaseStatus(str, Enum):
    """LeaseStatus 的 L0 枚举，只表达稳定事实，不实现上层算法或真实执行。"""
    PROPOSED = "proposed"
    ISSUED = "issued"
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    CONSUMED = "consumed"
    SUSPENDED = "suspended"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class GrantRef:
    """GrantRef 的 L0 不可变事实对象，只表达稳定事实，不实现上层算法或真实执行。"""
    value: RefId
    kind: GrantKind = GrantKind.UNKNOWN
    source_ref: TypedRef | None = None
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("GrantRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class LeaseRef:
    """LeaseRef 的 L0 不可变事实对象，只表达稳定事实，不实现上层算法或真实执行。"""
    value: RefId
    status: LeaseStatus = LeaseStatus.UNKNOWN
    grant_ref: GrantRef | None = None
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("LeaseRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class PermissionWindow:
    """PermissionWindow 的 L0 不可变事实对象，只表达稳定事实，不实现上层算法或真实执行。"""
    window: TemporalWindow
    lease_ref: LeaseRef | None = None
    scope_ref: TypedRef | None = None
    label: str = ""
