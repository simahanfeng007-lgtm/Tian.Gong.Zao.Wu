"""L1 第八阶段状态连续性端口协议。

本模块在 L1 中的职责：定义快照、检查点、恢复点、状态连续性边界、恢复提示和连续性证据协议。
本模块定义哪些端口：SnapshotReferencePort、SnapshotIntentPort、CheckpointReferencePort、CheckpointIntentPort、RestorePointReferencePort、RecoveryPointPort、StateContinuityBoundaryPort、StateRecoveryHintPort、ContinuityEvidencePort。
本模块不实现哪些能力：不创建真实快照、不保存检查点、不恢复状态、不实现状态机、不采集真实证据。
本模块禁止事项：不得读取或写入真实状态，不得访问文件、数据库、网络、模型、工具或插件系统。
本模块与 L2-L6 的关系：L2 可记录生命体状态连续性，L3 可编排恢复意图，L4 可实现外部恢复适配，L5 可隔离插件状态，L6 可提交子系统连续性证据。
本模块如何服务工程生命体：为长链任务、自我迭代和进化候选提供不中断的状态引用语言。
本模块如何维持大模型执行力与绝对边界：只表达恢复和连续性协议，不执行恢复迁移。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.audit import AuditRef
from tiangong_kernel.l0_primitives.evidence import EvidenceRef
from tiangong_kernel.l0_primitives.resource import ResourceRef
from tiangong_kernel.l0_primitives.state import CheckpointRef, RecoveryPointRef, RuntimeStateRef, StateDeltaRef, StateSnapshotRef
from tiangong_kernel.l0_primitives.trace import TraceContext
from tiangong_kernel.l0_primitives.validation import VerificationRef
from tiangong_kernel.l0_primitives.versioning import VersionRef

from .envelope import PortBoundaryContext
from .evolution_ports import EvolutionContinuity
from .port_boundary import BoundaryViolation, PortBoundary
from .port_result import PortResult

@dataclass(frozen=True, slots=True)
class SnapshotReference:
    """快照引用对象。作用：表达快照引用；边界：不创建真实快照。"""
    snapshot_ref: StateSnapshotRef
    state_ref: RuntimeStateRef | None = None
    version_ref: VersionRef | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class SnapshotIntent:
    """快照意图对象。作用：表达快照创建意图；边界：不读取状态、不写状态。"""
    intent_ref: ResourceRef
    state_ref: RuntimeStateRef | None = None
    snapshot_ref: StateSnapshotRef = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class CheckpointReference:
    """检查点引用对象。作用：表达检查点引用；边界：不创建检查点。"""
    checkpoint_ref: CheckpointRef
    snapshot_ref: StateSnapshotRef = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class CheckpointIntent:
    """检查点意图对象。作用：表达检查点保存意图；边界：不保存检查点。"""
    intent_ref: ResourceRef
    checkpoint_ref: CheckpointRef = None
    state_delta_ref: StateDeltaRef | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class RestorePointReference:
    """恢复点引用对象。作用：表达恢复点引用；边界：不创建恢复点、不恢复状态。"""
    restore_ref: ResourceRef
    recovery_point_ref: RecoveryPointRef = None
    checkpoint_ref: CheckpointRef = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class RecoveryPoint:
    """恢复点对象。作用：表达恢复点协议；边界：不执行恢复。"""
    recovery_point_ref: RecoveryPointRef
    snapshot_ref: StateSnapshotRef = None
    verification_refs: tuple[VerificationRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class StateContinuityBoundary:
    """状态连续性边界对象。作用：表达状态连续性约束；边界：不实现状态机。"""
    boundary_ref: ResourceRef
    boundary: PortBoundary | None = None
    evolution_continuity: EvolutionContinuity | None = None
    violations: tuple[BoundaryViolation, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class StateRecoveryHint:
    """状态恢复提示对象。作用：表达恢复策略提示；边界：不执行恢复策略。"""
    hint_ref: ResourceRef
    recovery_point_ref: RecoveryPointRef = None
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class ContinuityEvidence:
    """连续性证据对象。作用：表达状态连续性证据引用；边界：不采集真实证据。"""
    evidence_ref: EvidenceRef
    audit_ref: AuditRef | None = None
    snapshot_ref: StateSnapshotRef = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class SnapshotReferenceRequest:
    """SnapshotReference请求。作用：提交SnapshotReference；边界：只声明协议。"""
    payload: SnapshotReference
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class SnapshotIntentRequest:
    """SnapshotIntent请求。作用：提交SnapshotIntent；边界：只声明协议。"""
    payload: SnapshotIntent
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class CheckpointReferenceRequest:
    """CheckpointReference请求。作用：提交CheckpointReference；边界：只声明协议。"""
    payload: CheckpointReference
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class CheckpointIntentRequest:
    """CheckpointIntent请求。作用：提交CheckpointIntent；边界：只声明协议。"""
    payload: CheckpointIntent
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class RestorePointReferenceRequest:
    """RestorePointReference请求。作用：提交RestorePointReference；边界：只声明协议。"""
    payload: RestorePointReference
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class RecoveryPointRequest:
    """RecoveryPoint请求。作用：提交RecoveryPoint；边界：只声明协议。"""
    payload: RecoveryPoint
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class StateContinuityBoundaryRequest:
    """StateContinuityBoundary请求。作用：提交StateContinuityBoundary；边界：只声明协议。"""
    payload: StateContinuityBoundary
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class StateRecoveryHintRequest:
    """StateRecoveryHint请求。作用：提交StateRecoveryHint；边界：只声明协议。"""
    payload: StateRecoveryHint
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class ContinuityEvidenceRequest:
    """ContinuityEvidence请求。作用：提交ContinuityEvidence；边界：只声明协议。"""
    payload: ContinuityEvidence
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class SnapshotReferenceResponse:
    """SnapshotReference响应。作用：返回SnapshotReference；边界：不执行真实能力。"""
    payload: SnapshotReference
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class SnapshotIntentResponse:
    """SnapshotIntent响应。作用：返回SnapshotIntent；边界：不执行真实能力。"""
    payload: SnapshotIntent
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class CheckpointReferenceResponse:
    """CheckpointReference响应。作用：返回CheckpointReference；边界：不执行真实能力。"""
    payload: CheckpointReference
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class CheckpointIntentResponse:
    """CheckpointIntent响应。作用：返回CheckpointIntent；边界：不执行真实能力。"""
    payload: CheckpointIntent
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class RestorePointReferenceResponse:
    """RestorePointReference响应。作用：返回RestorePointReference；边界：不执行真实能力。"""
    payload: RestorePointReference
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class RecoveryPointResponse:
    """RecoveryPoint响应。作用：返回RecoveryPoint；边界：不执行真实能力。"""
    payload: RecoveryPoint
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class StateContinuityBoundaryResponse:
    """StateContinuityBoundary响应。作用：返回StateContinuityBoundary；边界：不执行真实能力。"""
    payload: StateContinuityBoundary
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class StateRecoveryHintResponse:
    """StateRecoveryHint响应。作用：返回StateRecoveryHint；边界：不执行真实能力。"""
    payload: StateRecoveryHint
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class ContinuityEvidenceResponse:
    """ContinuityEvidence响应。作用：返回ContinuityEvidence；边界：不执行真实能力。"""
    payload: ContinuityEvidence
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

class SnapshotReferencePort(ABC):
    """快照引用端口。中文名称：快照引用端口。端口职责：定义快照引用协议。输入输出边界：输入 SnapshotReferenceRequest 与 TraceContext，输出 PortResult。所属 L1 层：第八阶段状态连续性。不承担的实现职责：不创建真实快照。如何服务大模型执行力：让模型可引用状态锚点。如何维持绝对边界：引用不改变状态。与后续 L2-L6 的关系：供状态层和恢复链引用。"""
    @abstractmethod
    def reference_snapshot(self, request: SnapshotReferenceRequest, trace: TraceContext) -> PortResult[SnapshotReferenceResponse]:
        """声明快照引用端口。"""
        raise NotImplementedError

class SnapshotIntentPort(ABC):
    """快照意图端口。中文名称：快照意图端口。端口职责：定义快照意图协议。输入输出边界：输入 SnapshotIntentRequest 与 TraceContext，输出 PortResult。所属 L1 层：第八阶段状态连续性。不承担的实现职责：不读取状态、不写状态。如何服务大模型执行力：让高影响行动可声明保护点。如何维持绝对边界：意图不创建快照。与后续 L2-L6 的关系：供编排层和恢复适配引用。"""
    @abstractmethod
    def submit_snapshot_intent(self, request: SnapshotIntentRequest, trace: TraceContext) -> PortResult[SnapshotIntentResponse]:
        """声明快照意图端口。"""
        raise NotImplementedError

class CheckpointReferencePort(ABC):
    """检查点引用端口。中文名称：检查点引用端口。端口职责：定义检查点引用协议。输入输出边界：输入 CheckpointReferenceRequest 与 TraceContext，输出 PortResult。所属 L1 层：第八阶段状态连续性。不承担的实现职责：不创建检查点。如何服务大模型执行力：让任务链有检查点引用。如何维持绝对边界：引用不保存状态。与后续 L2-L6 的关系：供状态与恢复链引用。"""
    @abstractmethod
    def reference_checkpoint(self, request: CheckpointReferenceRequest, trace: TraceContext) -> PortResult[CheckpointReferenceResponse]:
        """声明检查点引用端口。"""
        raise NotImplementedError

class CheckpointIntentPort(ABC):
    """检查点意图端口。中文名称：检查点意图端口。端口职责：定义检查点意图协议。输入输出边界：输入 CheckpointIntentRequest 与 TraceContext，输出 PortResult。所属 L1 层：第八阶段状态连续性。不承担的实现职责：不保存检查点。如何服务大模型执行力：为长链行动保留候选检查点。如何维持绝对边界：意图不是持久化。与后续 L2-L6 的关系：供编排和恢复适配引用。"""
    @abstractmethod
    def submit_checkpoint_intent(self, request: CheckpointIntentRequest, trace: TraceContext) -> PortResult[CheckpointIntentResponse]:
        """声明检查点意图端口。"""
        raise NotImplementedError

class RestorePointReferencePort(ABC):
    """恢复点引用端口。中文名称：恢复点引用端口。端口职责：定义恢复点引用协议。输入输出边界：输入 RestorePointReferenceRequest 与 TraceContext，输出 PortResult。所属 L1 层：第八阶段状态连续性。不承担的实现职责：不创建恢复点、不恢复状态。如何服务大模型执行力：让风险动作有恢复引用。如何维持绝对边界：引用不触发恢复。与后续 L2-L6 的关系：供恢复验证和状态层引用。"""
    @abstractmethod
    def reference_restore_point(self, request: RestorePointReferenceRequest, trace: TraceContext) -> PortResult[RestorePointReferenceResponse]:
        """声明恢复点引用端口。"""
        raise NotImplementedError

class RecoveryPointPort(ABC):
    """恢复点端口。中文名称：恢复点端口。端口职责：定义恢复点协议。输入输出边界：输入 RecoveryPointRequest 与 TraceContext，输出 PortResult。所属 L1 层：第八阶段状态连续性。不承担的实现职责：不执行恢复。如何服务大模型执行力：让恢复目标可被引用。如何维持绝对边界：恢复点协议不改变状态。与后续 L2-L6 的关系：供恢复适配与验证链引用。"""
    @abstractmethod
    def describe_recovery_point(self, request: RecoveryPointRequest, trace: TraceContext) -> PortResult[RecoveryPointResponse]:
        """声明恢复点端口。"""
        raise NotImplementedError

class StateContinuityBoundaryPort(ABC):
    """状态连续性边界端口。中文名称：状态连续性边界端口。端口职责：定义状态连续性边界协议。输入输出边界：输入 StateContinuityBoundaryRequest 与 TraceContext，输出 PortResult。所属 L1 层：第八阶段状态连续性。不承担的实现职责：不实现状态机。如何服务大模型执行力：保证行动链不断裂。如何维持绝对边界：边界不执行迁移。与后续 L2-L6 的关系：供状态层、编排层和进化链引用。"""
    @abstractmethod
    def describe_state_continuity_boundary(self, request: StateContinuityBoundaryRequest, trace: TraceContext) -> PortResult[StateContinuityBoundaryResponse]:
        """声明状态连续性边界端口。"""
        raise NotImplementedError

class StateRecoveryHintPort(ABC):
    """状态恢复提示端口。中文名称：状态恢复提示端口。端口职责：定义状态恢复提示协议。输入输出边界：输入 StateRecoveryHintRequest 与 TraceContext，输出 PortResult。所属 L1 层：第八阶段状态连续性。不承担的实现职责：不执行恢复策略。如何服务大模型执行力：让失败后可形成恢复建议。如何维持绝对边界：提示不触发恢复。与后续 L2-L6 的关系：供恢复、验证和审计链引用。"""
    @abstractmethod
    def submit_state_recovery_hint(self, request: StateRecoveryHintRequest, trace: TraceContext) -> PortResult[StateRecoveryHintResponse]:
        """声明状态恢复提示端口。"""
        raise NotImplementedError

class ContinuityEvidencePort(ABC):
    """连续性证据端口。中文名称：连续性证据端口。端口职责：定义连续性证据协议。输入输出边界：输入 ContinuityEvidenceRequest 与 TraceContext，输出 PortResult。所属 L1 层：第八阶段状态连续性。不承担的实现职责：不采集真实证据。如何服务大模型执行力：让连续性判断有引用来源。如何维持绝对边界：证据引用不等于验证通过。与后续 L2-L6 的关系：供状态层和验证链引用。"""
    @abstractmethod
    def attach_continuity_evidence(self, request: ContinuityEvidenceRequest, trace: TraceContext) -> PortResult[ContinuityEvidenceResponse]:
        """声明连续性证据端口。"""
        raise NotImplementedError
