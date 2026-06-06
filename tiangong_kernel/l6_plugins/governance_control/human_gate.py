"""Human gate prompt-hint declarations for L6 phase5."""

from __future__ import annotations

from dataclasses import dataclass, field

from .common import GovernanceArtifactBase, ensure_bool, ensure_no_live_or_sensitive_text, ensure_ref_items, ensure_ref_text


@dataclass(frozen=True)
class HumanConfirmationPromptHint(GovernanceArtifactBase):
    object_ref: str = "hint:l6_phase5_human_confirmation_prompt"
    governance_reason_ref: str = "policy:l6_phase5_human_gate_reason"
    prompt_summary: str = "summary:minimal_confirmation_prompt_hint"
    ticket_issued: bool = False
    user_confirmation_claimed: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_text(self.governance_reason_ref, "HumanConfirmationPromptHint.governance_reason_ref")
        ensure_no_live_or_sensitive_text(self.prompt_summary, "HumanConfirmationPromptHint.prompt_summary")
        ensure_bool(self.ticket_issued, "HumanConfirmationPromptHint.ticket_issued")
        ensure_bool(self.user_confirmation_claimed, "HumanConfirmationPromptHint.user_confirmation_claimed")
        if self.ticket_issued or self.user_confirmation_claimed:
            raise ValueError("HumanConfirmationPromptHint cannot issue ticket or claim confirmation")


@dataclass(frozen=True)
class HumanGatePluginPlan(GovernanceArtifactBase):
    object_ref: str = "l6_phase5:human_gate_plugin_plan"
    prompt_hint_refs: tuple[str, ...] = field(default_factory=lambda: ("hint:l6_phase5_human_confirmation_prompt",))
    batches_when_safe: bool = True
    confirms_every_step: bool = False
    emotion_as_reason: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_items(self.prompt_hint_refs, "HumanGatePluginPlan.prompt_hint_refs", required=True)
        for field_name in ("batches_when_safe", "confirms_every_step", "emotion_as_reason"):
            ensure_bool(getattr(self, field_name), f"HumanGatePluginPlan.{field_name}")
        if not self.batches_when_safe or self.confirms_every_step or self.emotion_as_reason:
            raise ValueError("HumanGatePluginPlan must minimize safe interruptions")
