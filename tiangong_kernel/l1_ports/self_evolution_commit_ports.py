"""L1 自我进化提交、激活、热切换与回滚验证端口。

本模块只定义候选通过验证后进入提交门、激活/热切换边界、提交后观察、
Tombstone 和回滚验证的协议对象；不生成补丁，不提交，不热切换，不回滚。
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
class EvolutionCommitIntent:
    """进化提交意图。"""

    intent_ref: TypedRef
    candidate_ref: TypedRef | None = None
    validation_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    human_confirmation_ref: TypedRef | None = None
    boundary_permit_ref: TypedRef | None = None
    intent_only: bool = True
    applies_patch: bool = False
    commits_change: bool = False
    auto_merge: bool = False
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        _true(self.intent_only, "EvolutionCommitIntent.intent_only")
        _false(self.applies_patch, "EvolutionCommitIntent.applies_patch")
        _false(self.commits_change, "EvolutionCommitIntent.commits_change")
        _false(self.auto_merge, "EvolutionCommitIntent.auto_merge")
        if not self.schema_version:
            raise ValueError("EvolutionCommitIntent.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class EvolutionActivationHint:
    """进化激活提示。"""

    hint_ref: TypedRef
    commit_intent_ref: TypedRef | None = None
    activation_window_ref: TypedRef | None = None
    hint_only: bool = True
    activates_runtime: bool = False
    hot_switches: bool = False
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        _true(self.hint_only, "EvolutionActivationHint.hint_only")
        _false(self.activates_runtime, "EvolutionActivationHint.activates_runtime")
        _false(self.hot_switches, "EvolutionActivationHint.hot_switches")
        if not self.schema_version:
            raise ValueError("EvolutionActivationHint.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class EvolutionHotSwitchBoundary:
    """进化热切换边界。"""

    boundary_ref: TypedRef
    activation_hint_ref: TypedRef | None = None
    rollback_anchor_ref: TypedRef | None = None
    requires_l5_permit: bool = True
    boundary_only: bool = True
    executes_hot_switch: bool = False
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        _true(self.requires_l5_permit, "EvolutionHotSwitchBoundary.requires_l5_permit")
        _true(self.boundary_only, "EvolutionHotSwitchBoundary.boundary_only")
        _false(self.executes_hot_switch, "EvolutionHotSwitchBoundary.executes_hot_switch")
        if not self.schema_version:
            raise ValueError("EvolutionHotSwitchBoundary.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class EvolutionPostCommitObservationIntent:
    """提交后观察意图。"""

    intent_ref: TypedRef
    commit_intent_ref: TypedRef | None = None
    observation_requirement_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    intent_only: bool = True
    samples_real_observation: bool = False
    writes_state: bool = False
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        _true(self.intent_only, "EvolutionPostCommitObservationIntent.intent_only")
        _false(self.samples_real_observation, "EvolutionPostCommitObservationIntent.samples_real_observation")
        _false(self.writes_state, "EvolutionPostCommitObservationIntent.writes_state")
        if not self.schema_version:
            raise ValueError("EvolutionPostCommitObservationIntent.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class EvolutionTombstoneHint:
    """进化废弃与迁移 Tombstone 提示。"""

    hint_ref: TypedRef
    superseded_candidate_ref: TypedRef | None = None
    tombstone_ref: TypedRef | None = None
    migration_ref: TypedRef | None = None
    hint_only: bool = True
    deletes_artifact: bool = False
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        _true(self.hint_only, "EvolutionTombstoneHint.hint_only")
        _false(self.deletes_artifact, "EvolutionTombstoneHint.deletes_artifact")
        if not self.schema_version:
            raise ValueError("EvolutionTombstoneHint.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class EvolutionRollbackValidationHint:
    """进化回滚验证提示。"""

    hint_ref: TypedRef
    rollback_ref: TypedRef | None = None
    validation_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    hint_only: bool = True
    executes_rollback: bool = False
    marks_success_without_validation: bool = False
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        _true(self.hint_only, "EvolutionRollbackValidationHint.hint_only")
        _false(self.executes_rollback, "EvolutionRollbackValidationHint.executes_rollback")
        _false(self.marks_success_without_validation, "EvolutionRollbackValidationHint.marks_success_without_validation")
        if not self.schema_version:
            raise ValueError("EvolutionRollbackValidationHint.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class SelfEvolutionCommitBoundaryRequest:
    """自我进化提交边界请求。"""

    request_ref: TypedRef
    commit_intent: EvolutionCommitIntent | None = None
    activation_hint: EvolutionActivationHint | None = None
    hot_switch_boundary: EvolutionHotSwitchBoundary | None = None
    request_only: bool = True
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        _true(self.request_only, "SelfEvolutionCommitBoundaryRequest.request_only")
        if not self.schema_version:
            raise ValueError("SelfEvolutionCommitBoundaryRequest.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class SelfEvolutionCommitBoundaryResponse:
    """自我进化提交边界响应。"""

    response_ref: TypedRef
    boundary_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    response_only: bool = True
    grants_commit_permission: bool = False
    grants_hot_switch_permission: bool = False
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        _true(self.response_only, "SelfEvolutionCommitBoundaryResponse.response_only")
        _false(self.grants_commit_permission, "SelfEvolutionCommitBoundaryResponse.grants_commit_permission")
        _false(self.grants_hot_switch_permission, "SelfEvolutionCommitBoundaryResponse.grants_hot_switch_permission")
        if not self.schema_version:
            raise ValueError("SelfEvolutionCommitBoundaryResponse.schema_version cannot be empty")


class SelfEvolutionCommitBoundaryPort(ABC):
    """自我进化提交边界端口协议。"""

    @abstractmethod
    def describe_self_evolution_commit_boundary(
        self, request: SelfEvolutionCommitBoundaryRequest, trace: TraceContext
    ) -> PortResult[SelfEvolutionCommitBoundaryResponse]:
        """描述自我进化提交边界。"""
