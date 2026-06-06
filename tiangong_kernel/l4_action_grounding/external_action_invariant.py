"""Hard safety invariants reserved for future L5 checks."""

from __future__ import annotations

from dataclasses import dataclass

from tiangong_kernel.l0_primitives.identity import TypedRef

from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_short_text, ensure_true


@dataclass(frozen=True, slots=True)
class ExternalActionHardSafetyInvariant:
    """A5-like invariant placeholder; it describes hard safety and cannot allow action."""

    invariant_ref: TypedRef
    invariant_name: str
    surface: str
    requires_l5_permit: bool = True
    l4_can_override: bool = False
    live_action_allowed: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_short_text(self.invariant_name, "ExternalActionHardSafetyInvariant.invariant_name", 128)
        ensure_short_text(self.surface, "ExternalActionHardSafetyInvariant.surface", 128)
        ensure_true(self.requires_l5_permit, "ExternalActionHardSafetyInvariant.requires_l5_permit")
        ensure_false(self.l4_can_override, "ExternalActionHardSafetyInvariant.l4_can_override")
        ensure_false(self.live_action_allowed, "ExternalActionHardSafetyInvariant.live_action_allowed")
        ensure_schema_version(self.schema_version, "ExternalActionHardSafetyInvariant.schema_version")


@dataclass(frozen=True, slots=True)
class NoRealFileSystemMutationInvariant(ExternalActionHardSafetyInvariant):
    invariant_name: str = "NoRealFileSystemMutationInvariant"
    surface: str = "filesystem"


@dataclass(frozen=True, slots=True)
class NoRealNetworkAccessInvariant(ExternalActionHardSafetyInvariant):
    invariant_name: str = "NoRealNetworkAccessInvariant"
    surface: str = "network"


@dataclass(frozen=True, slots=True)
class NoRealShellExecutionInvariant(ExternalActionHardSafetyInvariant):
    invariant_name: str = "NoRealShellExecutionInvariant"
    surface: str = "terminal"


@dataclass(frozen=True, slots=True)
class NoRealDesktopControlInvariant(ExternalActionHardSafetyInvariant):
    invariant_name: str = "NoRealDesktopControlInvariant"
    surface: str = "desktop"


@dataclass(frozen=True, slots=True)
class ExternalActionRequiresL5PermitInvariant(ExternalActionHardSafetyInvariant):
    invariant_name: str = "ExternalActionRequiresL5PermitInvariant"
    surface: str = "external_action"


@dataclass(frozen=True, slots=True)
class A5LikeHardSafetyInvariant(ExternalActionHardSafetyInvariant):
    invariant_name: str = "A5LikeHardSafetyInvariant"
    surface: str = "future_l5_hard_safety"
