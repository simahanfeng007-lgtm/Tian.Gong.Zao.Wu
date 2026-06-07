"""L0 信任与来源事实语言原语。

本模块在 L0 中的职责：定义信任边界、可信等级、来源证明、责任链、证明声明与完整性摘要的最小事实语言。
本模块只表达：信息、动作、资源、Actor、插件或适配器所在信任边界及来源引用事实。
本模块明确不做：身份认证、权限裁决、签名校验、加密握手、外部证书解析或安全协议流程。
禁止事项：不得接触真实证书、密钥、网络、存储或外部安全服务；不得实现任何安全策略流程。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .identity import RefId, TypedRef


class TrustBoundaryKind(str, Enum):
    """信任边界类别：只标记对象所处边界；UNKNOWN 表示边界未知或暂不归类。

    SELF_CORE：自我核心；TRUSTED_PLUGIN：可信插件；SANDBOX：沙箱；USER_INPUT：用户输入；
    MODEL_OUTPUT：模型输出；EXTERNAL_TOOL：外部工具；NETWORK：网络边界；STORAGE：存储边界；UNKNOWN：未知兜底。
    """

    SELF_CORE = "self_core"
    TRUSTED_PLUGIN = "trusted_plugin"
    SANDBOX = "sandbox"
    USER_INPUT = "user_input"
    MODEL_OUTPUT = "model_output"
    EXTERNAL_TOOL = "external_tool"
    NETWORK = "network"
    STORAGE = "storage"
    UNKNOWN = "unknown"


class TrustLevel(str, Enum):
    """可信等级：只表达当前上下文中的可信程度；UNKNOWN 表示无法判断。

    VERIFIED：已核验；TRUSTED：可信；CONSTRAINED：受约束可信；UNTRUSTED：不可信；HOSTILE：敌意来源；UNKNOWN：未知兜底。
    """

    VERIFIED = "verified"
    TRUSTED = "trusted"
    CONSTRAINED = "constrained"
    UNTRUSTED = "untrusted"
    HOSTILE = "hostile"
    UNKNOWN = "unknown"


class ProvenanceKind(str, Enum):
    """来源证明类别：只标记事实来源类型；UNKNOWN 表示来源未知或暂不归类。

    USER_PROVIDED：用户提供；MODEL_GENERATED：模型生成；SYSTEM_GENERATED：系统生成；PLUGIN_GENERATED：插件生成；
    TOOL_GENERATED：工具生成；EXTERNAL_IMPORTED：外部导入；RECOVERED：恢复得到；DERIVED：派生得到；UNKNOWN：未知兜底。
    """

    USER_PROVIDED = "user_provided"
    MODEL_GENERATED = "model_generated"
    SYSTEM_GENERATED = "system_generated"
    PLUGIN_GENERATED = "plugin_generated"
    TOOL_GENERATED = "tool_generated"
    EXTERNAL_IMPORTED = "external_imported"
    RECOVERED = "recovered"
    DERIVED = "derived"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class TrustBoundaryRef:
    """信任边界引用。

    作用：表达对象所处的信任边界引用事实。
    所属 L0 边界：只保存 trust_boundary_id、kind、level 与证据引用。
    不能承担的上层职责：不能做身份认证、权限裁决、安全协议或真实访问控制。
    字段：value 为信任边界引用 ID；kind 为边界类别；level 为可信等级；evidence_refs 为证据引用集合。
    """

    value: RefId
    kind: TrustBoundaryKind = TrustBoundaryKind.UNKNOWN
    level: TrustLevel = TrustLevel.UNKNOWN
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("TrustBoundaryRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ProvenanceRef:
    """来源证明引用。

    作用：记录对象的来源、生成链、传递链或依据引用。
    所属 L0 边界：只保存 provenance_ref、kind、source_ref 与 evidence_refs。
    不能承担的上层职责：不能验证来源真实性、不能读取原始内容、不能执行安全检查。
    字段：value 为来源证明引用 ID；kind 为来源类别；source_ref 为来源对象引用。
    """

    value: RefId
    kind: ProvenanceKind = ProvenanceKind.UNKNOWN
    source_ref: TypedRef | None = None
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("ProvenanceRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ResponsibilityChainRef:
    """责任链引用。

    作用：引用一次行动从发起者到结果之间的责任链事实。
    所属 L0 边界：只保存 chain_id 与 chain_refs 等引用集合。
    不能承担的上层职责：不能判责、不能审计归因、不能裁决责任。
    字段：value 为责任链引用 ID；chain_refs 为责任节点引用集合；provenance_ref 为来源证明引用。
    """

    value: RefId
    chain_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    provenance_ref: ProvenanceRef | None = None
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("ResponsibilityChainRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class AttestationRef:
    """证明声明引用。

    作用：表达身份、环境、插件、工具或结果的可验证声明引用事实。
    所属 L0 边界：只保存 attestation_id、subject_ref、issuer_ref 与 evidence_refs。
    不能承担的上层职责：不能解析证书、不能核验签名、不能建立信任链。
    字段：value 为证明声明引用 ID；subject_ref 为被声明对象；issuer_ref 为声明来源。
    """

    value: RefId
    subject_ref: TypedRef | None = None
    issuer_ref: TypedRef | None = None
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("AttestationRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class IntegrityDigest:
    """完整性摘要。

    作用：引用内容或状态未被篡改的摘要事实。
    所属 L0 边界：只保存 digest、algorithm、target_ref 与 schema_version。
    不能承担的上层职责：不能读取内容、不能重新计算摘要、不能做签名校验。
    字段：digest 为摘要文本；algorithm 为摘要算法名称；target_ref 为被摘要对象引用。
    """

    digest: str
    algorithm: str = "sha256"
    target_ref: TypedRef | None = None
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.digest:
            raise ValueError("IntegrityDigest.digest cannot be empty")
        if not self.algorithm:
            raise ValueError("IntegrityDigest.algorithm cannot be empty")
        if not self.schema_version:
            raise ValueError("IntegrityDigest.schema_version cannot be empty")
