"""L3 编排错误事实对象，遵循 Result-first 风格。"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.errors import CoreError
from tiangong_kernel.l0_primitives.identity import TypedRef

from .orchestration_identity import L3_ORCHESTRATION_SCHEMA_VERSION, OrchestrationIdentity
from .orchestration_status import OrchestrationStatus


class OrchestrationErrorKind(str, Enum):
    """编排错误类别。"""

    UNKNOWN = "unknown"
    INVALID_INPUT = "invalid_input"
    BOUNDARY_FACT = "boundary_fact"
    SERIALIZATION_FACT = "serialization_fact"
    INVARIANT_FACT = "invariant_fact"


@dataclass(frozen=True, slots=True)
class OrchestrationError:
    """L3 编排错误事实。

    作用：包装 L0 CoreError、错误类别、摘要和证据引用。
    边界：不抛出普通流程错误，不修复问题，不改变任何计划。
    """

    identity: OrchestrationIdentity
    status: OrchestrationStatus
    error_ref: TypedRef | None = None
    error_kind: OrchestrationErrorKind = OrchestrationErrorKind.UNKNOWN
    core_error: CoreError | None = None
    message: str = ""
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    recoverable: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if len(self.message) > 512:
            raise ValueError("OrchestrationError.message must be a short summary")
        if not self.schema_version:
            raise ValueError("OrchestrationError.schema_version cannot be empty")
