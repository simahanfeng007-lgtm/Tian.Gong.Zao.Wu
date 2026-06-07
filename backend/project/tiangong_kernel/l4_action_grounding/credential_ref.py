"""L4 第二阶段凭据句柄引用。"""

from __future__ import annotations

from dataclasses import dataclass

from tiangong_kernel.l0_primitives.identity import TypedRef

from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_short_text, ensure_true
from .permit_scope import PermitScope


@dataclass(frozen=True, slots=True)
class CredentialHandleRef:
    """凭据句柄引用；不保存明文凭据，不解析真实凭据。"""

    handle_ref: TypedRef
    scope: PermitScope | None = None
    availability_hint: str = "referenced"
    ref_only: bool = True
    contains_plain_secret: bool = False
    l4_resolved_credential: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_short_text(self.availability_hint, "CredentialHandleRef.availability_hint", 128)
        ensure_true(self.ref_only, "CredentialHandleRef.ref_only")
        ensure_false(self.contains_plain_secret, "CredentialHandleRef.contains_plain_secret")
        ensure_false(self.l4_resolved_credential, "CredentialHandleRef.l4_resolved_credential")
        ensure_schema_version(self.schema_version, "CredentialHandleRef.schema_version")
