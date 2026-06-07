"""L0 隐私与数据治理事实语言原语。

本模块在 L0 中的职责：定义隐私属性、同意、数据主体、处理目的、保留策略、数据生命周期和敏感度事实。
本模块只表达：数据、事件、观察、记忆、上下文、证据或资源的隐私治理引用事实。
本模块明确不做：个人信息识别、法律合规判断、删除执行、脱敏处理、用户界面或数据库清理。
禁止事项：不得读取真实数据，不得进行真实脱敏，不得执行隐私合规流程。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .identity import RefId, TypedRef


class DataClass(str, Enum):
    """数据分类：只表达治理分类；UNKNOWN 表示分类未知或暂不归类。

    PUBLIC：公开；INTERNAL：内部；USER_PROVIDED：用户提供；PERSONAL：个人；SENSITIVE：敏感；
    SECRET：机密；SYSTEM：系统；DERIVED：派生；UNKNOWN：未知兜底。
    """

    PUBLIC = "public"
    INTERNAL = "internal"
    USER_PROVIDED = "user_provided"
    PERSONAL = "personal"
    SENSITIVE = "sensitive"
    SECRET = "secret"
    SYSTEM = "system"
    DERIVED = "derived"
    UNKNOWN = "unknown"


class DataLifecycleState(str, Enum):
    """数据生命周期状态：只表达数据治理阶段；UNKNOWN 表示状态未知。

    OBSERVED：已观察；RECORDED：已记录；PROCESSING：处理中；ACTIVE：活动；RETAINED：保留；
    REDACTED：已遮蔽；ANONYMIZED：已匿名化；EXPIRED：已过期；DELETION_REQUESTED：请求删除；
    DELETED：已删除；ARCHIVED：已归档；BLOCKED：已阻塞；UNKNOWN：未知兜底。
    """

    OBSERVED = "observed"
    RECORDED = "recorded"
    PROCESSING = "processing"
    ACTIVE = "active"
    RETAINED = "retained"
    REDACTED = "redacted"
    ANONYMIZED = "anonymized"
    EXPIRED = "expired"
    DELETION_REQUESTED = "deletion_requested"
    DELETED = "deleted"
    ARCHIVED = "archived"
    BLOCKED = "blocked"
    UNKNOWN = "unknown"


class AccessSensitivity(str, Enum):
    """访问敏感度：只表达访问敏感等级；UNKNOWN 表示敏感度未知。

    LOW：低；NORMAL：普通；HIGH：高；CRITICAL：关键；UNKNOWN：未知兜底。
    """

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class DataSubjectRef:
    """数据主体引用。

    作用：表达数据对应的主体引用事实。
    所属 L0 边界：只保存 subject_id 与 evidence_refs。
    不能承担的上层职责：不能识别真实个人、不能做法律身份判断。
    字段：value 为数据主体引用 ID；evidence_refs 为证据引用集合。
    """

    value: RefId
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("DataSubjectRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ProcessingPurposeRef:
    """处理目的引用。

    作用：表达某类数据处理目的的引用事实。
    所属 L0 边界：只保存 purpose_id 与 related_refs。
    不能承担的上层职责：不能判断目的是否合法，不能执行数据处理流程。
    字段：value 为处理目的引用 ID；related_refs 为关联事实引用集合。
    """

    value: RefId
    related_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("ProcessingPurposeRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class RetentionPolicyRef:
    """保留策略引用。

    作用：表达数据保留、过期或删除策略的引用事实。
    所属 L0 边界：只保存 policy_id 与 scope_ref。
    不能承担的上层职责：不能计算保留期限，不能执行清理或删除。
    字段：value 为保留策略引用 ID；scope_ref 为适用范围引用。
    """

    value: RefId
    scope_ref: TypedRef | None = None
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("RetentionPolicyRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ConsentRef:
    """同意授权引用。

    作用：表达用户或主体对某类处理的授权事实引用。
    所属 L0 边界：只保存 consent_id、subject_ref、purpose_ref 与 evidence_refs。
    不能承担的上层职责：不能展示同意界面，不能验证同意流程，不能执行权限裁决。
    字段：value 为同意引用 ID；subject_ref 为主体引用；purpose_ref 为处理目的引用。
    """

    value: RefId
    subject_ref: DataSubjectRef | None = None
    purpose_ref: ProcessingPurposeRef | None = None
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("ConsentRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class RedactionRef:
    """内容遮蔽引用。

    作用：表达敏感部分被遮蔽或移除的引用事实。
    所属 L0 边界：只保存 redaction_id 与 target_ref。
    不能承担的上层职责：不能执行遮蔽算法，不能改写真实内容。
    字段：value 为遮蔽引用 ID；target_ref 为目标对象引用。
    """

    value: RefId
    target_ref: TypedRef | None = None
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("RedactionRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class AnonymizationRef:
    """匿名化引用。

    作用：表达对象已进行去标识化治理的引用事实。
    所属 L0 边界：只保存 anonymization_id 与 target_ref。
    不能承担的上层职责：不能执行匿名化算法，不能评估重识别风险。
    字段：value 为匿名化引用 ID；target_ref 为目标对象引用。
    """

    value: RefId
    target_ref: TypedRef | None = None
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("AnonymizationRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class PrivacyRef:
    """隐私属性引用。

    作用：表达某个数据、事件、观察、记忆、上下文、证据或资源具有隐私属性。
    所属 L0 边界：只保存 privacy_id、data_class、lifecycle_state、sensitivity 与治理引用。
    不能承担的上层职责：不能检测个人信息、不能执行合规流程、不能删除或脱敏真实数据。
    字段：value 为隐私引用 ID；data_class 为数据分类；sensitivity 为访问敏感度。
    """

    value: RefId
    data_class: DataClass = DataClass.UNKNOWN
    lifecycle_state: DataLifecycleState = DataLifecycleState.UNKNOWN
    sensitivity: AccessSensitivity = AccessSensitivity.UNKNOWN
    subject_ref: DataSubjectRef | None = None
    consent_ref: ConsentRef | None = None
    purpose_ref: ProcessingPurposeRef | None = None
    retention_policy_ref: RetentionPolicyRef | None = None
    redaction_ref: RedactionRef | None = None
    anonymization_ref: AnonymizationRef | None = None
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("PrivacyRef.schema_version cannot be empty")
