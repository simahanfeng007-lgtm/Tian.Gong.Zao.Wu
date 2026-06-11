"""L2 观察源状态对象。

作用：记录外部观察事实来自哪个来源及其可信、边界、安全和环境引用。
边界：这是状态对象，不是观察器、采集器或监听器，不从观察源读取任何内容。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef

from .base_state import L2_STATE_SCHEMA_VERSION, L2StateMetadata
from .state_identity import L2StateIdentity
from .state_status import L2StateStatus


class ObservationSourceKind(str, Enum):
    """观察源类型。

    作用：表达外部观察事实来自模型输出、工具结果、边界事件、测试事件或人工输入等来源。
    边界：这是状态标签，不恢复旧 Runtime 主链，不读取来源内容。
    """

    MODEL_OUTPUT = "model_output"
    TOOL_RESULT = "tool_result"
    RUNTIME_EVENT = "runtime_event"
    BOUNDARY_EVENT = "boundary_event"
    SECURITY_EVENT = "security_event"
    RESOURCE_EVENT = "resource_event"
    ENVIRONMENT_EVENT = "environment_event"
    AUDIT_EVENT = "audit_event"
    TEST_EVENT = "test_event"
    HUMAN_INPUT = "human_input"
    SYSTEM_NOTE = "system_note"
    EXTERNAL_ADAPTER = "external_adapter"
    UNKNOWN = "unknown"


class ObservationSourceStatus(str, Enum):
    """观察源状态。

    作用：表达外部报告的观察源声明、可用、不可用、过期、撤销或脱敏状态。
    边界：这是状态对象的状态标签，不检查来源可用性，不读取真实内容。
    """

    DECLARED = "declared"
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    STALE = "stale"
    REVOKED = "revoked"
    REDACTED = "redacted"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class ObservationSourceState:
    """观察源状态。

    作用：记录观察源引用、来源类型、来源状态、可信标签及相关运行、任务、Skill、工具和效果引用。
    边界：这是状态对象，不是观察器、采集器或监听器，不读取模型输出、工具结果、日志或外部适配器。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    source_ref: TypedRef | None = None
    source_kind: ObservationSourceKind = ObservationSourceKind.UNKNOWN
    source_status: ObservationSourceStatus = ObservationSourceStatus.UNKNOWN
    display_name: str | None = None
    boundary_state_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    security_state_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    environment_state_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    trust_level_label: str | None = None
    reliability_label: str | None = None
    created_at_ref: TypedRef | None = None
    owner_actor_ref: TypedRef | None = None
    related_run_ref: TypedRef | None = None
    related_task_ref: TypedRef | None = None
    related_skill_ref: TypedRef | None = None
    related_tool_group_ref: TypedRef | None = None
    related_tool_intent_ref: TypedRef | None = None
    related_action_ref: TypedRef | None = None
    related_effect_ref: TypedRef | None = None
    redaction_reason_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name, value in (
            ("display_name", self.display_name),
            ("trust_level_label", self.trust_level_label),
            ("reliability_label", self.reliability_label),
        ):
            if value == "":
                raise ValueError(f"ObservationSourceState.{name} cannot be empty when provided")
        if not self.schema_version:
            raise ValueError("ObservationSourceState.schema_version cannot be empty")
