"""L6 phase4 interoperation matrix for cognitive continuity plugins."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l6_plugins.common._common import L6_COMMON_SCHEMA_VERSION, ensure_bool, ensure_ref_items, ensure_ref_text, ensure_schema_version, stable_digest


class Phase4CollaborationChannel(str, Enum):
    EVENT = "event"
    STATE_PROJECTION = "state_projection"
    HANDOFF = "handoff"
    PUBLIC_PROJECTION = "public_projection"
    COGNITIVE_REENTRY = "cognitive_reentry"


@dataclass(frozen=True)
class Phase4InteroperationRule:
    rule_ref: str
    source_plugin_ref: str
    target_plugin_ref: str
    channel: Phase4CollaborationChannel | str
    output_refs: tuple[str, ...]
    host_mediated_only: bool = True
    direct_import_allowed: bool = False
    direct_call_allowed: bool = False
    shared_mutable_state_allowed: bool = False
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.rule_ref, "Phase4InteroperationRule.rule_ref")
        ensure_ref_text(self.source_plugin_ref, "Phase4InteroperationRule.source_plugin_ref")
        ensure_ref_text(self.target_plugin_ref, "Phase4InteroperationRule.target_plugin_ref")
        object.__setattr__(self, "channel", Phase4CollaborationChannel(self.channel))
        ensure_ref_items(self.output_refs, "Phase4InteroperationRule.output_refs", required=True)
        for field_name in ("host_mediated_only", "direct_import_allowed", "direct_call_allowed", "shared_mutable_state_allowed"):
            ensure_bool(getattr(self, field_name), f"Phase4InteroperationRule.{field_name}")
        if not self.host_mediated_only or self.direct_import_allowed or self.direct_call_allowed or self.shared_mutable_state_allowed:
            raise ValueError("Phase4 interoperation must use host-mediated projection/event/handoff/reentry only")
        ensure_schema_version(self.schema_version)

    @property
    def digest(self) -> str:
        return stable_digest(self)


def default_phase4_interoperation_matrix() -> tuple[Phase4InteroperationRule, ...]:
    return (
        Phase4InteroperationRule("l6:phase4_context_to_memory", "l6_phase4:context_continuity", "l6_phase4:memory_candidate", Phase4CollaborationChannel.STATE_PROJECTION, ("projection:l6_phase4_context_continuity",)),
        Phase4InteroperationRule("l6:phase4_memory_to_forgetting", "l6_phase4:memory_candidate", "l6_phase4:forgetting_candidate", Phase4CollaborationChannel.HANDOFF, ("projection:l6_phase4_memory_recall_candidate",)),
        Phase4InteroperationRule("l6:phase4_affective_to_memory", "l6_phase4:affective_reentry", "l6_phase4:memory_candidate", Phase4CollaborationChannel.STATE_PROJECTION, ("projection:l6_phase4_affective_memory_weight_hint",)),
        Phase4InteroperationRule("l6:phase4_affective_to_context", "l6_phase4:affective_reentry", "l6_phase4:context_continuity", Phase4CollaborationChannel.STATE_PROJECTION, ("projection:l6_phase4_affective_context_modulation",)),
        Phase4InteroperationRule("l6:phase4_belief_world_to_reentry", "l6_phase4:belief_world_review", "l6_phase4:cognitive_reentry_fusion", Phase4CollaborationChannel.COGNITIVE_REENTRY, ("projection:l6_phase4_belief_world_review",)),
        Phase4InteroperationRule("l6:phase4_learning_to_reentry", "l6_phase4:self_reflection_learning", "l6_phase4:cognitive_reentry_fusion", Phase4CollaborationChannel.HANDOFF, ("projection:l6_phase4_self_reflection_learning_candidate",)),
    )
