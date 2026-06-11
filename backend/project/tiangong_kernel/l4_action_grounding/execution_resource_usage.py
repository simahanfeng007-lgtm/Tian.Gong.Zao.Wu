"""Resource usage summary for L4 phase 6 returns."""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_short_text, ensure_true


@dataclass(frozen=True, slots=True)
class ExecutionResourceUsage:
    """Resource usage summary only; it allocates nothing and decides no policy."""

    resource_usage_ref: TypedRef
    action_ref: TypedRef | None = None
    tokens_hint_ref: TypedRef | None = None
    time_ms_hint_ref: TypedRef | None = None
    bytes_hint_ref: TypedRef | None = None
    adapter_usage_hint_ref: TypedRef | None = None
    process_hint_ref: TypedRef | None = None
    network_hint_ref: TypedRef | None = None
    usage_items: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    summary_only: bool = True
    allocates_resource: bool = False
    makes_resource_policy: bool = False
    starts_process: bool = False
    accesses_real_network: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for key, value in self.usage_items:
            ensure_short_text(key, "ExecutionResourceUsage.usage_items key", 128)
            ensure_short_text(value, "ExecutionResourceUsage.usage_items value")
        ensure_true(self.summary_only, "ExecutionResourceUsage.summary_only")
        ensure_false(self.allocates_resource, "ExecutionResourceUsage.allocates_resource")
        ensure_false(self.makes_resource_policy, "ExecutionResourceUsage.makes_resource_policy")
        ensure_false(self.starts_process, "ExecutionResourceUsage.starts_process")
        ensure_false(self.accesses_real_network, "ExecutionResourceUsage.accesses_real_network")
        ensure_schema_version(self.schema_version, "ExecutionResourceUsage.schema_version")
