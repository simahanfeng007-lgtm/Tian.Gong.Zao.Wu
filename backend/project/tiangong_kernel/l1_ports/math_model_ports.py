"""L1 数学模型端口协议。

This module reserves stable L1 entry points for future mathematical model
engines.  It defines protocol shapes only: no formulas, no scoring algorithm,
no model invocation, no persistence, and no upper-layer imports.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef
from tiangong_kernel.l0_primitives.result import CoreResult
from tiangong_kernel.l0_primitives.trace import TraceContext

from .port_result import PortResult


MATH_MODEL_PORT_SCHEMA_VERSION = "0.1"


@dataclass(frozen=True, slots=True)
class MathModelPortBoundary:
    """数学模型端口边界声明，只表达协议边界事实。"""

    boundary_ref: TypedRef | None = None
    port_family: str = "mathematical_model"
    protocol_only: bool = True
    advisory_only: bool = True
    allows_algorithm_implementation: bool = False
    allows_external_call: bool = False
    allows_state_write: bool = False
    allows_permission_grant: bool = False
    schema_version: str = MATH_MODEL_PORT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.protocol_only is not True:
            raise ValueError("MathModelPortBoundary.protocol_only must remain true")
        if self.advisory_only is not True:
            raise ValueError("MathModelPortBoundary.advisory_only must remain true")
        if self.allows_algorithm_implementation:
            raise ValueError("L1 math ports cannot implement algorithms")
        if self.allows_external_call:
            raise ValueError("L1 math ports cannot call external systems")
        if self.allows_state_write:
            raise ValueError("L1 math ports cannot write state")
        if self.allows_permission_grant:
            raise ValueError("L1 math ports cannot grant permission")
        if not self.schema_version:
            raise ValueError("MathModelPortBoundary.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class MathematicalModelRequest:
    """数学模型端口通用请求信封。"""

    request_ref: TypedRef | None = None
    model_ref: TypedRef | None = None
    input_snapshot_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    formula_profile_ref: TypedRef | None = None
    trace_context: TraceContext | None = None
    request_kind: str = "mathematical_model"
    advisory_only: bool = True
    schema_version: str = MATH_MODEL_PORT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not self.request_kind:
            raise ValueError("MathematicalModelRequest.request_kind cannot be empty")
        if self.advisory_only is not True:
            raise ValueError("MathematicalModelRequest.advisory_only must remain true")
        if not self.schema_version:
            raise ValueError("MathematicalModelRequest.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class MathematicalModelResponse:
    """数学模型端口通用响应信封。"""

    response_ref: TypedRef | None = None
    model_ref: TypedRef | None = None
    output_snapshot_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    result_ref: TypedRef | None = None
    confidence_ref: TypedRef | None = None
    trace_ref: TypedRef | None = None
    response_kind: str = "mathematical_model"
    advisory_only: bool = True
    grants_permission: bool = False
    writes_state: bool = False
    schema_version: str = MATH_MODEL_PORT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not self.response_kind:
            raise ValueError("MathematicalModelResponse.response_kind cannot be empty")
        if self.advisory_only is not True:
            raise ValueError("MathematicalModelResponse.advisory_only must remain true")
        if self.grants_permission:
            raise ValueError("Math model responses cannot grant permission")
        if self.writes_state:
            raise ValueError("Math model responses cannot write state")
        if not self.schema_version:
            raise ValueError("MathematicalModelResponse.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ScoringRequest(MathematicalModelRequest):
    """评分端口请求，只携带候选与评分配置引用。"""

    request_kind: str = "scoring"
    candidate_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    score_profile_ref: TypedRef | None = None


@dataclass(frozen=True, slots=True)
class ScoringResponse(MathematicalModelResponse):
    """评分端口响应，只携带评分结果引用。"""

    response_kind: str = "scoring"
    score_refs: tuple[TypedRef, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class MemoryModelRequest(MathematicalModelRequest):
    """记忆模型端口请求，只携带记忆状态引用。"""

    request_kind: str = "memory_model"
    memory_refs: tuple[TypedRef, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class MemoryModelResponse(MathematicalModelResponse):
    """记忆模型端口响应，只携带记忆评分引用。"""

    response_kind: str = "memory_model"
    memory_score_refs: tuple[TypedRef, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class ForgettingModelRequest(MathematicalModelRequest):
    """遗忘模型端口请求，只携带保留候选引用。"""

    request_kind: str = "forgetting_model"
    retention_candidate_refs: tuple[TypedRef, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class ForgettingModelResponse(MathematicalModelResponse):
    """遗忘模型端口响应，只携带遗忘评分引用。"""

    response_kind: str = "forgetting_model"
    forgetting_score_refs: tuple[TypedRef, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class RetentionModelRequest(MathematicalModelRequest):
    """保留模型端口请求，只携带保留目标引用。"""

    request_kind: str = "retention_model"
    retention_target_refs: tuple[TypedRef, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class RetentionModelResponse(MathematicalModelResponse):
    """保留模型端口响应，只携带保留评分引用。"""

    response_kind: str = "retention_model"
    retention_score_refs: tuple[TypedRef, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class DecayModelRequest(MathematicalModelRequest):
    """衰减模型端口请求，只携带衰减目标引用。"""

    request_kind: str = "decay_model"
    decay_target_refs: tuple[TypedRef, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class DecayModelResponse(MathematicalModelResponse):
    """衰减模型端口响应，只携带衰减评分引用。"""

    response_kind: str = "decay_model"
    decay_score_refs: tuple[TypedRef, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class ReinforcementModelRequest(MathematicalModelRequest):
    """强化模型端口请求，只携带强化信号引用。"""

    request_kind: str = "reinforcement_model"
    signal_refs: tuple[TypedRef, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class ReinforcementModelResponse(MathematicalModelResponse):
    """强化模型端口响应，只携带强化评分引用。"""

    response_kind: str = "reinforcement_model"
    reinforcement_score_refs: tuple[TypedRef, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class InterferenceModelRequest(MathematicalModelRequest):
    """干扰模型端口请求，只携带竞争信号引用。"""

    request_kind: str = "interference_model"
    competing_signal_refs: tuple[TypedRef, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class InterferenceModelResponse(MathematicalModelResponse):
    """干扰模型端口响应，只携带干扰评分引用。"""

    response_kind: str = "interference_model"
    interference_score_refs: tuple[TypedRef, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class HealthModelRequest(MathematicalModelRequest):
    """健康模型端口请求，只携带生命体征状态引用。"""

    request_kind: str = "health_model"
    vital_state_refs: tuple[TypedRef, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class HealthModelResponse(MathematicalModelResponse):
    """健康模型端口响应，只携带健康评分引用。"""

    response_kind: str = "health_model"
    health_score_refs: tuple[TypedRef, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class HomeostasisModelRequest(MathematicalModelRequest):
    """稳态模型端口请求，只携带平衡状态引用。"""

    request_kind: str = "homeostasis_model"
    balance_state_refs: tuple[TypedRef, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class HomeostasisModelResponse(MathematicalModelResponse):
    """稳态模型端口响应，只携带稳态评分引用。"""

    response_kind: str = "homeostasis_model"
    homeostasis_score_refs: tuple[TypedRef, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class RiskModelRequest(MathematicalModelRequest):
    """风险模型端口请求，只携带风险信号引用。"""

    request_kind: str = "risk_model"
    risk_signal_refs: tuple[TypedRef, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class RiskModelResponse(MathematicalModelResponse):
    """风险模型端口响应，只携带风险评分引用。"""

    response_kind: str = "risk_model"
    risk_score_refs: tuple[TypedRef, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class ResourcePressureModelRequest(MathematicalModelRequest):
    """资源压力模型端口请求，只携带资源状态引用。"""

    request_kind: str = "resource_pressure_model"
    resource_state_refs: tuple[TypedRef, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class ResourcePressureModelResponse(MathematicalModelResponse):
    """资源压力模型端口响应，只携带压力评分引用。"""

    response_kind: str = "resource_pressure_model"
    pressure_score_refs: tuple[TypedRef, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class EvolutionAssessmentRequest(MathematicalModelRequest):
    """进化评估端口请求，只携带候选引用。"""

    request_kind: str = "evolution_assessment"
    candidate_refs: tuple[TypedRef, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class EvolutionAssessmentResponse(MathematicalModelResponse):
    """进化评估端口响应，只携带评估引用。"""

    response_kind: str = "evolution_assessment"
    assessment_refs: tuple[TypedRef, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class RegressionRiskModelRequest(MathematicalModelRequest):
    """回归风险模型端口请求，只携带变更引用。"""

    request_kind: str = "regression_risk_model"
    change_refs: tuple[TypedRef, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class RegressionRiskModelResponse(MathematicalModelResponse):
    """回归风险模型端口响应，只携带回归风险引用。"""

    response_kind: str = "regression_risk_model"
    regression_risk_refs: tuple[TypedRef, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class LearningAssessmentRequest(MathematicalModelRequest):
    """学习评估端口请求，只携带学习信号引用。"""

    request_kind: str = "learning_assessment"
    learning_signal_refs: tuple[TypedRef, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class LearningAssessmentResponse(MathematicalModelResponse):
    """学习评估端口响应，只携带学习评估引用。"""

    response_kind: str = "learning_assessment"
    learning_assessment_refs: tuple[TypedRef, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class AdaptationDecisionRequest(MathematicalModelRequest):
    """适应决策端口请求，只携带适应信号引用。"""

    request_kind: str = "adaptation_decision"
    adaptation_signal_refs: tuple[TypedRef, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class AdaptationDecisionResponse(MathematicalModelResponse):
    """适应决策端口响应，只携带适应建议引用。"""

    response_kind: str = "adaptation_decision"
    adaptation_advice_refs: tuple[TypedRef, ...] = field(default_factory=tuple)


class MathematicalModelPort(ABC):
    """数学模型端口基础抽象协议。"""

    @abstractmethod
    def describe_math_model_boundary(self) -> CoreResult[MathModelPortBoundary]:
        """Return protocol boundary facts only."""

    @abstractmethod
    def evaluate(self, request: MathematicalModelRequest) -> PortResult[MathematicalModelResponse]:
        """Evaluate a declared request through a future implementation."""


class ScoringPort(MathematicalModelPort):
    """评分端口抽象协议，只定义 score 形状。"""

    @abstractmethod
    def score(self, request: ScoringRequest) -> PortResult[ScoringResponse]:
        """Return scoring response facts from a future scoring implementation."""


class MemoryModelPort(MathematicalModelPort):
    """记忆模型端口抽象协议。"""

    @abstractmethod
    def model_memory(self, request: MemoryModelRequest) -> PortResult[MemoryModelResponse]:
        """Return memory model response facts."""


class ForgettingModelPort(MathematicalModelPort):
    """遗忘模型端口抽象协议。"""

    @abstractmethod
    def model_forgetting(self, request: ForgettingModelRequest) -> PortResult[ForgettingModelResponse]:
        """Return forgetting model response facts."""


class RetentionModelPort(MathematicalModelPort):
    """保留模型端口抽象协议。"""

    @abstractmethod
    def model_retention(self, request: RetentionModelRequest) -> PortResult[RetentionModelResponse]:
        """Return retention model response facts."""


class DecayModelPort(MathematicalModelPort):
    """衰减模型端口抽象协议。"""

    @abstractmethod
    def model_decay(self, request: DecayModelRequest) -> PortResult[DecayModelResponse]:
        """Return decay model response facts."""


class ReinforcementModelPort(MathematicalModelPort):
    """强化模型端口抽象协议。"""

    @abstractmethod
    def model_reinforcement(self, request: ReinforcementModelRequest) -> PortResult[ReinforcementModelResponse]:
        """Return reinforcement model response facts."""


class InterferenceModelPort(MathematicalModelPort):
    """干扰模型端口抽象协议。"""

    @abstractmethod
    def model_interference(self, request: InterferenceModelRequest) -> PortResult[InterferenceModelResponse]:
        """Return interference model response facts."""


class HealthModelPort(MathematicalModelPort):
    """健康模型端口抽象协议。"""

    @abstractmethod
    def model_health(self, request: HealthModelRequest) -> PortResult[HealthModelResponse]:
        """Return health model response facts."""


class HomeostasisModelPort(MathematicalModelPort):
    """稳态模型端口抽象协议。"""

    @abstractmethod
    def model_homeostasis(self, request: HomeostasisModelRequest) -> PortResult[HomeostasisModelResponse]:
        """Return homeostasis model response facts."""


class RiskModelPort(MathematicalModelPort):
    """风险模型端口抽象协议。"""

    @abstractmethod
    def model_risk(self, request: RiskModelRequest) -> PortResult[RiskModelResponse]:
        """Return risk model response facts."""


class ResourcePressureModelPort(MathematicalModelPort):
    """资源压力模型端口抽象协议。"""

    @abstractmethod
    def model_resource_pressure(
        self, request: ResourcePressureModelRequest
    ) -> PortResult[ResourcePressureModelResponse]:
        """Return resource pressure model response facts."""


class EvolutionAssessmentPort(MathematicalModelPort):
    """进化评估端口抽象协议。"""

    @abstractmethod
    def assess_evolution(self, request: EvolutionAssessmentRequest) -> PortResult[EvolutionAssessmentResponse]:
        """Return evolution assessment response facts."""


class RegressionRiskModelPort(MathematicalModelPort):
    """回归风险模型端口抽象协议。"""

    @abstractmethod
    def model_regression_risk(
        self, request: RegressionRiskModelRequest
    ) -> PortResult[RegressionRiskModelResponse]:
        """Return regression risk model response facts."""


class LearningAssessmentPort(MathematicalModelPort):
    """学习评估端口抽象协议。"""

    @abstractmethod
    def assess_learning(self, request: LearningAssessmentRequest) -> PortResult[LearningAssessmentResponse]:
        """Return learning assessment response facts."""


class AdaptationDecisionPort(MathematicalModelPort):
    """适应决策端口抽象协议，只产出建议事实。"""

    @abstractmethod
    def advise_adaptation(self, request: AdaptationDecisionRequest) -> PortResult[AdaptationDecisionResponse]:
        """Return adaptation advice facts without granting action."""
