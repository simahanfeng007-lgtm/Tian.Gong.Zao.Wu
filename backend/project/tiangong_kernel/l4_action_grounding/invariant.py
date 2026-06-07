"""L4 动作落地层硬不变量。"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef

from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_short_text, ensure_true


class ActionGroundingInvariantKind(str, Enum):
    BOUNDARY_PERMIT_REQUIRED = "boundary_permit_required"
    NO_LIVE_EXECUTION_WITHOUT_L5 = "no_live_execution_without_l5"
    NO_L4_AUTONOMOUS_EXECUTION = "no_l4_autonomous_execution"
    RESULT_ENVELOPE_REQUIRED = "result_envelope_required"
    NO_REAL_ACTIONS_IN_PHASE1 = "no_real_actions_in_phase1"


@dataclass(frozen=True, slots=True)
class ActionGroundingInvariant:
    """通用不变量对象。"""

    invariant_ref: TypedRef
    invariant_kind: ActionGroundingInvariantKind
    invariant_name: str
    description: str = ""
    enforced: bool = True
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_short_text(self.invariant_name, "ActionGroundingInvariant.invariant_name", 128)
        ensure_short_text(self.description, "ActionGroundingInvariant.description")
        ensure_true(self.enforced, "ActionGroundingInvariant.enforced")
        ensure_schema_version(self.schema_version, "ActionGroundingInvariant.schema_version")


@dataclass(frozen=True, slots=True)
class BoundaryPermitRequiredInvariant:
    """真实动作必须先有未来 L5 许可引用；第一阶段缺失时默认拒绝。"""

    invariant_ref: TypedRef
    invariant_name: str = "BoundaryPermitRequiredInvariant"
    requires_l5_permit: bool = True
    grants_permission: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_true(self.requires_l5_permit, "BoundaryPermitRequiredInvariant.requires_l5_permit")
        ensure_false(self.grants_permission, "BoundaryPermitRequiredInvariant.grants_permission")
        ensure_schema_version(self.schema_version, "BoundaryPermitRequiredInvariant.schema_version")

    def is_satisfied_by(self, l5_permit_ref: TypedRef | None) -> bool:
        """只检查许可引用是否存在，不做权限或风险裁决。"""

        return l5_permit_ref is not None


@dataclass(frozen=True, slots=True)
class NoLiveExecutionWithoutL5Invariant:
    """无未来 L5 许可引用时不得进入真实动作路径。"""

    invariant_ref: TypedRef
    invariant_name: str = "NoLiveExecutionWithoutL5Invariant"
    live_action_allowed_without_l5: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_false(self.live_action_allowed_without_l5, "NoLiveExecutionWithoutL5Invariant.live_action_allowed_without_l5")
        ensure_schema_version(self.schema_version, "NoLiveExecutionWithoutL5Invariant.schema_version")


@dataclass(frozen=True, slots=True)
class NoL4AutonomousExecutionInvariant:
    """L4 不拥有任务意图，不主动推进下一步。"""

    invariant_ref: TypedRef
    invariant_name: str = "NoL4AutonomousExecutionInvariant"
    l4_autonomous_execution_allowed: bool = False
    llm_is_controller: bool = True
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_false(self.l4_autonomous_execution_allowed, "NoL4AutonomousExecutionInvariant.l4_autonomous_execution_allowed")
        ensure_true(self.llm_is_controller, "NoL4AutonomousExecutionInvariant.llm_is_controller")
        ensure_schema_version(self.schema_version, "NoL4AutonomousExecutionInvariant.schema_version")
