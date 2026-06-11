"""L0 机密、凭证与能力令牌事实语言原语。

本模块在 L0 中的职责：定义机密材料、凭证、能力令牌、凭证范围、绑定和撤销的引用事实。
本模块只表达：密钥、令牌、密码、证书、连接凭证等敏感材料的引用、状态和绑定关系。
本模块明确不做：真实密钥保存、环境读取、凭证解析、加密、认证协议、令牌校验或外部密钥服务访问。
禁止事项：不得保存真实秘密文本，不得打印秘密，不得连接任何凭证管理服务。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .identity import RefId, TypedRef


class SecretKind(str, Enum):
    """机密类别：只标记机密材料类型；UNKNOWN 表示类别未知。

    API_KEY：接口密钥；PASSWORD：密码；PRIVATE_KEY：私钥；CERTIFICATE：证书；SESSION_TOKEN：会话令牌；
    OAUTH_TOKEN：授权令牌；DATABASE_SECRET：数据库机密；SSH_KEY：SSH 密钥；WEBHOOK_SECRET：Webhook 机密；ENCRYPTION_KEY：加密密钥；UNKNOWN：未知兜底。
    """

    API_KEY = "api_key"
    PASSWORD = "password"
    PRIVATE_KEY = "private_key"
    CERTIFICATE = "certificate"
    SESSION_TOKEN = "session_token"
    OAUTH_TOKEN = "oauth_token"
    DATABASE_SECRET = "database_secret"
    SSH_KEY = "ssh_key"
    WEBHOOK_SECRET = "webhook_secret"
    ENCRYPTION_KEY = "encryption_key"
    UNKNOWN = "unknown"


class CredentialKind(str, Enum):
    """凭证类别：只表达认证或授权凭证类型；UNKNOWN 表示类别未知。

    USER_CREDENTIAL：用户凭证；AGENT_CREDENTIAL：智能体凭证；SERVICE_ACCOUNT：服务账号；WORKLOAD_IDENTITY：工作负载身份；
    DELEGATED_CREDENTIAL：委托凭证；TEMPORARY_CREDENTIAL：临时凭证；SESSION_CREDENTIAL：会话凭证；UNKNOWN：未知兜底。
    """

    USER_CREDENTIAL = "user_credential"
    AGENT_CREDENTIAL = "agent_credential"
    SERVICE_ACCOUNT = "service_account"
    WORKLOAD_IDENTITY = "workload_identity"
    DELEGATED_CREDENTIAL = "delegated_credential"
    TEMPORARY_CREDENTIAL = "temporary_credential"
    SESSION_CREDENTIAL = "session_credential"
    UNKNOWN = "unknown"


class TokenKind(str, Enum):
    """令牌类别：只表达能力令牌约束形态；UNKNOWN 表示类别未知。

    CAPABILITY_TOKEN：能力令牌；INVOCATION_BOUND_TOKEN：调用绑定令牌；LEASE_BOUND_TOKEN：租约绑定令牌；
    SCOPE_BOUND_TOKEN：作用域绑定令牌；DELEGATION_TOKEN：委托令牌；REVOCATION_TOKEN：撤销令牌；UNKNOWN：未知兜底。
    """

    CAPABILITY_TOKEN = "capability_token"
    INVOCATION_BOUND_TOKEN = "invocation_bound_token"
    LEASE_BOUND_TOKEN = "lease_bound_token"
    SCOPE_BOUND_TOKEN = "scope_bound_token"
    DELEGATION_TOKEN = "delegation_token"
    REVOCATION_TOKEN = "revocation_token"
    UNKNOWN = "unknown"


class SecretState(str, Enum):
    """机密状态：只表达机密引用生命周期；UNKNOWN 表示状态未知。

    PROPOSED：提议；ISSUED：签发；ACTIVE：活动；BOUND：已绑定；EXPIRED：过期；REVOKED：撤销；
    ROTATED：轮换；QUARANTINED：隔离；COMPROMISED：疑似泄露；ARCHIVED：归档；UNKNOWN：未知兜底。
    """

    PROPOSED = "proposed"
    ISSUED = "issued"
    ACTIVE = "active"
    BOUND = "bound"
    EXPIRED = "expired"
    REVOKED = "revoked"
    ROTATED = "rotated"
    QUARANTINED = "quarantined"
    COMPROMISED = "compromised"
    ARCHIVED = "archived"
    UNKNOWN = "unknown"


class CredentialState(str, Enum):
    """凭证状态：只表达凭证引用生命周期；UNKNOWN 表示状态未知。

    PROPOSED：提议；ISSUED：签发；ACTIVE：活动；BOUND：已绑定；EXPIRED：过期；REVOKED：撤销；
    ROTATED：轮换；QUARANTINED：隔离；COMPROMISED：疑似泄露；ARCHIVED：归档；UNKNOWN：未知兜底。
    """

    PROPOSED = "proposed"
    ISSUED = "issued"
    ACTIVE = "active"
    BOUND = "bound"
    EXPIRED = "expired"
    REVOKED = "revoked"
    ROTATED = "rotated"
    QUARANTINED = "quarantined"
    COMPROMISED = "compromised"
    ARCHIVED = "archived"
    UNKNOWN = "unknown"


class TokenState(str, Enum):
    """令牌状态：只表达能力令牌生命周期；UNKNOWN 表示状态未知。

    PROPOSED：提议；ISSUED：签发；ACTIVE：活动；BOUND：已绑定；EXPIRED：过期；REVOKED：撤销；
    ROTATED：轮换；QUARANTINED：隔离；COMPROMISED：疑似泄露；ARCHIVED：归档；UNKNOWN：未知兜底。
    """

    PROPOSED = "proposed"
    ISSUED = "issued"
    ACTIVE = "active"
    BOUND = "bound"
    EXPIRED = "expired"
    REVOKED = "revoked"
    ROTATED = "rotated"
    QUARANTINED = "quarantined"
    COMPROMISED = "compromised"
    ARCHIVED = "archived"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class SecretRef:
    """机密引用。

    作用：表达密钥、令牌、密码、证书、私钥或连接凭证等机密材料的引用事实。
    所属 L0 边界：只保存 secret_id、kind、state 与 scope_ref。
    不能承担的上层职责：不能保存真实机密值，不能读取环境，不能加密、解密或认证。
    字段：value 为机密引用 ID；kind 为机密类别；state 为机密状态；scope_ref 为作用域引用。
    """

    value: RefId
    kind: SecretKind = SecretKind.UNKNOWN
    state: SecretState = SecretState.UNKNOWN
    scope_ref: TypedRef | None = None
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("SecretRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class CredentialRef:
    """凭证引用。

    作用：表达 Actor、适配器、工具、插件、环境或外部服务使用的认证授权凭证引用。
    所属 L0 边界：只保存 credential_id、kind、state、secret_ref 与 scope_ref。
    不能承担的上层职责：不能执行认证协议，不能校验凭证，不能接触真实凭证内容。
    字段：value 为凭证引用 ID；kind 为凭证类别；secret_ref 为关联机密引用。
    """

    value: RefId
    kind: CredentialKind = CredentialKind.UNKNOWN
    state: CredentialState = CredentialState.UNKNOWN
    secret_ref: SecretRef | None = None
    scope_ref: TypedRef | None = None
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("CredentialRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class CredentialScopeRef:
    """凭证范围引用。

    作用：表达凭证可被引用的作用域事实。
    所属 L0 边界：只保存 credential_scope_id 与 scope_refs。
    不能承担的上层职责：不能执行范围判断，不能裁决权限。
    字段：value 为凭证范围引用 ID；scope_refs 为作用域引用集合。
    """

    value: RefId
    scope_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("CredentialScopeRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class CapabilityTokenRef:
    """能力令牌引用。

    作用：表达带作用域、时效、调用绑定或委托链的能力令牌引用。
    所属 L0 边界：只保存 token_id、kind、state、scope_ref 与 binding_ref。
    不能承担的上层职责：不能签发令牌、不能校验令牌、不能执行调用授权。
    字段：value 为能力令牌引用 ID；kind 为令牌类别；state 为令牌状态。
    """

    value: RefId
    kind: TokenKind = TokenKind.UNKNOWN
    state: TokenState = TokenState.UNKNOWN
    scope_ref: CredentialScopeRef | None = None
    binding_ref: TypedRef | None = None
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("CapabilityTokenRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class CredentialBindingRef:
    """凭证绑定引用。

    作用：表达凭证与 Actor、Scope、Lease、Effect 或 Environment 的绑定事实。
    所属 L0 边界：只保存 binding_id、credential_ref 与 bound_refs。
    不能承担的上层职责：不能启用凭证，不能验证绑定，不能访问真实资源。
    字段：value 为绑定引用 ID；credential_ref 为凭证引用；bound_refs 为被绑定对象引用集合。
    """

    value: RefId
    credential_ref: CredentialRef | None = None
    bound_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("CredentialBindingRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class RevocationRef:
    """撤销引用。

    作用：表达凭证、令牌或授权被撤销的事实引用。
    所属 L0 边界：只保存 revocation_id、target_ref 与 reason_ref。
    不能承担的上层职责：不能执行撤销流程，不能通知外部服务，不能清理真实凭证。
    字段：value 为撤销引用 ID；target_ref 为被撤销对象引用；reason_ref 为撤销原因引用。
    """

    value: RefId
    target_ref: TypedRef | None = None
    reason_ref: TypedRef | None = None
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("RevocationRef.schema_version cannot be empty")
