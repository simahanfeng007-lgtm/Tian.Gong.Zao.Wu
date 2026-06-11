"""Protocol for disabled L4 math adapter reservations."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from tiangong_kernel.l0_primitives.identity import TypedRef

from .math_adapter_descriptor import MathAdapterDescriptor, MathAdapterInvocationRef


@runtime_checkable
class MathAdapterProtocol(Protocol):
    """Structural protocol for future math adapters."""

    @property
    def adapter_descriptor(self) -> MathAdapterDescriptor:
        ...

    @property
    def disabled_by_default(self) -> bool:
        ...

    @property
    def requires_l5_permit(self) -> bool:
        ...

    def describe(self) -> MathAdapterDescriptor:
        ...

    def dry_run(self, request_ref: TypedRef | None = None) -> MathAdapterInvocationRef:
        ...

    def invoke(self, request_ref: TypedRef | None = None) -> MathAdapterInvocationRef:
        ...
