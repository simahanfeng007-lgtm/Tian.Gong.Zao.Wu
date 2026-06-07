"""L0 Result-first 结果原语，只表达成功、错误与返回值事实；不抛出普通流程异常，不执行恢复逻辑。
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Generic, TypeVar

from .errors import CoreError


T = TypeVar("T")


class ResultStatus(str, Enum):
    """L0 Result 状态枚举；UNKNOWN 只作兼容兜底，不表示成功或失败。"""

    UNKNOWN = "unknown"
    OK = "ok"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class CoreResult(Generic[T]):
    """CoreResult 的 L0 不可变事实对象，只表达稳定事实，不实现上层算法或真实执行。"""
    status: ResultStatus
    value: T | None = None
    error: CoreError | None = None

    @property
    def is_ok(self) -> bool:
        return self.status is ResultStatus.OK

    @property
    def is_error(self) -> bool:
        return self.status is ResultStatus.ERROR


def ok(value: T | None = None) -> CoreResult[T]:
    return CoreResult(status=ResultStatus.OK, value=value, error=None)


def err(error: CoreError) -> CoreResult[None]:
    return CoreResult(status=ResultStatus.ERROR, value=None, error=error)
