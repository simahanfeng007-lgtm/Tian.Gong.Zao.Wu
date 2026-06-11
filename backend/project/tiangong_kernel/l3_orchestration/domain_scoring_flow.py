"""Domain-specific formal math scoring flow references."""

from __future__ import annotations

from dataclasses import dataclass

from .scoring_flow import ScoringFlow


@dataclass(frozen=True, slots=True)
class MemoryScoringFlow(ScoringFlow):
    flow_name: str = "memory_scoring_flow"
    scoring_domain: str = "memory"


@dataclass(frozen=True, slots=True)
class ForgettingScoringFlow(ScoringFlow):
    flow_name: str = "forgetting_scoring_flow"
    scoring_domain: str = "forgetting"


@dataclass(frozen=True, slots=True)
class HealthScoringFlow(ScoringFlow):
    flow_name: str = "health_scoring_flow"
    scoring_domain: str = "health"


@dataclass(frozen=True, slots=True)
class RiskScoringFlow(ScoringFlow):
    flow_name: str = "risk_scoring_flow"
    scoring_domain: str = "risk"


@dataclass(frozen=True, slots=True)
class ResourcePressureFlow(ScoringFlow):
    flow_name: str = "resource_pressure_flow"
    scoring_domain: str = "resource_pressure"


@dataclass(frozen=True, slots=True)
class EvolutionAssessmentFlow(ScoringFlow):
    flow_name: str = "evolution_assessment_flow"
    scoring_domain: str = "evolution_assessment"


@dataclass(frozen=True, slots=True)
class RegressionRiskFlow(ScoringFlow):
    flow_name: str = "regression_risk_flow"
    scoring_domain: str = "regression_risk"


@dataclass(frozen=True, slots=True)
class LearningAssessmentFlow(ScoringFlow):
    flow_name: str = "learning_assessment_flow"
    scoring_domain: str = "learning_assessment"


@dataclass(frozen=True, slots=True)
class AdaptationDecisionFlow(ScoringFlow):
    flow_name: str = "adaptation_decision_flow"
    scoring_domain: str = "adaptation_decision"
