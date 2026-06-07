"""L2 组件状态对象，记录状态层组件、状态域、健康、依赖、导出与版本事实。

本模块位于 L2 状态层，只提供组件状态的不可变数据结构，服务工程生命体对状态组件清单、依赖关系、公共导出和健康摘要的静态表达。
本模块不实现组件宿主，不启动组件，不扫描目录，不动态导入模块，不执行注册、调度、测试或外部 IO。
本模块为后续 L3-L6 提供可引用的组件状态事实，但不承担编排、执行、边界裁决或子系统实现职责。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef

from .base_state import L2_STATE_SCHEMA_VERSION, L2StateMetadata
from .state_identity import L2StateIdentity
from .state_status import L2StateStatus


class L2StateDomain(str, Enum):
    """L2 状态域枚举。

    作用：表达状态对象所属的阶段性状态域，便于 L2 总目录和 L3 交接引用。
    边界：只做分类，不创建模块、不注册组件、不扫描工程目录。
    """

    UNKNOWN = "unknown"
    BASE = "base"
    RUNTIME_CONTINUITY = "runtime_continuity"
    SKILL_TOOL_MODEL_ACTION = "skill_tool_model_action"
    CONTROL_RESOURCE_ENVIRONMENT_SAFETY = "control_resource_environment_safety"
    OBSERVATION = "observation"
    MEMORY_CONTEXT_RETRIEVAL_LEARNING = "memory_context_retrieval_learning"
    CANDIDATE_CHANGE_ITERATION_EVOLUTION_VALIDATION_RECOVERY = (
        "candidate_change_iteration_evolution_validation_recovery"
    )
    PROJECTION_COMPATIBILITY_CLOSURE = "projection_compatibility_closure"
    MATH_AFFECTIVE_DYNAMIC_DRIVE = "math_affective_dynamic_drive"


class ComponentStatus(str, Enum):
    """组件状态枚举。

    作用：记录组件声明、可用、部分可用、弃用、阻断、失败或归档等状态事实。
    边界：不启动组件，不判断组件真实可运行性，不执行修复。
    """

    DECLARED = "declared"
    AVAILABLE = "available"
    PARTIALLY_AVAILABLE = "partially_available"
    DEPRECATED = "deprecated"
    BLOCKED = "blocked"
    FAILED = "failed"
    ARCHIVED = "archived"
    UNKNOWN = "unknown"


class ComponentDependencyKind(str, Enum):
    """组件依赖类型枚举。

    作用：表达组件之间的导入、引用、序列化、测试、导出或文档关系。
    边界：不解析依赖图，不读取模块，不执行导入。
    """

    UNKNOWN = "unknown"
    IMPORT = "import"
    REFERENCE = "reference"
    SERIALIZATION = "serialization"
    HASH = "hash"
    TEST = "test"
    EXPORT = "export"
    DOCUMENTATION = "documentation"


class ComponentCompatibilityStatus(str, Enum):
    """组件兼容状态枚举。

    作用：记录组件依赖的兼容、警告、缺失、阻断或未知状态事实。
    边界：不执行兼容迁移，不修改依赖，不自动补齐导出。
    """

    COMPATIBLE = "compatible"
    WARNING = "warning"
    MISSING = "missing"
    BLOCKED = "blocked"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class L2ComponentState:
    """L2 组件状态。

    作用：记录某个 L2 状态组件的组件引用、状态域、模块引用、版本、公共导出、依赖和健康引用。
    边界：不加载组件，不调用组件，不扫描模块，不改变公共导出。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    component_id: TypedRef | None = None
    domain: L2StateDomain = L2StateDomain.UNKNOWN
    module_ref: TypedRef | None = None
    version: str = L2_STATE_SCHEMA_VERSION
    public_exports: tuple[str, ...] = field(default_factory=tuple)
    dependency_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    health_ref: TypedRef | None = None
    summary: str = ""
    created_at: str = ""
    updated_at: str = ""
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if len(self.summary) > 512:
            raise ValueError("L2ComponentState.summary must be a short summary")
        if not self.version:
            raise ValueError("L2ComponentState.version cannot be empty")
        if not self.schema_version:
            raise ValueError("L2ComponentState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class L2ComponentDependencyState:
    """L2 组件依赖状态。

    作用：记录源组件、目标组件、依赖类型、兼容状态、缺失引用和原因摘要。
    边界：不解析真实依赖图，不执行导入，不安装依赖，不修改组件。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    dependency_id: TypedRef | None = None
    source_component_ref: TypedRef | None = None
    target_component_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    dependency_kind: ComponentDependencyKind = ComponentDependencyKind.UNKNOWN
    compatibility_status: ComponentCompatibilityStatus = ComponentCompatibilityStatus.UNKNOWN
    missing_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    reason_summary: str = ""
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if len(self.reason_summary) > 512:
            raise ValueError("L2ComponentDependencyState.reason_summary must be a short summary")
        if not self.schema_version:
            raise ValueError("L2ComponentDependencyState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class L2ComponentHealthState:
    """L2 组件健康状态。

    作用：记录组件集合的导入、序列化、哈希、测试状态、问题数量和摘要。
    边界：不运行导入检查，不运行测试，不计算哈希，不执行修复。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    health_id: TypedRef | None = None
    component_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    import_status: ComponentStatus = ComponentStatus.UNKNOWN
    serialization_status: ComponentStatus = ComponentStatus.UNKNOWN
    hash_status: ComponentStatus = ComponentStatus.UNKNOWN
    test_status: ComponentStatus = ComponentStatus.UNKNOWN
    issue_count: int = 0
    summary: str = ""
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.issue_count < 0:
            raise ValueError("L2ComponentHealthState.issue_count cannot be negative")
        if len(self.summary) > 512:
            raise ValueError("L2ComponentHealthState.summary must be a short summary")
        if not self.schema_version:
            raise ValueError("L2ComponentHealthState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class L2ExportState:
    """L2 导出状态。

    作用：记录模块引用、已导出名称、缺失预期名称、弃用名称、导出状态和摘要。
    边界：不动态导入模块，不生成导出，不删除旧导出，不执行注册。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    export_id: TypedRef | None = None
    module_ref: TypedRef | None = None
    exported_names: tuple[str, ...] = field(default_factory=tuple)
    missing_expected_names: tuple[str, ...] = field(default_factory=tuple)
    deprecated_names: tuple[str, ...] = field(default_factory=tuple)
    export_status: ComponentStatus = ComponentStatus.UNKNOWN
    summary: str = ""
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if len(self.summary) > 512:
            raise ValueError("L2ExportState.summary must be a short summary")
        if not self.schema_version:
            raise ValueError("L2ExportState.schema_version cannot be empty")
