"""L4 to L6 validation, evaluation, and regression requirements."""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from ._common import L4_EXECUTION_CLOSURE_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_text_items, ensure_true


@dataclass(frozen=True, slots=True)
class L4ToL6ValidationRequirement:
    requirement_ref: TypedRef
    required_test_kinds: tuple[str, ...] = field(default_factory=tuple)
    required_validation_kinds: tuple[str, ...] = field(default_factory=tuple)
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    requirement_only: bool = True
    implements_validation_system: bool = False
    schema_version: str = L4_EXECUTION_CLOSURE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_text_items(self.required_test_kinds, "L4ToL6ValidationRequirement.required_test_kinds", 128)
        ensure_text_items(self.required_validation_kinds, "L4ToL6ValidationRequirement.required_validation_kinds", 128)
        ensure_true(self.requirement_only, "L4ToL6ValidationRequirement.requirement_only")
        ensure_false(self.implements_validation_system, "L4ToL6ValidationRequirement.implements_validation_system")
        ensure_schema_version(self.schema_version, "L4ToL6ValidationRequirement.schema_version")


@dataclass(frozen=True, slots=True)
class L4ToL6EvaluationRequirement:
    requirement_ref: TypedRef
    required_evaluation_targets: tuple[str, ...] = field(default_factory=tuple)
    required_metric_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    requirement_only: bool = True
    executes_evaluation: bool = False
    schema_version: str = L4_EXECUTION_CLOSURE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_text_items(self.required_evaluation_targets, "L4ToL6EvaluationRequirement.required_evaluation_targets", 128)
        ensure_true(self.requirement_only, "L4ToL6EvaluationRequirement.requirement_only")
        ensure_false(self.executes_evaluation, "L4ToL6EvaluationRequirement.executes_evaluation")
        ensure_schema_version(self.schema_version, "L4ToL6EvaluationRequirement.schema_version")


@dataclass(frozen=True, slots=True)
class L4ToL6RegressionRequirement:
    requirement_ref: TypedRef
    required_regression_baselines: tuple[TypedRef, ...] = field(default_factory=tuple)
    required_regression_kinds: tuple[str, ...] = field(default_factory=tuple)
    requirement_only: bool = True
    detects_regression: bool = False
    schema_version: str = L4_EXECUTION_CLOSURE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_text_items(self.required_regression_kinds, "L4ToL6RegressionRequirement.required_regression_kinds", 128)
        ensure_true(self.requirement_only, "L4ToL6RegressionRequirement.requirement_only")
        ensure_false(self.detects_regression, "L4ToL6RegressionRequirement.detects_regression")
        ensure_schema_version(self.schema_version, "L4ToL6RegressionRequirement.schema_version")
