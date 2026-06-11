"""L3 Context / Belief / World 安全转换建议。

本模块只提供 belief update、world reconciliation、context pollution review 和
tool/model result demotion 的建议，不写状态、不装配上下文、不生成系统指令。
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


@dataclass(frozen=True, slots=True)
class BeliefWorldContextAdviceBase:
    """信念、世界和上下文安全建议基础对象。"""

    advice_ref: TypedRef
    source_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    advisory_only: bool = True
    ref_only: bool = True
    writes_l2_state: bool = False
    assembles_context: bool = False
    emits_instruction: bool = False
    belief_overrides_event: bool = False
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _true(self.advisory_only, f"{self.__class__.__name__}.advisory_only")
        _true(self.ref_only, f"{self.__class__.__name__}.ref_only")
        _false(self.writes_l2_state, f"{self.__class__.__name__}.writes_l2_state")
        _false(self.assembles_context, f"{self.__class__.__name__}.assembles_context")
        _false(self.emits_instruction, f"{self.__class__.__name__}.emits_instruction")
        _false(self.belief_overrides_event, f"{self.__class__.__name__}.belief_overrides_event")
        if not self.schema_version:
            raise ValueError(f"{self.__class__.__name__}.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class BeliefUpdateAdvice(BeliefWorldContextAdviceBase):
    """信念更新建议。"""

    belief_ref: TypedRef | None = None


@dataclass(frozen=True, slots=True)
class BeliefConflictReviewAdvice(BeliefWorldContextAdviceBase):
    """信念冲突复核建议。"""

    conflicting_belief_refs: tuple[TypedRef, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class BeliefEventPrecedenceAdvice(BeliefWorldContextAdviceBase):
    """事件事实优先建议。"""

    event_ref: TypedRef | None = None
    belief_ref: TypedRef | None = None
    event_precedes_belief: bool = True

    def __post_init__(self) -> None:
        BeliefWorldContextAdviceBase.__post_init__(self)
        _true(self.event_precedes_belief, "BeliefEventPrecedenceAdvice.event_precedes_belief")


@dataclass(frozen=True, slots=True)
class WorldStateReconciliationAdvice(BeliefWorldContextAdviceBase):
    """世界状态对齐建议。"""

    world_state_ref: TypedRef | None = None


@dataclass(frozen=True, slots=True)
class WorldStalenessReviewAdvice(BeliefWorldContextAdviceBase):
    """世界状态过期复核建议。"""

    world_state_ref: TypedRef | None = None
    staleness_ref: TypedRef | None = None


@dataclass(frozen=True, slots=True)
class ContextPollutionReviewAdvice(BeliefWorldContextAdviceBase):
    """上下文污染复核建议。"""

    taint_refs: tuple[TypedRef, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class ToolResultContextDemotionAdvice(BeliefWorldContextAdviceBase):
    """工具结果上下文降级建议。"""

    tool_result_ref: TypedRef | None = None
    untrusted_output: bool = True
    instruction_eligible: bool = False
    system_instruction_eligible: bool = False
    context_injection_allowed: bool = False

    def __post_init__(self) -> None:
        BeliefWorldContextAdviceBase.__post_init__(self)
        _true(self.untrusted_output, "ToolResultContextDemotionAdvice.untrusted_output")
        _false(self.instruction_eligible, "ToolResultContextDemotionAdvice.instruction_eligible")
        _false(self.system_instruction_eligible, "ToolResultContextDemotionAdvice.system_instruction_eligible")
        _false(self.context_injection_allowed, "ToolResultContextDemotionAdvice.context_injection_allowed")


@dataclass(frozen=True, slots=True)
class ModelResultContextDemotionAdvice(ToolResultContextDemotionAdvice):
    """模型结果上下文降级建议。"""

    model_result_ref: TypedRef | None = None
