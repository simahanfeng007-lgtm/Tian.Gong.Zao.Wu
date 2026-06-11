"""L2 兼容迁移状态对象，记录 schema 兼容、旧状态映射、弃用、迁移提示和兼容门禁事实。

本模块位于 L2 状态层，只定义兼容与迁移相关的不可变状态对象，服务工程生命体在冻结收口时表达旧状态与新状态之间的关系。
本模块不读取旧数据，不执行真实迁移，不写转换结果，不删除弃用对象，不修改 schema，也不把历史执行体系迁回新版主链。
本模块为后续 L3-L6 提供兼容引用和风险提示，但不承担迁移执行、验证执行、恢复执行或边界裁决职责。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef

from .base_state import L2_STATE_SCHEMA_VERSION, L2StateMetadata
from .component_state import L2StateDomain
from .state_identity import L2StateIdentity
from .state_status import L2StateStatus


class CompatibilityStatus(str, Enum):
    """兼容状态枚举。

    作用：记录兼容、带警告兼容、需要迁移、弃用、不兼容或未知等状态事实。
    边界：不执行迁移，不做真实裁决，不修改 schema。
    """

    COMPATIBLE = "compatible"
    COMPATIBLE_WITH_WARNING = "compatible_with_warning"
    MIGRATION_NEEDED = "migration_needed"
    DEPRECATED = "deprecated"
    INCOMPATIBLE = "incompatible"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class SchemaVersionState:
    """Schema 版本状态。

    作用：记录 schema 引用、版本、状态域、稳定哈希提示、兼容状态和摘要。
    边界：不生成 schema，不计算真实哈希文件，不执行 schema 升级。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    schema_ref: TypedRef | None = None
    version: str = L2_STATE_SCHEMA_VERSION
    domain: L2StateDomain = L2StateDomain.UNKNOWN
    stable_hash: str = ""
    compatibility_status: CompatibilityStatus = CompatibilityStatus.UNKNOWN
    summary: str = ""
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not self.version:
            raise ValueError("SchemaVersionState.version cannot be empty")
        if len(self.summary) > 512:
            raise ValueError("SchemaVersionState.summary must be a short summary")
        if not self.schema_version:
            raise ValueError("SchemaVersionState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class LegacyMappingState:
    """旧状态映射状态。

    作用：记录旧引用、新引用、映射状态、置信提示、损失风险和原因摘要。
    边界：不读取旧数据，不执行转换，不创建新状态，不写入映射结果。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    mapping_id: TypedRef | None = None
    legacy_ref: TypedRef | None = None
    new_ref: TypedRef | None = None
    mapping_status: CompatibilityStatus = CompatibilityStatus.UNKNOWN
    confidence_hint: float = 0.0
    loss_risk: str = ""
    reason_summary: str = ""
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence_hint <= 1.0:
            raise ValueError("LegacyMappingState.confidence_hint must be between 0 and 1")
        if len(self.loss_risk) > 256:
            raise ValueError("LegacyMappingState.loss_risk must be a short hint")
        if len(self.reason_summary) > 512:
            raise ValueError("LegacyMappingState.reason_summary must be a short summary")
        if not self.schema_version:
            raise ValueError("LegacyMappingState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class DeprecationState:
    """弃用状态。

    作用：记录目标引用、替代引用、弃用状态、移除提示和原因摘要。
    边界：不删除对象，不修改导出，不强制迁移调用方。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    deprecation_id: TypedRef | None = None
    target_ref: TypedRef | None = None
    replacement_ref: TypedRef | None = None
    deprecation_status: CompatibilityStatus = CompatibilityStatus.UNKNOWN
    remove_after_hint: str = ""
    reason_summary: str = ""
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if len(self.remove_after_hint) > 256:
            raise ValueError("DeprecationState.remove_after_hint must be a short hint")
        if len(self.reason_summary) > 512:
            raise ValueError("DeprecationState.reason_summary must be a short summary")
        if not self.schema_version:
            raise ValueError("DeprecationState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class MigrationHintState:
    """迁移提示状态。

    作用：记录源 schema、目标 schema、所需步骤摘要、风险提示、验证需要提示和恢复需要提示。
    边界：只记录提示，不执行迁移步骤，不写入结果，不触发验证或恢复。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    migration_hint_id: TypedRef | None = None
    source_schema_ref: TypedRef | None = None
    target_schema_ref: TypedRef | None = None
    required_steps_summary: str = ""
    risk_hint: str = ""
    validation_need_hint: str = ""
    recovery_need_hint: str = ""
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if len(self.required_steps_summary) > 512:
            raise ValueError("MigrationHintState.required_steps_summary must be a short summary")
        if len(self.risk_hint) > 256:
            raise ValueError("MigrationHintState.risk_hint must be a short hint")
        if len(self.validation_need_hint) > 256:
            raise ValueError("MigrationHintState.validation_need_hint must be a short hint")
        if len(self.recovery_need_hint) > 256:
            raise ValueError("MigrationHintState.recovery_need_hint must be a short hint")
        if not self.schema_version:
            raise ValueError("MigrationHintState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class CompatibilityGateState:
    """兼容门禁状态。

    作用：记录目标引用、schema 引用、映射引用、验证引用、门禁状态和原因摘要。
    边界：不执行真实门禁，不批准迁移，不阻断运行，只提供状态事实。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    gate_id: TypedRef | None = None
    target_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    schema_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    mapping_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    validation_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    gate_status: CompatibilityStatus = CompatibilityStatus.UNKNOWN
    reason_summary: str = ""
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if len(self.reason_summary) > 512:
            raise ValueError("CompatibilityGateState.reason_summary must be a short summary")
        if not self.schema_version:
            raise ValueError("CompatibilityGateState.schema_version cannot be empty")
