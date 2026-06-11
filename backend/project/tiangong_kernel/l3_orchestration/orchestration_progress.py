"""L3 第二阶段进度快照对象。

这些对象只表达进度事实与自洽性提示，不启动运行循环、不派发任务、不写入状态。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef

from .orchestration_identity import L3_ORCHESTRATION_SCHEMA_VERSION
from .orchestration_lifecycle import OrchestrationLifecycleKind


class ProgressSnapshotKind(str, Enum):
    """进度快照类别。"""

    UNKNOWN = "unknown"
    RUN = "run"
    TASK = "task"
    STEP = "step"


def _ensure_unit_interval(value: float, field_name: str) -> None:
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{field_name} must be between 0.0 and 1.0")


def progress_ratio_from_counts(completed_count: int, total_count: int) -> float:
    """根据计数生成确定性的进度比例；只做内存数学归一化。"""

    if completed_count < 0:
        raise ValueError("completed_count cannot be negative")
    if total_count < 0:
        raise ValueError("total_count cannot be negative")
    if total_count == 0:
        return 0.0
    if completed_count > total_count:
        raise ValueError("completed_count cannot exceed total_count")
    return completed_count / total_count


@dataclass(frozen=True, slots=True)
class ProgressMarker:
    """单个进度标记事实。"""

    marker_ref: TypedRef | None = None
    marker_index: int = 0
    label: str = ""
    completed: bool = False
    state_ref: TypedRef | None = None
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.marker_index < 0:
            raise ValueError("ProgressMarker.marker_index cannot be negative")
        if len(self.label) > 128:
            raise ValueError("ProgressMarker.label must be short")
        if not self.schema_version:
            raise ValueError("ProgressMarker.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class RunProgressSnapshot:
    """Run 级进度快照。"""

    snapshot_ref: TypedRef | None = None
    snapshot_kind: ProgressSnapshotKind = ProgressSnapshotKind.RUN
    run_ref: TypedRef | None = None
    lifecycle: OrchestrationLifecycleKind = OrchestrationLifecycleKind.UNKNOWN
    task_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    completed_task_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    active_task_ref: TypedRef | None = None
    progress_ratio: float = 0.0
    markers: tuple[ProgressMarker, ...] = field(default_factory=tuple)
    missing_state_fields: tuple[str, ...] = field(default_factory=tuple)
    summary: str = ""
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_unit_interval(self.progress_ratio, "RunProgressSnapshot.progress_ratio")
        if len(self.completed_task_refs) > len(self.task_refs):
            raise ValueError("RunProgressSnapshot.completed_task_refs cannot exceed task_refs")
        if any(len(item) > 128 for item in self.missing_state_fields):
            raise ValueError("RunProgressSnapshot.missing_state_fields entries must be short")
        if len(self.summary) > 512:
            raise ValueError("RunProgressSnapshot.summary must be a short summary")
        if not self.schema_version:
            raise ValueError("RunProgressSnapshot.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class TaskProgressSnapshot:
    """Task 级进度快照。"""

    snapshot_ref: TypedRef | None = None
    snapshot_kind: ProgressSnapshotKind = ProgressSnapshotKind.TASK
    task_ref: TypedRef | None = None
    run_ref: TypedRef | None = None
    lifecycle: OrchestrationLifecycleKind = OrchestrationLifecycleKind.UNKNOWN
    step_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    completed_step_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    active_step_ref: TypedRef | None = None
    progress_ratio: float = 0.0
    markers: tuple[ProgressMarker, ...] = field(default_factory=tuple)
    missing_state_fields: tuple[str, ...] = field(default_factory=tuple)
    summary: str = ""
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_unit_interval(self.progress_ratio, "TaskProgressSnapshot.progress_ratio")
        if len(self.completed_step_refs) > len(self.step_refs):
            raise ValueError("TaskProgressSnapshot.completed_step_refs cannot exceed step_refs")
        if any(len(item) > 128 for item in self.missing_state_fields):
            raise ValueError("TaskProgressSnapshot.missing_state_fields entries must be short")
        if len(self.summary) > 512:
            raise ValueError("TaskProgressSnapshot.summary must be a short summary")
        if not self.schema_version:
            raise ValueError("TaskProgressSnapshot.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class StepProgressSnapshot:
    """Step 级进度快照。"""

    snapshot_ref: TypedRef | None = None
    snapshot_kind: ProgressSnapshotKind = ProgressSnapshotKind.STEP
    step_ref: TypedRef | None = None
    task_ref: TypedRef | None = None
    lifecycle: OrchestrationLifecycleKind = OrchestrationLifecycleKind.UNKNOWN
    completed: bool = False
    progress_ratio: float = 0.0
    required_state_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    available_state_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    missing_state_fields: tuple[str, ...] = field(default_factory=tuple)
    summary: str = ""
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_unit_interval(self.progress_ratio, "StepProgressSnapshot.progress_ratio")
        if any(len(item) > 128 for item in self.missing_state_fields):
            raise ValueError("StepProgressSnapshot.missing_state_fields entries must be short")
        if len(self.summary) > 512:
            raise ValueError("StepProgressSnapshot.summary must be a short summary")
        if not self.schema_version:
            raise ValueError("StepProgressSnapshot.schema_version cannot be empty")
