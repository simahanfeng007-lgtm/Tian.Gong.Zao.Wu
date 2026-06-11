"""Concurrency scopes for L4 phase 7."""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_short_text, ensure_true


@dataclass(frozen=True, slots=True)
class ConcurrencyScope:
    """Describe a concurrency scope; it starts no thread or scheduler."""

    concurrency_scope_ref: TypedRef
    run_ref: TypedRef | None = None
    session_ref: TypedRef | None = None
    step_ref: TypedRef | None = None
    adapter_ref: TypedRef | None = None
    tool_group_ref: TypedRef | None = None
    scope_items: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    descriptor_only: bool = True
    starts_concurrency: bool = False
    schedules_threads: bool = False
    schedules_processes: bool = False
    grants_concurrency_permission: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for key, value in self.scope_items:
            ensure_short_text(key, "ConcurrencyScope.scope_items key", 128)
            ensure_short_text(value, "ConcurrencyScope.scope_items value")
        ensure_true(self.descriptor_only, "ConcurrencyScope.descriptor_only")
        ensure_false(self.starts_concurrency, "ConcurrencyScope.starts_concurrency")
        ensure_false(self.schedules_threads, "ConcurrencyScope.schedules_threads")
        ensure_false(self.schedules_processes, "ConcurrencyScope.schedules_processes")
        ensure_false(self.grants_concurrency_permission, "ConcurrencyScope.grants_concurrency_permission")
        ensure_schema_version(self.schema_version, "ConcurrencyScope.schema_version")
