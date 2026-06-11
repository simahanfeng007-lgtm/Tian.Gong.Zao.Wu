from __future__ import annotations
from dataclasses import dataclass
from .common import AdaptiveArtifactBase

@dataclass(frozen=True)
class SkillAcquisitionCandidate(AdaptiveArtifactBase):
    object_ref: str = "learning:l6_phase7_skill_acquisition_candidate"
    registered_skill: bool = False
    visible_capability: bool = False
    def __post_init__(self) -> None:
        super().__post_init__()
        if self.registered_skill or self.visible_capability:
            raise ValueError("SkillAcquisitionCandidate is not a registered or visible Skill")

@dataclass(frozen=True)
class SkillPatchCandidate(AdaptiveArtifactBase):
    object_ref: str = "learning:l6_phase7_skill_patch_candidate"
    writes_skill: bool = False
    def __post_init__(self) -> None:
        super().__post_init__()
        if self.writes_skill:
            raise ValueError("SkillPatchCandidate cannot write Skill data")

@dataclass(frozen=True)
class SkillVersionCandidate(AdaptiveArtifactBase):
    object_ref: str = "learning:l6_phase7_skill_version_candidate"
    published: bool = False

@dataclass(frozen=True)
class SkillValidationRequirement(AdaptiveArtifactBase):
    object_ref: str = "validation:l6_phase7_skill_validation_requirement"

@dataclass(frozen=True)
class SkillRollbackRequirement(AdaptiveArtifactBase):
    object_ref: str = "rollback:l6_phase7_skill_rollback_requirement"

@dataclass(frozen=True)
class SkillPublicProjectionCandidate(AdaptiveArtifactBase):
    object_ref: str = "public:l6_phase7_skill_public_projection_candidate"

class SkillAcquisitionCandidatePlugin:
    declaration_ref = "decl:l6_phase7_skill_acquisition_candidate_plugin"
