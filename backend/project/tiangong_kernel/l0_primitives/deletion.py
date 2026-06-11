"""L0 删除事实原语，只表达删除、擦除、墓碑、脱敏与保留例外引用；不删除文件、不擦除数据。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .identity import RefId, TypedRef


class DeletionKind(str, Enum):
    """DeletionKind 的 L0 枚举，只表达稳定事实，不实现上层算法或真实执行。"""
    USER_REQUESTED = "user_requested"
    RETENTION_EXPIRED = "retention_expired"
    PRIVACY_REQUIRED = "privacy_required"
    SAFETY_REQUIRED = "safety_required"
    SECURITY_REQUIRED = "security_required"
    SYSTEM_CLEANUP = "system_cleanup"
    SUPERSEDED = "superseded"
    DUPLICATE = "duplicate"
    CORRUPTED = "corrupted"
    UNKNOWN = "unknown"


class ErasureKind(str, Enum):
    """ErasureKind 的 L0 枚举，只表达稳定事实，不实现上层算法或真实执行。"""
    LOGICAL_DELETE = "logical_delete"
    PHYSICAL_DELETE = "physical_delete"
    CRYPTOGRAPHIC_ERASURE = "cryptographic_erasure"
    REDACTION = "redaction"
    ANONYMIZATION = "anonymization"
    SUPPRESSION = "suppression"
    TOMBSTONE_ONLY = "tombstone_only"
    UNKNOWN = "unknown"


class DeletionState(str, Enum):
    """DeletionState 的 L0 枚举，只表达稳定事实，不实现上层算法或真实执行。"""
    REQUESTED = "requested"
    APPROVED = "approved"
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    EXCEPTION_RECORDED = "exception_recorded"
    FAILED = "failed"
    VERIFIED = "verified"
    ARCHIVED = "archived"
    UNKNOWN = "unknown"


class ErasureState(str, Enum):
    """ErasureState 的 L0 枚举，只表达稳定事实，不实现上层算法或真实执行。"""
    REQUESTED = "requested"
    APPROVED = "approved"
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    EXCEPTION_RECORDED = "exception_recorded"
    FAILED = "failed"
    VERIFIED = "verified"
    ARCHIVED = "archived"
    UNKNOWN = "unknown"


class TombstoneKind(str, Enum):
    """TombstoneKind 的 L0 枚举，只表达稳定事实，不实现上层算法或真实执行。"""
    DELETED_OBJECT = "deleted_object"
    REDACTED_CONTENT = "redacted_content"
    ANONYMIZED_SUBJECT = "anonymized_subject"
    SUPPRESSED_RECORD = "suppressed_record"
    CRYPTO_ERASED = "crypto_erased"
    UNKNOWN = "unknown"


class TombstoneState(str, Enum):
    """TombstoneState 的 L0 枚举，只表达稳定事实，不实现上层算法或真实执行。"""
    REQUESTED = "requested"
    APPROVED = "approved"
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    EXCEPTION_RECORDED = "exception_recorded"
    FAILED = "failed"
    VERIFIED = "verified"
    ARCHIVED = "archived"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class DeletionRef:
    """DeletionRef 的 L0 不可变事实对象，只表达稳定事实，不实现上层算法或真实执行。"""
    value: RefId
    kind: DeletionKind = DeletionKind.UNKNOWN
    state: DeletionState = DeletionState.UNKNOWN
    subject_ref: TypedRef | None = None
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("DeletionRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ErasureRef:
    """ErasureRef 的 L0 不可变事实对象，只表达稳定事实，不实现上层算法或真实执行。"""
    value: RefId
    kind: ErasureKind = ErasureKind.UNKNOWN
    state: ErasureState = ErasureState.UNKNOWN
    deletion_ref: DeletionRef | None = None
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("ErasureRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class TombstoneRef:
    """TombstoneRef 的 L0 不可变事实对象，只表达稳定事实，不实现上层算法或真实执行。"""
    value: RefId
    kind: TombstoneKind = TombstoneKind.UNKNOWN
    state: TombstoneState = TombstoneState.UNKNOWN
    subject_ref: TypedRef | None = None
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("TombstoneRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class RedactionRef:
    """RedactionRef 的 L0 不可变事实对象，只表达稳定事实，不实现上层算法或真实执行。"""
    value: RefId
    target_ref: TypedRef | None = None
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("RedactionRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class AnonymizationRef:
    """AnonymizationRef 的 L0 不可变事实对象，只表达稳定事实，不实现上层算法或真实执行。"""
    value: RefId
    target_ref: TypedRef | None = None
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("AnonymizationRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class CryptoErasureRef:
    """CryptoErasureRef 的 L0 不可变事实对象，只表达稳定事实，不实现上层算法或真实执行。"""
    value: RefId
    key_ref: TypedRef | None = None
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("CryptoErasureRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class RetentionExceptionRef:
    """RetentionExceptionRef 的 L0 不可变事实对象，只表达稳定事实，不实现上层算法或真实执行。"""
    value: RefId
    reason_ref: TypedRef | None = None
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("RetentionExceptionRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class DeletionEvidenceRef:
    """DeletionEvidenceRef 的 L0 不可变事实对象，只表达稳定事实，不实现上层算法或真实执行。"""
    value: RefId
    evidence_type: str = "unknown"
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.evidence_type:
            raise ValueError("DeletionEvidenceRef.evidence_type cannot be empty")
        if not self.schema_version:
            raise ValueError("DeletionEvidenceRef.schema_version cannot be empty")
