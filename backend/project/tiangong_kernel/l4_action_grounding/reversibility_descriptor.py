"""Reversibility descriptors for external action grounding."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef

from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_short_text, ensure_true


class ReversibilityKind(str, Enum):
    REVERSIBLE = "reversible"
    PARTIALLY_REVERSIBLE = "partially_reversible"
    IRREVERSIBLE = "irreversible"
    UNKNOWN = "unknown"
    NOT_APPLICABLE = "not_applicable"


@dataclass(frozen=True, slots=True)
class ReversibilityDescriptor:
    """Describe reversibility hints; it never performs recovery."""

    reversibility_ref: TypedRef
    reversibility_kind: ReversibilityKind = ReversibilityKind.UNKNOWN
    summary: str = "reversibility unknown"
    descriptor_only: bool = True
    enables_action: bool = False
    performs_recovery: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_short_text(self.summary, "ReversibilityDescriptor.summary")
        ensure_true(self.descriptor_only, "ReversibilityDescriptor.descriptor_only")
        ensure_false(self.enables_action, "ReversibilityDescriptor.enables_action")
        ensure_false(self.performs_recovery, "ReversibilityDescriptor.performs_recovery")
        ensure_schema_version(self.schema_version, "ReversibilityDescriptor.schema_version")
