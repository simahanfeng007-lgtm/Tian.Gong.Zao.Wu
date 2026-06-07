"""L1 第八阶段行动、副作用、事务、补偿与删除意图端口协议。

本模块在 L1 中的职责：定义行动意图、行动边界、副作用报告、副作用边界、事务边界、事务意图、补偿意图、变更回退提示、删除意图和删除边界协议。
本模块定义哪些端口：ActionIntentPort、ActionBoundaryPort、EffectReportPort、SideEffectBoundaryPort、TransactionBoundaryPort、TransactionIntentPort、CompensationIntentPort、ChangeRevertHintPort、DeletionIntentPort、DeletionBoundaryPort。
本模块不实现哪些能力：不执行行动、不产生副作用、不打开事务、不提交事务、不执行补偿、不执行删除、不写审计。
本模块禁止事项：不得访问文件、数据库、网络、模型、工具、插件或真实事务系统。
本模块与 L2-L6 的关系：L2 可记录行动状态，L3 可编排行动意图，L4 可实现外部适配，L5 可约束插件副作用，L6 可提交子系统变更和删除候选。
本模块如何服务工程生命体：让每次行动、副作用、补偿和删除都先有协议边界。
本模块如何维持大模型执行力与绝对边界：只声明高影响动作边界，不替大模型执行工具或选择 Skill。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.action import ActionIntent, ActionRef
from tiangong_kernel.l0_primitives.audit import AuditRef
from tiangong_kernel.l0_primitives.deletion import DeletionRef, TombstoneRef
from tiangong_kernel.l0_primitives.effect import EffectRef, EffectResultRef
from tiangong_kernel.l0_primitives.evidence import EvidenceRef
from tiangong_kernel.l0_primitives.resource import ResourceRef
from tiangong_kernel.l0_primitives.risk import RiskView
from tiangong_kernel.l0_primitives.trace import TraceContext
from tiangong_kernel.l0_primitives.transaction import CompensationRef, RollbackRef, TransactionRef
from tiangong_kernel.l0_primitives.validation import VerificationRef

from .envelope import PortBoundaryContext
from .port_boundary import BoundaryViolation, PortBoundary
from .port_result import PortResult

@dataclass(frozen=True, slots=True)
class ActionIntentEnvelope:
    """行动意图对象。作用：包装 L0 行动意图；边界：不执行行动。"""
    intent: ActionIntent
    action_ref: ActionRef | None = None
    risk_view: RiskView | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class ActionBoundary:
    """行动边界对象。作用：表达行动可用范围；边界：不做真实裁决。"""
    action_ref: ActionRef | None = None
    boundary: PortBoundary | None = None
    violations: tuple[BoundaryViolation, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class EffectReport:
    """副作用报告对象。作用：表达行动可能造成的效果引用；边界：不产生副作用、不写审计。"""
    effect_ref: EffectRef
    result_ref: EffectResultRef | None = None
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class SideEffectBoundary:
    """副作用边界对象。作用：表达副作用范围；边界：不清理副作用。"""
    effect_ref: EffectRef = None
    boundary: PortBoundary | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class TransactionBoundary:
    """事务边界对象。作用：表达事务边界；边界：不打开、不提交、不回滚事务。"""
    transaction_ref: TransactionRef = None
    boundary: PortBoundary | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class TransactionIntent:
    """事务意图对象。作用：表达事务意图；边界：不连接数据库、不锁资源。"""
    transaction_ref: TransactionRef
    target_ref: ResourceRef | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class CompensationIntent:
    """补偿意图对象。作用：表达补偿动作意图；边界：不执行补偿。"""
    compensation_ref: CompensationRef
    effect_ref: EffectRef = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class ChangeRevertHint:
    """变更回退提示对象。作用：表达变更可回退提示；边界：不执行回退。"""
    hint_ref: ResourceRef
    rollback_ref: RollbackRef | None = None
    verification_refs: tuple[VerificationRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class DeletionIntent:
    """删除意图对象。作用：表达删除意图；边界：不删除文件、不删除数据。"""
    deletion_ref: DeletionRef
    target_ref: ResourceRef | None = None
    tombstone_ref: TombstoneRef | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class DeletionBoundary:
    """删除边界对象。作用：表达删除边界；边界：不执行删除。"""
    deletion_ref: DeletionRef = None
    boundary: PortBoundary | None = None
    audit_ref: AuditRef | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class ActionIntentEnvelopeRequest:
    """ActionIntentEnvelope请求。作用：提交ActionIntentEnvelope；边界：只声明协议。"""
    payload: ActionIntentEnvelope
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class ActionBoundaryRequest:
    """ActionBoundary请求。作用：提交ActionBoundary；边界：只声明协议。"""
    payload: ActionBoundary
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class EffectReportRequest:
    """EffectReport请求。作用：提交EffectReport；边界：只声明协议。"""
    payload: EffectReport
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class SideEffectBoundaryRequest:
    """SideEffectBoundary请求。作用：提交SideEffectBoundary；边界：只声明协议。"""
    payload: SideEffectBoundary
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class TransactionBoundaryRequest:
    """TransactionBoundary请求。作用：提交TransactionBoundary；边界：只声明协议。"""
    payload: TransactionBoundary
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class TransactionIntentRequest:
    """TransactionIntent请求。作用：提交TransactionIntent；边界：只声明协议。"""
    payload: TransactionIntent
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class CompensationIntentRequest:
    """CompensationIntent请求。作用：提交CompensationIntent；边界：只声明协议。"""
    payload: CompensationIntent
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class ChangeRevertHintRequest:
    """ChangeRevertHint请求。作用：提交ChangeRevertHint；边界：只声明协议。"""
    payload: ChangeRevertHint
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class DeletionIntentRequest:
    """DeletionIntent请求。作用：提交DeletionIntent；边界：只声明协议。"""
    payload: DeletionIntent
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class DeletionBoundaryRequest:
    """DeletionBoundary请求。作用：提交DeletionBoundary；边界：只声明协议。"""
    payload: DeletionBoundary
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class ActionIntentEnvelopeResponse:
    """ActionIntentEnvelope响应。作用：返回ActionIntentEnvelope；边界：不执行真实能力。"""
    payload: ActionIntentEnvelope
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class ActionBoundaryResponse:
    """ActionBoundary响应。作用：返回ActionBoundary；边界：不执行真实能力。"""
    payload: ActionBoundary
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class EffectReportResponse:
    """EffectReport响应。作用：返回EffectReport；边界：不执行真实能力。"""
    payload: EffectReport
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class SideEffectBoundaryResponse:
    """SideEffectBoundary响应。作用：返回SideEffectBoundary；边界：不执行真实能力。"""
    payload: SideEffectBoundary
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class TransactionBoundaryResponse:
    """TransactionBoundary响应。作用：返回TransactionBoundary；边界：不执行真实能力。"""
    payload: TransactionBoundary
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class TransactionIntentResponse:
    """TransactionIntent响应。作用：返回TransactionIntent；边界：不执行真实能力。"""
    payload: TransactionIntent
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class CompensationIntentResponse:
    """CompensationIntent响应。作用：返回CompensationIntent；边界：不执行真实能力。"""
    payload: CompensationIntent
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class ChangeRevertHintResponse:
    """ChangeRevertHint响应。作用：返回ChangeRevertHint；边界：不执行真实能力。"""
    payload: ChangeRevertHint
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class DeletionIntentResponse:
    """DeletionIntent响应。作用：返回DeletionIntent；边界：不执行真实能力。"""
    payload: DeletionIntent
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class DeletionBoundaryResponse:
    """DeletionBoundary响应。作用：返回DeletionBoundary；边界：不执行真实能力。"""
    payload: DeletionBoundary
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

class ActionIntentPort(ABC):
    """行动意图端口。中文名称：行动意图端口。端口职责：定义行动意图协议。输入输出边界：输入 ActionIntentEnvelopeRequest 与 TraceContext，输出 PortResult。所属 L1 层：第八阶段行动边界。不承担的实现职责：不执行行动。如何服务大模型执行力：让模型动作先形成可审计意图。如何维持绝对边界：意图不产生副作用。与后续 L2-L6 的关系：供编排和审计链引用。"""
    @abstractmethod
    def declare_action_intent(self, request: ActionIntentEnvelopeRequest, trace: TraceContext) -> PortResult[ActionIntentEnvelopeResponse]:
        """声明行动意图端口。"""
        raise NotImplementedError

class ActionBoundaryPort(ABC):
    """行动边界端口。中文名称：行动边界端口。端口职责：定义行动边界协议。输入输出边界：输入 ActionBoundaryRequest 与 TraceContext，输出 PortResult。所属 L1 层：第八阶段行动边界。不承担的实现职责：不做真实裁决。如何服务大模型执行力：清晰表达越界原因。如何维持绝对边界：边界不执行动作。与后续 L2-L6 的关系：供控制面和编排层引用。"""
    @abstractmethod
    def describe_action_boundary(self, request: ActionBoundaryRequest, trace: TraceContext) -> PortResult[ActionBoundaryResponse]:
        """声明行动边界端口。"""
        raise NotImplementedError

class EffectReportPort(ABC):
    """副作用报告端口。中文名称：副作用报告端口。端口职责：定义副作用报告协议。输入输出边界：输入 EffectReportRequest 与 TraceContext，输出 PortResult。所属 L1 层：第八阶段副作用协议。不承担的实现职责：不产生副作用、不写审计。如何服务大模型执行力：让工具结果可表达影响。如何维持绝对边界：报告不产生新动作。与后续 L2-L6 的关系：供观察面和审计链引用。"""
    @abstractmethod
    def report_effect(self, request: EffectReportRequest, trace: TraceContext) -> PortResult[EffectReportResponse]:
        """声明副作用报告端口。"""
        raise NotImplementedError

class SideEffectBoundaryPort(ABC):
    """副作用边界端口。中文名称：副作用边界端口。端口职责：定义副作用边界协议。输入输出边界：输入 SideEffectBoundaryRequest 与 TraceContext，输出 PortResult。所属 L1 层：第八阶段副作用协议。不承担的实现职责：不清理副作用。如何服务大模型执行力：让高影响副作用可解释。如何维持绝对边界：边界不代替补偿。与后续 L2-L6 的关系：供事务和恢复链引用。"""
    @abstractmethod
    def describe_side_effect_boundary(self, request: SideEffectBoundaryRequest, trace: TraceContext) -> PortResult[SideEffectBoundaryResponse]:
        """声明副作用边界端口。"""
        raise NotImplementedError

class TransactionBoundaryPort(ABC):
    """事务边界端口。中文名称：事务边界端口。端口职责：定义事务边界协议。输入输出边界：输入 TransactionBoundaryRequest 与 TraceContext，输出 PortResult。所属 L1 层：第八阶段事务协议。不承担的实现职责：不打开事务、不提交事务。如何服务大模型执行力：让复杂动作有事务边界说明。如何维持绝对边界：边界不锁资源。与后续 L2-L6 的关系：供编排和外部适配引用。"""
    @abstractmethod
    def describe_transaction_boundary(self, request: TransactionBoundaryRequest, trace: TraceContext) -> PortResult[TransactionBoundaryResponse]:
        """声明事务边界端口。"""
        raise NotImplementedError

class TransactionIntentPort(ABC):
    """事务意图端口。中文名称：事务意图端口。端口职责：定义事务意图协议。输入输出边界：输入 TransactionIntentRequest 与 TraceContext，输出 PortResult。所属 L1 层：第八阶段事务协议。不承担的实现职责：不连接数据库、不锁资源。如何服务大模型执行力：为组合行动表达原子性需求。如何维持绝对边界：意图不打开事务。与后续 L2-L6 的关系：供编排层引用。"""
    @abstractmethod
    def submit_transaction_intent(self, request: TransactionIntentRequest, trace: TraceContext) -> PortResult[TransactionIntentResponse]:
        """声明事务意图端口。"""
        raise NotImplementedError

class CompensationIntentPort(ABC):
    """补偿意图端口。中文名称：补偿意图端口。端口职责：定义补偿意图协议。输入输出边界：输入 CompensationIntentRequest 与 TraceContext，输出 PortResult。所属 L1 层：第八阶段补偿协议。不承担的实现职责：不执行补偿。如何服务大模型执行力：让失败链条有补偿建议。如何维持绝对边界：建议不触发动作。与后续 L2-L6 的关系：供恢复和事务链引用。"""
    @abstractmethod
    def submit_compensation_intent(self, request: CompensationIntentRequest, trace: TraceContext) -> PortResult[CompensationIntentResponse]:
        """声明补偿意图端口。"""
        raise NotImplementedError

class ChangeRevertHintPort(ABC):
    """变更回退提示端口。中文名称：变更回退提示端口。端口职责：定义变更回退提示协议。输入输出边界：输入 ChangeRevertHintRequest 与 TraceContext，输出 PortResult。所属 L1 层：第八阶段回退协议。不承担的实现职责：不执行回退。如何服务大模型执行力：保留可逆性信息。如何维持绝对边界：提示不改系统。与后续 L2-L6 的关系：供变更和回退验证引用。"""
    @abstractmethod
    def submit_change_revert_hint(self, request: ChangeRevertHintRequest, trace: TraceContext) -> PortResult[ChangeRevertHintResponse]:
        """声明变更回退提示端口。"""
        raise NotImplementedError

class DeletionIntentPort(ABC):
    """删除意图端口。中文名称：删除意图端口。端口职责：定义删除意图协议。输入输出边界：输入 DeletionIntentRequest 与 TraceContext，输出 PortResult。所属 L1 层：第八阶段删除边界。不承担的实现职责：不删除文件、不删除数据。如何服务大模型执行力：让删除先变成可审核意图。如何维持绝对边界：意图不能删除真实对象。与后续 L2-L6 的关系：供边界、验证和审计链引用。"""
    @abstractmethod
    def declare_deletion_intent(self, request: DeletionIntentRequest, trace: TraceContext) -> PortResult[DeletionIntentResponse]:
        """声明删除意图端口。"""
        raise NotImplementedError

class DeletionBoundaryPort(ABC):
    """删除边界端口。中文名称：删除边界端口。端口职责：定义删除边界协议。输入输出边界：输入 DeletionBoundaryRequest 与 TraceContext，输出 PortResult。所属 L1 层：第八阶段删除边界。不承担的实现职责：不执行删除。如何服务大模型执行力：给危险动作提供替代路径。如何维持绝对边界：边界不触发物理操作。与后续 L2-L6 的关系：供外部适配和审计链引用。"""
    @abstractmethod
    def describe_deletion_boundary(self, request: DeletionBoundaryRequest, trace: TraceContext) -> PortResult[DeletionBoundaryResponse]:
        """声明删除边界端口。"""
        raise NotImplementedError
