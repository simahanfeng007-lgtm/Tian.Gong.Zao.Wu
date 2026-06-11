"""L1 第八阶段变更集、影响、可逆性、证据与复核端口协议。

本模块在 L1 中的职责：定义变更集意图、变更集边界、变更影响提示、变更可逆性提示、变更证据、变更复核意图、补丁意图边界和变更回退提示协议。
本模块定义哪些端口：ChangeSetIntentPort、ChangeSetBoundaryPort、ChangeImpactHintPort、ChangeReversibilityHintPort、ChangeEvidencePort、ChangeReviewIntentPort、PatchIntentBoundaryPort、ChangeRollbackHintPort。
本模块不实现哪些能力：不修改文件、不生成真实 patch、不做影响分析算法、不执行回退、不采集证据、不复核、不应用变更。
本模块禁止事项：不得访问文件、数据库、网络、模型、工具、插件或真实版本系统。
本模块与 L2-L6 的关系：L2 可记录变更状态，L3 可编排变更候选，L4 可实现外部变更适配，L5 可约束插件变更，L6 可提交学习、迭代、进化变更。
本模块如何服务工程生命体：让每个自我迭代和进化候选有影响、证据和可逆性协议。
本模块如何维持大模型执行力与绝对边界：变更只作为候选意图，不在 L1 真实应用。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.audit import AuditRef
from tiangong_kernel.l0_primitives.evidence import EvidenceRef
from tiangong_kernel.l0_primitives.relation import RelationRef
from tiangong_kernel.l0_primitives.resource import ResourceRef
from tiangong_kernel.l0_primitives.skill_capability import SkillRef
from tiangong_kernel.l0_primitives.tool_adapter import ToolRef
from tiangong_kernel.l0_primitives.trace import TraceContext
from tiangong_kernel.l0_primitives.validation import ValidationRef, VerificationRef
from tiangong_kernel.l0_primitives.versioning import SchemaRef, VersionRef

from .candidate_ports import CandidatePromotionHint
from .envelope import PortBoundaryContext
from .evolution_ports import EvolutionCandidate
from .port_boundary import BoundaryViolation, PortBoundary
from .port_result import PortResult
from .self_iteration_ports import IterationCandidate, IterationPatchIntent

@dataclass(frozen=True, slots=True)
class ChangeSetIntent:
    """变更集意图对象。作用：表达变更集意图；边界：不修改文件、不生成真实 patch。"""
    change_ref: ResourceRef
    iteration_candidate: IterationCandidate | None = None
    evolution_candidate: EvolutionCandidate | None = None
    skill_refs: tuple[SkillRef, ...] = field(default_factory=tuple)
    tool_refs: tuple[ToolRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class ChangeSetBoundary:
    """变更集边界对象。作用：表达变更集边界；边界：不做真实裁决。"""
    change_ref: ResourceRef
    boundary: PortBoundary | None = None
    violations: tuple[BoundaryViolation, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class ChangeImpactHint:
    """变更影响提示对象。作用：表达变更可能影响；边界：不做真实影响分析算法。"""
    hint_ref: ResourceRef
    change_ref: ResourceRef | None = None
    relation_refs: tuple[RelationRef, ...] = field(default_factory=tuple)
    schema_ref: SchemaRef | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class ChangeReversibilityHint:
    """变更可逆性提示对象。作用：表达变更可逆性；边界：不执行回退。"""
    hint_ref: ResourceRef
    change_ref: ResourceRef | None = None
    version_ref: VersionRef | None = None
    verification_refs: tuple[VerificationRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class ChangeEvidence:
    """变更证据对象。作用：表达变更证据；边界：不采集证据。"""
    change_ref: ResourceRef
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    audit_ref: AuditRef | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class ChangeReviewIntent:
    """变更复核意图对象。作用：表达变更复核意图；边界：不执行复核。"""
    change_ref: ResourceRef
    candidate_promotion_hint: CandidatePromotionHint | None = None
    verification_refs: tuple[VerificationRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class PatchIntentBoundary:
    """补丁意图边界对象。作用：表达补丁意图边界；边界：不写代码、不应用 patch。"""
    patch_intent: IterationPatchIntent | None = None
    boundary: PortBoundary | None = None
    validation_refs: tuple[ValidationRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class ChangeRollbackHint:
    """变更回退提示对象。作用：表达变更回退提示；边界：不执行回退。"""
    hint_ref: ResourceRef
    change_ref: ResourceRef | None = None
    version_ref: VersionRef | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class ChangeSetIntentRequest:
    """ChangeSetIntent请求。作用：提交ChangeSetIntent；边界：只声明变更协议。"""
    payload: ChangeSetIntent
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class ChangeSetBoundaryRequest:
    """ChangeSetBoundary请求。作用：提交ChangeSetBoundary；边界：只声明变更协议。"""
    payload: ChangeSetBoundary
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class ChangeImpactHintRequest:
    """ChangeImpactHint请求。作用：提交ChangeImpactHint；边界：只声明变更协议。"""
    payload: ChangeImpactHint
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class ChangeReversibilityHintRequest:
    """ChangeReversibilityHint请求。作用：提交ChangeReversibilityHint；边界：只声明变更协议。"""
    payload: ChangeReversibilityHint
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class ChangeEvidenceRequest:
    """ChangeEvidence请求。作用：提交ChangeEvidence；边界：只声明变更协议。"""
    payload: ChangeEvidence
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class ChangeReviewIntentRequest:
    """ChangeReviewIntent请求。作用：提交ChangeReviewIntent；边界：只声明变更协议。"""
    payload: ChangeReviewIntent
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class PatchIntentBoundaryRequest:
    """PatchIntentBoundary请求。作用：提交PatchIntentBoundary；边界：只声明变更协议。"""
    payload: PatchIntentBoundary
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class ChangeRollbackHintRequest:
    """ChangeRollbackHint请求。作用：提交ChangeRollbackHint；边界：只声明变更协议。"""
    payload: ChangeRollbackHint
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class ChangeSetIntentResponse:
    """ChangeSetIntent响应。作用：返回ChangeSetIntent；边界：不应用变更。"""
    payload: ChangeSetIntent
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class ChangeSetBoundaryResponse:
    """ChangeSetBoundary响应。作用：返回ChangeSetBoundary；边界：不应用变更。"""
    payload: ChangeSetBoundary
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class ChangeImpactHintResponse:
    """ChangeImpactHint响应。作用：返回ChangeImpactHint；边界：不应用变更。"""
    payload: ChangeImpactHint
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class ChangeReversibilityHintResponse:
    """ChangeReversibilityHint响应。作用：返回ChangeReversibilityHint；边界：不应用变更。"""
    payload: ChangeReversibilityHint
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class ChangeEvidenceResponse:
    """ChangeEvidence响应。作用：返回ChangeEvidence；边界：不应用变更。"""
    payload: ChangeEvidence
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class ChangeReviewIntentResponse:
    """ChangeReviewIntent响应。作用：返回ChangeReviewIntent；边界：不应用变更。"""
    payload: ChangeReviewIntent
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class PatchIntentBoundaryResponse:
    """PatchIntentBoundary响应。作用：返回PatchIntentBoundary；边界：不应用变更。"""
    payload: PatchIntentBoundary
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class ChangeRollbackHintResponse:
    """ChangeRollbackHint响应。作用：返回ChangeRollbackHint；边界：不应用变更。"""
    payload: ChangeRollbackHint
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

class ChangeSetIntentPort(ABC):
    """变更集意图端口。中文名称：变更集意图端口。端口职责：定义变更集意图协议。输入输出边界：输入 ChangeSetIntentRequest 与 TraceContext，输出 PortResult。所属 L1 层：第八阶段变更协议。不承担的实现职责：不修改文件、不生成真实 patch。如何服务大模型执行力：让模型建议形成结构化变更候选。如何维持绝对边界：意图不应用变更。与后续 L2-L6 的关系：供迭代和进化候选引用。"""
    @abstractmethod
    def submit_change_set_intent(self, request: ChangeSetIntentRequest, trace: TraceContext) -> PortResult[ChangeSetIntentResponse]:
        """声明变更集意图端口。"""
        raise NotImplementedError

class ChangeSetBoundaryPort(ABC):
    """变更集边界端口。中文名称：变更集边界端口。端口职责：定义变更集边界协议。输入输出边界：输入 ChangeSetBoundaryRequest 与 TraceContext，输出 PortResult。所属 L1 层：第八阶段变更协议。不承担的实现职责：不做真实裁决。如何服务大模型执行力：明确高影响变更范围。如何维持绝对边界：边界不放行变更。与后续 L2-L6 的关系：供控制面和验证链引用。"""
    @abstractmethod
    def describe_change_set_boundary(self, request: ChangeSetBoundaryRequest, trace: TraceContext) -> PortResult[ChangeSetBoundaryResponse]:
        """声明变更集边界端口。"""
        raise NotImplementedError

class ChangeImpactHintPort(ABC):
    """变更影响提示端口。中文名称：变更影响提示端口。端口职责：定义变更影响提示协议。输入输出边界：输入 ChangeImpactHintRequest 与 TraceContext，输出 PortResult。所属 L1 层：第八阶段变更协议。不承担的实现职责：不做真实影响分析算法。如何服务大模型执行力：让模型理解可能影响面。如何维持绝对边界：提示不更改系统。与后续 L2-L6 的关系：供验证和进化链引用。"""
    @abstractmethod
    def submit_change_impact_hint(self, request: ChangeImpactHintRequest, trace: TraceContext) -> PortResult[ChangeImpactHintResponse]:
        """声明变更影响提示端口。"""
        raise NotImplementedError

class ChangeReversibilityHintPort(ABC):
    """变更可逆性提示端口。中文名称：变更可逆性提示端口。端口职责：定义变更可逆性提示协议。输入输出边界：输入 ChangeReversibilityHintRequest 与 TraceContext，输出 PortResult。所属 L1 层：第八阶段变更协议。不承担的实现职责：不执行回退。如何服务大模型执行力：让变更保留可恢复思路。如何维持绝对边界：提示不恢复状态。与后续 L2-L6 的关系：供回退验证引用。"""
    @abstractmethod
    def submit_change_reversibility_hint(self, request: ChangeReversibilityHintRequest, trace: TraceContext) -> PortResult[ChangeReversibilityHintResponse]:
        """声明变更可逆性提示端口。"""
        raise NotImplementedError

class ChangeEvidencePort(ABC):
    """变更证据端口。中文名称：变更证据端口。端口职责：定义变更证据协议。输入输出边界：输入 ChangeEvidenceRequest 与 TraceContext，输出 PortResult。所属 L1 层：第八阶段变更协议。不承担的实现职责：不采集证据。如何服务大模型执行力：让变更依据可追踪。如何维持绝对边界：证据不等于验证通过。与后续 L2-L6 的关系：供候选验证和审计链引用。"""
    @abstractmethod
    def attach_change_evidence(self, request: ChangeEvidenceRequest, trace: TraceContext) -> PortResult[ChangeEvidenceResponse]:
        """声明变更证据端口。"""
        raise NotImplementedError

class ChangeReviewIntentPort(ABC):
    """变更复核意图端口。中文名称：变更复核意图端口。端口职责：定义变更复核意图协议。输入输出边界：输入 ChangeReviewIntentRequest 与 TraceContext，输出 PortResult。所属 L1 层：第八阶段变更协议。不承担的实现职责：不执行复核。如何服务大模型执行力：让变更进入复核链。如何维持绝对边界：复核意图不合入。与后续 L2-L6 的关系：供候选治理引用。"""
    @abstractmethod
    def submit_change_review_intent(self, request: ChangeReviewIntentRequest, trace: TraceContext) -> PortResult[ChangeReviewIntentResponse]:
        """声明变更复核意图端口。"""
        raise NotImplementedError

class PatchIntentBoundaryPort(ABC):
    """补丁意图边界端口。中文名称：补丁意图边界端口。端口职责：定义补丁意图边界协议。输入输出边界：输入 PatchIntentBoundaryRequest 与 TraceContext，输出 PortResult。所属 L1 层：第八阶段变更协议。不承担的实现职责：不写代码、不应用 patch。如何服务大模型执行力：让代码变更先过边界说明。如何维持绝对边界：边界不修改源码。与后续 L2-L6 的关系：供迭代验证引用。"""
    @abstractmethod
    def describe_patch_intent_boundary(self, request: PatchIntentBoundaryRequest, trace: TraceContext) -> PortResult[PatchIntentBoundaryResponse]:
        """声明补丁意图边界端口。"""
        raise NotImplementedError

class ChangeRollbackHintPort(ABC):
    """变更回退提示端口。中文名称：变更回退提示端口。端口职责：定义变更回退提示协议。输入输出边界：输入 ChangeRollbackHintRequest 与 TraceContext，输出 PortResult。所属 L1 层：第八阶段变更协议。不承担的实现职责：不执行回退。如何服务大模型执行力：确保高影响变更有回退提示。如何维持绝对边界：提示不恢复系统。与后续 L2-L6 的关系：供回退验证链引用。"""
    @abstractmethod
    def submit_change_rollback_hint(self, request: ChangeRollbackHintRequest, trace: TraceContext) -> PortResult[ChangeRollbackHintResponse]:
        """声明变更回退提示端口。"""
        raise NotImplementedError
