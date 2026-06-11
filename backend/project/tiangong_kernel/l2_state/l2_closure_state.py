"""L2 总收口状态对象，记录冻结、验收、已知问题、交接和稳定性整修提示事实。

本模块位于 L2 状态层，只定义 L2 第八阶段总收口相关的不可变状态对象，服务工程生命体对全阶段冻结边界、验证摘要、L3 交接和已知问题进行状态化表达。
本模块不打包压缩包，不运行测试，不写报告文件，不改版本号，不启动 L3，也不执行恢复或迁移。
本模块为后续 L3-L6 提供冻结基线引用，但不承担编排、执行、真实验证、真实恢复或子系统实现职责。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef

from .base_state import L2_STATE_SCHEMA_VERSION, L2StateMetadata
from .state_identity import L2StateIdentity
from .state_status import L2StateStatus


class L2ClosureStatus(str, Enum):
    """L2 收口状态枚举。

    作用：记录收口处于开放、收集、验收、可冻结、已冻结、阻断或重开等状态事实。
    边界：不改变冻结状态，不运行测试，不执行打包。
    """

    OPEN = "open"
    COLLECTING = "collecting"
    VALIDATING = "validating"
    READY_FOR_FREEZE = "ready_for_freeze"
    FROZEN = "frozen"
    BLOCKED = "blocked"
    REOPENED = "reopened"
    UNKNOWN = "unknown"


class L2IssueSeverity(str, Enum):
    """L2 已知问题严重度枚举。

    作用：记录问题处于提示、低、中、高、阻断或未知级别。
    边界：不做风险评分，不生成修复计划，不执行修复。
    """

    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    BLOCKER = "blocker"
    UNKNOWN = "unknown"


class L2IssueStatus(str, Enum):
    """L2 已知问题状态枚举。

    作用：记录问题处于已记录、需跟进、已缓解、阻断、关闭或未知状态。
    边界：不推进问题流转，不关闭问题，不执行治理。
    """

    RECORDED = "recorded"
    NEEDS_FOLLOWUP = "needs_followup"
    MITIGATED = "mitigated"
    BLOCKED = "blocked"
    CLOSED = "closed"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class L2ValidationSummaryState:
    """L2 验收摘要状态。

    作用：记录 compileall、pytest、序列化、哈希、导入、边界状态、通过数、失败数、警告数和未运行摘要。
    边界：不运行测试，不计算结果，不写测试报告。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    summary_id: TypedRef | None = None
    compileall_status: str = "unknown"
    pytest_status: str = "unknown"
    serialization_status: str = "unknown"
    hash_status: str = "unknown"
    import_status: str = "unknown"
    boundary_status: str = "unknown"
    passed_count: int = 0
    failed_count: int = 0
    warning_count: int = 0
    not_run_summary: str = ""
    created_at: str = ""
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.passed_count < 0:
            raise ValueError("L2ValidationSummaryState.passed_count cannot be negative")
        if self.failed_count < 0:
            raise ValueError("L2ValidationSummaryState.failed_count cannot be negative")
        if self.warning_count < 0:
            raise ValueError("L2ValidationSummaryState.warning_count cannot be negative")
        if len(self.not_run_summary) > 512:
            raise ValueError("L2ValidationSummaryState.not_run_summary must be a short summary")
        if not self.schema_version:
            raise ValueError("L2ValidationSummaryState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class L2KnownIssueState:
    """L2 已知问题状态。

    作用：记录问题引用、严重度、影响引用、摘要、规避摘要、目标跟进层和问题状态。
    边界：不修复问题，不创建任务，不修改受影响对象。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    issue_id: TypedRef | None = None
    severity: L2IssueSeverity = L2IssueSeverity.UNKNOWN
    affected_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    summary: str = ""
    workaround_summary: str = ""
    target_followup_layer: str = ""
    issue_status: L2IssueStatus = L2IssueStatus.UNKNOWN
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if len(self.summary) > 512:
            raise ValueError("L2KnownIssueState.summary must be a short summary")
        if len(self.workaround_summary) > 512:
            raise ValueError("L2KnownIssueState.workaround_summary must be a short summary")
        if len(self.target_followup_layer) > 64:
            raise ValueError("L2KnownIssueState.target_followup_layer must be short")
        if not self.schema_version:
            raise ValueError("L2KnownIssueState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class L2HandoffState:
    """L2 交接状态。

    作用：记录交接引用、L2 版本、冻结引用、L3 入口引用、L3 允许与禁止使用摘要、已知问题引用和验收摘要引用。
    边界：不启动 L3，不生成编排，不改变冻结对象。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    handoff_id: TypedRef | None = None
    l2_version: str = L2_STATE_SCHEMA_VERSION
    frozen_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    l3_entry_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    l3_allowed_usage_summary: str = ""
    l3_forbidden_usage_summary: str = ""
    known_issue_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    validation_summary_ref: TypedRef | None = None
    closure_status: L2ClosureStatus = L2ClosureStatus.UNKNOWN
    created_at: str = ""
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not self.l2_version:
            raise ValueError("L2HandoffState.l2_version cannot be empty")
        if len(self.l3_allowed_usage_summary) > 512:
            raise ValueError("L2HandoffState.l3_allowed_usage_summary must be a short summary")
        if len(self.l3_forbidden_usage_summary) > 512:
            raise ValueError("L2HandoffState.l3_forbidden_usage_summary must be a short summary")
        if not self.schema_version:
            raise ValueError("L2HandoffState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class L2FreezeState:
    """L2 冻结状态。

    作用：记录冻结引用、L2 版本、源归档引用、manifest 哈希、验收摘要引用、交接引用、冻结状态和原因摘要。
    边界：不打包归档，不生成哈希文件，不运行测试，不写报告。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    freeze_id: TypedRef | None = None
    l2_version: str = L2_STATE_SCHEMA_VERSION
    source_archive_ref: TypedRef | None = None
    manifest_hash: str = ""
    validation_summary_ref: TypedRef | None = None
    handoff_ref: TypedRef | None = None
    freeze_status: L2ClosureStatus = L2ClosureStatus.UNKNOWN
    reason_summary: str = ""
    created_at: str = ""
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not self.l2_version:
            raise ValueError("L2FreezeState.l2_version cannot be empty")
        if len(self.reason_summary) > 512:
            raise ValueError("L2FreezeState.reason_summary must be a short summary")
        if not self.schema_version:
            raise ValueError("L2FreezeState.schema_version cannot be empty")
