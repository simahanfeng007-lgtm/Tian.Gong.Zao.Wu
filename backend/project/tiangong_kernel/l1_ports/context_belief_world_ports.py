"""L1 Context / BeliefState / WorldState 安全边界端口。

本模块只定义上下文安全、信念证据绑定、事件事实优先级、世界状态引用、
工具/模型输出降级和指令资格边界协议，不装配 prompt，不推理信念，不同步世界。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef
from tiangong_kernel.l0_primitives.trace import TraceContext

from .port_result import PortResult


def _true(value: bool, field_name: str) -> None:
    if value is not True:
        raise ValueError(f"{field_name} must remain true")


def _false(value: bool, field_name: str) -> None:
    if value is not False:
        raise ValueError(f"{field_name} must remain false")


@dataclass(frozen=True, slots=True)
class BeliefStateReference:
    """信念状态引用。"""

    belief_ref: TypedRef
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    event_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    reference_only: bool = True
    cannot_override_event: bool = True
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        _true(self.reference_only, "BeliefStateReference.reference_only")
        _true(self.cannot_override_event, "BeliefStateReference.cannot_override_event")
        if not self.schema_version:
            raise ValueError("BeliefStateReference.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class BeliefEvidenceBinding:
    """信念证据绑定。"""

    binding_ref: TypedRef
    belief_ref: TypedRef
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    binding_only: bool = True
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        _true(self.binding_only, "BeliefEvidenceBinding.binding_only")
        if not self.schema_version:
            raise ValueError("BeliefEvidenceBinding.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class BeliefEventPrecedenceBoundary:
    """事件事实优先于信念的边界。"""

    boundary_ref: TypedRef
    event_ref: TypedRef
    belief_ref: TypedRef
    event_precedes_belief: bool = True
    belief_overrides_event: bool = False
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        _true(self.event_precedes_belief, "BeliefEventPrecedenceBoundary.event_precedes_belief")
        _false(self.belief_overrides_event, "BeliefEventPrecedenceBoundary.belief_overrides_event")
        if not self.schema_version:
            raise ValueError("BeliefEventPrecedenceBoundary.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class WorldStateReference:
    """世界状态引用。"""

    world_state_ref: TypedRef
    observation_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    trust_boundary_ref: TypedRef | None = None
    reference_only: bool = True
    syncs_real_world: bool = False
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        _true(self.reference_only, "WorldStateReference.reference_only")
        _false(self.syncs_real_world, "WorldStateReference.syncs_real_world")
        if not self.schema_version:
            raise ValueError("WorldStateReference.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class WorldObservationBinding:
    """世界状态与观察绑定。"""

    binding_ref: TypedRef
    world_state_ref: TypedRef
    observation_ref: TypedRef
    evidence_ref: TypedRef | None = None
    binding_only: bool = True
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        _true(self.binding_only, "WorldObservationBinding.binding_only")
        if not self.schema_version:
            raise ValueError("WorldObservationBinding.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ContextPollutionBoundary:
    """上下文污染边界。"""

    boundary_ref: TypedRef
    taint_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    boundary_only: bool = True
    allows_polluted_context: bool = False
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        _true(self.boundary_only, "ContextPollutionBoundary.boundary_only")
        _false(self.allows_polluted_context, "ContextPollutionBoundary.allows_polluted_context")
        if not self.schema_version:
            raise ValueError("ContextPollutionBoundary.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ToolOutputDemotionBoundary:
    """工具输出降级边界。"""

    boundary_ref: TypedRef
    tool_result_ref: TypedRef
    untrusted_output: bool = True
    instruction_eligible: bool = False
    system_instruction_eligible: bool = False
    context_injection_allowed: bool = False
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        _true(self.untrusted_output, "ToolOutputDemotionBoundary.untrusted_output")
        _false(self.instruction_eligible, "ToolOutputDemotionBoundary.instruction_eligible")
        _false(self.system_instruction_eligible, "ToolOutputDemotionBoundary.system_instruction_eligible")
        _false(self.context_injection_allowed, "ToolOutputDemotionBoundary.context_injection_allowed")
        if not self.schema_version:
            raise ValueError("ToolOutputDemotionBoundary.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ModelOutputDemotionBoundary(ToolOutputDemotionBoundary):
    """模型输出降级边界。"""


@dataclass(frozen=True, slots=True)
class InstructionEligibilityBoundary:
    """指令资格边界。"""

    boundary_ref: TypedRef
    source_ref: TypedRef
    instruction_eligible: bool = False
    system_instruction_eligible: bool = False
    requires_l5_boundary_review: bool = True
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        _false(self.instruction_eligible, "InstructionEligibilityBoundary.instruction_eligible")
        _false(self.system_instruction_eligible, "InstructionEligibilityBoundary.system_instruction_eligible")
        _true(self.requires_l5_boundary_review, "InstructionEligibilityBoundary.requires_l5_boundary_review")
        if not self.schema_version:
            raise ValueError("InstructionEligibilityBoundary.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ContextSafetyBoundary:
    """上下文安全边界。"""

    boundary_ref: TypedRef
    pollution_boundary_ref: TypedRef | None = None
    instruction_boundary_ref: TypedRef | None = None
    trust_boundary_ref: TypedRef | None = None
    boundary_only: bool = True
    assembles_context: bool = False
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        _true(self.boundary_only, "ContextSafetyBoundary.boundary_only")
        _false(self.assembles_context, "ContextSafetyBoundary.assembles_context")
        if not self.schema_version:
            raise ValueError("ContextSafetyBoundary.schema_version cannot be empty")


class ContextSafetyBoundaryPort(ABC):
    """上下文安全边界端口协议。"""

    @abstractmethod
    def describe_context_safety_boundary(self, boundary: ContextSafetyBoundary, trace: TraceContext) -> PortResult[ContextSafetyBoundary]:
        """描述上下文安全边界。"""


class BeliefStateReferencePort(ABC):
    """信念状态引用端口协议。"""

    @abstractmethod
    def reference_belief_state(self, reference: BeliefStateReference, trace: TraceContext) -> PortResult[BeliefStateReference]:
        """描述信念状态引用。"""


class WorldStateReferencePort(ABC):
    """世界状态引用端口协议。"""

    @abstractmethod
    def reference_world_state(self, reference: WorldStateReference, trace: TraceContext) -> PortResult[WorldStateReference]:
        """描述世界状态引用。"""
