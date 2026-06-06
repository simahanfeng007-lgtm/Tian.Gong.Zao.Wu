"""Future bridge governance review declarations for product, learning and healing."""

from __future__ import annotations

from dataclasses import dataclass

from .common import GovernanceArtifactBase, ensure_bool, ensure_ref_text


@dataclass(frozen=True)
class ProductSpecSeedGovernanceReview(GovernanceArtifactBase):
    object_ref: str = "request:l6_phase5_product_spec_seed_governance_review"
    seed_ref: str = "ref:l6_phase4_product_spec_seed_candidate"
    real_product_spec_generated: bool = False
    build_plan_executed: bool = False
    file_write_allowed: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_text(self.seed_ref, "ProductSpecSeedGovernanceReview.seed_ref")
        for field_name in ("real_product_spec_generated", "build_plan_executed", "file_write_allowed"):
            ensure_bool(getattr(self, field_name), f"ProductSpecSeedGovernanceReview.{field_name}")
        if self.real_product_spec_generated or self.build_plan_executed or self.file_write_allowed:
            raise ValueError("ProductSpecSeedGovernanceReview is an inert bridge review only")


@dataclass(frozen=True)
class ProductContextPrivacyCheck(GovernanceArtifactBase):
    object_ref: str = "request:l6_phase5_product_context_privacy_check"
    context_projection_ref: str = "projection:l6_phase4_product_context_safety"
    exposes_raw_context: bool = False
    writes_build_context: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_text(self.context_projection_ref, "ProductContextPrivacyCheck.context_projection_ref")
        ensure_bool(self.exposes_raw_context, "ProductContextPrivacyCheck.exposes_raw_context")
        ensure_bool(self.writes_build_context, "ProductContextPrivacyCheck.writes_build_context")
        if self.exposes_raw_context or self.writes_build_context:
            raise ValueError("ProductContextPrivacyCheck cannot expose or write build context")


@dataclass(frozen=True)
class ArtifactIntentRiskProjection(GovernanceArtifactBase):
    object_ref: str = "projection:l6_phase5_artifact_intent_risk"
    artifact_build_allowed: bool = False
    tool_call_allowed: bool = False
    risk_review_required: bool = True

    def __post_init__(self) -> None:
        super().__post_init__()
        for field_name in ("artifact_build_allowed", "tool_call_allowed", "risk_review_required"):
            ensure_bool(getattr(self, field_name), f"ArtifactIntentRiskProjection.{field_name}")
        if self.artifact_build_allowed or self.tool_call_allowed or not self.risk_review_required:
            raise ValueError("ArtifactIntentRiskProjection is not artifact build")


@dataclass(frozen=True)
class BuildPlanRequirementHint(GovernanceArtifactBase):
    object_ref: str = "hint:l6_phase5_build_plan_requirement"
    requirement_ref: str = "ref:l6_phase5_build_plan_requirement"
    real_build_plan: bool = False
    executes_build: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_text(self.requirement_ref, "BuildPlanRequirementHint.requirement_ref")
        ensure_bool(self.real_build_plan, "BuildPlanRequirementHint.real_build_plan")
        ensure_bool(self.executes_build, "BuildPlanRequirementHint.executes_build")
        if self.real_build_plan or self.executes_build:
            raise ValueError("BuildPlanRequirementHint is not a real build plan")


@dataclass(frozen=True)
class LearningNeedGovernanceReview(GovernanceArtifactBase):
    object_ref: str = "request:l6_phase5_learning_need_governance_review"
    learning_need_ref: str = "projection:l6_phase4_learning_need"
    auto_learning_enabled: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_text(self.learning_need_ref, "LearningNeedGovernanceReview.learning_need_ref")
        ensure_bool(self.auto_learning_enabled, "LearningNeedGovernanceReview.auto_learning_enabled")
        if self.auto_learning_enabled:
            raise ValueError("LearningNeedGovernanceReview cannot auto-learn")


@dataclass(frozen=True)
class RepairSuggestionRiskReview(GovernanceArtifactBase):
    object_ref: str = "request:l6_phase5_repair_suggestion_risk_review"
    repair_suggestion_ref: str = "suggestion:l6_phase4_repair"
    auto_repair_enabled: bool = False
    code_write_allowed: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_text(self.repair_suggestion_ref, "RepairSuggestionRiskReview.repair_suggestion_ref")
        ensure_bool(self.auto_repair_enabled, "RepairSuggestionRiskReview.auto_repair_enabled")
        ensure_bool(self.code_write_allowed, "RepairSuggestionRiskReview.code_write_allowed")
        if self.auto_repair_enabled or self.code_write_allowed:
            raise ValueError("RepairSuggestionRiskReview cannot auto-repair or write code")


@dataclass(frozen=True)
class EvolutionCandidateSafetyReview(GovernanceArtifactBase):
    object_ref: str = "request:l6_phase5_evolution_candidate_safety_review"
    evolution_candidate_ref: str = "projection:l6_phase4_evolution_candidate"
    auto_evolution_enabled: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_text(self.evolution_candidate_ref, "EvolutionCandidateSafetyReview.evolution_candidate_ref")
        ensure_bool(self.auto_evolution_enabled, "EvolutionCandidateSafetyReview.auto_evolution_enabled")
        if self.auto_evolution_enabled:
            raise ValueError("EvolutionCandidateSafetyReview cannot auto-evolve")


@dataclass(frozen=True)
class RollbackSuggestionGovernanceReview(GovernanceArtifactBase):
    object_ref: str = "request:l6_phase5_rollback_suggestion_governance_review"
    rollback_suggestion_ref: str = "suggestion:l6_phase4_rollback"
    auto_rollback_enabled: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_text(self.rollback_suggestion_ref, "RollbackSuggestionGovernanceReview.rollback_suggestion_ref")
        ensure_bool(self.auto_rollback_enabled, "RollbackSuggestionGovernanceReview.auto_rollback_enabled")
        if self.auto_rollback_enabled:
            raise ValueError("RollbackSuggestionGovernanceReview cannot auto-rollback")


@dataclass(frozen=True)
class MigrationSuggestionGovernanceReview(GovernanceArtifactBase):
    object_ref: str = "request:l6_phase5_migration_suggestion_governance_review"
    migration_suggestion_ref: str = "suggestion:l6_phase4_migration"
    auto_migration_enabled: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_text(self.migration_suggestion_ref, "MigrationSuggestionGovernanceReview.migration_suggestion_ref")
        ensure_bool(self.auto_migration_enabled, "MigrationSuggestionGovernanceReview.auto_migration_enabled")
        if self.auto_migration_enabled:
            raise ValueError("MigrationSuggestionGovernanceReview cannot auto-migrate")


@dataclass(frozen=True)
class HotSwitchReadinessGovernanceReview(GovernanceArtifactBase):
    object_ref: str = "request:l6_phase5_hot_switch_readiness_governance_review"
    readiness_ref: str = "hint:l6_phase4_hot_switch_readiness"
    performs_hot_switch: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_text(self.readiness_ref, "HotSwitchReadinessGovernanceReview.readiness_ref")
        ensure_bool(self.performs_hot_switch, "HotSwitchReadinessGovernanceReview.performs_hot_switch")
        if self.performs_hot_switch:
            raise ValueError("HotSwitchReadinessGovernanceReview cannot perform hot switch")
