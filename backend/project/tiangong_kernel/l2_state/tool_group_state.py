"""L2 ToolGroup 状态对象，只记录声明、可见、释放和租约事实，不创建或释放工具。"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef

from .base_state import L2_STATE_SCHEMA_VERSION, L2StateMetadata
from .state_boundary import L2StateBoundary
from .state_identity import L2StateIdentity
from .state_status import L2StateStatus


class ToolGroupDeclarationStatus(str, Enum):
    """工具组声明状态。

    作用：表达某个 Skill 需要的工具组是否已被声明为状态事实。
    边界：不创建工具，不扫描工具注册表，不调用工具。
    """

    UNKNOWN = "unknown"
    DECLARED = "declared"
    MISSING = "missing"
    INCOMPLETE = "incomplete"
    CONFLICTED = "conflicted"
    DEPRECATED = "deprecated"


class ToolGroupVisibilityStatus(str, Enum):
    """工具组可见状态。

    作用：表达工具组是否对模型可见。
    边界：不展示工具，不把工具裸露给模型，不执行过滤。
    """

    UNKNOWN = "unknown"
    HIDDEN = "hidden"
    VISIBLE = "visible"
    MASKED = "masked"
    BOUNDARY_BLOCKED = "boundary_blocked"
    REVOKED = "revoked"


class ToolGroupReleaseStatus(str, Enum):
    """工具组释放状态。

    作用：表达工具组释放、阻断、过期或撤销的状态事实。
    边界：不释放工具，不创建工具执行入口，不调用工具。
    """

    UNKNOWN = "unknown"
    NOT_RELEASED = "not_released"
    RELEASE_REQUESTED = "release_requested"
    RELEASED = "released"
    PARTIALLY_RELEASED = "partially_released"
    REVOKED = "revoked"
    EXPIRED = "expired"
    BLOCKED = "blocked"


class ToolGroupLeaseStatus(str, Enum):
    """工具组租约状态。

    作用：表达工具组租约、过期、续租请求或撤销状态。
    边界：不续租工具，不延长租约，不持有可执行函数。
    """

    UNKNOWN = "unknown"
    NO_LEASE = "no_lease"
    LEASED = "leased"
    LEASE_EXPIRING = "lease_expiring"
    EXPIRED = "expired"
    RENEWAL_REQUESTED = "renewal_requested"
    RENEWAL_BLOCKED = "renewal_blocked"
    REVOKED = "revoked"


@dataclass(frozen=True, slots=True)
class ToolGroupDeclarationState:
    """工具组声明状态。

    作用：记录工具组引用、关联 Skill、所需工具、缺失工具和工具 schema 引用。
    边界：不创建工具，不注册工具，不调用工具。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    declaration_status: ToolGroupDeclarationStatus = ToolGroupDeclarationStatus.UNKNOWN
    tool_group_ref: TypedRef | None = None
    skill_ref: TypedRef | None = None
    skill_activation_ref: TypedRef | None = None
    required_tool_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    missing_tool_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    tool_schema_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    boundary_ref: L2StateBoundary | None = None
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("ToolGroupDeclarationState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ToolGroupVisibilityState:
    """工具组可见状态。

    作用：记录工具组对模型请求、运行和任务的可见工具与遮蔽工具引用。
    边界：不展示工具，不执行可见性过滤，不调用模型或工具。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    visibility_status: ToolGroupVisibilityStatus = ToolGroupVisibilityStatus.UNKNOWN
    tool_group_ref: TypedRef | None = None
    declaration_state_ref: TypedRef | None = None
    skill_ref: TypedRef | None = None
    run_ref: TypedRef | None = None
    task_ref: TypedRef | None = None
    visible_tool_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    masked_tool_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    boundary_ref: L2StateBoundary | None = None
    model_request_ref: TypedRef | None = None
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("ToolGroupVisibilityState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ToolGroupReleaseState:
    """工具组释放状态。

    作用：记录工具组释放状态、已释放工具、阻断工具、租约状态和审计引用。
    边界：不释放工具，不生成执行器，不调用工具。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    release_status: ToolGroupReleaseStatus = ToolGroupReleaseStatus.UNKNOWN
    tool_group_ref: TypedRef | None = None
    visibility_state_ref: TypedRef | None = None
    skill_ref: TypedRef | None = None
    run_ref: TypedRef | None = None
    task_ref: TypedRef | None = None
    released_tool_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    blocked_tool_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    lease_state_ref: TypedRef | None = None
    boundary_ref: L2StateBoundary | None = None
    audit_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("ToolGroupReleaseState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ToolGroupLeaseState:
    """工具组租约状态。

    作用：记录工具组租约引用、发放/过期引用、续租提示、撤销和边界引用。
    边界：不续租工具，不撤销真实租约，不持有可执行函数。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    lease_status: ToolGroupLeaseStatus = ToolGroupLeaseStatus.UNKNOWN
    tool_group_ref: TypedRef | None = None
    release_state_ref: TypedRef | None = None
    lease_ref: TypedRef | None = None
    run_ref: TypedRef | None = None
    task_ref: TypedRef | None = None
    issued_at_ref: TypedRef | None = None
    expires_at_ref: TypedRef | None = None
    renewal_hint_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    revocation_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    boundary_ref: L2StateBoundary | None = None
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("ToolGroupLeaseState.schema_version cannot be empty")
