"""L2 上下文安全状态。

本模块只保存污染、指令污染、工具输出污染、模型输出污染和记忆注入边界引用。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from .base_state import L2_STATE_SCHEMA_VERSION, L2StateMetadata
from .state_identity import L2StateIdentity
from .state_status import L2StateStatus


def _true(value: bool, field_name: str) -> None:
    if value is not True:
        raise ValueError(f"{field_name} must remain true")


def _false(value: bool, field_name: str) -> None:
    if value is not False:
        raise ValueError(f"{field_name} must remain false")


@dataclass(frozen=True, slots=True)
class ContextSafetyStateBase:
    """上下文安全状态基础对象。"""

    identity: L2StateIdentity
    status: L2StateStatus
    taint_ref: TypedRef | None = None
    source_ref: TypedRef | None = None
    boundary_ref: TypedRef | None = None
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    state_only: bool = True
    ref_only: bool = True
    stores_plain_output: bool = False
    assembles_context: bool = False
    writes_context: bool = False
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _true(self.state_only, f"{self.__class__.__name__}.state_only")
        _true(self.ref_only, f"{self.__class__.__name__}.ref_only")
        _false(self.stores_plain_output, f"{self.__class__.__name__}.stores_plain_output")
        _false(self.assembles_context, f"{self.__class__.__name__}.assembles_context")
        _false(self.writes_context, f"{self.__class__.__name__}.writes_context")
        if not self.schema_version:
            raise ValueError(f"{self.__class__.__name__}.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ContextPollutionState(ContextSafetyStateBase):
    """上下文污染状态。"""

    pollution_level: str = "unknown"
    allows_context_injection: bool = False

    def __post_init__(self) -> None:
        ContextSafetyStateBase.__post_init__(self)
        _false(self.allows_context_injection, "ContextPollutionState.allows_context_injection")


@dataclass(frozen=True, slots=True)
class InstructionTaintState(ContextSafetyStateBase):
    """指令污染状态。"""

    instruction_eligible: bool = False
    system_instruction_eligible: bool = False

    def __post_init__(self) -> None:
        ContextSafetyStateBase.__post_init__(self)
        _false(self.instruction_eligible, "InstructionTaintState.instruction_eligible")
        _false(self.system_instruction_eligible, "InstructionTaintState.system_instruction_eligible")


@dataclass(frozen=True, slots=True)
class ToolOutputTaintState(ContextSafetyStateBase):
    """工具输出污染状态。"""

    untrusted_output: bool = True

    def __post_init__(self) -> None:
        ContextSafetyStateBase.__post_init__(self)
        _true(self.untrusted_output, "ToolOutputTaintState.untrusted_output")


@dataclass(frozen=True, slots=True)
class ModelOutputTaintState(ContextSafetyStateBase):
    """模型输出污染状态。"""

    untrusted_output: bool = True

    def __post_init__(self) -> None:
        ContextSafetyStateBase.__post_init__(self)
        _true(self.untrusted_output, "ModelOutputTaintState.untrusted_output")


@dataclass(frozen=True, slots=True)
class MemoryInjectionBoundaryState(ContextSafetyStateBase):
    """记忆注入边界状态。"""

    memory_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    boundary_status: str = "not_reviewed"
    injected: bool = False

    def __post_init__(self) -> None:
        ContextSafetyStateBase.__post_init__(self)
        if self.boundary_status != "approved":
            _false(self.injected, "MemoryInjectionBoundaryState.injected")
