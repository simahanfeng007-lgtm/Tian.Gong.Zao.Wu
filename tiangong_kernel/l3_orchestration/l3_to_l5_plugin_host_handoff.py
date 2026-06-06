"""L3 to L5 plugin host handoff objects."""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from .orchestration_identity import L3_ORCHESTRATION_SCHEMA_VERSION


@dataclass(frozen=True, slots=True)
class L3ToL5PluginHostRequestBundle:
    bundle_ref: TypedRef
    plugin_manifest_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    sandbox_requirement_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    audit_requirement_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION


@dataclass(frozen=True, slots=True)
class L3ToL5PluginHostRefBundle:
    bundle_ref: TypedRef
    plugin_ref: TypedRef | None = None
    host_boundary_ref: TypedRef | None = None
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION


@dataclass(frozen=True, slots=True)
class L3ToL5PluginHostReadinessSummary:
    summary_ref: TypedRef
    readiness_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    summary_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION


@dataclass(frozen=True, slots=True)
class L3ToL5PluginHostNonExecutionGuarantee:
    guarantee_ref: TypedRef
    guarantee_only: bool = True
    loads_plugin: bool = False
    writes_registry: bool = False
    creates_sandbox: bool = False
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION


@dataclass(frozen=True, slots=True)
class L3ToL5PluginHostInterfaceFreezeNote:
    note_ref: TypedRef
    frozen_surface_names: tuple[str, ...] = field(default_factory=tuple)
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION


@dataclass(frozen=True, slots=True)
class L3ToL5PluginHostHandoffEnvelope:
    handoff_ref: TypedRef
    request_bundle: L3ToL5PluginHostRequestBundle | None = None
    ref_bundle: L3ToL5PluginHostRefBundle | None = None
    readiness_summary: L3ToL5PluginHostReadinessSummary | None = None
    non_execution_guarantee: L3ToL5PluginHostNonExecutionGuarantee | None = None
    interface_freeze_note: L3ToL5PluginHostInterfaceFreezeNote | None = None
    handoff_only: bool = True
    implements_plugin_host: bool = False
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION
