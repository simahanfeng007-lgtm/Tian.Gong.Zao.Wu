"""Public projection safety plugin declaration."""

from __future__ import annotations

from dataclasses import dataclass, field

from .common import GovernanceArtifactBase, ensure_bool, ensure_ref_items


@dataclass(frozen=True)
class PublicProjectionSafetyPluginPlan(GovernanceArtifactBase):
    object_ref: str = "l6_phase5:public_projection_safety_plugin_plan"
    safety_hint_refs: tuple[str, ...] = field(default_factory=lambda: ("hint:l6_phase5_public_projection_safety",))
    minimal_disclosure_required: bool = True
    exposes_sensitive_payload: bool = False
    executes_redaction: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_items(self.safety_hint_refs, "PublicProjectionSafetyPluginPlan.safety_hint_refs", required=True)
        for field_name in ("minimal_disclosure_required", "exposes_sensitive_payload", "executes_redaction"):
            ensure_bool(getattr(self, field_name), f"PublicProjectionSafetyPluginPlan.{field_name}")
        if not self.minimal_disclosure_required or self.exposes_sensitive_payload or self.executes_redaction:
            raise ValueError("PublicProjectionSafetyPluginPlan is minimal-disclosure and non-executing")
