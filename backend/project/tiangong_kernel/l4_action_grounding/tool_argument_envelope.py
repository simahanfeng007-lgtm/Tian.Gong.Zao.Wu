"""Tool argument envelope for L4 phase 4."""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from .credential_ref import CredentialHandleRef
from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_short_text, ensure_true


@dataclass(frozen=True, slots=True)
class ToolArgumentEnvelope:
    """Standardized tool argument carrier; no business inference or secrets."""

    argument_ref: TypedRef
    argument_items: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    credential_handle_ref: CredentialHandleRef | None = None
    parameter_spec_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    contains_plain_credential: bool = False
    argument_envelope_only: bool = True
    l4_grants_permission: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for key, value in self.argument_items:
            ensure_short_text(key, "ToolArgumentEnvelope.argument key", 128)
            ensure_short_text(value, "ToolArgumentEnvelope.argument value")
        ensure_false(self.contains_plain_credential, "ToolArgumentEnvelope.contains_plain_credential")
        ensure_false(self.l4_grants_permission, "ToolArgumentEnvelope.l4_grants_permission")
        ensure_true(self.argument_envelope_only, "ToolArgumentEnvelope.argument_envelope_only")
        ensure_schema_version(self.schema_version, "ToolArgumentEnvelope.schema_version")
