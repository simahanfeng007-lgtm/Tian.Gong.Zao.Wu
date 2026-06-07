"""L1 端口错误边界声明。

本模块只定义端口错误的类型、提示和策略表达，供后续层统一包装失败信息。
它不执行真实错误处理、不重试、不恢复、不写日志。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.errors import ErrorSeverity
from tiangong_kernel.l0_primitives.identity import TypedRef


class PortErrorKind(str, Enum):
    """端口错误类型枚举；只表达错误类别。"""

    UNKNOWN = "unknown"
    INVALID_REQUEST = "invalid_request"
    UNSUPPORTED_OPERATION = "unsupported_operation"
    BOUNDARY_VIOLATION = "boundary_violation"
    UNAVAILABLE = "unavailable"
    TIMEOUT_DECLARED = "timeout_declared"
    DEPENDENCY_UNREADY = "dependency_unready"


class PortErrorPolicy(str, Enum):
    """端口错误策略声明；只表达后续层可参考的处理倾向。"""

    RETURN_FAILURE = "return_failure"
    RETURN_ALTERNATIVE = "return_alternative"
    ESCALATE_TO_CALLER = "escalate_to_caller"
    MARK_UNAVAILABLE = "mark_unavailable"


@dataclass(frozen=True, slots=True)
class PortFailureHint:
    """端口失败提示。

    作用：给调用方提供可读原因、建议修正和替代路径。
    边界：不自动修正请求，不启动任何外部动作。
    """

    reason: str
    suggested_fix: str = ""
    alternative_paths: tuple[str, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.reason:
            raise ValueError("PortFailureHint.reason cannot be empty")
        if not self.schema_version:
            raise ValueError("PortFailureHint.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class PortErrorBoundary:
    """端口错误边界。

    作用：说明端口可能返回哪些错误、严重度与建议策略。
    边界：不捕获异常，不执行恢复，不替上层做最终裁决。
    """

    kind: PortErrorKind = PortErrorKind.UNKNOWN
    severity: ErrorSeverity = ErrorSeverity.RECOVERABLE
    policy: PortErrorPolicy = PortErrorPolicy.RETURN_FAILURE
    hint: PortFailureHint | None = None
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("PortErrorBoundary.schema_version cannot be empty")
