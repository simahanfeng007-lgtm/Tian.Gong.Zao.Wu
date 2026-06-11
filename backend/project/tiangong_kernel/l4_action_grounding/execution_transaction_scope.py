"""Transaction scope descriptors for L4 phase 7."""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_short_text, ensure_true


@dataclass(frozen=True, slots=True)
class ExecutionTransactionScope:
    """Describe transaction scope; it does not allow or execute a transaction."""

    transaction_scope_ref: TypedRef
    action_ref: TypedRef | None = None
    step_ref: TypedRef | None = None
    tool_group_ref: TypedRef | None = None
    side_effect_scope_ref: TypedRef | None = None
    scope_items: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    descriptor_only: bool = True
    boundary_permission_granted: bool = False
    starts_real_transaction: bool = False
    writes_l2_state: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for key, value in self.scope_items:
            ensure_short_text(key, "ExecutionTransactionScope.scope_items key", 128)
            ensure_short_text(value, "ExecutionTransactionScope.scope_items value")
        ensure_true(self.descriptor_only, "ExecutionTransactionScope.descriptor_only")
        ensure_false(self.boundary_permission_granted, "ExecutionTransactionScope.boundary_permission_granted")
        ensure_false(self.starts_real_transaction, "ExecutionTransactionScope.starts_real_transaction")
        ensure_false(self.writes_l2_state, "ExecutionTransactionScope.writes_l2_state")
        ensure_schema_version(self.schema_version, "ExecutionTransactionScope.schema_version")
