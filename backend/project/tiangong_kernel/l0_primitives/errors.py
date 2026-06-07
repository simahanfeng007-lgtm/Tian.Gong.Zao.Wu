"""L0 错误事实原语，只表达错误码、严重度与错误详情；不实现日志、告警、重试或恢复系统。
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class ErrorSeverity(str, Enum):
    """L0 错误严重度枚举；UNKNOWN 用作无法归类时的稳定兜底。"""

    UNKNOWN = "unknown"
    INFO = "info"
    WARNING = "warning"
    RECOVERABLE = "recoverable"
    FATAL = "fatal"


class ErrorCode(str, Enum):
    """ErrorCode 的 L0 枚举，只表达稳定事实，不实现上层算法或真实执行。"""
    INVALID_ID = "invalid_id"
    INVALID_VALUE = "invalid_value"
    INVALID_TIME = "invalid_time"
    SERIALIZATION_ERROR = "serialization_error"
    TRACE_ERROR = "trace_error"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class CoreError:
    """CoreError 的 L0 不可变事实对象，只表达稳定事实，不实现上层算法或真实执行。"""
    code: ErrorCode
    message: str
    severity: ErrorSeverity = ErrorSeverity.RECOVERABLE
    details: tuple[tuple[str, Any], ...] = ()
