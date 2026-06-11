"""Adapter invariants for L4 phase 3."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from tiangong_kernel.l0_primitives.identity import TypedRef

from .adapter_descriptor import AdapterDescriptor
from .adapter_envelope import AdapterInputEnvelope
from .adapter_mode import AdapterMode
from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_short_text, ensure_true


@dataclass(frozen=True, slots=True)
class NoRealAdapterActivationWithoutL5Invariant:
    invariant_ref: TypedRef
    invariant_name: str = "no_real_adapter_activation_without_l5"
    invariant_only: bool = True
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_short_text(self.invariant_name, "NoRealAdapterActivationWithoutL5Invariant.invariant_name", 128)
        ensure_true(self.invariant_only, "NoRealAdapterActivationWithoutL5Invariant.invariant_only")
        ensure_schema_version(self.schema_version, "NoRealAdapterActivationWithoutL5Invariant.schema_version")

    def is_satisfied_by_descriptor(self, descriptor: AdapterDescriptor) -> bool:
        return descriptor.mode != AdapterMode.REAL_STUB or (descriptor.requires_l5_permit and not descriptor.production_enabled)


@dataclass(frozen=True, slots=True)
class FakeAdapterNeverProductionInvariant:
    __test__: ClassVar[bool] = False

    invariant_ref: TypedRef
    invariant_name: str = "fake_adapter_never_production"
    invariant_only: bool = True
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_short_text(self.invariant_name, "FakeAdapterNeverProductionInvariant.invariant_name", 128)
        ensure_true(self.invariant_only, "FakeAdapterNeverProductionInvariant.invariant_only")
        ensure_schema_version(self.schema_version, "FakeAdapterNeverProductionInvariant.schema_version")

    def is_satisfied_by_descriptor(self, descriptor: AdapterDescriptor) -> bool:
        return not (descriptor.test_only and descriptor.production_enabled)


@dataclass(frozen=True, slots=True)
class AdapterCannotHoldPlainCredentialInvariant:
    invariant_ref: TypedRef
    invariant_name: str = "adapter_cannot_hold_plain_credential"
    invariant_only: bool = True
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_short_text(self.invariant_name, "AdapterCannotHoldPlainCredentialInvariant.invariant_name", 128)
        ensure_true(self.invariant_only, "AdapterCannotHoldPlainCredentialInvariant.invariant_only")
        ensure_schema_version(self.schema_version, "AdapterCannotHoldPlainCredentialInvariant.schema_version")

    def is_satisfied_by_envelope(self, envelope: AdapterInputEnvelope) -> bool:
        return envelope.contains_plain_credential is False


@dataclass(frozen=True, slots=True)
class AdapterCannotBypassL3Invariant:
    invariant_ref: TypedRef
    invariant_name: str = "adapter_cannot_bypass_l3"
    invariant_only: bool = True
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_short_text(self.invariant_name, "AdapterCannotBypassL3Invariant.invariant_name", 128)
        ensure_true(self.invariant_only, "AdapterCannotBypassL3Invariant.invariant_only")
        ensure_schema_version(self.schema_version, "AdapterCannotBypassL3Invariant.schema_version")

    def is_satisfied_by_envelope(self, envelope: AdapterInputEnvelope) -> bool:
        return envelope.l3_controlled and not envelope.l4_autonomous


@dataclass(frozen=True, slots=True)
class AdapterCannotBypassL5Invariant:
    invariant_ref: TypedRef
    invariant_name: str = "adapter_cannot_bypass_l5"
    invariant_only: bool = True
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_short_text(self.invariant_name, "AdapterCannotBypassL5Invariant.invariant_name", 128)
        ensure_true(self.invariant_only, "AdapterCannotBypassL5Invariant.invariant_only")
        ensure_schema_version(self.schema_version, "AdapterCannotBypassL5Invariant.schema_version")

    def is_satisfied_by_descriptor(self, descriptor: AdapterDescriptor) -> bool:
        return descriptor.mode != AdapterMode.REAL_STUB or descriptor.requires_l5_permit


@dataclass(frozen=True, slots=True)
class AdapterCannotImplementL6SubsystemInvariant:
    invariant_ref: TypedRef
    invariant_name: str = "adapter_cannot_implement_l6_subsystem"
    invariant_only: bool = True
    implements_l6_subsystem: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_short_text(self.invariant_name, "AdapterCannotImplementL6SubsystemInvariant.invariant_name", 128)
        ensure_true(self.invariant_only, "AdapterCannotImplementL6SubsystemInvariant.invariant_only")
        ensure_false(self.implements_l6_subsystem, "AdapterCannotImplementL6SubsystemInvariant.implements_l6_subsystem")
        ensure_schema_version(self.schema_version, "AdapterCannotImplementL6SubsystemInvariant.schema_version")
