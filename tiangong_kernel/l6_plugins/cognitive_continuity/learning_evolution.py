"""L6 phase4 self-reflection, learning, evolution, and rollback candidates.

These objects close the full planning-pack coverage for self-learning and
self-healing handoff.  They remain suggestions/candidates only.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l6_plugins.common._common import ensure_bool, ensure_score, ensure_ref_items, ensure_ref_text
from .common import CognitiveOutputKind
from .projection import CognitiveOutputBase


def _score(value: float, field_name: str) -> None:
    ensure_score(value, field_name)


@dataclass(frozen=True)
class LearningNeedProjection(CognitiveOutputBase):
    output_ref: str = "projection:l6_phase4_learning_need"
    plugin_ref: str = "l6_phase4:self_reflection_learning"
    learning_need_score: float = 0.5
    starts_learning: bool = False

    def __post_init__(self) -> None:
        super().__post_init__(); _score(self.learning_need_score, "LearningNeedProjection.learning_need_score")
        ensure_bool(self.starts_learning, "LearningNeedProjection.starts_learning")
        if self.starts_learning:
            raise ValueError("learning need projection cannot start learning")


@dataclass(frozen=True)
class FailureDiagnosisProjection(CognitiveOutputBase):
    output_ref: str = "projection:l6_phase4_failure_diagnosis"
    output_kind: CognitiveOutputKind | str = CognitiveOutputKind.REPORT
    plugin_ref: str = "l6_phase4:self_reflection_learning"
    diagnosis_confidence_score: float = 0.5
    failure_kind_ref: str = "healing:l6_phase4_failure_kind"
    fault_kind_ref: str = "healing:l6_phase4_fault_kind_candidate"
    source_projection_refs: tuple[str, ...] = field(default_factory=lambda: ("projection:l6_phase4_failure_source",))
    affected_candidate_refs: tuple[str, ...] = field(default_factory=lambda: ("projection:l6_phase4_affected_candidate",))
    affected_module_refs: tuple[str, ...] = field(default_factory=lambda: ("l6_phase4:self_reflection_learning",))
    expires_at_ref: str = "ref:l6_phase4_failure_diagnosis_expires_at"
    assigns_fault_finally: bool = False
    final_fault_assignment_allowed: bool = False

    def __post_init__(self) -> None:
        super().__post_init__(); _score(self.diagnosis_confidence_score, "FailureDiagnosisProjection.diagnosis_confidence_score")
        for field_name in ("failure_kind_ref", "fault_kind_ref", "expires_at_ref"):
            ensure_ref_text(getattr(self, field_name), f"FailureDiagnosisProjection.{field_name}")
        for field_name in ("source_projection_refs", "affected_candidate_refs", "affected_module_refs"):
            ensure_ref_items(getattr(self, field_name), f"FailureDiagnosisProjection.{field_name}", required=True)
        ensure_bool(self.assigns_fault_finally, "FailureDiagnosisProjection.assigns_fault_finally")
        ensure_bool(self.final_fault_assignment_allowed, "FailureDiagnosisProjection.final_fault_assignment_allowed")
        if self.assigns_fault_finally or self.final_fault_assignment_allowed:
            raise ValueError("failure diagnosis projection cannot be final fault assignment")


@dataclass(frozen=True)
class QualityGapReport(CognitiveOutputBase):
    output_ref: str = "projection:l6_phase4_quality_gap_report"
    output_kind: CognitiveOutputKind | str = CognitiveOutputKind.REPORT
    plugin_ref: str = "l6_phase4:self_reflection_learning"
    gap_refs: tuple[str, ...] = field(default_factory=lambda: ("ref:l6_phase4_quality_gap",))
    direct_fix_allowed: bool = False

    def __post_init__(self) -> None:
        super().__post_init__(); ensure_ref_items(self.gap_refs, "QualityGapReport.gap_refs", required=True)
        ensure_bool(self.direct_fix_allowed, "QualityGapReport.direct_fix_allowed")
        if self.direct_fix_allowed:
            raise ValueError("quality gap report cannot directly fix")


@dataclass(frozen=True)
class RepairSuggestion(CognitiveOutputBase):
    output_ref: str = "projection:l6_phase4_repair_suggestion"
    output_kind: CognitiveOutputKind | str = CognitiveOutputKind.SUGGESTION
    plugin_ref: str = "l6_phase4:self_reflection_learning"
    repair_summary_ref: str = "summary:l6_phase4_repair_candidate"
    patch_summary_ref: str = "summary:l6_phase4_repair_patch_summary"
    validation_need_ref: str = "validation:l6_phase4_repair_validation_need"
    regression_need_ref: str = "regression:l6_phase4_repair_regression_need"
    executable_patch_included: bool = False
    auto_repair_allowed: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        for field_name in ("repair_summary_ref", "patch_summary_ref", "validation_need_ref", "regression_need_ref"):
            ensure_ref_text(getattr(self, field_name), f"RepairSuggestion.{field_name}")
        ensure_bool(self.executable_patch_included, "RepairSuggestion.executable_patch_included")
        ensure_bool(self.auto_repair_allowed, "RepairSuggestion.auto_repair_allowed")
        if self.executable_patch_included or self.auto_repair_allowed:
            raise ValueError("repair suggestion cannot include executable patch or auto repair")


@dataclass(frozen=True)
class EvolutionCandidate(CognitiveOutputBase):
    output_ref: str = "projection:l6_phase4_evolution_candidate"
    output_kind: CognitiveOutputKind | str = CognitiveOutputKind.CANDIDATE
    plugin_ref: str = "l6_phase4:self_reflection_learning"
    evolution_score: float = 0.5
    patch_summary_ref: str = "summary:l6_phase4_evolution_patch_summary"
    validation_need_ref: str = "validation:l6_phase4_evolution_validation_need"
    regression_need_ref: str = "regression:l6_phase4_evolution_regression_need"
    executable_patch_included: bool = False
    applies_change: bool = False

    def __post_init__(self) -> None:
        super().__post_init__(); _score(self.evolution_score, "EvolutionCandidate.evolution_score")
        for field_name in ("patch_summary_ref", "validation_need_ref", "regression_need_ref"):
            ensure_ref_text(getattr(self, field_name), f"EvolutionCandidate.{field_name}")
        ensure_bool(self.executable_patch_included, "EvolutionCandidate.executable_patch_included")
        ensure_bool(self.applies_change, "EvolutionCandidate.applies_change")
        if self.executable_patch_included or self.applies_change:
            raise ValueError("evolution candidate cannot include executable patch or apply change")


@dataclass(frozen=True)
class IterationCandidate(EvolutionCandidate):
    output_ref: str = "projection:l6_phase4_iteration_candidate"


@dataclass(frozen=True)
class RollbackSuggestion(CognitiveOutputBase):
    output_ref: str = "projection:l6_phase4_rollback_suggestion"
    output_kind: CognitiveOutputKind | str = CognitiveOutputKind.SUGGESTION
    plugin_ref: str = "l6_phase4:self_reflection_learning"
    rollback_policy_ref: str = "rollback:l6_phase4_review_only"
    validation_need_ref: str = "validation:l6_phase4_rollback_validation_need"
    regression_need_ref: str = "regression:l6_phase4_rollback_regression_need"
    auto_rollback_allowed: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        for field_name in ("rollback_policy_ref", "validation_need_ref", "regression_need_ref"):
            ensure_ref_text(getattr(self, field_name), f"RollbackSuggestion.{field_name}")
        ensure_bool(self.auto_rollback_allowed, "RollbackSuggestion.auto_rollback_allowed")
        if self.auto_rollback_allowed:
            raise ValueError("rollback suggestion cannot auto rollback")


@dataclass(frozen=True)
class MigrationSuggestion(CognitiveOutputBase):
    output_ref: str = "projection:l6_phase4_migration_suggestion"
    output_kind: CognitiveOutputKind | str = CognitiveOutputKind.SUGGESTION
    plugin_ref: str = "l6_phase4:self_reflection_learning"
    migration_policy_ref: str = "migration:l6_phase4_review_only"
    auto_migration_allowed: bool = False

    def __post_init__(self) -> None:
        super().__post_init__(); ensure_ref_text(self.migration_policy_ref, "MigrationSuggestion.migration_policy_ref")
        ensure_bool(self.auto_migration_allowed, "MigrationSuggestion.auto_migration_allowed")
        if self.auto_migration_allowed:
            raise ValueError("migration suggestion cannot auto migrate")


@dataclass(frozen=True)
class HotSwitchReadinessHint(CognitiveOutputBase):
    output_ref: str = "projection:l6_phase4_hot_switch_readiness_hint"
    output_kind: CognitiveOutputKind | str = CognitiveOutputKind.HINT
    plugin_ref: str = "l6_phase4:self_reflection_learning"
    readiness_score: float = 0.5
    is_permit: bool = False

    def __post_init__(self) -> None:
        super().__post_init__(); _score(self.readiness_score, "HotSwitchReadinessHint.readiness_score")
        ensure_bool(self.is_permit, "HotSwitchReadinessHint.is_permit")
        if self.is_permit:
            raise ValueError("hot switch readiness hint is not permit")


@dataclass(frozen=True)
class LearningEvolutionReentryEnvelope(CognitiveOutputBase):
    output_ref: str = "l6:l6_phase4_learning_evolution_reentry_envelope"
    output_kind: CognitiveOutputKind | str = CognitiveOutputKind.REENTRY_ENVELOPE
    plugin_ref: str = "l6_phase4:self_reflection_learning"
    candidate_refs: tuple[str, ...] = field(default_factory=lambda: ("projection:l6_phase4_learning_need",))
    l3_l5_review_required: bool = True
    auto_apply_allowed: bool = False

    def __post_init__(self) -> None:
        super().__post_init__(); ensure_ref_items(self.candidate_refs, "LearningEvolutionReentryEnvelope.candidate_refs", required=True)
        ensure_bool(self.l3_l5_review_required, "LearningEvolutionReentryEnvelope.l3_l5_review_required")
        ensure_bool(self.auto_apply_allowed, "LearningEvolutionReentryEnvelope.auto_apply_allowed")
        if not self.l3_l5_review_required or self.auto_apply_allowed:
            raise ValueError("learning evolution reentry is review-only")

@dataclass(frozen=True)
class ValidationNeedProjection(CognitiveOutputBase):
    output_ref: str = "validation:l6_phase4_validation_need"
    output_kind: CognitiveOutputKind | str = CognitiveOutputKind.PROJECTION
    plugin_ref: str = "l6_phase4:self_reflection_learning"
    target_candidate_refs: tuple[str, ...] = field(default_factory=lambda: ("projection:l6_phase4_repair_suggestion",))
    validation_summary_ref: str = "summary:l6_phase4_validation_need"
    validation_executed: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_items(self.target_candidate_refs, "ValidationNeedProjection.target_candidate_refs", required=True)
        ensure_ref_text(self.validation_summary_ref, "ValidationNeedProjection.validation_summary_ref")
        ensure_bool(self.validation_executed, "ValidationNeedProjection.validation_executed")
        if self.validation_executed:
            raise ValueError("validation need projection cannot execute validation")


@dataclass(frozen=True)
class RegressionNeedProjection(CognitiveOutputBase):
    output_ref: str = "regression:l6_phase4_regression_need"
    output_kind: CognitiveOutputKind | str = CognitiveOutputKind.PROJECTION
    plugin_ref: str = "l6_phase4:self_reflection_learning"
    target_candidate_refs: tuple[str, ...] = field(default_factory=lambda: ("projection:l6_phase4_repair_suggestion",))
    regression_summary_ref: str = "summary:l6_phase4_regression_need"
    regression_executed: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_items(self.target_candidate_refs, "RegressionNeedProjection.target_candidate_refs", required=True)
        ensure_ref_text(self.regression_summary_ref, "RegressionNeedProjection.regression_summary_ref")
        ensure_bool(self.regression_executed, "RegressionNeedProjection.regression_executed")
        if self.regression_executed:
            raise ValueError("regression need projection cannot execute regression")


@dataclass(frozen=True)
class LearningEvidenceIndex(CognitiveOutputBase):
    output_ref: str = "evidence:l6_phase4_learning_evidence_index"
    output_kind: CognitiveOutputKind | str = CognitiveOutputKind.REPORT
    plugin_ref: str = "l6_phase4:self_reflection_learning"
    evidence_refs: tuple[str, ...] = field(default_factory=lambda: ("evidence:l6_phase4_learning_source",))
    complete_raw_trace_included: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_bool(self.complete_raw_trace_included, "LearningEvidenceIndex.complete_raw_trace_included")
        if self.complete_raw_trace_included:
            raise ValueError("learning evidence index cannot expose complete raw trace")


@dataclass(frozen=True)
class LearningNeedReviewEnvelope(CognitiveOutputBase):
    output_ref: str = "learning:l6_phase4_learning_need_review_envelope"
    output_kind: CognitiveOutputKind | str = CognitiveOutputKind.REVIEW_REQUEST
    plugin_ref: str = "l6_phase4:self_reflection_learning"
    candidate_refs: tuple[str, ...] = field(default_factory=lambda: ("projection:l6_phase4_learning_need",))
    l3_l5_review_required: bool = True
    starts_learning: bool = False

    def __post_init__(self) -> None:
        super().__post_init__(); ensure_ref_items(self.candidate_refs, "LearningNeedReviewEnvelope.candidate_refs", required=True)
        ensure_bool(self.l3_l5_review_required, "LearningNeedReviewEnvelope.l3_l5_review_required")
        ensure_bool(self.starts_learning, "LearningNeedReviewEnvelope.starts_learning")
        if not self.l3_l5_review_required or self.starts_learning:
            raise ValueError("learning need review envelope cannot start learning")


@dataclass(frozen=True)
class EvolutionCandidateReviewEnvelope(CognitiveOutputBase):
    output_ref: str = "learning:l6_phase4_evolution_candidate_review_envelope"
    output_kind: CognitiveOutputKind | str = CognitiveOutputKind.REVIEW_REQUEST
    plugin_ref: str = "l6_phase4:self_reflection_learning"
    candidate_refs: tuple[str, ...] = field(default_factory=lambda: ("projection:l6_phase4_evolution_candidate",))
    l3_l5_review_required: bool = True
    applies_change: bool = False

    def __post_init__(self) -> None:
        super().__post_init__(); ensure_ref_items(self.candidate_refs, "EvolutionCandidateReviewEnvelope.candidate_refs", required=True)
        ensure_bool(self.l3_l5_review_required, "EvolutionCandidateReviewEnvelope.l3_l5_review_required")
        ensure_bool(self.applies_change, "EvolutionCandidateReviewEnvelope.applies_change")
        if not self.l3_l5_review_required or self.applies_change:
            raise ValueError("evolution candidate review envelope cannot apply change")


@dataclass(frozen=True)
class CandidateMaturityProjection(CognitiveOutputBase):
    output_ref: str = "projection:l6_phase4_candidate_maturity"
    plugin_ref: str = "l6_phase4:self_reflection_learning"
    maturity_score: float = 0.5
    mature_enough_to_apply: bool = False

    def __post_init__(self) -> None:
        super().__post_init__(); _score(self.maturity_score, "CandidateMaturityProjection.maturity_score")
        ensure_bool(self.mature_enough_to_apply, "CandidateMaturityProjection.mature_enough_to_apply")
        if self.mature_enough_to_apply:
            raise ValueError("candidate maturity projection is not authorization to apply")


@dataclass(frozen=True)
class NoAutoEvolutionGuard(CognitiveOutputBase):
    output_ref: str = "policy:l6_phase4_no_auto_evolution_guard"
    output_kind: CognitiveOutputKind | str = CognitiveOutputKind.REPORT
    plugin_ref: str = "l6_phase4:self_reflection_learning"
    auto_learning_allowed: bool = False
    auto_repair_allowed: bool = False
    auto_evolution_allowed: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        for field_name in ("auto_learning_allowed", "auto_repair_allowed", "auto_evolution_allowed"):
            ensure_bool(getattr(self, field_name), f"NoAutoEvolutionGuard.{field_name}")
        if self.auto_learning_allowed or self.auto_repair_allowed or self.auto_evolution_allowed:
            raise ValueError("L6 phase4 learning/evolution guard forbids auto execution")

