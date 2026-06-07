"""L6 phase3 mind and state plugin group.

Importing this package exposes inert dataclass contracts only. It does not load
providers, call tools, write state, write memory, write audit data, charge
budget, read credentials, or create a parallel runtime.
"""

from __future__ import annotations

from .common import (
    L6_PHASE3,
    GovernanceRefusalReason,
    MindCollaborationChannel,
    MindOutputKind,
    MindPluginDeclaration,
    MindPluginGroupArchitecture,
    MindPluginKind,
    default_mind_plugin_declarations,
)
from .mind_forbidden_scan import default_l6_phase3_mind_forbidden_scan_rules, scan_l6_phase3_mind_text
from .mind_invariants import default_l6_phase3_mind_invariant_rules
from .mind_interoperation import MindInteroperationMatrix, MindInteroperationRule, default_mind_interoperation_matrix
from .mind_quality_gate import L6Phase3MindQualityGateDecision
from .mind_requirement import MindModelNeed, MindToolNeed
from .mind_score import (
    AffectiveTendencyScoreModel,
    AttentionFocusScoreModel,
    BeliefConfidenceScore,
    ForgettingScoreModel,
    GoalPriorityScoreModel,
    MemoryPromotionScoreModel,
    MindFusionScoreModel,
    MindScoreBase,
    PollutionRiskScoreModel,
    SelfReflectionScoreModel,
    WorldConstraintScore,
    clamp01,
    weighted_mean,
)
from .mind_state import (
    AffectiveMindState,
    AttentionMindState,
    BeliefMindState,
    ContextMindState,
    ForgettingCandidateMindState,
    GoalMindState,
    IntentionMindState,
    LearningEvolutionMindState,
    MemoryCandidateMindState,
    MindFusionState,
    MindPollutionDefenseState,
    MindStateDomain,
    MindStateEnvelope,
    PreferenceMindState,
    SelfReflectionMindState,
    WorldMindState,
)
from .mind_projection import *

__all__ = [name for name in globals() if not name.startswith("_")]
