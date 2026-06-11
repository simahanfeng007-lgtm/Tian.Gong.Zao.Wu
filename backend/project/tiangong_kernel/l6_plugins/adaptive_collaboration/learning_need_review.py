from __future__ import annotations
from dataclasses import dataclass, field
from .common import AdaptiveArtifactBase

@dataclass(frozen=True)
class LearningNeedReviewRequest(AdaptiveArtifactBase):
    object_ref: str = "learning:l6_phase7_need_review_request"
    learning_executed: bool = False
    writes_knowledge: bool = False
    writes_skill_registry: bool = False
    priority_score_ref: str = "score:l6_phase7_learning_priority"

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.learning_executed or self.writes_knowledge or self.writes_skill_registry:
            raise ValueError("LearningNeedReviewRequest is not learning execution or a write")

@dataclass(frozen=True)
class LearningNeedPriorityScore(AdaptiveArtifactBase):
    object_ref: str = "score:l6_phase7_learning_need_priority"

@dataclass(frozen=True)
class LearningEvidenceIndex(AdaptiveArtifactBase):
    object_ref: str = "evidence:l6_phase7_learning_evidence_index"

@dataclass(frozen=True)
class LearningRiskHint(AdaptiveArtifactBase):
    object_ref: str = "hint:l6_phase7_learning_risk"

@dataclass(frozen=True)
class LearningGovernanceRequirement(AdaptiveArtifactBase):
    object_ref: str = "requirement:l6_phase7_learning_governance"

@dataclass(frozen=True)
class LearningNeedPublicSummary(AdaptiveArtifactBase):
    object_ref: str = "public:l6_phase7_learning_need_summary"
    public_summary: str = "summary:l6_phase7_learning_need_public_summary"

class LearningNeedReviewPlugin:
    declaration_ref = "decl:l6_phase7_learning_need_review_plugin"
