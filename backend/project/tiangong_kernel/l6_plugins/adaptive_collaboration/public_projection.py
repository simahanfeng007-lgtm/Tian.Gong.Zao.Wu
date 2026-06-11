from __future__ import annotations
from dataclasses import dataclass, field
from .common import AdaptiveArtifactBase, AdaptivePrivacyClass, AdaptiveRedactionState

@dataclass(frozen=True)
class AdaptivePublicProjection(AdaptiveArtifactBase):
    object_ref: str = "public:l6_phase7_adaptive_projection"
    privacy_class: AdaptivePrivacyClass | str = AdaptivePrivacyClass.PUBLIC_SUMMARY
    redaction_state: AdaptiveRedactionState | str = AdaptiveRedactionState.APPLIED_SUMMARY_ONLY
    public_summary: str = "summary:l6_phase7_adaptive_public_projection"
    exposes_full_prompt: bool = False
    exposes_full_context: bool = False
    exposes_memory_body: bool = False
    exposes_user_profile: bool = False
    exposes_affective_profile: bool = False
    exposes_code_patch: bool = False
    exposes_file_path: bool = False
    exposes_provider_locator: bool = False
    exposes_secret: bool = False
    exposes_execution_plan: bool = False
    exposes_complete_evidence_chain: bool = False
    exposes_tool_schema: bool = False
    exposes_model_client: bool = False
    exposes_credential_handle_detail: bool = False
    exposes_exploit_detail: bool = False
    def __post_init__(self) -> None:
        super().__post_init__()
        leaks = (
            self.exposes_full_prompt, self.exposes_full_context, self.exposes_memory_body, self.exposes_user_profile,
            self.exposes_affective_profile, self.exposes_code_patch, self.exposes_file_path, self.exposes_provider_locator,
            self.exposes_secret, self.exposes_execution_plan, self.exposes_complete_evidence_chain, self.exposes_tool_schema,
            self.exposes_model_client, self.exposes_credential_handle_detail, self.exposes_exploit_detail,
        )
        if any(leaks):
            raise ValueError("AdaptivePublicProjection must use minimal disclosure")

@dataclass(frozen=True)
class LearningPublicSummary(AdaptiveArtifactBase):
    object_ref: str = "public:l6_phase7_learning_public_summary"

@dataclass(frozen=True)
class RepairPublicSummary(AdaptiveArtifactBase):
    object_ref: str = "public:l6_phase7_repair_public_summary"

@dataclass(frozen=True)
class CollaborationPublicSummary(AdaptiveArtifactBase):
    object_ref: str = "public:l6_phase7_collaboration_public_summary"

@dataclass(frozen=True)
class AdaptiveRedactionReport(AdaptiveArtifactBase):
    object_ref: str = "redaction:l6_phase7_adaptive_redaction_report"

class AdaptivePublicProjectionPlugin:
    declaration_ref = "decl:l6_phase7_adaptive_public_projection_plugin"
