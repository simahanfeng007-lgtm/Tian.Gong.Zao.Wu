"""L6 phase4 self-healing candidate contracts.

Self-healing is represented as review candidates only.  No object in this file
repairs, edits, migrates, rolls back, or switches anything.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l6_plugins.common._common import ensure_bool, ensure_score, ensure_ref_items, ensure_ref_text
from .common import CognitiveOutputKind
from .projection import CognitiveOutputBase


def _score(value: float, field_name: str) -> None:
    ensure_score(value, field_name)


@dataclass(frozen=True)
class HealingNeedProjection(CognitiveOutputBase):
    output_ref: str = "projection:l6_phase4_healing_need"
    plugin_ref: str = "l6_phase4:self_healing_bridge"
    healing_need_score: float = 0.5
    starts_repair: bool = False

    def __post_init__(self) -> None:
        super().__post_init__(); _score(self.healing_need_score, "HealingNeedProjection.healing_need_score")
        ensure_bool(self.starts_repair, "HealingNeedProjection.starts_repair")
        if self.starts_repair:
            raise ValueError("healing need projection cannot start repair")


@dataclass(frozen=True)
class RecoveryCandidateProjection(CognitiveOutputBase):
    output_ref: str = "projection:l6_phase4_recovery_candidate"
    output_kind: CognitiveOutputKind | str = CognitiveOutputKind.CANDIDATE
    plugin_ref: str = "l6_phase4:self_healing_bridge"
    recovery_point_refs: tuple[str, ...] = field(default_factory=lambda: ("rollback:l6_phase4_recovery_point_candidate",))
    auto_recover_allowed: bool = False

    def __post_init__(self) -> None:
        super().__post_init__(); ensure_ref_items(self.recovery_point_refs, "RecoveryCandidateProjection.recovery_point_refs", required=True)
        ensure_bool(self.auto_recover_allowed, "RecoveryCandidateProjection.auto_recover_allowed")
        if self.auto_recover_allowed:
            raise ValueError("recovery candidate cannot auto recover")


@dataclass(frozen=True)
class SafeRepairSuggestion(CognitiveOutputBase):
    output_ref: str = "projection:l6_phase4_safe_repair_suggestion"
    output_kind: CognitiveOutputKind | str = CognitiveOutputKind.SUGGESTION
    plugin_ref: str = "l6_phase4:self_healing_bridge"
    repair_candidate_refs: tuple[str, ...] = field(default_factory=lambda: ("projection:l6_phase4_repair_candidate",))
    validation_need_ref: str = "validation:l6_phase4_safe_repair_validation_need"
    regression_need_ref: str = "regression:l6_phase4_safe_repair_regression_need"
    executable_patch_included: bool = False
    applies_patch: bool = False

    def __post_init__(self) -> None:
        super().__post_init__(); ensure_ref_items(self.repair_candidate_refs, "SafeRepairSuggestion.repair_candidate_refs", required=True)
        ensure_ref_text(self.validation_need_ref, "SafeRepairSuggestion.validation_need_ref")
        ensure_ref_text(self.regression_need_ref, "SafeRepairSuggestion.regression_need_ref")
        ensure_bool(self.executable_patch_included, "SafeRepairSuggestion.executable_patch_included")
        ensure_bool(self.applies_patch, "SafeRepairSuggestion.applies_patch")
        if self.executable_patch_included or self.applies_patch:
            raise ValueError("safe repair suggestion cannot include or apply patch")


@dataclass(frozen=True)
class SelfHealingReentryEnvelope(CognitiveOutputBase):
    output_ref: str = "l6:l6_phase4_self_healing_reentry_envelope"
    output_kind: CognitiveOutputKind | str = CognitiveOutputKind.REENTRY_ENVELOPE
    plugin_ref: str = "l6_phase4:self_healing_bridge"
    candidate_refs: tuple[str, ...] = field(default_factory=lambda: ("projection:l6_phase4_healing_need",))
    target_review_layer_ref: str = "review:l3_l5_self_healing_review"
    l3_l5_review_required: bool = True
    auto_heal_allowed: bool = False

    def __post_init__(self) -> None:
        super().__post_init__(); ensure_ref_items(self.candidate_refs, "SelfHealingReentryEnvelope.candidate_refs", required=True)
        ensure_ref_text(self.target_review_layer_ref, "SelfHealingReentryEnvelope.target_review_layer_ref")
        ensure_bool(self.l3_l5_review_required, "SelfHealingReentryEnvelope.l3_l5_review_required")
        ensure_bool(self.auto_heal_allowed, "SelfHealingReentryEnvelope.auto_heal_allowed")
        if not self.l3_l5_review_required or self.auto_heal_allowed:
            raise ValueError("self-healing reentry is review-only")
