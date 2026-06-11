"""L4 到 L5 自我进化边界与许可需求。"""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from ._common import L4_EXECUTION_CLOSURE_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_short_text, ensure_true


@dataclass(frozen=True, slots=True)
class L4ToL5SelfEvolutionBoundaryRequirement:
    """L4 到 L5 自我进化边界需求。"""

    requirement_ref: TypedRef
    candidate_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    validation_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    summary: str = ""
    requirement_only: bool = True
    grants_permission: bool = False
    applies_patch: bool = False
    hot_switches: bool = False
    requires_human_confirmation_when_required: bool = field(default=True)
    schema_version: str = L4_EXECUTION_CLOSURE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_short_text(self.summary, "L4ToL5SelfEvolutionBoundaryRequirement.summary")
        ensure_true(self.requirement_only, "L4ToL5SelfEvolutionBoundaryRequirement.requirement_only")
        ensure_false(self.grants_permission, "L4ToL5SelfEvolutionBoundaryRequirement.grants_permission")
        ensure_false(self.applies_patch, "L4ToL5SelfEvolutionBoundaryRequirement.applies_patch")
        ensure_false(self.hot_switches, "L4ToL5SelfEvolutionBoundaryRequirement.hot_switches")
        ensure_true(self.requires_human_confirmation_when_required, "L4ToL5SelfEvolutionBoundaryRequirement.requires_human_confirmation_when_required")
        ensure_schema_version(self.schema_version, "L4ToL5SelfEvolutionBoundaryRequirement.schema_version")


@dataclass(frozen=True, slots=True)
class L4ToL5SelfEvolutionPermitRequirement:
    """L4 到 L5 自我进化许可需求。"""

    requirement_ref: TypedRef
    commit_intent_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    activation_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    rollback_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    requirement_only: bool = True
    grants_commit_permission: bool = False
    grants_hot_switch_permission: bool = False
    grants_rollback_permission: bool = False
    schema_version: str = L4_EXECUTION_CLOSURE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_true(self.requirement_only, "L4ToL5SelfEvolutionPermitRequirement.requirement_only")
        ensure_false(self.grants_commit_permission, "L4ToL5SelfEvolutionPermitRequirement.grants_commit_permission")
        ensure_false(self.grants_hot_switch_permission, "L4ToL5SelfEvolutionPermitRequirement.grants_hot_switch_permission")
        ensure_false(self.grants_rollback_permission, "L4ToL5SelfEvolutionPermitRequirement.grants_rollback_permission")
        ensure_schema_version(self.schema_version, "L4ToL5SelfEvolutionPermitRequirement.schema_version")
