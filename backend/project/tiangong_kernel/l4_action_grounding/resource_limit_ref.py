"""L4 第二阶段资源限制引用。"""

from __future__ import annotations

from dataclasses import dataclass

from tiangong_kernel.l0_primitives.identity import TypedRef

from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_short_text, ensure_true
from .permit_scope import PermitScope


@dataclass(frozen=True, slots=True)
class ResourceLimitRef:
    """资源限制引用；不创建额度、不消费真实资源。"""

    limit_ref: TypedRef
    scope: PermitScope | None = None
    availability_hint: str = "referenced"
    ref_only: bool = True
    l4_budget_created: bool = False
    l4_resource_consumed: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_short_text(self.availability_hint, "ResourceLimitRef.availability_hint", 128)
        ensure_true(self.ref_only, "ResourceLimitRef.ref_only")
        ensure_false(self.l4_budget_created, "ResourceLimitRef.l4_budget_created")
        ensure_false(self.l4_resource_consumed, "ResourceLimitRef.l4_resource_consumed")
        ensure_schema_version(self.schema_version, "ResourceLimitRef.schema_version")
