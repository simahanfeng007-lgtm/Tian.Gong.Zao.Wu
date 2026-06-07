"""L6 state projection contract declarations.

L6 may read projections or emit projection proposals, never write L2 facts or
mutate memory, forgetting, affective, budget, audit, credential, or policy state.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from ._common import L6_COMMON_SCHEMA_VERSION, ensure_ref_items, ensure_ref_text, ensure_schema_version


class L6StateProjectionMode(str, Enum):
    READ_PROJECTION = "read_projection"
    EMIT_PROJECTION = "emit_projection"
    EMIT_PROPOSAL = "emit_proposal"
    EMIT_EVENT = "emit_event"


@dataclass(frozen=True, slots=True)
class L6StateProjectionContract:
    projection_contract_ref: str = "projection:l6_state_projection_contract"
    source_state_projection_refs: tuple[str, ...] = field(default_factory=lambda: ("projection:l2_read_only_projection_ref",))
    output_projection_refs: tuple[str, ...] = field(default_factory=lambda: ("projection:l6_output_projection_ref",))
    mode: L6StateProjectionMode | str = L6StateProjectionMode.EMIT_PROJECTION
    target_state_kind_refs: tuple[str, ...] = field(default_factory=tuple)
    audit_requirement_ref: str = "audit:l6_state_projection_audit_requirement"
    policy_ref: str = "policy:l6_no_direct_state_write"
    writes_l2_state_fact: bool = False
    mutates_core_state: bool = False
    treats_projection_as_fact: bool = False
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.projection_contract_ref, "L6StateProjectionContract.projection_contract_ref")
        ensure_ref_items(self.source_state_projection_refs, "L6StateProjectionContract.source_state_projection_refs")
        ensure_ref_items(self.output_projection_refs, "L6StateProjectionContract.output_projection_refs")
        object.__setattr__(self, "mode", L6StateProjectionMode(self.mode))
        ensure_ref_items(self.target_state_kind_refs, "L6StateProjectionContract.target_state_kind_refs")
        ensure_ref_text(self.audit_requirement_ref, "L6StateProjectionContract.audit_requirement_ref")
        ensure_ref_text(self.policy_ref, "L6StateProjectionContract.policy_ref")
        if self.writes_l2_state_fact or self.mutates_core_state or self.treats_projection_as_fact:
            raise ValueError("L6 state projection contract cannot write L2 facts or mutate core state")
        ensure_schema_version(self.schema_version)
