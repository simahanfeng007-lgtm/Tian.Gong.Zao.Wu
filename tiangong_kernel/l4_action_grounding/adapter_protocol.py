"""Structural adapter protocol for L4 action grounding."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from .adapter_descriptor import AdapterDescriptor
from .adapter_envelope import AdapterFailureEnvelope, AdapterInputEnvelope, AdapterOutputEnvelope
from .adapter_mode import AdapterMode


@runtime_checkable
class ActionAdapterProtocol(Protocol):
    """Adapter protocol; implementations are not autonomous agents."""

    @property
    def adapter_descriptor(self) -> AdapterDescriptor:
        ...

    @property
    def is_real_adapter(self) -> bool:
        ...

    @property
    def is_enabled_by_default(self) -> bool:
        ...

    @property
    def requires_l5_permit(self) -> bool:
        ...

    @property
    def allowed_modes(self) -> tuple[AdapterMode, ...]:
        ...

    def supports(self, envelope: AdapterInputEnvelope) -> bool:
        """Return structural support only; no permission or risk decision."""
        ...

    def prepare(self, envelope: AdapterInputEnvelope) -> AdapterOutputEnvelope | AdapterFailureEnvelope:
        ...

    def invoke(self, envelope: AdapterInputEnvelope) -> AdapterOutputEnvelope | AdapterFailureEnvelope:
        ...

    def normalize_result(self, raw: object) -> AdapterOutputEnvelope:
        ...

    def normalize_failure(self, error: object) -> AdapterFailureEnvelope:
        ...


ExecutionAdapterProtocol = ActionAdapterProtocol
