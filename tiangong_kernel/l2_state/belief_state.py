"""L2 信念状态对象。

信念状态只表达假设、证据绑定、冲突、修订和事件事实优先级，不覆盖 Event 事实。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from .base_state import L2_STATE_SCHEMA_VERSION, L2StateMetadata
from .state_identity import L2StateIdentity
from .state_status import L2StateStatus


def _unit(value: float, field_name: str) -> None:
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{field_name} must be between 0.0 and 1.0")


def _true(value: bool, field_name: str) -> None:
    if value is not True:
        raise ValueError(f"{field_name} must remain true")


def _false(value: bool, field_name: str) -> None:
    if value is not False:
        raise ValueError(f"{field_name} must remain false")


@dataclass(frozen=True, slots=True)
class BeliefStateBase:
    """信念状态基础对象。"""

    identity: L2StateIdentity
    status: L2StateStatus
    belief_ref: TypedRef | None = None
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    event_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    summary: str = ""
    state_only: bool = True
    ref_only: bool = True
    updates_belief: bool = False
    overrides_event_fact: bool = False
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if len(self.summary) > 512:
            raise ValueError(f"{self.__class__.__name__}.summary must be short")
        _true(self.state_only, f"{self.__class__.__name__}.state_only")
        _true(self.ref_only, f"{self.__class__.__name__}.ref_only")
        _false(self.updates_belief, f"{self.__class__.__name__}.updates_belief")
        _false(self.overrides_event_fact, f"{self.__class__.__name__}.overrides_event_fact")
        if not self.schema_version:
            raise ValueError(f"{self.__class__.__name__}.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class BeliefHypothesisState(BeliefStateBase):
    """信念假设状态。"""

    confidence: float = 0.0

    def __post_init__(self) -> None:
        BeliefStateBase.__post_init__(self)
        _unit(self.confidence, "BeliefHypothesisState.confidence")


@dataclass(frozen=True, slots=True)
class BeliefEvidenceBindingState(BeliefStateBase):
    """信念证据绑定状态。"""

    binding_ref: TypedRef | None = None


@dataclass(frozen=True, slots=True)
class BeliefConflictState(BeliefStateBase):
    """信念冲突状态。"""

    conflicting_belief_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    conflict_level: str = "unknown"


@dataclass(frozen=True, slots=True)
class BeliefRevisionState(BeliefStateBase):
    """信念修订状态。"""

    revision_ref: TypedRef | None = None
    superseded_belief_refs: tuple[TypedRef, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class BeliefEventPrecedenceState(BeliefStateBase):
    """事件事实优先状态。"""

    event_precedes_belief: bool = True

    def __post_init__(self) -> None:
        BeliefStateBase.__post_init__(self)
        _true(self.event_precedes_belief, "BeliefEventPrecedenceState.event_precedes_belief")
