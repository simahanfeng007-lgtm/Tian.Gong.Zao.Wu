"""L3 第七阶段与前六阶段的验证/恢复/迭代/进化接线建议对象。"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef

from .orchestration_identity import L3_ORCHESTRATION_SCHEMA_VERSION


class ValidationRecoveryTransitionKind(str, Enum):
    UNKNOWN = "unknown"
    OBSERVATION_TO_VALIDATION = "observation_to_validation"
    EXECUTION_FAILURE_TO_RECOVERY = "execution_failure_to_recovery"
    CANDIDATE_TO_VALIDATION = "candidate_to_validation"
    LEARNING_SIGNAL_TO_ITERATION = "learning_signal_to_iteration"
    AFFECTIVE_DRIVE_TO_RECOVERY = "affective_drive_to_recovery"
    DYNAMIC_DRIVE_TO_EXPERIMENT = "dynamic_drive_to_experiment"
    RUN_VALIDATION = "run_validation"
    TASK_VALIDATION = "task_validation"
    TURN_VALIDATION = "turn_validation"
    STEP_VALIDATION = "step_validation"
    RUN_RECOVERY = "run_recovery"
    TASK_RECOVERY = "task_recovery"
    TURN_RECOVERY = "turn_recovery"
    STEP_RECOVERY = "step_recovery"


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
class ValidationRecoveryTransitionAdviceBase:
    advice_ref: TypedRef
    transition_kind: ValidationRecoveryTransitionKind = ValidationRecoveryTransitionKind.UNKNOWN
    source_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    target_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
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
class ObservationToValidationAdvice(ValidationRecoveryTransitionAdviceBase):
    transition_kind: ValidationRecoveryTransitionKind = ValidationRecoveryTransitionKind.OBSERVATION_TO_VALIDATION


@dataclass(frozen=True, slots=True)
class ExecutionFailureToRecoveryAdvice(ValidationRecoveryTransitionAdviceBase):
    transition_kind: ValidationRecoveryTransitionKind = ValidationRecoveryTransitionKind.EXECUTION_FAILURE_TO_RECOVERY


@dataclass(frozen=True, slots=True)
class CandidateToValidationAdvice(ValidationRecoveryTransitionAdviceBase):
    transition_kind: ValidationRecoveryTransitionKind = ValidationRecoveryTransitionKind.CANDIDATE_TO_VALIDATION


@dataclass(frozen=True, slots=True)
class LearningSignalToIterationAdvice(ValidationRecoveryTransitionAdviceBase):
    transition_kind: ValidationRecoveryTransitionKind = ValidationRecoveryTransitionKind.LEARNING_SIGNAL_TO_ITERATION


@dataclass(frozen=True, slots=True)
class AffectiveDriveToRecoveryAdvice(ValidationRecoveryTransitionAdviceBase):
    transition_kind: ValidationRecoveryTransitionKind = ValidationRecoveryTransitionKind.AFFECTIVE_DRIVE_TO_RECOVERY


@dataclass(frozen=True, slots=True)
class DynamicDriveToExperimentAdvice(ValidationRecoveryTransitionAdviceBase):
    transition_kind: ValidationRecoveryTransitionKind = ValidationRecoveryTransitionKind.DYNAMIC_DRIVE_TO_EXPERIMENT


@dataclass(frozen=True, slots=True)
class RunValidationAdvice(ValidationRecoveryTransitionAdviceBase):
    transition_kind: ValidationRecoveryTransitionKind = ValidationRecoveryTransitionKind.RUN_VALIDATION


@dataclass(frozen=True, slots=True)
class TaskValidationAdvice(ValidationRecoveryTransitionAdviceBase):
    transition_kind: ValidationRecoveryTransitionKind = ValidationRecoveryTransitionKind.TASK_VALIDATION


@dataclass(frozen=True, slots=True)
class TurnValidationAdvice(ValidationRecoveryTransitionAdviceBase):
    transition_kind: ValidationRecoveryTransitionKind = ValidationRecoveryTransitionKind.TURN_VALIDATION


@dataclass(frozen=True, slots=True)
class StepValidationAdvice(ValidationRecoveryTransitionAdviceBase):
    transition_kind: ValidationRecoveryTransitionKind = ValidationRecoveryTransitionKind.STEP_VALIDATION


@dataclass(frozen=True, slots=True)
class RunRecoveryAdvice(ValidationRecoveryTransitionAdviceBase):
    transition_kind: ValidationRecoveryTransitionKind = ValidationRecoveryTransitionKind.RUN_RECOVERY


@dataclass(frozen=True, slots=True)
class TaskRecoveryAdvice(ValidationRecoveryTransitionAdviceBase):
    transition_kind: ValidationRecoveryTransitionKind = ValidationRecoveryTransitionKind.TASK_RECOVERY


@dataclass(frozen=True, slots=True)
class TurnRecoveryAdvice(ValidationRecoveryTransitionAdviceBase):
    transition_kind: ValidationRecoveryTransitionKind = ValidationRecoveryTransitionKind.TURN_RECOVERY


@dataclass(frozen=True, slots=True)
class StepRecoveryAdvice(ValidationRecoveryTransitionAdviceBase):
    transition_kind: ValidationRecoveryTransitionKind = ValidationRecoveryTransitionKind.STEP_RECOVERY
