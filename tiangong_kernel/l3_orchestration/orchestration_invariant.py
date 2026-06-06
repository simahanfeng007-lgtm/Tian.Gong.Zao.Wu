"""L3 编排不变量对象，记录第一阶段边界约束事实。"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef

from .orchestration_identity import L3_ORCHESTRATION_SCHEMA_VERSION, OrchestrationIdentity
from .orchestration_status import OrchestrationStatus


class OrchestrationInvariantKind(str, Enum):
    """编排不变量类别。"""

    UNKNOWN = "unknown"
    PHASE1_SCOPE = "phase1_scope"
    SERIALIZATION_STABILITY = "serialization_stability"
    L2_REFERENCE_ONLY = "l2_reference_only"
    RECOMMENDATION_ONLY = "recommendation_only"


@dataclass(frozen=True, slots=True)
class OrchestrationInvariant:
    """L3 编排不变量。

    作用：表达第一阶段范围、稳定序列化、L2 引用和建议语义等不变量。
    边界：不自动检查工程目录，不扫描外部内容，只保存不变量声明。
    """

    identity: OrchestrationIdentity
    status: OrchestrationStatus
    invariant_ref: TypedRef | None = None
    invariant_kind: OrchestrationInvariantKind = OrchestrationInvariantKind.UNKNOWN
    subject_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    statement: str = ""
    violation_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.advisory_only is not True:
            raise ValueError("OrchestrationInvariant.advisory_only must remain true in L3 phase 1")
        if len(self.statement) > 512:
            raise ValueError("OrchestrationInvariant.statement must be a short statement")
        if not self.schema_version:
            raise ValueError("OrchestrationInvariant.schema_version cannot be empty")
