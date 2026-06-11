"""Binding between affective expression and real governance reasons."""

from __future__ import annotations

from dataclasses import dataclass

from tiangong_kernel.l6_plugins.common._common import L6_COMMON_SCHEMA_VERSION, ensure_bool, ensure_ref_text, ensure_schema_version, stable_digest
from ..common import GovernanceReasonKind


@dataclass(frozen=True)
class AffectiveGovernanceBinding:
    binding_ref: str = "projection:l6_phase4_affective_governance_binding"
    affective_projection_ref: str = "projection:l6_phase4_affective_projection"
    governance_reason: GovernanceReasonKind | str | None = GovernanceReasonKind.BUDGET_EXHAUSTED
    governance_reason_ref: str = "policy:l6_phase4_governance_reason"
    allows_refusal_expression: bool = True
    creates_governance_reason: bool = False
    bypasses_l5: bool = False
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.binding_ref, "AffectiveGovernanceBinding.binding_ref")
        ensure_ref_text(self.affective_projection_ref, "AffectiveGovernanceBinding.affective_projection_ref")
        if self.governance_reason is None:
            raise ValueError("affective governance binding requires governance reason")
        object.__setattr__(self, "governance_reason", GovernanceReasonKind(self.governance_reason))
        ensure_ref_text(self.governance_reason_ref, "AffectiveGovernanceBinding.governance_reason_ref")
        ensure_bool(self.allows_refusal_expression, "AffectiveGovernanceBinding.allows_refusal_expression")
        ensure_bool(self.creates_governance_reason, "AffectiveGovernanceBinding.creates_governance_reason")
        ensure_bool(self.bypasses_l5, "AffectiveGovernanceBinding.bypasses_l5")
        if self.creates_governance_reason or self.bypasses_l5:
            raise ValueError("affective binding cannot invent governance reasons or bypass L5")
        ensure_schema_version(self.schema_version)

    @property
    def digest(self) -> str:
        return stable_digest(self)
