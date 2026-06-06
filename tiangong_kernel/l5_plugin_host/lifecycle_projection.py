"""Safe public projection for L5 phase 4 lifecycle and mount declarations."""

from __future__ import annotations

from dataclasses import dataclass, field

from ._common import L5_PLUGIN_HOST_SCHEMA_VERSION, ensure_ref_items, ensure_ref_text, ensure_schema_version, ensure_short_text
from .lifecycle_declaration import PluginLifecycleStateMachine, PluginMountDeclaration, is_live_entry_text, lifecycle_declaration_digest
from .self_healing_declaration import PluginRecoveryPlanDeclaration, PluginSelfHealingDeclaration


@dataclass(frozen=True, slots=True)
class PluginLifecycleProjectionSummary:
    summary_ref: str
    summary_kind: str
    summary_text: str = ""
    risk_tags: tuple[str, ...] = field(default_factory=tuple)
    evidence_refs: tuple[str, ...] = field(default_factory=tuple)
    trace_ref: str = ""
    responsibility_chain_ref: str = ""
    schema_version: str = L5_PLUGIN_HOST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.summary_ref, "PluginLifecycleProjectionSummary.summary_ref")
        ensure_short_text(self.summary_kind, "PluginLifecycleProjectionSummary.summary_kind", 64)
        ensure_short_text(self.summary_text, "PluginLifecycleProjectionSummary.summary_text")
        ensure_ref_items(self.risk_tags, "PluginLifecycleProjectionSummary.risk_tags")
        ensure_ref_items(self.evidence_refs, "PluginLifecycleProjectionSummary.evidence_refs")
        ensure_ref_text(self.trace_ref, "PluginLifecycleProjectionSummary.trace_ref", required=False)
        ensure_ref_text(self.responsibility_chain_ref, "PluginLifecycleProjectionSummary.responsibility_chain_ref", required=False)
        ensure_schema_version(self.schema_version, "PluginLifecycleProjectionSummary.schema_version")


@dataclass(frozen=True, slots=True)
class PluginLifecyclePublicProjection:
    projection_ref: str
    lifecycle_summaries: tuple[PluginLifecycleProjectionSummary, ...] = field(default_factory=tuple)
    mount_summaries: tuple[PluginLifecycleProjectionSummary, ...] = field(default_factory=tuple)
    self_healing_summaries: tuple[PluginLifecycleProjectionSummary, ...] = field(default_factory=tuple)
    conflict_summary_refs: tuple[str, ...] = field(default_factory=tuple)
    quality_gate_summary_ref: str = ""
    redacted_evidence_refs: tuple[str, ...] = field(default_factory=tuple)
    boundary_refs: tuple[str, ...] = field(default_factory=tuple)
    policy_refs: tuple[str, ...] = field(default_factory=tuple)
    switch_readiness_summary_ref: str = ""
    pre_switch_checkpoint_summary_ref: str = ""
    post_switch_observation_summary_ref: str = ""
    switch_rollback_route_summary_ref: str = ""
    compatibility_check_summary_ref: str = ""
    breaking_change_check_summary_ref: str = ""
    actor_ref: str = ""
    scope_ref: str = ""
    trace_ref: str = ""
    policy_ref: str = ""
    approval_ref: str = ""
    accountability_ref: str = ""
    provenance_refs: tuple[str, ...] = field(default_factory=tuple)
    tamper_evidence_ref: str = ""
    event_kind_refs: tuple[str, ...] = field(default_factory=tuple)
    projection_digest: str = ""
    schema_version: str = L5_PLUGIN_HOST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.projection_ref, "PluginLifecyclePublicProjection.projection_ref")
        for seq_name in ("lifecycle_summaries", "mount_summaries", "self_healing_summaries"):
            for item in getattr(self, seq_name):
                if not isinstance(item, PluginLifecycleProjectionSummary):
                    raise ValueError(f"PluginLifecyclePublicProjection.{seq_name} must contain PluginLifecycleProjectionSummary")
        for name in ("conflict_summary_refs", "redacted_evidence_refs", "boundary_refs", "policy_refs", "provenance_refs", "event_kind_refs"):
            ensure_ref_items(getattr(self, name), f"PluginLifecyclePublicProjection.{name}")
        for name in (
            "quality_gate_summary_ref", "switch_readiness_summary_ref", "pre_switch_checkpoint_summary_ref",
            "post_switch_observation_summary_ref", "switch_rollback_route_summary_ref", "compatibility_check_summary_ref",
            "breaking_change_check_summary_ref", "actor_ref", "scope_ref", "trace_ref", "policy_ref", "approval_ref",
            "accountability_ref", "tamper_evidence_ref",
        ):
            ensure_ref_text(getattr(self, name), f"PluginLifecyclePublicProjection.{name}", required=False)
        ensure_schema_version(self.schema_version, "PluginLifecyclePublicProjection.schema_version")
        if not self.projection_digest:
            object.__setattr__(self, "projection_digest", lifecycle_declaration_digest(self))


def projection_text_is_safe(value: str) -> bool:
    lowered = value.lower()
    if any(term in lowered for term in ("raw_value", "token_value", "secret_value", "api_key_value", "password_value", "credential_handle", "decrypted_value", "env_value", "file_path_to_secret")):
        return False
    return not is_live_entry_text(value)


@dataclass(frozen=True, slots=True)
class PluginLifecyclePublicProjectionBuilder:
    builder_ref: str
    schema_version: str = L5_PLUGIN_HOST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.builder_ref, "PluginLifecyclePublicProjectionBuilder.builder_ref")
        ensure_schema_version(self.schema_version, "PluginLifecyclePublicProjectionBuilder.schema_version")

    def build_projection(
        self,
        state_machine: PluginLifecycleStateMachine,
        mount_declarations: tuple[PluginMountDeclaration, ...] = tuple(),
        self_healing_declarations: tuple[PluginSelfHealingDeclaration, ...] = tuple(),
        recovery_plans: tuple[PluginRecoveryPlanDeclaration, ...] = tuple(),
        conflict_summary_refs: tuple[str, ...] = tuple(),
    ) -> PluginLifecyclePublicProjection:
        lifecycle_summary = PluginLifecycleProjectionSummary(
            summary_ref=f"lifecycle_summary:{state_machine.state_machine_ref}",
            summary_kind="lifecycle summary",
            summary_text=f"{len(state_machine.transition_rules)} declaration-only transition rules",
            evidence_refs=state_machine.evidence_refs,
            trace_ref=state_machine.trace_ref,
            responsibility_chain_ref=state_machine.responsibility_chain_ref,
        )
        mount_summaries = tuple(
            PluginLifecycleProjectionSummary(
                summary_ref=f"mount_summary:{item.mount_decl_ref}",
                summary_kind="mount summary",
                summary_text="declaration-only mount surface",
                evidence_refs=item.evidence_refs,
                trace_ref=item.trace_ref,
                responsibility_chain_ref=item.responsibility_chain_ref,
            )
            for item in mount_declarations
        )
        self_healing_summaries = tuple(
            PluginLifecycleProjectionSummary(
                summary_ref=f"self_healing_summary:{item.self_healing_decl_ref}",
                summary_kind="self-healing summary",
                summary_text="declaration-only self-healing chain",
                risk_tags=(item.severity,),
                evidence_refs=item.evidence_refs,
                trace_ref=item.trace_ref,
                responsibility_chain_ref=item.responsibility_chain_ref,
            )
            for item in self_healing_declarations
        ) + tuple(
            PluginLifecycleProjectionSummary(
                summary_ref=f"recovery_plan_summary:{item.recovery_plan_ref}",
                summary_kind="recovery plan summary",
                summary_text="declaration-only recovery plan",
                risk_tags=item.risk_tags,
                evidence_refs=item.evidence_refs,
                responsibility_chain_ref=item.responsibility_chain_ref,
            )
            for item in recovery_plans
        )
        redacted_evidence_refs = tuple(sorted(set(state_machine.evidence_refs + tuple(ref for item in mount_declarations for ref in item.evidence_refs))))
        boundary_refs = tuple(sorted(set(item.boundary_ref for item in mount_declarations if item.boundary_ref)))
        policy_refs = tuple(sorted(set(state_machine.allowed_transition_refs + tuple(ref for item in mount_declarations for ref in item.policy_refs))))
        return PluginLifecyclePublicProjection(
            projection_ref=f"lifecycle_projection:{state_machine.state_machine_ref}",
            lifecycle_summaries=(lifecycle_summary,),
            mount_summaries=mount_summaries,
            self_healing_summaries=self_healing_summaries,
            conflict_summary_refs=conflict_summary_refs,
            quality_gate_summary_ref="quality_gate:l5_phase4",
            redacted_evidence_refs=redacted_evidence_refs,
            boundary_refs=boundary_refs,
            policy_refs=policy_refs,
            switch_readiness_summary_ref="summary:switch_readiness_decl_only",
            pre_switch_checkpoint_summary_ref="summary:pre_switch_checkpoint_decl_only",
            post_switch_observation_summary_ref="summary:post_switch_observation_decl_only",
            switch_rollback_route_summary_ref="summary:switch_rollback_route_decl_only",
            compatibility_check_summary_ref="summary:compatibility_check_decl_only",
            breaking_change_check_summary_ref="summary:breaking_change_check_decl_only",
            actor_ref=state_machine.actor_ref,
            scope_ref=state_machine.scope_ref,
            trace_ref=state_machine.trace_ref,
            policy_ref=state_machine.policy_ref,
            approval_ref=state_machine.approval_ref,
            accountability_ref=state_machine.accountability_ref,
            provenance_refs=state_machine.provenance_refs,
            tamper_evidence_ref=state_machine.tamper_evidence_ref,
            event_kind_refs=("event:lifecycle_public_projection",),
        )


__all__ = (
    "PluginLifecycleProjectionSummary",
    "PluginLifecyclePublicProjection",
    "PluginLifecyclePublicProjectionBuilder",
    "projection_text_is_safe",
)
