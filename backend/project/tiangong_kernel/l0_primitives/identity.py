"""L0 身份与引用基础原语，只定义 CoreId、RefId 与 TypedRef 等稳定事实标识；不承载执行器、客户端或真实资源句柄。
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re
import uuid

from .errors import CoreError, ErrorCode, ErrorSeverity
from .result import CoreResult, err, ok


_CORE_ID_RE = re.compile(r"^[a-z][a-z0-9_]{1,31}:[0-9a-f]{32}$")
_PREFIX_RE = re.compile(r"^[a-z][a-z0-9_]{1,31}$")


class IdPrefix(str, Enum):
    """L0 核心标识前缀枚举；UNKNOWN 用作无法归类时的稳定兜底。"""

    UNKNOWN = "unknown"
    CORE = "core"
    REF = "ref"
    TRACE = "trace"
    SPAN = "span"
    ACTOR = "actor"
    SCOPE = "scope"


@dataclass(frozen=True, slots=True)
class CoreId:
    """CoreId 的 L0 不可变事实对象，只表达稳定事实，不实现上层算法或真实执行。"""
    value: str

    def __post_init__(self) -> None:
        if not _CORE_ID_RE.match(self.value):
            raise ValueError("Invalid CoreId format")

    @property
    def prefix(self) -> str:
        return self.value.split(":", 1)[0]


@dataclass(frozen=True, slots=True)
class RefId:
    """RefId 的 L0 不可变事实对象，只表达稳定事实，不实现上层算法或真实执行。"""
    value: str

    def __post_init__(self) -> None:
        if not _CORE_ID_RE.match(self.value):
            raise ValueError("Invalid RefId format")

    @property
    def prefix(self) -> str:
        return self.value.split(":", 1)[0]


@dataclass(frozen=True, slots=True)
class TypedRef:
    """TypedRef 的 L0 不可变事实对象，只表达稳定事实，不实现上层算法或真实执行。"""
    ref_id: RefId
    ref_type: str
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.ref_type:
            raise ValueError("TypedRef.ref_type cannot be empty")
        if not self.schema_version:
            raise ValueError("TypedRef.schema_version cannot be empty")


def new_core_id(prefix: str | IdPrefix = IdPrefix.CORE) -> CoreId:
    raw_prefix = prefix.value if isinstance(prefix, IdPrefix) else prefix
    if not _PREFIX_RE.match(raw_prefix):
        raise ValueError("Invalid CoreId prefix")
    return CoreId(f"{raw_prefix}:{uuid.uuid4().hex}")


def validate_core_id(value: str) -> CoreResult[CoreId]:
    if not _CORE_ID_RE.match(value):
        return err(
            CoreError(
                code=ErrorCode.INVALID_ID,
                message="CoreId must match '<prefix>:<32 lowercase hex chars>'",
                severity=ErrorSeverity.RECOVERABLE,
            )
        )
    return ok(CoreId(value))
