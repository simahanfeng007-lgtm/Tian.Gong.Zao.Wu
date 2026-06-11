"""L2 安全、隐私、凭据和信任边界状态对象。

作用：记录安全边界、隐私、凭据、密钥引用和信任边界的状态事实。
边界：不执行安全扫描，不读取密钥，不验证身份，不保存真实敏感值。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef

from .base_state import L2_STATE_SCHEMA_VERSION, L2StateMetadata
from .state_identity import L2StateIdentity
from .state_status import L2StateStatus


class SecurityStatus(str, Enum):
    """安全状态。

    作用：表达外部记录的安全声明、清晰、警告、违规、阻断、脱敏或复核状态。
    边界：不执行安全扫描，不访问权限系统，不读取密钥。
    """

    UNKNOWN = "unknown"
    DECLARED = "declared"
    CLEAR_RECORDED = "clear_recorded"
    WARNING_RECORDED = "warning_recorded"
    VIOLATION_RECORDED = "violation_recorded"
    BLOCKED_RECORDED = "blocked_recorded"
    REDACTED = "redacted"
    REVIEW_REQUIRED = "review_required"
    EXPIRED = "expired"
    REVOKED = "revoked"


class PrivacyStatus(str, Enum):
    """隐私状态。

    作用：表达外部记录的无个人数据、仅引用、敏感数据仅引用、脱敏或披露阻断状态。
    边界：不保存个人隐私正文，不执行同意流程，不披露任何真实内容。
    """

    UNKNOWN = "unknown"
    NO_PERSONAL_DATA_RECORDED = "no_personal_data_recorded"
    PERSONAL_DATA_REF_ONLY = "personal_data_ref_only"
    SENSITIVE_DATA_REF_ONLY = "sensitive_data_ref_only"
    REDACTED = "redacted"
    CONSENT_REQUIRED_RECORDED = "consent_required_recorded"
    DISCLOSURE_BLOCKED_RECORDED = "disclosure_blocked_recorded"


class CredentialStatus(str, Enum):
    """凭据引用状态。

    作用：表达凭据仅引用、存在、缺失、脱敏、过期、撤销或访问阻断的外部记录状态。
    边界：不读取凭据，不保存真实敏感值，不访问权限系统。
    """

    UNKNOWN = "unknown"
    REF_ONLY = "ref_only"
    PRESENT_RECORDED = "present_recorded"
    MISSING_RECORDED = "missing_recorded"
    REDACTED = "redacted"
    EXPIRED_RECORDED = "expired_recorded"
    REVOKED_RECORDED = "revoked_recorded"
    ACCESS_BLOCKED_RECORDED = "access_blocked_recorded"


class TrustBoundaryStatus(str, Enum):
    """信任边界状态。

    作用：表达对象位于边界内、边界外、跨越边界、跨越被阻断或需要复核的状态。
    边界：不验证身份，不授权，不改变访问范围。
    """

    UNKNOWN = "unknown"
    DECLARED = "declared"
    INSIDE_BOUNDARY_RECORDED = "inside_boundary_recorded"
    OUTSIDE_BOUNDARY_RECORDED = "outside_boundary_recorded"
    CROSSING_RECORDED = "crossing_recorded"
    CROSSING_BLOCKED_RECORDED = "crossing_blocked_recorded"
    REVIEW_REQUIRED_RECORDED = "review_required_recorded"


@dataclass(frozen=True, slots=True)
class SecurityBoundaryState:
    """安全边界状态。

    作用：记录安全边界引用、信任边界引用、隐私状态引用、凭据状态引用和边界检查引用。
    边界：不执行安全扫描，不读取密钥，不访问权限系统。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    security_status: SecurityStatus = SecurityStatus.UNKNOWN
    security_boundary_ref: TypedRef | None = None
    subject_ref: TypedRef | None = None
    trust_boundary_ref: TypedRef | None = None
    privacy_state_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    credential_state_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    boundary_check_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    risk_decision_state_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    audit_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    summary: str | None = None
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.summary == "":
            raise ValueError("SecurityBoundaryState.summary cannot be empty when provided")
        if not self.schema_version:
            raise ValueError("SecurityBoundaryState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class PrivacyCredentialState:
    """隐私与凭据状态。

    作用：记录隐私引用、凭据引用、密钥引用、脱敏状态和缺值状态。
    边界：不保存真实敏感值，不读取凭据，不披露隐私正文。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    privacy_status: PrivacyStatus = PrivacyStatus.UNKNOWN
    credential_status: CredentialStatus = CredentialStatus.UNKNOWN
    privacy_ref: TypedRef | None = None
    credential_ref: TypedRef | None = None
    secret_ref: TypedRef | None = None
    redacted: bool = True
    value_absent: bool = True
    subject_ref: TypedRef | None = None
    consent_ref: TypedRef | None = None
    purpose_ref: TypedRef | None = None
    retention_policy_ref: TypedRef | None = None
    data_lifecycle_state_hint: str | None = None
    trust_boundary_ref: TypedRef | None = None
    boundary_check_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    summary: str | None = None
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not self.redacted:
            raise ValueError("PrivacyCredentialState.redacted must remain true")
        if not self.value_absent:
            raise ValueError("PrivacyCredentialState.value_absent must remain true")
        if self.summary == "":
            raise ValueError("PrivacyCredentialState.summary cannot be empty when provided")
        if not self.schema_version:
            raise ValueError("PrivacyCredentialState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class TrustBoundaryState:
    """信任边界状态。

    作用：记录信任边界引用、边界内外对象、跨越对象和相关边界检查引用。
    边界：不验证身份，不授权，不改变访问范围。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    trust_boundary_status: TrustBoundaryStatus = TrustBoundaryStatus.UNKNOWN
    trust_boundary_ref: TypedRef | None = None
    inside_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    outside_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    crossing_subject_ref: TypedRef | None = None
    boundary_check_ref: TypedRef | None = None
    risk_decision_state_ref: TypedRef | None = None
    summary: str | None = None
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.summary == "":
            raise ValueError("TrustBoundaryState.summary cannot be empty when provided")
        if not self.schema_version:
            raise ValueError("TrustBoundaryState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class SecretReferenceState:
    """密钥引用状态。

    作用：只记录密钥引用、凭据引用、所有者引用、作用域引用和脱敏缺值姿态。
    边界：不保存真实敏感值，不读取密钥，不验证凭据。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    credential_status: CredentialStatus = CredentialStatus.UNKNOWN
    secret_ref: TypedRef | None = None
    credential_ref: TypedRef | None = None
    redacted: bool = True
    value_absent: bool = True
    owner_ref: TypedRef | None = None
    scope_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not self.redacted:
            raise ValueError("SecretReferenceState.redacted must remain true")
        if not self.value_absent:
            raise ValueError("SecretReferenceState.value_absent must remain true")
        if not self.schema_version:
            raise ValueError("SecretReferenceState.schema_version cannot be empty")
