"""L4 到 L6 自学习/自进化服务需求。

这些对象只声明 L6 后续服务需求，不实现验证、提交、热切换或观察。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from ._common import L4_EXECUTION_CLOSURE_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_true


@dataclass(frozen=True, slots=True)
class L4ToL6SelfLearningSinkRequirement:
    """自学习 sink 需求。"""

    requirement_ref: TypedRef
    learning_signal_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    candidate_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    requirement_only: bool = True
    implements_learning_system: bool = False
    writes_runtime: bool = False
    schema_version: str = L4_EXECUTION_CLOSURE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_true(self.requirement_only, "L4ToL6SelfLearningSinkRequirement.requirement_only")
        ensure_false(self.implements_learning_system, "L4ToL6SelfLearningSinkRequirement.implements_learning_system")
        ensure_false(self.writes_runtime, "L4ToL6SelfLearningSinkRequirement.writes_runtime")
        ensure_schema_version(self.schema_version, "L4ToL6SelfLearningSinkRequirement.schema_version")


@dataclass(frozen=True, slots=True)
class L4ToL6EvolutionValidationRequirement:
    """进化验证需求。"""

    requirement_ref: TypedRef
    candidate_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    validation_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    requirement_only: bool = True
    runs_validation: bool = False
    schema_version: str = L4_EXECUTION_CLOSURE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_true(self.requirement_only, "L4ToL6EvolutionValidationRequirement.requirement_only")
        ensure_false(self.runs_validation, "L4ToL6EvolutionValidationRequirement.runs_validation")
        ensure_schema_version(self.schema_version, "L4ToL6EvolutionValidationRequirement.schema_version")


@dataclass(frozen=True, slots=True)
class L4ToL6EvolutionCommitRequirement:
    """进化提交需求。"""

    requirement_ref: TypedRef
    commit_intent_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    requirement_only: bool = True
    commits_change: bool = False
    hot_switches: bool = False
    applies_patch: bool = False
    schema_version: str = L4_EXECUTION_CLOSURE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_true(self.requirement_only, "L4ToL6EvolutionCommitRequirement.requirement_only")
        ensure_false(self.commits_change, "L4ToL6EvolutionCommitRequirement.commits_change")
        ensure_false(self.hot_switches, "L4ToL6EvolutionCommitRequirement.hot_switches")
        ensure_false(self.applies_patch, "L4ToL6EvolutionCommitRequirement.applies_patch")
        ensure_schema_version(self.schema_version, "L4ToL6EvolutionCommitRequirement.schema_version")


@dataclass(frozen=True, slots=True)
class L4ToL6PostCommitObservationRequirement:
    """提交后观察需求。"""

    requirement_ref: TypedRef
    observation_requirement_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    requirement_only: bool = True
    samples_real_observation: bool = False
    writes_l2_state: bool = False
    schema_version: str = L4_EXECUTION_CLOSURE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_true(self.requirement_only, "L4ToL6PostCommitObservationRequirement.requirement_only")
        ensure_false(self.samples_real_observation, "L4ToL6PostCommitObservationRequirement.samples_real_observation")
        ensure_false(self.writes_l2_state, "L4ToL6PostCommitObservationRequirement.writes_l2_state")
        ensure_schema_version(self.schema_version, "L4ToL6PostCommitObservationRequirement.schema_version")
