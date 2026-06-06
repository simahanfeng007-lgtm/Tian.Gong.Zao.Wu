"""L1 第八阶段实验、对比、观察与结果端口协议。

本模块在 L1 中的职责：定义实验意图、实验边界、实验设计提示、实验观察、实验结果、实验对比提示和实验回退提示协议。
本模块定义哪些端口：ExperimentIntentPort、ExperimentBoundaryPort、ExperimentDesignHintPort、ExperimentObservationPort、ExperimentResultPort、ExperimentComparisonHintPort、ExperimentRollbackHintPort。
本模块不实现哪些能力：不启动实验、不隔离环境、不执行动作、不生成真实实验计划、不采集真实观察、不计算结果、不执行 A/B 测试、不做统计检验、不执行回退。
本模块禁止事项：不得访问文件、数据库、网络、模型、工具、插件或真实实验平台。
本模块与 L2-L6 的关系：L2 可记录实验状态，L3 可编排实验意图，L4 可实现外部实验适配，L5 可隔离插件实验，L6 可提交子系统候选对比。
本模块如何服务工程生命体：让学习、迭代、进化候选可以被实验化、对比化、证据化。
本模块如何维持大模型执行力与绝对边界：实验只做协议入口，不直接改变系统。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.evidence import EvidenceRef
from tiangong_kernel.l0_primitives.metric import MetricRef
from tiangong_kernel.l0_primitives.observation import ObservationRef
from .candidate_ports import CandidateReference
from .model_reflection_ports import ModelOutcomeAssessment
from tiangong_kernel.l0_primitives.resource import ResourceRef
from tiangong_kernel.l0_primitives.trace import TraceContext
from tiangong_kernel.l0_primitives.validation import TestRef, ValidationRef

from .candidate_ports import CandidateReference
from .envelope import PortBoundaryContext
from .model_reflection_ports import ModelOutcomeAssessment
from .port_boundary import BoundaryViolation, PortBoundary
from .port_result import PortResult

@dataclass(frozen=True, slots=True)
class ExperimentIntent:
    """实验意图对象。作用：表达实验意图；边界：不启动实验。"""
    experiment_ref: ResourceRef
    candidate: CandidateReference | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class ExperimentBoundary:
    """实验边界对象。作用：表达实验边界；边界：不隔离环境、不执行动作。"""
    experiment_ref: ResourceRef
    boundary: PortBoundary | None = None
    violations: tuple[BoundaryViolation, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class ExperimentDesignHint:
    """实验设计提示对象。作用：表达实验设计提示；边界：不生成真实实验计划。"""
    hint_ref: ResourceRef
    experiment_ref: ResourceRef | None = None
    test_refs: tuple[TestRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class ExperimentObservation:
    """实验观察对象。作用：表达实验观察引用；边界：不采集真实观察。"""
    experiment_ref: ResourceRef
    observation_refs: tuple[ObservationRef, ...] = field(default_factory=tuple)
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class ExperimentResult:
    """实验结果对象。作用：表达实验结果引用；边界：不计算结果。"""
    experiment_ref: ResourceRef
    metric_refs: tuple[MetricRef, ...] = field(default_factory=tuple)
    validation_refs: tuple[ValidationRef, ...] = field(default_factory=tuple)
    assessment: ModelOutcomeAssessment | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class ExperimentComparisonHint:
    """实验对比提示对象。作用：表达候选对比提示；边界：不执行 A/B 测试、不做统计检验算法。"""
    hint_ref: ResourceRef
    left_candidate: CandidateReference | None = None
    right_candidate: CandidateReference | None = None
    metric_refs: tuple[MetricRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class ExperimentRollbackHint:
    """实验回退提示对象。作用：表达实验回退提示；边界：不执行回退。"""
    hint_ref: ResourceRef
    experiment_ref: ResourceRef | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class ExperimentIntentRequest:
    """ExperimentIntent请求。作用：提交ExperimentIntent；边界：只声明实验协议。"""
    payload: ExperimentIntent
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class ExperimentBoundaryRequest:
    """ExperimentBoundary请求。作用：提交ExperimentBoundary；边界：只声明实验协议。"""
    payload: ExperimentBoundary
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class ExperimentDesignHintRequest:
    """ExperimentDesignHint请求。作用：提交ExperimentDesignHint；边界：只声明实验协议。"""
    payload: ExperimentDesignHint
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class ExperimentObservationRequest:
    """ExperimentObservation请求。作用：提交ExperimentObservation；边界：只声明实验协议。"""
    payload: ExperimentObservation
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class ExperimentResultRequest:
    """ExperimentResult请求。作用：提交ExperimentResult；边界：只声明实验协议。"""
    payload: ExperimentResult
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class ExperimentComparisonHintRequest:
    """ExperimentComparisonHint请求。作用：提交ExperimentComparisonHint；边界：只声明实验协议。"""
    payload: ExperimentComparisonHint
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class ExperimentRollbackHintRequest:
    """ExperimentRollbackHint请求。作用：提交ExperimentRollbackHint；边界：只声明实验协议。"""
    payload: ExperimentRollbackHint
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class ExperimentIntentResponse:
    """ExperimentIntent响应。作用：返回ExperimentIntent；边界：不执行实验。"""
    payload: ExperimentIntent
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class ExperimentBoundaryResponse:
    """ExperimentBoundary响应。作用：返回ExperimentBoundary；边界：不执行实验。"""
    payload: ExperimentBoundary
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class ExperimentDesignHintResponse:
    """ExperimentDesignHint响应。作用：返回ExperimentDesignHint；边界：不执行实验。"""
    payload: ExperimentDesignHint
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class ExperimentObservationResponse:
    """ExperimentObservation响应。作用：返回ExperimentObservation；边界：不执行实验。"""
    payload: ExperimentObservation
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class ExperimentResultResponse:
    """ExperimentResult响应。作用：返回ExperimentResult；边界：不执行实验。"""
    payload: ExperimentResult
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class ExperimentComparisonHintResponse:
    """ExperimentComparisonHint响应。作用：返回ExperimentComparisonHint；边界：不执行实验。"""
    payload: ExperimentComparisonHint
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class ExperimentRollbackHintResponse:
    """ExperimentRollbackHint响应。作用：返回ExperimentRollbackHint；边界：不执行实验。"""
    payload: ExperimentRollbackHint
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

class ExperimentIntentPort(ABC):
    """实验意图端口。中文名称：实验意图端口。端口职责：定义实验意图协议。输入输出边界：输入 ExperimentIntentRequest 与 TraceContext，输出 PortResult。所属 L1 层：第八阶段实验协议。不承担的实现职责：不启动实验。如何服务大模型执行力：让模型可提出候选实验方向。如何维持绝对边界：意图不执行实验。与后续 L2-L6 的关系：供验证和子系统实验链引用。"""
    @abstractmethod
    def submit_experiment_intent(self, request: ExperimentIntentRequest, trace: TraceContext) -> PortResult[ExperimentIntentResponse]:
        """声明实验意图端口。"""
        raise NotImplementedError

class ExperimentBoundaryPort(ABC):
    """实验边界端口。中文名称：实验边界端口。端口职责：定义实验边界协议。输入输出边界：输入 ExperimentBoundaryRequest 与 TraceContext，输出 PortResult。所属 L1 层：第八阶段实验协议。不承担的实现职责：不隔离环境、不执行动作。如何服务大模型执行力：让实验风险可解释。如何维持绝对边界：边界不启动实验。与后续 L2-L6 的关系：供安全和验证链引用。"""
    @abstractmethod
    def describe_experiment_boundary(self, request: ExperimentBoundaryRequest, trace: TraceContext) -> PortResult[ExperimentBoundaryResponse]:
        """声明实验边界端口。"""
        raise NotImplementedError

class ExperimentDesignHintPort(ABC):
    """实验设计提示端口。中文名称：实验设计提示端口。端口职责：定义实验设计提示协议。输入输出边界：输入 ExperimentDesignHintRequest 与 TraceContext，输出 PortResult。所属 L1 层：第八阶段实验协议。不承担的实现职责：不生成真实实验计划。如何服务大模型执行力：让候选验证更清晰。如何维持绝对边界：提示不执行计划。与后续 L2-L6 的关系：供实验适配和验证链引用。"""
    @abstractmethod
    def submit_experiment_design_hint(self, request: ExperimentDesignHintRequest, trace: TraceContext) -> PortResult[ExperimentDesignHintResponse]:
        """声明实验设计提示端口。"""
        raise NotImplementedError

class ExperimentObservationPort(ABC):
    """实验观察端口。中文名称：实验观察端口。端口职责：定义实验观察协议。输入输出边界：输入 ExperimentObservationRequest 与 TraceContext，输出 PortResult。所属 L1 层：第八阶段实验协议。不承担的实现职责：不采集真实观察。如何服务大模型执行力：让实验结果可回传模型。如何维持绝对边界：观察协议不读取环境。与后续 L2-L6 的关系：供观察面和验证链引用。"""
    @abstractmethod
    def submit_experiment_observation(self, request: ExperimentObservationRequest, trace: TraceContext) -> PortResult[ExperimentObservationResponse]:
        """声明实验观察端口。"""
        raise NotImplementedError

class ExperimentResultPort(ABC):
    """实验结果端口。中文名称：实验结果端口。端口职责：定义实验结果协议。输入输出边界：输入 ExperimentResultRequest 与 TraceContext，输出 PortResult。所属 L1 层：第八阶段实验协议。不承担的实现职责：不计算结果。如何服务大模型执行力：让模型获得结果引用。如何维持绝对边界：结果引用不合入候选。与后续 L2-L6 的关系：供候选验证和状态层引用。"""
    @abstractmethod
    def submit_experiment_result(self, request: ExperimentResultRequest, trace: TraceContext) -> PortResult[ExperimentResultResponse]:
        """声明实验结果端口。"""
        raise NotImplementedError

class ExperimentComparisonHintPort(ABC):
    """实验对比提示端口。中文名称：实验对比提示端口。端口职责：定义实验对比提示协议。输入输出边界：输入 ExperimentComparisonHintRequest 与 TraceContext，输出 PortResult。所属 L1 层：第八阶段实验协议。不承担的实现职责：不执行 A/B 测试、不做统计检验算法。如何服务大模型执行力：让候选可以被比较。如何维持绝对边界：对比提示不改变系统。与后续 L2-L6 的关系：供实验验证和候选治理引用。"""
    @abstractmethod
    def submit_experiment_comparison_hint(self, request: ExperimentComparisonHintRequest, trace: TraceContext) -> PortResult[ExperimentComparisonHintResponse]:
        """声明实验对比提示端口。"""
        raise NotImplementedError

class ExperimentRollbackHintPort(ABC):
    """实验回退提示端口。中文名称：实验回退提示端口。端口职责：定义实验回退提示协议。输入输出边界：输入 ExperimentRollbackHintRequest 与 TraceContext，输出 PortResult。所属 L1 层：第八阶段实验协议。不承担的实现职责：不执行回退。如何服务大模型执行力：让实验失败有恢复方向。如何维持绝对边界：提示不恢复状态。与后续 L2-L6 的关系：供恢复和验证链引用。"""
    @abstractmethod
    def submit_experiment_rollback_hint(self, request: ExperimentRollbackHintRequest, trace: TraceContext) -> PortResult[ExperimentRollbackHintResponse]:
        """声明实验回退提示端口。"""
        raise NotImplementedError
