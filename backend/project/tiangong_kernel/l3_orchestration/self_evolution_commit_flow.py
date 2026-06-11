"""L3 自我学习/迭代/进化提交闭环建议。

本模块只描述候选验证到提交、激活、热切换、提交后观察、回滚验证和 Tombstone
迁移的建议，不生成补丁、不应用补丁、不提交、不热切换、不回滚。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from .orchestration_identity import L3_ORCHESTRATION_SCHEMA_VERSION


def _true(value: bool, field_name: str) -> None:
    if value is not True:
        raise ValueError(f"{field_name} must remain true")


def _false(value: bool, field_name: str) -> None:
    if value is not False:
        raise ValueError(f"{field_name} must remain false")


def _unit(value: float, field_name: str) -> None:
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{field_name} must be between 0.0 and 1.0")


@dataclass(frozen=True, slots=True)
class SelfEvolutionCommitAdviceBase:
    """自我进化提交闭环建议基础对象。"""

    advice_ref: TypedRef
    candidate_ref: TypedRef | None = None
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    validation_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    boundary_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    confidence: float = 0.0
    advisory_only: bool = True
    ref_only: bool = True
    no_patch_generation: bool = True
    no_patch_apply: bool = True
    no_auto_merge: bool = True
    no_hot_switch: bool = True
    no_real_rollback: bool = True
    grants_permission: bool = False
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _unit(self.confidence, f"{self.__class__.__name__}.confidence")
        _true(self.advisory_only, f"{self.__class__.__name__}.advisory_only")
        _true(self.ref_only, f"{self.__class__.__name__}.ref_only")
        _true(self.no_patch_generation, f"{self.__class__.__name__}.no_patch_generation")
        _true(self.no_patch_apply, f"{self.__class__.__name__}.no_patch_apply")
        _true(self.no_auto_merge, f"{self.__class__.__name__}.no_auto_merge")
        _true(self.no_hot_switch, f"{self.__class__.__name__}.no_hot_switch")
        _true(self.no_real_rollback, f"{self.__class__.__name__}.no_real_rollback")
        _false(self.grants_permission, f"{self.__class__.__name__}.grants_permission")
        if not self.schema_version:
            raise ValueError(f"{self.__class__.__name__}.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class CandidateValidatedToCommitAdvice(SelfEvolutionCommitAdviceBase):
    """候选验证通过到提交门建议。"""

    commit_intent_ref: TypedRef | None = None
    requires_human_confirmation: bool = True


@dataclass(frozen=True, slots=True)
class EvolutionCommitFlowAdvice(SelfEvolutionCommitAdviceBase):
    """进化提交流建议。"""

    requires_l5_permit: bool = True


@dataclass(frozen=True, slots=True)
class EvolutionActivationAdvice(SelfEvolutionCommitAdviceBase):
    """进化激活建议。"""

    activation_hint_ref: TypedRef | None = None


@dataclass(frozen=True, slots=True)
class HotSwitchGuardAdvice(SelfEvolutionCommitAdviceBase):
    """热切换防护建议。"""

    rollback_anchor_ref: TypedRef | None = None
    requires_l5_boundary: bool = True


@dataclass(frozen=True, slots=True)
class PostCommitObservationAdvice(SelfEvolutionCommitAdviceBase):
    """提交后观察建议。"""

    observation_requirement_refs: tuple[TypedRef, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class EvolutionRollbackAfterActivationAdvice(SelfEvolutionCommitAdviceBase):
    """激活后回滚验证建议。"""

    rollback_ref: TypedRef | None = None
    rollback_validation_refs: tuple[TypedRef, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class TombstoneMigrationAdvice(SelfEvolutionCommitAdviceBase):
    """废弃与迁移 Tombstone 建议。"""

    tombstone_ref: TypedRef | None = None
    migration_ref: TypedRef | None = None
