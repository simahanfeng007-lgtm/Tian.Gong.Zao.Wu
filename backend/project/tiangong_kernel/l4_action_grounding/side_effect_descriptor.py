"""Side-effect descriptors for external action grounding."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef

from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_short_text, ensure_true


class SideEffectKind(str, Enum):
    READ_ONLY = "read_only"
    WRITE = "write"
    DELETE = "delete"
    OVERWRITE = "overwrite"
    NETWORK_SEND = "network_send"
    PROCESS_SPAWN = "process_spawn"
    UI_INPUT = "ui_input"
    SCREEN_ACCESS = "screen_access"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class SideEffectDescriptor:
    """Describe possible external side effects; it never authorizes them."""

    side_effect_ref: TypedRef
    effect_kinds: tuple[SideEffectKind, ...] = field(default_factory=tuple)
    summary: str = "no side effect declared"
    descriptor_only: bool = True
    authorizes_action: bool = False
    performs_side_effect: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_short_text(self.summary, "SideEffectDescriptor.summary")
        ensure_true(self.descriptor_only, "SideEffectDescriptor.descriptor_only")
        ensure_false(self.authorizes_action, "SideEffectDescriptor.authorizes_action")
        ensure_false(self.performs_side_effect, "SideEffectDescriptor.performs_side_effect")
        ensure_schema_version(self.schema_version, "SideEffectDescriptor.schema_version")
