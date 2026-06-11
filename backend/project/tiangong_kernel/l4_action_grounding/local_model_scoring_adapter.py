"""Disabled local model scoring adapter reservation."""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from .math_adapter_descriptor import MathAdapterDescriptor, MathAdapterInvocationRef, build_math_adapter_descriptor, disabled_math_adapter_invocation


def _descriptor() -> MathAdapterDescriptor:
    return build_math_adapter_descriptor(
        adapter_id="disabled.local_model_scoring_adapter",
        adapter_kind="local_model_scoring_adapter",
        adapter_name="Disabled Local Model Scoring Adapter",
        supported_model_domains=("local_model_scoring", "learning_assessment", "regression_risk"),
    )


@dataclass(frozen=True, slots=True)
class LocalModelScoringAdapter:
    """Disabled stub for future local model scoring."""

    adapter_descriptor: MathAdapterDescriptor = field(default_factory=_descriptor)

    @property
    def disabled_by_default(self) -> bool:
        return self.adapter_descriptor.disabled_by_default

    @property
    def requires_l5_permit(self) -> bool:
        return self.adapter_descriptor.requires_l5_permit

    def describe(self) -> MathAdapterDescriptor:
        return self.adapter_descriptor

    def dry_run(self, request_ref: TypedRef | None = None) -> MathAdapterInvocationRef:
        return disabled_math_adapter_invocation(self.adapter_descriptor, request_ref)

    def invoke(self, request_ref: TypedRef | None = None) -> MathAdapterInvocationRef:
        return disabled_math_adapter_invocation(self.adapter_descriptor, request_ref)
