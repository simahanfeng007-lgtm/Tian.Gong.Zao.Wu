"""Model action adapter port for L4 phase 4."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from .adapter_descriptor import AdapterDescriptor
from .model_action_failure import ModelActionFailure
from .model_action_request import ModelActionRequest
from .model_action_result import ModelActionResult


@runtime_checkable
class ModelActionAdapterPort(Protocol):
    """Protocol only; it does not define a real model API client."""

    @property
    def adapter_descriptor(self) -> AdapterDescriptor:
        ...

    def describe(self) -> AdapterDescriptor:
        ...

    def prepare(self, request: ModelActionRequest) -> ModelActionResult | ModelActionFailure:
        ...

    def dry_run_model_action(self, request: ModelActionRequest) -> ModelActionResult | ModelActionFailure:
        ...

    def invoke(self, request: ModelActionRequest) -> ModelActionResult | ModelActionFailure:
        ...
