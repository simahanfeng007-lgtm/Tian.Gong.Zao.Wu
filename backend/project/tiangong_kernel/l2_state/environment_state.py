"""L2 环境与沙箱状态对象。

作用：记录环境引用、沙箱引用和外部世界引用的状态事实。
边界：不读取真实环境变量，不探测系统路径，不访问沙箱，不访问外部世界。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef

from .base_state import L2_STATE_SCHEMA_VERSION, L2StateMetadata
from .state_identity import L2StateIdentity
from .state_status import L2StateStatus


class EnvironmentStatus(str, Enum):
    """环境状态。

    作用：表达外部记录的环境可用、受限、不可用、隔离、过期或失败状态。
    边界：不探测当前机器、沙箱、目录、网络或设备。
    """

    UNKNOWN = "unknown"
    DECLARED = "declared"
    AVAILABLE_RECORDED = "available_recorded"
    LIMITED_RECORDED = "limited_recorded"
    UNAVAILABLE_RECORDED = "unavailable_recorded"
    ISOLATED_RECORDED = "isolated_recorded"
    STALE = "stale"
    EXPIRED = "expired"
    FAILED = "failed"


class EnvironmentKind(str, Enum):
    """环境种类。

    作用：表达本地、远端、沙箱、浏览器、桌面、移动端、服务器或容器等环境标签。
    边界：不根据标签探测真实机器、系统路径、网络或设备。
    """

    UNKNOWN = "unknown"
    LOCAL_HOST = "local_host"
    REMOTE_HOST = "remote_host"
    SANDBOX = "sandbox"
    BROWSER = "browser"
    DESKTOP = "desktop"
    MOBILE = "mobile"
    SERVER = "server"
    CONTAINER = "container"
    TEST_ENVIRONMENT = "test_environment"
    CUSTOM = "custom"


class SandboxStatus(str, Enum):
    """沙箱状态。

    作用：表达外部记录的沙箱声明、活动、受限、隔离、异常、不可用或失败状态。
    边界：不启动沙箱，不进入沙箱，不检测沙箱，不执行安全扫描。
    """

    UNKNOWN = "unknown"
    DECLARED = "declared"
    ACTIVE_RECORDED = "active_recorded"
    LIMITED_RECORDED = "limited_recorded"
    ISOLATED_RECORDED = "isolated_recorded"
    ESCAPED_RECORDED = "escaped_recorded"
    UNAVAILABLE_RECORDED = "unavailable_recorded"
    EXPIRED = "expired"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class EnvironmentState:
    """环境状态。

    作用：记录环境引用、环境种类、环境状态、关联沙箱、边界和资源状态引用。
    边界：不读取真实环境变量，不探测系统路径，不访问网络或设备。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    environment_status: EnvironmentStatus = EnvironmentStatus.UNKNOWN
    environment_kind: EnvironmentKind = EnvironmentKind.UNKNOWN
    environment_ref: TypedRef | None = None
    subject_ref: TypedRef | None = None
    sandbox_state_ref: TypedRef | None = None
    boundary_state_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    resource_state_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    summary: str | None = None
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.summary == "":
            raise ValueError("EnvironmentState.summary cannot be empty when provided")
        if not self.schema_version:
            raise ValueError("EnvironmentState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class SandboxState:
    """沙箱状态。

    作用：记录沙箱引用、沙箱状态、允许范围、限制范围和信任边界引用。
    边界：不启动沙箱，不进入沙箱，不探测沙箱，不执行逃逸检测。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    sandbox_status: SandboxStatus = SandboxStatus.UNKNOWN
    sandbox_ref: TypedRef | None = None
    subject_ref: TypedRef | None = None
    allowed_scope_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    restricted_scope_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    trust_boundary_ref: TypedRef | None = None
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    summary: str | None = None
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.summary == "":
            raise ValueError("SandboxState.summary cannot be empty when provided")
        if not self.schema_version:
            raise ValueError("SandboxState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ExternalWorldReferenceState:
    """外部世界引用状态。

    作用：记录网页、文件系统、桌面、数据库、API 或设备等外部对象的引用状态。
    边界：不访问外部世界，不读取文件，不访问网络，不连接数据库或设备。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    access_status: EnvironmentStatus = EnvironmentStatus.UNKNOWN
    external_ref: TypedRef | None = None
    environment_ref: TypedRef | None = None
    trust_boundary_ref: TypedRef | None = None
    privacy_ref: TypedRef | None = None
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    summary: str | None = None
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.summary == "":
            raise ValueError("ExternalWorldReferenceState.summary cannot be empty when provided")
        if not self.schema_version:
            raise ValueError("ExternalWorldReferenceState.schema_version cannot be empty")
