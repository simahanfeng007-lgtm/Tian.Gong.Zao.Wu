"""External action scope descriptors for L4 phase 5."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef

from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_short_text, ensure_true


class ExternalActionSurface(str, Enum):
    MODEL = "model"
    TOOL = "tool"
    FILE = "file"
    FILESYSTEM = "filesystem"
    NETWORK = "network"
    TERMINAL = "terminal"
    DESKTOP = "desktop"
    DATABASE = "database"
    BROWSER = "browser"
    GIT = "git"
    BUILD = "build"
    TEST = "test"
    SANDBOX = "sandbox"
    STORAGE = "storage"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class ExternalActionScope:
    """Structural scope only; L5 owns policy and risk decisions."""

    scope_ref: TypedRef
    surface: ExternalActionSurface = ExternalActionSurface.UNKNOWN
    path_scope_ref: TypedRef | None = None
    domain_scope_ref: TypedRef | None = None
    command_scope_ref: TypedRef | None = None
    desktop_scope_ref: TypedRef | None = None
    scope_items: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    scope_only: bool = True
    policy_decision_made: bool = False
    permission_granted: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for key, value in self.scope_items:
            ensure_short_text(key, "ExternalActionScope.scope_items key", 128)
            ensure_short_text(value, "ExternalActionScope.scope_items value")
        ensure_true(self.scope_only, "ExternalActionScope.scope_only")
        ensure_false(self.policy_decision_made, "ExternalActionScope.policy_decision_made")
        ensure_false(self.permission_granted, "ExternalActionScope.permission_granted")
        ensure_schema_version(self.schema_version, "ExternalActionScope.schema_version")
