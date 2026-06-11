"""L2 自我进化提交、激活、热切换、观察与回滚验证状态。

所有对象均为事实状态，不应用补丁、不提交、不激活、不热切换、不回滚。
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
class SelfEvolutionCommitStateBase:
    """自我进化提交链基础状态。"""

    identity: L2StateIdentity
    status: L2StateStatus
    candidate_ref: TypedRef | None = None
    validation_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    boundary_ref: TypedRef | None = None
    human_confirmation_ref: TypedRef | None = None
    audit_ref: TypedRef | None = None
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    summary: str = ""
    state_only: bool = True
    ref_only: bool = True
    no_patch_apply: bool = True
    no_auto_merge: bool = True
    writes_runtime: bool = False
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if len(self.summary) > 512:
            raise ValueError(f"{self.__class__.__name__}.summary must be short")
        _true(self.state_only, f"{self.__class__.__name__}.state_only")
        _true(self.ref_only, f"{self.__class__.__name__}.ref_only")
        _true(self.no_patch_apply, f"{self.__class__.__name__}.no_patch_apply")
        _true(self.no_auto_merge, f"{self.__class__.__name__}.no_auto_merge")
        _false(self.writes_runtime, f"{self.__class__.__name__}.writes_runtime")
        if not self.schema_version:
            raise ValueError(f"{self.__class__.__name__}.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class EvolutionCommitState(SelfEvolutionCommitStateBase):
    """进化提交状态。"""

    commit_intent_ref: TypedRef | None = None
    requires_l5_permit: bool = True

    def __post_init__(self) -> None:
        SelfEvolutionCommitStateBase.__post_init__(self)
        _true(self.requires_l5_permit, "EvolutionCommitState.requires_l5_permit")


@dataclass(frozen=True, slots=True)
class EvolutionActivationState(SelfEvolutionCommitStateBase):
    """进化激活状态。"""

    activation_hint_ref: TypedRef | None = None
    activates_runtime: bool = False

    def __post_init__(self) -> None:
        SelfEvolutionCommitStateBase.__post_init__(self)
        _false(self.activates_runtime, "EvolutionActivationState.activates_runtime")


@dataclass(frozen=True, slots=True)
class EvolutionHotSwitchState(SelfEvolutionCommitStateBase):
    """进化热切换状态。"""

    hot_switch_boundary_ref: TypedRef | None = None
    rollback_anchor_ref: TypedRef | None = None
    executes_hot_switch: bool = False

    def __post_init__(self) -> None:
        SelfEvolutionCommitStateBase.__post_init__(self)
        _false(self.executes_hot_switch, "EvolutionHotSwitchState.executes_hot_switch")


@dataclass(frozen=True, slots=True)
class EvolutionPostCommitObservationState(SelfEvolutionCommitStateBase):
    """提交后观察状态。"""

    observation_requirement_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    samples_real_observation: bool = False

    def __post_init__(self) -> None:
        SelfEvolutionCommitStateBase.__post_init__(self)
        _false(self.samples_real_observation, "EvolutionPostCommitObservationState.samples_real_observation")


@dataclass(frozen=True, slots=True)
class EvolutionTombstoneState(SelfEvolutionCommitStateBase):
    """进化废弃、迁移与 Tombstone 状态。"""

    tombstone_ref: TypedRef | None = None
    migration_ref: TypedRef | None = None
    deletes_artifact: bool = False

    def __post_init__(self) -> None:
        SelfEvolutionCommitStateBase.__post_init__(self)
        _false(self.deletes_artifact, "EvolutionTombstoneState.deletes_artifact")


@dataclass(frozen=True, slots=True)
class EvolutionRollbackValidationState(SelfEvolutionCommitStateBase):
    """进化回滚验证状态。"""

    rollback_ref: TypedRef | None = None
    rollback_validation_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    executes_rollback: bool = False
    marks_success_without_validation: bool = False

    def __post_init__(self) -> None:
        SelfEvolutionCommitStateBase.__post_init__(self)
        _false(self.executes_rollback, "EvolutionRollbackValidationState.executes_rollback")
        _false(self.marks_success_without_validation, "EvolutionRollbackValidationState.marks_success_without_validation")
