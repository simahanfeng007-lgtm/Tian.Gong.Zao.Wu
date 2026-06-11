"""GoalMindPlugin inert declaration and output skeleton."""

from __future__ import annotations

from dataclasses import dataclass, field

from .common import MindPluginDeclaration, MindPluginKind
from .mind_projection import GoalProjection, GoalPriorityScore


@dataclass(frozen=True)
class GoalMindPlugin:
    declaration: MindPluginDeclaration = field(default_factory=lambda: MindPluginDeclaration(
        plugin_ref="mind:goal_mind",
        plugin_kind=MindPluginKind.GOAL,
        summary="L6 phase3 mind:goal_mind inert mind helper declaration.",
        output_kind_refs=("projection:l6_phase3_mind", "score:l6_phase3_mind", "suggestion:l6_phase3_mind"),
    ))
    primary_output: GoalProjection = field(default_factory=GoalProjection)
    secondary_output: GoalPriorityScore = field(default_factory=GoalPriorityScore)

    @property
    def is_runtime(self) -> bool:
        return self.declaration.is_runtime

    @property
    def calls_model_or_tool(self) -> bool:
        return self.declaration.calls_model or self.declaration.calls_tool

    @property
    def mutates_state(self) -> bool:
        return self.declaration.writes_l2_fact or self.declaration.writes_memory or self.declaration.writes_audit or self.declaration.charges_budget
