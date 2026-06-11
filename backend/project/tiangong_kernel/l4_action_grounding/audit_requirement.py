"""L4 第二阶段审计需求引用。"""

from __future__ import annotations

from dataclasses import dataclass

from tiangong_kernel.l0_primitives.identity import TypedRef

from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_short_text, ensure_true


@dataclass(frozen=True, slots=True)
class AuditRequirementRef:
    """审计需求引用；只表达未来 L5/L6 审计需求，不写审计存储。"""

    requirement_ref: TypedRef
    audit_scope_hint: str = "future_l5_audit_requirement_ref"
    ref_only: bool = True
    l4_audit_written: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_short_text(self.audit_scope_hint, "AuditRequirementRef.audit_scope_hint", 128)
        ensure_true(self.ref_only, "AuditRequirementRef.ref_only")
        ensure_false(self.l4_audit_written, "AuditRequirementRef.l4_audit_written")
        ensure_schema_version(self.schema_version, "AuditRequirementRef.schema_version")
