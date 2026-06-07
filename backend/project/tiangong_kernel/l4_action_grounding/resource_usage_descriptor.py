"""Resource usage descriptors for external action grounding."""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_short_text, ensure_true


@dataclass(frozen=True, slots=True)
class ResourceUsageDescriptor:
    """Describe expected or simulated usage; it never allocates resources."""

    resource_usage_ref: TypedRef
    summary: str = "no resource usage declared"
    time_hint_ref: TypedRef | None = None
    token_hint_ref: TypedRef | None = None
    byte_hint_ref: TypedRef | None = None
    cpu_hint_ref: TypedRef | None = None
    network_hint_ref: TypedRef | None = None
    process_hint_ref: TypedRef | None = None
    usage_items: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    descriptor_only: bool = True
    allocates_resource: bool = False
    starts_process: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_short_text(self.summary, "ResourceUsageDescriptor.summary")
        for key, value in self.usage_items:
            ensure_short_text(key, "ResourceUsageDescriptor.usage_items key", 128)
            ensure_short_text(value, "ResourceUsageDescriptor.usage_items value")
        ensure_true(self.descriptor_only, "ResourceUsageDescriptor.descriptor_only")
        ensure_false(self.allocates_resource, "ResourceUsageDescriptor.allocates_resource")
        ensure_false(self.starts_process, "ResourceUsageDescriptor.starts_process")
        ensure_schema_version(self.schema_version, "ResourceUsageDescriptor.schema_version")
