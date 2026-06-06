"""Humanized expression and refusal style hints for L6 phase4."""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l6_plugins.common._common import ensure_bool, ensure_no_live_or_sensitive_text, ensure_ref_items, ensure_ref_text
from ..common import CognitiveOutputKind, GovernanceReasonKind
from ..projection import CognitiveOutputBase


@dataclass(frozen=True)
class HumanizedRefusalStyleHint(CognitiveOutputBase):
    output_ref: str = "projection:l6_phase4_humanized_refusal_style_hint"
    output_kind: CognitiveOutputKind | str = CognitiveOutputKind.HINT
    plugin_ref: str = "l6_phase4:affective_reentry"
    governance_reason: GovernanceReasonKind | str | None = GovernanceReasonKind.BUDGET_EXHAUSTED
    governance_reason_ref: str = "policy:l6_phase4_governance_reason"
    style_examples: tuple[str, ...] = field(default_factory=lambda: ("summary:l6_phase4_humanized_low_energy_expression",))
    style_only: bool = True
    refusal_authority: bool = False
    synthetic_governance_reason: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.governance_reason is None:
            raise ValueError("humanized refusal style hint requires governance reason")
        object.__setattr__(self, "governance_reason", GovernanceReasonKind(self.governance_reason))
        ensure_ref_text(self.governance_reason_ref, "HumanizedRefusalStyleHint.governance_reason_ref")
        ensure_ref_items(self.style_examples, "HumanizedRefusalStyleHint.style_examples", required=True)
        for item in self.style_examples:
            ensure_no_live_or_sensitive_text(item, "HumanizedRefusalStyleHint.style_examples")
        ensure_bool(self.style_only, "HumanizedRefusalStyleHint.style_only")
        ensure_bool(self.refusal_authority, "HumanizedRefusalStyleHint.refusal_authority")
        ensure_bool(self.synthetic_governance_reason, "HumanizedRefusalStyleHint.synthetic_governance_reason")
        if not self.style_only or self.refusal_authority or self.synthetic_governance_reason:
            raise ValueError("humanized refusal hint must bind a real governance reason and stay style-only")
