"""MindFusionScoringPlugin inert declaration and output skeleton."""

from __future__ import annotations

from dataclasses import dataclass, field

from .common import MindPluginDeclaration, MindPluginKind
from .mind_projection import MindScoreVector, WeightedDecisionHint


@dataclass(frozen=True)
class MindFusionScoringPlugin:
    declaration: MindPluginDeclaration = field(default_factory=lambda: MindPluginDeclaration(
        plugin_ref="mind:mind_fusion_scoring",
        plugin_kind=MindPluginKind.FUSION_SCORING,
        summary="L6 phase3 mind:mind_fusion_scoring inert mind helper declaration.",
        output_kind_refs=("projection:l6_phase3_mind", "score:l6_phase3_mind", "suggestion:l6_phase3_mind"),
    ))
    primary_output: MindScoreVector = field(default_factory=MindScoreVector)
    secondary_output: WeightedDecisionHint = field(default_factory=WeightedDecisionHint)

    @property
    def is_runtime(self) -> bool:
        return self.declaration.is_runtime

    @property
    def calls_model_or_tool(self) -> bool:
        return self.declaration.calls_model or self.declaration.calls_tool

    @property
    def mutates_state(self) -> bool:
        return self.declaration.writes_l2_fact or self.declaration.writes_memory or self.declaration.writes_audit or self.declaration.charges_budget
