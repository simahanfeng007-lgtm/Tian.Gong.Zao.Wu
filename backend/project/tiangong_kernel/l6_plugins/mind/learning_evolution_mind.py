"""LearningEvolutionMindPlugin inert declaration and output skeleton."""

from __future__ import annotations

from dataclasses import dataclass, field

from .common import MindPluginDeclaration, MindPluginKind
from .mind_projection import LearningNeedProjection, RepairSuggestion


@dataclass(frozen=True)
class LearningEvolutionMindPlugin:
    declaration: MindPluginDeclaration = field(default_factory=lambda: MindPluginDeclaration(
        plugin_ref="mind:learning_evolution_mind",
        plugin_kind=MindPluginKind.LEARNING_EVOLUTION,
        summary="L6 phase3 mind:learning_evolution_mind inert mind helper declaration.",
        output_kind_refs=("projection:l6_phase3_mind", "score:l6_phase3_mind", "suggestion:l6_phase3_mind"),
    ))
    primary_output: LearningNeedProjection = field(default_factory=LearningNeedProjection)
    secondary_output: RepairSuggestion = field(default_factory=RepairSuggestion)

    @property
    def is_runtime(self) -> bool:
        return self.declaration.is_runtime

    @property
    def calls_model_or_tool(self) -> bool:
        return self.declaration.calls_model or self.declaration.calls_tool

    @property
    def mutates_state(self) -> bool:
        return self.declaration.writes_l2_fact or self.declaration.writes_memory or self.declaration.writes_audit or self.declaration.charges_budget
