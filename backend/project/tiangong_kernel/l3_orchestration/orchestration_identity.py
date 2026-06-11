"""L3 编排身份对象，只表达编排对象的稳定引用与来源状态引用。"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef


L3_ORCHESTRATION_SCHEMA_VERSION = "0.1"


class OrchestrationObjectKind(str, Enum):
    """L3 编排对象类别枚举。"""

    UNKNOWN = "unknown"
    REQUEST = "request"
    CONTEXT = "context"
    STEP = "step"
    PLAN = "plan"
    RESULT = "result"
    TRANSITION = "transition"
    INVARIANT = "invariant"
    ERROR = "error"
    MATH_INPUT = "math_input"
    MATH_RESULT = "math_result"


@dataclass(frozen=True, slots=True)
class OrchestrationIdentity:
    """编排对象身份。

    作用：记录 L3 编排对象引用、对象类别、来源引用和来源状态引用。
    边界：不生成真实身份，不注册对象，不读取状态，只保存可序列化事实。
    """

    orchestration_ref: TypedRef
    object_kind: OrchestrationObjectKind = OrchestrationObjectKind.UNKNOWN
    source_ref: TypedRef | None = None
    source_state_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("OrchestrationIdentity.schema_version cannot be empty")
