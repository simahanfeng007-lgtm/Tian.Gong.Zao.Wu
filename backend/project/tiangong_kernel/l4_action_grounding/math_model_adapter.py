"""L4 disabled math model adapter skeletons for the 100-point baseline."""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from .math_adapter_descriptor import MathAdapterDescriptor, MathAdapterInvocationRef, build_math_adapter_descriptor, disabled_math_adapter_invocation


@dataclass(frozen=True, slots=True)
class AdapterTelemetryCollector:
    """适配器遥测收集骨架，只返回引用型遥测摘要。"""

    collector_ref: TypedRef | None = None
    adapter_name: str = "disabled_math_model_adapter"
    latency_ms: float = 0.0
    status: str = "disabled"
    error_code: str = ""
    timeout: bool = False
    fallback: bool = True
    disabled_reason: str = "disabled_by_default"
    collector_only: bool = True

    def __post_init__(self) -> None:
        if self.latency_ms < 0.0:
            raise ValueError("AdapterTelemetryCollector.latency_ms cannot be negative")
        if self.collector_only is not True:
            raise ValueError("AdapterTelemetryCollector.collector_only must remain true")


def _descriptor(adapter_id: str, adapter_kind: str, adapter_name: str, domains: tuple[str, ...]) -> MathAdapterDescriptor:
    return build_math_adapter_descriptor(
        adapter_id=adapter_id,
        adapter_kind=adapter_kind,
        adapter_name=adapter_name,
        supported_model_domains=domains,
    )


@dataclass(frozen=True, slots=True)
class BaseMathModelAdapter:
    """数学模型适配器基础骨架，默认禁用。"""

    adapter_descriptor: MathAdapterDescriptor = field(
        default_factory=lambda: _descriptor(
            "disabled.base_math_model_adapter",
            "base_math_model_adapter",
            "Disabled Base Math Model Adapter",
            ("math_model",),
        )
    )

    @property
    def disabled_by_default(self) -> bool:
        return self.adapter_descriptor.disabled_by_default

    @property
    def requires_l5_permit(self) -> bool:
        return self.adapter_descriptor.requires_l5_permit

    def can_run(self) -> bool:
        return False

    def prepare(self, request_ref: TypedRef | None = None) -> MathAdapterInvocationRef:
        return disabled_math_adapter_invocation(self.adapter_descriptor, request_ref)

    def run_disabled(self, request_ref: TypedRef | None = None) -> MathAdapterInvocationRef:
        return disabled_math_adapter_invocation(self.adapter_descriptor, request_ref)

    def run_shadow(self, request_ref: TypedRef | None = None) -> MathAdapterInvocationRef:
        return disabled_math_adapter_invocation(self.adapter_descriptor, request_ref)

    def run_replay(self, request_ref: TypedRef | None = None) -> MathAdapterInvocationRef:
        return disabled_math_adapter_invocation(self.adapter_descriptor, request_ref)

    def build_telemetry(self) -> AdapterTelemetryCollector:
        return AdapterTelemetryCollector(adapter_name=self.adapter_descriptor.adapter_name)

    def fallback(self, request_ref: TypedRef | None = None) -> MathAdapterInvocationRef:
        return disabled_math_adapter_invocation(self.adapter_descriptor, request_ref)


@dataclass(frozen=True, slots=True)
class DeterministicLocalScoreAdapter(BaseMathModelAdapter):
    """确定性本地评分骨架，当前只返回禁用降级引用。"""

    adapter_descriptor: MathAdapterDescriptor = field(
        default_factory=lambda: _descriptor(
            "disabled.deterministic_local_score_adapter",
            "deterministic_local_score_adapter",
            "Disabled Deterministic Local Score Adapter",
            ("deterministic_score", "fallback"),
        )
    )


@dataclass(frozen=True, slots=True)
class ExternalModelAdapter(BaseMathModelAdapter):
    """外部模型适配器骨架，默认禁用且不联网。"""

    adapter_descriptor: MathAdapterDescriptor = field(
        default_factory=lambda: _descriptor(
            "disabled.external_model_adapter",
            "external_model_adapter",
            "Disabled External Model Adapter",
            ("external_model",),
        )
    )


@dataclass(frozen=True, slots=True)
class ReplayAdapter(BaseMathModelAdapter):
    """回放适配器骨架，只返回回放引用。"""

    adapter_descriptor: MathAdapterDescriptor = field(
        default_factory=lambda: _descriptor(
            "disabled.replay_adapter",
            "replay_adapter",
            "Disabled Replay Adapter",
            ("replay",),
        )
    )


@dataclass(frozen=True, slots=True)
class ShadowAdapter(BaseMathModelAdapter):
    """影子适配器骨架，影子结果不影响主路径。"""

    adapter_descriptor: MathAdapterDescriptor = field(
        default_factory=lambda: _descriptor(
            "disabled.shadow_adapter",
            "shadow_adapter",
            "Disabled Shadow Adapter",
            ("shadow",),
        )
    )


@dataclass(frozen=True, slots=True)
class FallbackAdapter(BaseMathModelAdapter):
    """降级适配器骨架，返回安全默认引用。"""

    adapter_descriptor: MathAdapterDescriptor = field(
        default_factory=lambda: _descriptor(
            "disabled.fallback_adapter",
            "fallback_adapter",
            "Disabled Fallback Adapter",
            ("fallback",),
        )
    )
