"""Math adapter descriptor reservations for L4.

These descriptors reserve future adapter shapes only.  They do not load math
libraries, call services, score risk, grant permission, or turn scores into
actions.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_short_text, ensure_true


@dataclass(frozen=True, slots=True)
class MathAdapterDescriptor:
    """Declarative L4 math adapter descriptor."""

    adapter_ref: TypedRef | None = None
    adapter_id: str = "disabled.math_adapter"
    adapter_kind: str = "math_adapter"
    adapter_name: str = "Disabled Math Adapter"
    supported_model_domains: tuple[str, ...] = field(default_factory=tuple)
    supported_modes: tuple[str, ...] = ("disabled_stub", "dry_run", "no_op")
    optional_dependency_names: tuple[str, ...] = field(default_factory=tuple)
    disabled_by_default: bool = True
    enabled_by_default: bool = False
    requires_l5_permit: bool = True
    production_enabled: bool = False
    descriptor_only: bool = True
    protocol_only: bool = True
    dry_run_only: bool = True
    no_op_only: bool = True
    performs_real_calculation: bool = False
    calls_external_service: bool = False
    accesses_files: bool = False
    accesses_network: bool = False
    executes_shell: bool = False
    writes_l2_state: bool = False
    grants_permission: bool = False
    decides_strategy: bool = False
    turns_score_into_action: bool = False
    implements_l6_plugin: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for value in (
            self.adapter_id,
            self.adapter_kind,
            self.adapter_name,
            *self.supported_model_domains,
            *self.supported_modes,
            *self.optional_dependency_names,
        ):
            ensure_short_text(value, "MathAdapterDescriptor text", 128)
        ensure_true(self.disabled_by_default, "MathAdapterDescriptor.disabled_by_default")
        ensure_false(self.enabled_by_default, "MathAdapterDescriptor.enabled_by_default")
        ensure_true(self.requires_l5_permit, "MathAdapterDescriptor.requires_l5_permit")
        ensure_false(self.production_enabled, "MathAdapterDescriptor.production_enabled")
        ensure_true(self.descriptor_only, "MathAdapterDescriptor.descriptor_only")
        ensure_true(self.protocol_only, "MathAdapterDescriptor.protocol_only")
        ensure_true(self.dry_run_only, "MathAdapterDescriptor.dry_run_only")
        ensure_true(self.no_op_only, "MathAdapterDescriptor.no_op_only")
        ensure_false(self.performs_real_calculation, "MathAdapterDescriptor.performs_real_calculation")
        ensure_false(self.calls_external_service, "MathAdapterDescriptor.calls_external_service")
        ensure_false(self.accesses_files, "MathAdapterDescriptor.accesses_files")
        ensure_false(self.accesses_network, "MathAdapterDescriptor.accesses_network")
        ensure_false(self.executes_shell, "MathAdapterDescriptor.executes_shell")
        ensure_false(self.writes_l2_state, "MathAdapterDescriptor.writes_l2_state")
        ensure_false(self.grants_permission, "MathAdapterDescriptor.grants_permission")
        ensure_false(self.decides_strategy, "MathAdapterDescriptor.decides_strategy")
        ensure_false(self.turns_score_into_action, "MathAdapterDescriptor.turns_score_into_action")
        ensure_false(self.implements_l6_plugin, "MathAdapterDescriptor.implements_l6_plugin")
        ensure_schema_version(self.schema_version, "MathAdapterDescriptor.schema_version")


@dataclass(frozen=True, slots=True)
class MathAdapterInvocationRef:
    """Disabled invocation reference returned by math adapter stubs."""

    invocation_ref: TypedRef | None = None
    adapter_descriptor: MathAdapterDescriptor = field(default_factory=MathAdapterDescriptor)
    request_ref: TypedRef | None = None
    result_ref: TypedRef | None = None
    blocked_reason: str = "math adapter disabled by default until future L5 permit"
    dry_run: bool = True
    no_op: bool = True
    disabled: bool = True
    real_calculation_performed: bool = False
    external_call_performed: bool = False
    action_enabled: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_short_text(self.blocked_reason, "MathAdapterInvocationRef.blocked_reason")
        ensure_true(self.dry_run, "MathAdapterInvocationRef.dry_run")
        ensure_true(self.no_op, "MathAdapterInvocationRef.no_op")
        ensure_true(self.disabled, "MathAdapterInvocationRef.disabled")
        ensure_false(self.real_calculation_performed, "MathAdapterInvocationRef.real_calculation_performed")
        ensure_false(self.external_call_performed, "MathAdapterInvocationRef.external_call_performed")
        ensure_false(self.action_enabled, "MathAdapterInvocationRef.action_enabled")
        ensure_schema_version(self.schema_version, "MathAdapterInvocationRef.schema_version")


def build_math_adapter_descriptor(
    *,
    adapter_id: str,
    adapter_kind: str,
    adapter_name: str,
    supported_model_domains: tuple[str, ...] = (),
    optional_dependency_names: tuple[str, ...] = (),
) -> MathAdapterDescriptor:
    """Build a disabled descriptor for a future math adapter."""

    return MathAdapterDescriptor(
        adapter_id=adapter_id,
        adapter_kind=adapter_kind,
        adapter_name=adapter_name,
        supported_model_domains=supported_model_domains,
        optional_dependency_names=optional_dependency_names,
    )


def disabled_math_adapter_invocation(
    adapter_descriptor: MathAdapterDescriptor,
    request_ref: TypedRef | None = None,
) -> MathAdapterInvocationRef:
    """Return a disabled dry-run/no-op invocation reference."""

    return MathAdapterInvocationRef(adapter_descriptor=adapter_descriptor, request_ref=request_ref)
