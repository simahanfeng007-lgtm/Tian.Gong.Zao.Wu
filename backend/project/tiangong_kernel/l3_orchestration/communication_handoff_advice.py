"""L3 communication and handoff collaboration advice."""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from .orchestration_identity import L3_ORCHESTRATION_SCHEMA_VERSION


@dataclass(frozen=True, slots=True)
class HandoffCompletenessScore:
    score_ref: TypedRef
    required_ref_names: tuple[str, ...] = field(default_factory=tuple)
    missing_ref_names: tuple[str, ...] = field(default_factory=tuple)
    value: float = 0.0
    score_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not 0.0 <= self.value <= 1.0:
            raise ValueError("HandoffCompletenessScore.value must be between 0 and 1")


@dataclass(frozen=True, slots=True)
class HandoffContinuityCheckAdvice:
    advice_ref: TypedRef
    handoff_ref: TypedRef | None = None
    communication_envelope_ref: TypedRef | None = None
    score_ref: TypedRef | None = None
    result_return_ref: TypedRef | None = None
    failure_return_ref: TypedRef | None = None
    advisory_only: bool = True
    executes_handoff: bool = False
    creates_subagent: bool = False
    shares_raw_tool_handle: bool = False
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION


ActorRouteAdvice = HandoffContinuityCheckAdvice
MultiActorCollaborationPlanAdvice = HandoffContinuityCheckAdvice
ActorResultReturnAdvice = HandoffContinuityCheckAdvice
