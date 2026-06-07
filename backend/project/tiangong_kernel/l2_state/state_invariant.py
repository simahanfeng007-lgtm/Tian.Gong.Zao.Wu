"""L2 状态不变量对象，只表达约束声明和检查结果状态，不扫描系统或自动修复。"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef
from tiangong_kernel.l0_primitives.state import ConstraintRef, InvariantRef


class L2InvariantStatusKind(str, Enum):
    """L2 不变量状态枚举；只表达声明或检查结果，不执行检查。"""

    UNKNOWN = "unknown"
    DECLARED = "declared"
    SATISFIED = "satisfied"
    VIOLATED = "violated"
    WAIVED = "waived"
    NEEDS_REVIEW = "needs_review"


@dataclass(frozen=True, slots=True)
class L2StateInvariant:
    """L2 状态不变量声明。

    作用：记录不变量引用、约束引用、主体引用和说明文本。
    边界：不执行真实检查，不读取系统状态，不自动修复。
    """

    invariant_ref: InvariantRef
    constraint_refs: tuple[ConstraintRef, ...] = field(default_factory=tuple)
    subject_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    description: str = ""
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("L2StateInvariant.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class L2InvariantCheck:
    """L2 不变量检查结果。

    作用：记录某个不变量的检查状态、违规引用和证据引用。
    边界：不执行真实检查，不扫描真实系统，不做自动修复。
    """

    invariant_ref: InvariantRef
    status: L2InvariantStatusKind = L2InvariantStatusKind.UNKNOWN
    violation_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("L2InvariantCheck.schema_version cannot be empty")
