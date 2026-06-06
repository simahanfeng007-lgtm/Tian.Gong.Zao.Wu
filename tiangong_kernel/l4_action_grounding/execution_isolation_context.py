"""Isolation context descriptors for L4 phase 7."""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_short_text, ensure_true


@dataclass(frozen=True, slots=True)
class ExecutionIsolationContext:
    """Isolation context only; it creates no real sandbox or permission change."""

    isolation_context_ref: TypedRef
    namespace_ref: TypedRef | None = None
    scope_ref: TypedRef | None = None
    trace_ref: TypedRef | None = None
    resource_budget_ref: TypedRef | None = None
    permit_ref: TypedRef | None = None
    isolation_items: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    context_only: bool = True
    creates_real_sandbox: bool = False
    switches_real_user: bool = False
    changes_system_permission: bool = False
    starts_process: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for key, value in self.isolation_items:
            ensure_short_text(key, "ExecutionIsolationContext.isolation_items key", 128)
            ensure_short_text(value, "ExecutionIsolationContext.isolation_items value")
        ensure_true(self.context_only, "ExecutionIsolationContext.context_only")
        ensure_false(self.creates_real_sandbox, "ExecutionIsolationContext.creates_real_sandbox")
        ensure_false(self.switches_real_user, "ExecutionIsolationContext.switches_real_user")
        ensure_false(self.changes_system_permission, "ExecutionIsolationContext.changes_system_permission")
        ensure_false(self.starts_process, "ExecutionIsolationContext.starts_process")
        ensure_schema_version(self.schema_version, "ExecutionIsolationContext.schema_version")
