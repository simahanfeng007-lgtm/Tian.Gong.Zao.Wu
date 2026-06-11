"""ForgettingCandidateMindPlugin inert declaration and output skeleton."""

from __future__ import annotations

from dataclasses import dataclass, field

from .common import MindPluginDeclaration, MindPluginKind
from .mind_projection import ForgettingCandidate, MemoryDecayProjection


@dataclass(frozen=True)
class ForgettingCandidateMindPlugin:
    declaration: MindPluginDeclaration = field(default_factory=lambda: MindPluginDeclaration(
        plugin_ref="mind:forgetting_candidate_mind",
        plugin_kind=MindPluginKind.FORGETTING_CANDIDATE,
        summary="L6 phase3 mind:forgetting_candidate_mind inert mind helper declaration.",
        output_kind_refs=("projection:l6_phase3_mind", "score:l6_phase3_mind", "suggestion:l6_phase3_mind"),
    ))
    primary_output: ForgettingCandidate = field(default_factory=ForgettingCandidate)
    secondary_output: MemoryDecayProjection = field(default_factory=MemoryDecayProjection)

    @property
    def is_runtime(self) -> bool:
        return self.declaration.is_runtime

    @property
    def calls_model_or_tool(self) -> bool:
        return self.declaration.calls_model or self.declaration.calls_tool

    @property
    def mutates_state(self) -> bool:
        return self.declaration.writes_l2_fact or self.declaration.writes_memory or self.declaration.writes_audit or self.declaration.charges_budget
