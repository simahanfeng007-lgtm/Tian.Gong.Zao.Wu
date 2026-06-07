"""L6 phase3 mind interoperation matrix.

Cross-plugin collaboration is represented through allowed envelopes and host
mediated paths only; no plugin-to-plugin direct linking is represented here.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l6_plugins.common._common import L6_COMMON_SCHEMA_VERSION, ensure_bool, ensure_ref_items, ensure_ref_text, ensure_schema_version

from .common import MindCollaborationChannel


@dataclass(frozen=True)
class MindInteroperationRule:
    rule_ref: str
    source_plugin_ref: str
    target_plugin_ref: str
    channel: MindCollaborationChannel | str
    summary_ref: str = "summary:l6_mind_interoperation"
    requires_l3_l5_reschedule: bool = False
    direct_import_allowed: bool = False
    direct_call_allowed: bool = False
    shared_mutable_state_allowed: bool = False
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for field_name in ("rule_ref", "source_plugin_ref", "target_plugin_ref", "summary_ref"):
            ensure_ref_text(getattr(self, field_name), f"MindInteroperationRule.{field_name}")
        object.__setattr__(self, "channel", MindCollaborationChannel(self.channel))
        for field_name in ("requires_l3_l5_reschedule", "direct_import_allowed", "direct_call_allowed", "shared_mutable_state_allowed"):
            ensure_bool(getattr(self, field_name), f"MindInteroperationRule.{field_name}")
        if self.direct_import_allowed or self.direct_call_allowed or self.shared_mutable_state_allowed:
            raise ValueError("Mind interoperation cannot allow direct import, direct call, or shared mutable state")
        ensure_schema_version(self.schema_version)


@dataclass(frozen=True)
class MindInteroperationMatrix:
    matrix_ref: str = "mind:l6_phase3_interoperation_matrix"
    event_rule_refs: tuple[str, ...] = field(default_factory=lambda: ("mind:event_affective_change", "mind:event_goal_change", "mind:event_attention_shift", "mind:event_reflection_report", "mind:event_learning_need", "mind:event_pollution_risk"))
    state_projection_rule_refs: tuple[str, ...] = field(default_factory=lambda: ("mind:projection_context", "mind:projection_belief", "mind:projection_world", "mind:projection_goal", "mind:projection_attention", "mind:projection_affective", "mind:projection_memory", "mind:projection_pollution"))
    handoff_rule_refs: tuple[str, ...] = field(default_factory=lambda: ("handoff:self_reflection_to_learning", "handoff:memory_to_forgetting", "handoff:attention_to_goal", "handoff:affective_to_pollution", "handoff:learning_to_phase4"))
    public_projection_rule_refs: tuple[str, ...] = field(default_factory=lambda: ("public:plugin_health", "public:plugin_output", "public:plugin_risk", "public:plugin_degradation", "public:plugin_test"))
    l3_l5_reschedule_refs: tuple[str, ...] = field(default_factory=lambda: ("l3:model_need", "l3:tool_need", "l5:state_write_need", "l5:memory_write_need", "l5:audit_need", "l5:budget_need", "l5:credential_need", "l5:migration_need"))
    rules: tuple[MindInteroperationRule, ...] = field(default_factory=tuple)
    direct_import_allowed: bool = False
    direct_call_allowed: bool = False
    shared_mutable_state_allowed: bool = False
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.matrix_ref, "MindInteroperationMatrix.matrix_ref")
        for field_name in ("event_rule_refs", "state_projection_rule_refs", "handoff_rule_refs", "public_projection_rule_refs", "l3_l5_reschedule_refs"):
            ensure_ref_items(getattr(self, field_name), f"MindInteroperationMatrix.{field_name}", required=True)
        for rule in self.rules:
            if not isinstance(rule, MindInteroperationRule):
                raise ValueError("MindInteroperationMatrix.rules must contain MindInteroperationRule")
        for field_name in ("direct_import_allowed", "direct_call_allowed", "shared_mutable_state_allowed"):
            ensure_bool(getattr(self, field_name), f"MindInteroperationMatrix.{field_name}")
        if self.direct_import_allowed or self.direct_call_allowed or self.shared_mutable_state_allowed:
            raise ValueError("Mind interoperation matrix cannot allow direct plugin coupling")
        ensure_schema_version(self.schema_version)

    @property
    def event_projection_handoff_only_collaboration(self) -> bool:
        return not (self.direct_import_allowed or self.direct_call_allowed or self.shared_mutable_state_allowed)


def default_mind_interoperation_matrix() -> MindInteroperationMatrix:
    rules = (
        MindInteroperationRule("mind:rule_self_reflection_learning", "mind:self_reflection_mind", "mind:learning_evolution_mind", MindCollaborationChannel.HANDOFF),
        MindInteroperationRule("mind:rule_memory_forgetting", "mind:memory_candidate_mind", "mind:forgetting_candidate_mind", MindCollaborationChannel.HANDOFF),
        MindInteroperationRule("mind:rule_attention_goal", "mind:attention_mind", "mind:goal_mind", MindCollaborationChannel.HANDOFF),
        MindInteroperationRule("mind:rule_affective_pollution", "mind:affective_mind", "mind:pollution_defense", MindCollaborationChannel.EVENT),
        MindInteroperationRule("mind:rule_learning_phase4", "mind:learning_evolution_mind", "mind:phase4", MindCollaborationChannel.HANDOFF, requires_l3_l5_reschedule=True),
    )
    return MindInteroperationMatrix(rules=rules)
