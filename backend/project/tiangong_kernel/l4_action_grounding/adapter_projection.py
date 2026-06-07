"""Adapter projection objects for L4 phase 3."""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from .adapter_registry import AdapterRegistrySnapshot
from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_short_text, ensure_true


@dataclass(frozen=True, slots=True)
class AdapterProjection:
    """Projection for one adapter selection or invocation result."""

    projection_ref: TypedRef
    adapter_id: str = ""
    adapter_kind: str = ""
    selection_result_ref: TypedRef | None = None
    output_ref: TypedRef | None = None
    failure_ref: TypedRef | None = None
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    projection_only: bool = True
    real_action_performed: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_short_text(self.adapter_id, "AdapterProjection.adapter_id", 128)
        ensure_short_text(self.adapter_kind, "AdapterProjection.adapter_kind", 128)
        for item in self.reason_codes:
            ensure_short_text(item, "AdapterProjection.reason_codes", 128)
        ensure_true(self.projection_only, "AdapterProjection.projection_only")
        ensure_false(self.real_action_performed, "AdapterProjection.real_action_performed")
        ensure_schema_version(self.schema_version, "AdapterProjection.schema_version")


@dataclass(frozen=True, slots=True)
class AdapterRegistryProjection:
    """Registry projection; it exposes descriptors without plugin hosting."""

    projection_ref: TypedRef
    adapter_ids: tuple[str, ...] = field(default_factory=tuple)
    adapter_kinds: tuple[str, ...] = field(default_factory=tuple)
    real_stub_adapter_ids: tuple[str, ...] = field(default_factory=tuple)
    test_only_adapter_ids: tuple[str, ...] = field(default_factory=tuple)
    enabled_by_default_adapter_ids: tuple[str, ...] = field(default_factory=tuple)
    projection_only: bool = True
    real_action_enabled: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for item in (
            self.adapter_ids
            + self.adapter_kinds
            + self.real_stub_adapter_ids
            + self.test_only_adapter_ids
            + self.enabled_by_default_adapter_ids
        ):
            ensure_short_text(item, "AdapterRegistryProjection text", 128)
        ensure_true(self.projection_only, "AdapterRegistryProjection.projection_only")
        ensure_false(self.real_action_enabled, "AdapterRegistryProjection.real_action_enabled")
        ensure_schema_version(self.schema_version, "AdapterRegistryProjection.schema_version")

    @classmethod
    def from_snapshot(cls, projection_ref: TypedRef, snapshot: AdapterRegistrySnapshot) -> "AdapterRegistryProjection":
        descriptors = tuple(entry.descriptor for entry in snapshot.entries)
        return cls(
            projection_ref=projection_ref,
            adapter_ids=tuple(item.adapter_id for item in descriptors),
            adapter_kinds=tuple(item.adapter_kind for item in descriptors),
            real_stub_adapter_ids=tuple(item.adapter_id for item in descriptors if item.mode.value == "real_stub"),
            test_only_adapter_ids=tuple(item.adapter_id for item in descriptors if item.test_only),
            enabled_by_default_adapter_ids=tuple(item.adapter_id for item in descriptors if item.enabled_by_default),
        )
