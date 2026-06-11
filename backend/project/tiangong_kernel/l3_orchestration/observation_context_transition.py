"""L3 第六阶段与前五阶段接线建议对象。

本模块只描述观察、上下文与未来子系统服务请求如何回接到 Run/Task/Turn/Step 等编排引用。
它不调用任何真实服务，不写状态。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef

from .orchestration_identity import L3_ORCHESTRATION_SCHEMA_VERSION
from .subsystem_service_request import SubsystemServiceKind


class ObservationContextTransitionKind(str, Enum):
    UNKNOWN = "unknown"
    EXECUTION_TO_OBSERVATION = "execution_to_observation"
    RESULT_TO_CONTEXT = "result_to_context"
    INTENT_TO_OBSERVATION_FEEDBACK = "intent_to_observation_feedback"
    SKILL_TOOL_TO_CONTEXT = "skill_tool_to_context"
    RUN_OBSERVATION = "run_observation"
    TASK_OBSERVATION = "task_observation"
    TURN_OBSERVATION = "turn_observation"
    STEP_OBSERVATION = "step_observation"
    RUN_SUBSYSTEM_SERVICE = "run_subsystem_service"
    TASK_SUBSYSTEM_SERVICE = "task_subsystem_service"
    TURN_SUBSYSTEM_SERVICE = "turn_subsystem_service"
    STEP_SUBSYSTEM_SERVICE = "step_subsystem_service"


def _ensure_short_text(value: str, field_name: str, limit: int = 512) -> None:
    if len(value) > limit:
        raise ValueError(f"{field_name} must be short")


def _ensure_unit_interval(value: float, field_name: str) -> None:
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{field_name} must be between 0.0 and 1.0")


def _ensure_advisory(flag: bool, field_name: str) -> None:
    if flag is not True:
        raise ValueError(f"{field_name} must remain true")


@dataclass(frozen=True, slots=True)
class ObservationContextTransitionAdviceBase:
    advice_ref: TypedRef
    transition_kind: ObservationContextTransitionKind
    source_ref: TypedRef | None = None
    target_ref: TypedRef | None = None
    observation_ref: TypedRef | None = None
    context_ref: TypedRef | None = None
    service_request_ref: TypedRef | None = None
    service_kind: SubsystemServiceKind = SubsystemServiceKind.UNKNOWN
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    confidence: float = 0.0
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for item in self.reason_codes:
            _ensure_short_text(item, f"{self.__class__.__name__}.reason_codes", 128)
        _ensure_unit_interval(self.confidence, f"{self.__class__.__name__}.confidence")
        _ensure_advisory(self.advisory_only, f"{self.__class__.__name__}.advisory_only")
        if not self.schema_version:
            raise ValueError(f"{self.__class__.__name__}.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ExecutionToObservationAdvice(ObservationContextTransitionAdviceBase):
    transition_kind: ObservationContextTransitionKind = ObservationContextTransitionKind.EXECUTION_TO_OBSERVATION


@dataclass(frozen=True, slots=True)
class ExecutionResultContextAdvice(ObservationContextTransitionAdviceBase):
    transition_kind: ObservationContextTransitionKind = ObservationContextTransitionKind.RESULT_TO_CONTEXT


@dataclass(frozen=True, slots=True)
class IntentObservationFeedbackAdvice(ObservationContextTransitionAdviceBase):
    transition_kind: ObservationContextTransitionKind = ObservationContextTransitionKind.INTENT_TO_OBSERVATION_FEEDBACK


@dataclass(frozen=True, slots=True)
class SkillToolContextCarryoverAdvice(ObservationContextTransitionAdviceBase):
    transition_kind: ObservationContextTransitionKind = ObservationContextTransitionKind.SKILL_TOOL_TO_CONTEXT


@dataclass(frozen=True, slots=True)
class RunObservationAdvice(ObservationContextTransitionAdviceBase):
    transition_kind: ObservationContextTransitionKind = ObservationContextTransitionKind.RUN_OBSERVATION


@dataclass(frozen=True, slots=True)
class TaskObservationAdvice(ObservationContextTransitionAdviceBase):
    transition_kind: ObservationContextTransitionKind = ObservationContextTransitionKind.TASK_OBSERVATION


@dataclass(frozen=True, slots=True)
class TurnObservationAdvice(ObservationContextTransitionAdviceBase):
    transition_kind: ObservationContextTransitionKind = ObservationContextTransitionKind.TURN_OBSERVATION


@dataclass(frozen=True, slots=True)
class StepObservationAdvice(ObservationContextTransitionAdviceBase):
    transition_kind: ObservationContextTransitionKind = ObservationContextTransitionKind.STEP_OBSERVATION


@dataclass(frozen=True, slots=True)
class RunSubsystemServiceAdvice(ObservationContextTransitionAdviceBase):
    transition_kind: ObservationContextTransitionKind = ObservationContextTransitionKind.RUN_SUBSYSTEM_SERVICE


@dataclass(frozen=True, slots=True)
class TaskSubsystemServiceAdvice(ObservationContextTransitionAdviceBase):
    transition_kind: ObservationContextTransitionKind = ObservationContextTransitionKind.TASK_SUBSYSTEM_SERVICE


@dataclass(frozen=True, slots=True)
class TurnSubsystemServiceAdvice(ObservationContextTransitionAdviceBase):
    transition_kind: ObservationContextTransitionKind = ObservationContextTransitionKind.TURN_SUBSYSTEM_SERVICE


@dataclass(frozen=True, slots=True)
class StepSubsystemServiceAdvice(ObservationContextTransitionAdviceBase):
    transition_kind: ObservationContextTransitionKind = ObservationContextTransitionKind.STEP_SUBSYSTEM_SERVICE
