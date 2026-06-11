"""Privacy redaction and public projection safety declarations."""

from __future__ import annotations

from dataclasses import dataclass, field

from .common import GovernanceArtifactBase, RedactionState, PrivacyClass, ensure_bool, ensure_ref_items, ensure_score


@dataclass(frozen=True)
class PrivacyRiskProjection(GovernanceArtifactBase):
    object_ref: str = "projection:l6_phase5_privacy_risk"
    privacy_risk_score: float = 0.5
    data_access_granted: bool = False
    minimal_summary_only: bool = True

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_score(self.privacy_risk_score, "PrivacyRiskProjection.privacy_risk_score")
        ensure_bool(self.data_access_granted, "PrivacyRiskProjection.data_access_granted")
        ensure_bool(self.minimal_summary_only, "PrivacyRiskProjection.minimal_summary_only")
        if self.data_access_granted or not self.minimal_summary_only:
            raise ValueError("PrivacyRiskProjection is not data access")


@dataclass(frozen=True)
class RedactionRequirement(GovernanceArtifactBase):
    object_ref: str = "requirement:l6_phase5_redaction"
    redaction_required: bool = True
    redaction_executed: bool = False
    blocked_field_refs: tuple[str, ...] = field(default_factory=lambda: ("policy:prompt", "policy:private_profile", "policy:credential_locator"))

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_bool(self.redaction_required, "RedactionRequirement.redaction_required")
        ensure_bool(self.redaction_executed, "RedactionRequirement.redaction_executed")
        ensure_ref_items(self.blocked_field_refs, "RedactionRequirement.blocked_field_refs", required=True)
        if not self.redaction_required or self.redaction_executed:
            raise ValueError("RedactionRequirement is a requirement, not redaction execution")


@dataclass(frozen=True)
class PublicProjectionSafetyHint(GovernanceArtifactBase):
    object_ref: str = "hint:l6_phase5_public_projection_safety"
    redaction_state: RedactionState | str = RedactionState.APPLIED_SUMMARY_ONLY
    privacy_class: PrivacyClass | str = PrivacyClass.PUBLIC_SUMMARY
    exposes_prompt: bool = False
    exposes_context: bool = False
    exposes_memory_body: bool = False
    exposes_user_profile: bool = False
    exposes_affective_profile: bool = False
    exposes_file_path: bool = False
    exposes_provider_locator: bool = False
    exposes_credential_material: bool = False
    exposes_execution_plan: bool = False
    exposes_full_evidence_chain: bool = False
    exposes_tool_schema: bool = False
    exposes_model_client: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        bool_fields = (
            "exposes_prompt", "exposes_context", "exposes_memory_body", "exposes_user_profile", "exposes_affective_profile",
            "exposes_file_path", "exposes_provider_locator", "exposes_credential_material", "exposes_execution_plan",
            "exposes_full_evidence_chain", "exposes_tool_schema", "exposes_model_client",
        )
        for field_name in bool_fields:
            ensure_bool(getattr(self, field_name), f"PublicProjectionSafetyHint.{field_name}")
        if any(getattr(self, field_name) for field_name in bool_fields):
            raise ValueError("PublicProjectionSafetyHint blocks sensitive disclosure")


@dataclass(frozen=True)
class SensitiveFieldBlockHint(GovernanceArtifactBase):
    object_ref: str = "hint:l6_phase5_sensitive_field_block"
    blocked_field_refs: tuple[str, ...] = field(default_factory=lambda: ("policy:prompt", "policy:memory_body", "policy:provider_locator"))
    block_is_execution: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_items(self.blocked_field_refs, "SensitiveFieldBlockHint.blocked_field_refs", required=True)
        ensure_bool(self.block_is_execution, "SensitiveFieldBlockHint.block_is_execution")
        if self.block_is_execution:
            raise ValueError("Sensitive field block hint is not redaction execution")


@dataclass(frozen=True)
class MinimalDisclosureRequirement(GovernanceArtifactBase):
    object_ref: str = "requirement:l6_phase5_minimal_disclosure"
    allows_summary: bool = True
    allows_digest: bool = True
    allows_full_payload: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        for field_name in ("allows_summary", "allows_digest", "allows_full_payload"):
            ensure_bool(getattr(self, field_name), f"MinimalDisclosureRequirement.{field_name}")
        if not self.allows_summary or not self.allows_digest or self.allows_full_payload:
            raise ValueError("Minimal disclosure must be summary/digest only")


@dataclass(frozen=True)
class PublicProjectionRedactionReport(GovernanceArtifactBase):
    object_ref: str = "report:l6_phase5_public_projection_redaction"
    redacted_field_refs: tuple[str, ...] = field(default_factory=lambda: ("policy:prompt", "policy:credential_locator"))
    complete_payload_public: bool = False
    redaction_state: RedactionState | str = RedactionState.APPLIED_SUMMARY_ONLY

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_items(self.redacted_field_refs, "PublicProjectionRedactionReport.redacted_field_refs", required=True)
        ensure_bool(self.complete_payload_public, "PublicProjectionRedactionReport.complete_payload_public")
        if self.complete_payload_public:
            raise ValueError("Public redaction report cannot expose complete payload")


@dataclass(frozen=True)
class PublicLeakRiskProjection(GovernanceArtifactBase):
    object_ref: str = "projection:l6_phase5_public_leak_risk"
    leak_risk_score: float = 0.35
    full_payload_exposure_possible: bool = False
    minimal_disclosure_required: bool = True

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_score(self.leak_risk_score, "PublicLeakRiskProjection.leak_risk_score")
        ensure_bool(self.full_payload_exposure_possible, "PublicLeakRiskProjection.full_payload_exposure_possible")
        ensure_bool(self.minimal_disclosure_required, "PublicLeakRiskProjection.minimal_disclosure_required")
        if self.full_payload_exposure_possible or not self.minimal_disclosure_required:
            raise ValueError("Public leak risk projection must enforce minimal disclosure")
