"""Adapter registry skeleton for L4 action grounding."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from tiangong_kernel.l0_primitives.identity import TypedRef

from .adapter_descriptor import AdapterDescriptor
from .adapter_failure import (
    AdapterDuplicateIdFailure,
    AdapterFailure,
    AdapterFailureKind,
    AdapterInvariantViolationFailure,
    AdapterMalformedDescriptorFailure,
    new_adapter_typed_ref,
)
from .adapter_mode import AdapterMode
from .adapter_protocol import ActionAdapterProtocol
from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_short_text, ensure_true


@dataclass(frozen=True, slots=True)
class AdapterRegistryEntry:
    """Registry entry; adapter is already constructed and not invoked."""

    entry_ref: TypedRef
    descriptor: AdapterDescriptor
    adapter: ActionAdapterProtocol
    entry_only: bool = True
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_true(self.entry_only, "AdapterRegistryEntry.entry_only")
        ensure_schema_version(self.schema_version, "AdapterRegistryEntry.schema_version")


@dataclass(frozen=True, slots=True)
class AdapterRegistrySnapshot:
    """Immutable registry snapshot; no plugin scanning or dynamic load."""

    snapshot_ref: TypedRef
    entries: tuple[AdapterRegistryEntry, ...] = field(default_factory=tuple)
    snapshot_only: bool = True
    real_action_enabled: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_true(self.snapshot_only, "AdapterRegistrySnapshot.snapshot_only")
        ensure_false(self.real_action_enabled, "AdapterRegistrySnapshot.real_action_enabled")
        ensure_schema_version(self.schema_version, "AdapterRegistrySnapshot.schema_version")


@dataclass(frozen=True, slots=True)
class AdapterRegistryRegistrationResult:
    """Standard registry result; failures are adapter failures."""

    result_ref: TypedRef
    adapter_id: str = ""
    registered: bool = False
    failure: AdapterFailure | None = None
    result_only: bool = True
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_short_text(self.adapter_id, "AdapterRegistryRegistrationResult.adapter_id", 128)
        ensure_true(self.result_only, "AdapterRegistryRegistrationResult.result_only")
        ensure_schema_version(self.schema_version, "AdapterRegistryRegistrationResult.schema_version")


class AdapterRegistry:
    """In-memory registry skeleton; it is not a plugin host."""

    def __init__(self, registry_ref: TypedRef) -> None:
        self.registry_ref = registry_ref
        self._entries: dict[str, AdapterRegistryEntry] = {}

    def register(self, adapter: ActionAdapterProtocol, *, entry_ref: TypedRef | None = None) -> AdapterRegistryRegistrationResult:
        descriptor = adapter.adapter_descriptor
        failure = self._validate_descriptor(descriptor)
        if failure is not None:
            return AdapterRegistryRegistrationResult(
                result_ref=new_adapter_typed_ref("adapter_registry_result"),
                adapter_id=descriptor.adapter_id,
                registered=False,
                failure=failure,
            )
        if descriptor.adapter_id in self._entries:
            failure = AdapterDuplicateIdFailure(
                failure_ref=new_adapter_typed_ref("adapter_failure"),
                message="duplicate adapter_id is not allowed",
                adapter_id=descriptor.adapter_id,
                adapter_kind=descriptor.adapter_kind,
                mode=descriptor.mode,
            )
            return AdapterRegistryRegistrationResult(
                result_ref=new_adapter_typed_ref("adapter_registry_result"),
                adapter_id=descriptor.adapter_id,
                registered=False,
                failure=failure,
            )
        entry = AdapterRegistryEntry(
            entry_ref=entry_ref or new_adapter_typed_ref("adapter_registry_entry"),
            descriptor=descriptor,
            adapter=adapter,
        )
        self._entries[descriptor.adapter_id] = entry
        return AdapterRegistryRegistrationResult(
            result_ref=new_adapter_typed_ref("adapter_registry_result"),
            adapter_id=descriptor.adapter_id,
            registered=True,
            failure=None,
        )

    def _validate_descriptor(self, descriptor: AdapterDescriptor) -> AdapterFailure | None:
        if not descriptor.is_structurally_complete():
            return AdapterMalformedDescriptorFailure(
                failure_ref=new_adapter_typed_ref("adapter_failure"),
                message="adapter descriptor must declare capability and risk surface",
                adapter_id=descriptor.adapter_id,
                adapter_kind=descriptor.adapter_kind,
                mode=descriptor.mode,
            )
        if descriptor.test_only and descriptor.production_enabled:
            return AdapterInvariantViolationFailure(
                failure_ref=new_adapter_typed_ref("adapter_failure"),
                failure_kind=AdapterFailureKind.TEST_ONLY_MODE,
                message="test-only adapter cannot be marked production enabled",
                adapter_id=descriptor.adapter_id,
                adapter_kind=descriptor.adapter_kind,
                mode=descriptor.mode,
            )
        if descriptor.mode == AdapterMode.REAL_STUB and descriptor.enabled_by_default:
            return AdapterInvariantViolationFailure(
                failure_ref=new_adapter_typed_ref("adapter_failure"),
                failure_kind=AdapterFailureKind.DISABLED_BY_DEFAULT,
                message="real adapter stub cannot be enabled by default in L4 phase 3",
                adapter_id=descriptor.adapter_id,
                adapter_kind=descriptor.adapter_kind,
                mode=descriptor.mode,
            )
        if descriptor.production_enabled:
            return AdapterInvariantViolationFailure(
                failure_ref=new_adapter_typed_ref("adapter_failure"),
                failure_kind=AdapterFailureKind.PRODUCTION_DISABLED,
                message="production_enabled must remain false in L4 phase 3",
                adapter_id=descriptor.adapter_id,
                adapter_kind=descriptor.adapter_kind,
                mode=descriptor.mode,
            )
        return None

    def get_descriptor(self, adapter_id: str) -> AdapterDescriptor | None:
        if adapter_id not in self._entries:
            return None
        return self._entries[adapter_id].descriptor

    def get_adapter(self, adapter_id: str) -> ActionAdapterProtocol | None:
        if adapter_id not in self._entries:
            return None
        return self._entries[adapter_id].adapter

    def descriptors_for_action(self, action_kind: str) -> tuple[AdapterDescriptor, ...]:
        return tuple(
            entry.descriptor
            for entry in self._entries.values()
            if action_kind in entry.descriptor.supported_action_kinds
        )

    def entries(self) -> tuple[AdapterRegistryEntry, ...]:
        return tuple(self._entries.values())

    def snapshot(self, snapshot_ref: TypedRef | None = None) -> AdapterRegistrySnapshot:
        return AdapterRegistrySnapshot(
            snapshot_ref=snapshot_ref or new_adapter_typed_ref("adapter_registry_snapshot"),
            entries=self.entries(),
        )

    def extend(self, adapters: Iterable[ActionAdapterProtocol]) -> tuple[AdapterRegistryRegistrationResult, ...]:
        return tuple(self.register(adapter) for adapter in adapters)
