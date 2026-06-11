"""L1 第八阶段秘密、凭据、隐私、信任与敏感内容边界端口协议。

本模块在 L1 中的职责：定义秘密引用、秘密边界、凭据引用、凭据边界、信任边界、隐私边界、敏感内容边界、数据外露边界和外传披露边界协议。
本模块定义哪些端口：SecretReferencePort、SecretBoundaryPort、CredentialReferencePort、CredentialBoundaryPort、TrustBoundaryPort、PrivacyBoundaryPort、SensitiveContentBoundaryPort、DataExposureBoundaryPort、ExternalDisclosureBoundaryPort。
本模块不实现哪些能力：不读取密钥、不读取凭据、不鉴权、不脱敏、不扫描真实内容、不上传、不发送。
本模块禁止事项：不得读取环境、文件、网络、真实密钥、真实凭据或外部安全系统。
本模块与 L2-L6 的关系：L2 可记录安全状态，L3 可编排高影响意图，L4 可实现安全适配，L5 可隔离插件边界，L6 可声明子系统数据边界。
本模块如何服务工程生命体：为长期运行系统建立秘密、隐私、信任和外露的统一协议入口。
本模块如何维持大模型执行力与绝对边界：只对敏感边界形成提示和引用，不阻碍普通 Skill 行动链。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.content import ContentRef
from tiangong_kernel.l0_primitives.evidence import EvidenceRef
from tiangong_kernel.l0_primitives.policy import PolicyRef
from tiangong_kernel.l0_primitives.grant_lease import LeaseRef
from tiangong_kernel.l0_primitives.privacy import (
    AccessSensitivity,
    ConsentRef,
    DataClass,
    DataLifecycleState,
    DataSubjectRef,
    PrivacyRef,
    ProcessingPurposeRef,
    RetentionPolicyRef,
)
from tiangong_kernel.l0_primitives.resource import ResourceRef
from tiangong_kernel.l0_primitives.risk import RiskView
from tiangong_kernel.l0_primitives.secret import CapabilityTokenRef, CredentialRef, CredentialScopeRef, RevocationRef, SecretRef
from tiangong_kernel.l0_primitives.trace import TraceContext
from tiangong_kernel.l0_primitives.trust import TrustBoundaryRef

from .envelope import PortBoundaryContext
from .port_boundary import BoundaryViolation, PortBoundary
from .port_result import PortResult

@dataclass(frozen=True, slots=True)
class SecretReference:
    """秘密引用对象。作用：表达秘密材料引用；边界：不读取真实秘密。"""
    secret_ref: SecretRef
    scope_ref: ResourceRef | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class SecretBoundary:
    """秘密边界对象。作用：表达秘密使用边界；边界：不管理真实密钥。"""
    secret_ref: SecretRef = None
    boundary: PortBoundary | None = None
    policy_refs: tuple[PolicyRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class CredentialReference:
    """凭据引用对象。作用：表达凭据引用；边界：不读取凭据。"""
    credential_ref: CredentialRef
    secret_ref: SecretRef = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class CredentialBoundary:
    """凭据边界对象。作用：表达凭据使用边界；边界：不执行鉴权。"""
    credential_ref: CredentialRef = None
    boundary: PortBoundary | None = None
    risk_view: RiskView | None = None
    capability_token_ref: CapabilityTokenRef | None = None
    lease_ref: LeaseRef | None = None
    revocation_ref: RevocationRef | None = None
    credential_scope_ref: CredentialScopeRef | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class TrustBoundary:
    """信任边界对象。作用：表达信任边界引用；边界：不计算信任分。"""
    trust_boundary_ref: TrustBoundaryRef
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class PrivacyBoundary:
    """隐私边界对象。作用：表达隐私边界；边界：不做真实脱敏。"""
    privacy_ref: PrivacyRef
    subject_ref: DataSubjectRef | None = None
    purpose_ref: ProcessingPurposeRef | None = None
    consent_ref: ConsentRef | None = None
    retention_policy_ref: RetentionPolicyRef | None = None
    data_class_hint: DataClass = DataClass.UNKNOWN
    lifecycle_state_hint: DataLifecycleState = DataLifecycleState.UNKNOWN
    sensitivity_hint: AccessSensitivity = AccessSensitivity.UNKNOWN
    trust_boundary_ref: TrustBoundaryRef | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class SensitiveContentBoundary:
    """敏感内容边界对象。作用：表达敏感内容引用边界；边界：不扫描真实内容。"""
    content_ref: ContentRef | None = None
    privacy_ref: PrivacyRef = None
    boundary: PortBoundary | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class DataExposureBoundary:
    """数据外露边界对象。作用：表达数据外露边界；边界：不上传、不联网。"""
    resource_ref: ResourceRef | None = None
    content_ref: ContentRef | None = None
    privacy_ref: PrivacyRef = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class ExternalDisclosureBoundary:
    """外传披露边界对象。作用：表达外传披露边界；边界：不发送、不外传。"""
    boundary_ref: ResourceRef
    trust_boundary_ref: TrustBoundaryRef = None
    violations: tuple[BoundaryViolation, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class SecretReferenceRequest:
    """SecretReference请求。作用：提交SecretReference；边界：只声明安全协议。"""
    payload: SecretReference
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class SecretBoundaryRequest:
    """SecretBoundary请求。作用：提交SecretBoundary；边界：只声明安全协议。"""
    payload: SecretBoundary
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class CredentialReferenceRequest:
    """CredentialReference请求。作用：提交CredentialReference；边界：只声明安全协议。"""
    payload: CredentialReference
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class CredentialBoundaryRequest:
    """CredentialBoundary请求。作用：提交CredentialBoundary；边界：只声明安全协议。"""
    payload: CredentialBoundary
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class TrustBoundaryRequest:
    """TrustBoundary请求。作用：提交TrustBoundary；边界：只声明安全协议。"""
    payload: TrustBoundary
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class PrivacyBoundaryRequest:
    """PrivacyBoundary请求。作用：提交PrivacyBoundary；边界：只声明安全协议。"""
    payload: PrivacyBoundary
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class SensitiveContentBoundaryRequest:
    """SensitiveContentBoundary请求。作用：提交SensitiveContentBoundary；边界：只声明安全协议。"""
    payload: SensitiveContentBoundary
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class DataExposureBoundaryRequest:
    """DataExposureBoundary请求。作用：提交DataExposureBoundary；边界：只声明安全协议。"""
    payload: DataExposureBoundary
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class ExternalDisclosureBoundaryRequest:
    """ExternalDisclosureBoundary请求。作用：提交ExternalDisclosureBoundary；边界：只声明安全协议。"""
    payload: ExternalDisclosureBoundary
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class SecretReferenceResponse:
    """SecretReference响应。作用：返回SecretReference；边界：不接触真实敏感材料。"""
    payload: SecretReference
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class SecretBoundaryResponse:
    """SecretBoundary响应。作用：返回SecretBoundary；边界：不接触真实敏感材料。"""
    payload: SecretBoundary
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class CredentialReferenceResponse:
    """CredentialReference响应。作用：返回CredentialReference；边界：不接触真实敏感材料。"""
    payload: CredentialReference
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class CredentialBoundaryResponse:
    """CredentialBoundary响应。作用：返回CredentialBoundary；边界：不接触真实敏感材料。"""
    payload: CredentialBoundary
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class TrustBoundaryResponse:
    """TrustBoundary响应。作用：返回TrustBoundary；边界：不接触真实敏感材料。"""
    payload: TrustBoundary
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class PrivacyBoundaryResponse:
    """PrivacyBoundary响应。作用：返回PrivacyBoundary；边界：不接触真实敏感材料。"""
    payload: PrivacyBoundary
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class SensitiveContentBoundaryResponse:
    """SensitiveContentBoundary响应。作用：返回SensitiveContentBoundary；边界：不接触真实敏感材料。"""
    payload: SensitiveContentBoundary
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class DataExposureBoundaryResponse:
    """DataExposureBoundary响应。作用：返回DataExposureBoundary；边界：不接触真实敏感材料。"""
    payload: DataExposureBoundary
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

@dataclass(frozen=True, slots=True)
class ExternalDisclosureBoundaryResponse:
    """ExternalDisclosureBoundary响应。作用：返回ExternalDisclosureBoundary；边界：不接触真实敏感材料。"""
    payload: ExternalDisclosureBoundary
    boundary_context: PortBoundaryContext | None = None
    schema_version: str = "0.1"

class SecretReferencePort(ABC):
    """秘密引用端口。中文名称：秘密引用端口。端口职责：定义秘密引用协议。输入输出边界：输入 SecretReferenceRequest 与 TraceContext，输出 PortResult。所属 L1 层：第八阶段安全边界。不承担的实现职责：不读取真实秘密。如何服务大模型执行力：让敏感对象以引用进入边界。如何维持绝对边界：引用不暴露秘密值。与后续 L2-L6 的关系：供安全适配和插件隔离引用。"""
    @abstractmethod
    def reference_secret(self, request: SecretReferenceRequest, trace: TraceContext) -> PortResult[SecretReferenceResponse]:
        """声明秘密引用端口。"""
        raise NotImplementedError

class SecretBoundaryPort(ABC):
    """秘密边界端口。中文名称：秘密边界端口。端口职责：定义秘密边界协议。输入输出边界：输入 SecretBoundaryRequest 与 TraceContext，输出 PortResult。所属 L1 层：第八阶段安全边界。不承担的实现职责：不管理真实密钥。如何服务大模型执行力：给模型安全替代路径。如何维持绝对边界：边界不读取秘密。与后续 L2-L6 的关系：供控制面和外部适配引用。"""
    @abstractmethod
    def describe_secret_boundary(self, request: SecretBoundaryRequest, trace: TraceContext) -> PortResult[SecretBoundaryResponse]:
        """声明秘密边界端口。"""
        raise NotImplementedError

class CredentialReferencePort(ABC):
    """凭据引用端口。中文名称：凭据引用端口。端口职责：定义凭据引用协议。输入输出边界：输入 CredentialReferenceRequest 与 TraceContext，输出 PortResult。所属 L1 层：第八阶段安全边界。不承担的实现职责：不读取凭据。如何服务大模型执行力：让凭据以不可见引用参与链路。如何维持绝对边界：引用不暴露凭据值。与后续 L2-L6 的关系：供鉴权适配和插件隔离引用。"""
    @abstractmethod
    def reference_credential(self, request: CredentialReferenceRequest, trace: TraceContext) -> PortResult[CredentialReferenceResponse]:
        """声明凭据引用端口。"""
        raise NotImplementedError

class CredentialBoundaryPort(ABC):
    """凭据边界端口。中文名称：凭据边界端口。端口职责：定义凭据边界协议。输入输出边界：输入 CredentialBoundaryRequest 与 TraceContext，输出 PortResult。所属 L1 层：第八阶段安全边界。不承担的实现职责：不执行真实鉴权。如何服务大模型执行力：明确凭据不可越界使用。如何维持绝对边界：边界不授权。与后续 L2-L6 的关系：供安全适配引用。"""
    @abstractmethod
    def describe_credential_boundary(self, request: CredentialBoundaryRequest, trace: TraceContext) -> PortResult[CredentialBoundaryResponse]:
        """声明凭据边界端口。"""
        raise NotImplementedError

class TrustBoundaryPort(ABC):
    """信任边界端口。中文名称：信任边界端口。端口职责：定义信任边界协议。输入输出边界：输入 TrustBoundaryRequest 与 TraceContext，输出 PortResult。所属 L1 层：第八阶段安全边界。不承担的实现职责：不计算信任分。如何服务大模型执行力：让来源可信度可被引用。如何维持绝对边界：信任引用不替代裁决。与后续 L2-L6 的关系：供外部适配和插件隔离引用。"""
    @abstractmethod
    def describe_trust_boundary(self, request: TrustBoundaryRequest, trace: TraceContext) -> PortResult[TrustBoundaryResponse]:
        """声明信任边界端口。"""
        raise NotImplementedError

class PrivacyBoundaryPort(ABC):
    """隐私边界端口。中文名称：隐私边界端口。端口职责：定义隐私边界协议。输入输出边界：输入 PrivacyBoundaryRequest 与 TraceContext，输出 PortResult。所属 L1 层：第八阶段安全边界。不承担的实现职责：不做真实脱敏。如何服务大模型执行力：让模型知道可用内容边界。如何维持绝对边界：边界不处理真实隐私数据。与后续 L2-L6 的关系：供内容、通信和外部适配引用。"""
    @abstractmethod
    def describe_privacy_boundary(self, request: PrivacyBoundaryRequest, trace: TraceContext) -> PortResult[PrivacyBoundaryResponse]:
        """声明隐私边界端口。"""
        raise NotImplementedError

class SensitiveContentBoundaryPort(ABC):
    """敏感内容边界端口。中文名称：敏感内容边界端口。端口职责：定义敏感内容边界协议。输入输出边界：输入 SensitiveContentBoundaryRequest 与 TraceContext，输出 PortResult。所属 L1 层：第八阶段安全边界。不承担的实现职责：不扫描真实内容。如何服务大模型执行力：把敏感边界表达给模型。如何维持绝对边界：不泄露内容。与后续 L2-L6 的关系：供内容适配和模型上下文边界引用。"""
    @abstractmethod
    def describe_sensitive_content_boundary(self, request: SensitiveContentBoundaryRequest, trace: TraceContext) -> PortResult[SensitiveContentBoundaryResponse]:
        """声明敏感内容边界端口。"""
        raise NotImplementedError

class DataExposureBoundaryPort(ABC):
    """数据外露边界端口。中文名称：数据外露边界端口。端口职责：定义数据外露边界协议。输入输出边界：输入 DataExposureBoundaryRequest 与 TraceContext，输出 PortResult。所属 L1 层：第八阶段安全边界。不承担的实现职责：不上传、不联网。如何服务大模型执行力：让外露风险有替代路径。如何维持绝对边界：边界不发送数据。与后续 L2-L6 的关系：供通信和外部适配引用。"""
    @abstractmethod
    def describe_data_exposure_boundary(self, request: DataExposureBoundaryRequest, trace: TraceContext) -> PortResult[DataExposureBoundaryResponse]:
        """声明数据外露边界端口。"""
        raise NotImplementedError

class ExternalDisclosureBoundaryPort(ABC):
    """外传披露边界端口。中文名称：外传披露边界端口。端口职责：定义外传披露边界协议。输入输出边界：输入 ExternalDisclosureBoundaryRequest 与 TraceContext，输出 PortResult。所属 L1 层：第八阶段安全边界。不承担的实现职责：不执行外传。如何服务大模型执行力：明确哪些信息不能外传。如何维持绝对边界：协议不发送信息。与后续 L2-L6 的关系：供通信适配和插件隔离引用。"""
    @abstractmethod
    def describe_external_disclosure_boundary(self, request: ExternalDisclosureBoundaryRequest, trace: TraceContext) -> PortResult[ExternalDisclosureBoundaryResponse]:
        """声明外传披露边界端口。"""
        raise NotImplementedError
