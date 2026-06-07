"""L3 第四阶段意图引用与意图信封对象。

本模块只表达 ModelIntent / ToolIntent / ActionIntent 的 L3 编排表示。
它不调用模型，不调用工具，不执行动作，不生成真实边界审查请求或真实执行请求。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef

from .orchestration_identity import L3_ORCHESTRATION_SCHEMA_VERSION


class IntentKind(str, Enum):
    """第四阶段意图类别。"""

    UNKNOWN = "unknown"
    MODEL = "model"
    TOOL = "tool"
    ACTION = "action"


class IntentEnvelopeStatus(str, Enum):
    """意图信封结构状态；仅表达检查结果，不做裁决。"""

    UNKNOWN = "unknown"
    STRUCTURED = "structured"
    PARTIAL = "partial"
    AMBIGUOUS = "ambiguous"
    CONFLICTING = "conflicting"
    NEED_CLARIFICATION = "need_clarification"


def _ensure_short_text(value: str, field_name: str, limit: int = 512) -> None:
    if len(value) > limit:
        raise ValueError(f"{field_name} must be short")


def _ensure_unit_interval(value: float, field_name: str) -> None:
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{field_name} must be between 0.0 and 1.0")


def _ensure_short_items(values: tuple[str, ...], field_name: str, limit: int = 128) -> None:
    for value in values:
        if not value or len(value) > limit:
            raise ValueError(f"{field_name} entries must be non-empty and short")


@dataclass(frozen=True, slots=True)
class ModelIntentRef:
    """模型意图引用；不代表模型真实调用。"""

    intent_ref: TypedRef
    source_turn_ref: TypedRef | None = None
    run_ref: TypedRef | None = None
    task_ref: TypedRef | None = None
    step_ref: TypedRef | None = None
    skill_ref: TypedRef | None = None
    tool_group_ref: TypedRef | None = None
    source_advice_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.advisory_only is not True:
            raise ValueError("ModelIntentRef.advisory_only must remain true")
        if not self.schema_version:
            raise ValueError("ModelIntentRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ToolIntentRef:
    """工具调用意图引用；不代表真实工具调用。"""

    intent_ref: TypedRef
    tool_group_ref: TypedRef | None = None
    tool_ref: TypedRef | None = None
    model_intent_ref: TypedRef | None = None
    run_ref: TypedRef | None = None
    task_ref: TypedRef | None = None
    turn_ref: TypedRef | None = None
    step_ref: TypedRef | None = None
    source_advice_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.advisory_only is not True:
            raise ValueError("ToolIntentRef.advisory_only must remain true")
        if not self.schema_version:
            raise ValueError("ToolIntentRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ActionIntentRef:
    """动作意图引用；不代表动作已执行。"""

    intent_ref: TypedRef
    action_label: str = ""
    model_intent_ref: TypedRef | None = None
    tool_intent_ref: TypedRef | None = None
    run_ref: TypedRef | None = None
    task_ref: TypedRef | None = None
    turn_ref: TypedRef | None = None
    step_ref: TypedRef | None = None
    source_advice_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.action_label, "ActionIntentRef.action_label", 128)
        if self.advisory_only is not True:
            raise ValueError("ActionIntentRef.advisory_only must remain true")
        if not self.schema_version:
            raise ValueError("ActionIntentRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ModelIntentEnvelope:
    """模型意图信封；只承载结构化摘要与字段状态。"""

    envelope_ref: TypedRef
    intent_ref: ModelIntentRef
    intent_kind: IntentKind = IntentKind.MODEL
    status: IntentEnvelopeStatus = IntentEnvelopeStatus.PARTIAL
    stated_goal: str = ""
    requested_capability_hint: str = ""
    provided_fields: tuple[str, ...] = field(default_factory=tuple)
    missing_fields: tuple[str, ...] = field(default_factory=tuple)
    conflict_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    ambiguity_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    confidence: float = 0.0
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.intent_kind is not IntentKind.MODEL:
            raise ValueError("ModelIntentEnvelope.intent_kind must be MODEL")
        _ensure_short_text(self.stated_goal, "ModelIntentEnvelope.stated_goal")
        _ensure_short_text(self.requested_capability_hint, "ModelIntentEnvelope.requested_capability_hint", 128)
        _ensure_short_items(self.provided_fields, "ModelIntentEnvelope.provided_fields")
        for item in self.missing_fields:
            if len(item) > 128:
                raise ValueError("ModelIntentEnvelope.missing_fields entries must be short")
        _ensure_unit_interval(self.confidence, "ModelIntentEnvelope.confidence")
        if self.advisory_only is not True:
            raise ValueError("ModelIntentEnvelope.advisory_only must remain true")
        if not self.schema_version:
            raise ValueError("ModelIntentEnvelope.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ToolIntentParameterSpecRef:
    """工具意图参数规格引用；只用于完整度检查建议。"""

    parameter_spec_ref: TypedRef
    parameter_name: str
    required: bool = True
    expected_type_hint: str = "unknown"
    source_tool_ref: TypedRef | None = None
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.parameter_name, "ToolIntentParameterSpecRef.parameter_name", 128)
        _ensure_short_text(self.expected_type_hint, "ToolIntentParameterSpecRef.expected_type_hint", 128)
        if not self.parameter_name:
            raise ValueError("ToolIntentParameterSpecRef.parameter_name cannot be empty")
        if not self.schema_version:
            raise ValueError("ToolIntentParameterSpecRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ToolIntentEnvelope:
    """工具意图信封；不调用工具，不生成工具参数执行体。"""

    envelope_ref: TypedRef
    intent_ref: ToolIntentRef
    intent_kind: IntentKind = IntentKind.TOOL
    status: IntentEnvelopeStatus = IntentEnvelopeStatus.PARTIAL
    tool_name_hint: str = ""
    parameter_spec_refs: tuple[ToolIntentParameterSpecRef, ...] = field(default_factory=tuple)
    provided_parameter_names: tuple[str, ...] = field(default_factory=tuple)
    missing_parameter_names: tuple[str, ...] = field(default_factory=tuple)
    conflict_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    confidence: float = 0.0
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.intent_kind is not IntentKind.TOOL:
            raise ValueError("ToolIntentEnvelope.intent_kind must be TOOL")
        _ensure_short_text(self.tool_name_hint, "ToolIntentEnvelope.tool_name_hint", 128)
        _ensure_short_items(self.provided_parameter_names, "ToolIntentEnvelope.provided_parameter_names")
        for item in self.missing_parameter_names:
            if len(item) > 128:
                raise ValueError("ToolIntentEnvelope.missing_parameter_names entries must be short")
        _ensure_unit_interval(self.confidence, "ToolIntentEnvelope.confidence")
        if self.advisory_only is not True:
            raise ValueError("ToolIntentEnvelope.advisory_only must remain true")
        if not self.schema_version:
            raise ValueError("ToolIntentEnvelope.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ActionIntentTargetRef:
    """动作目标引用；只表达目标，不触发动作。"""

    target_ref: TypedRef
    target_label: str = ""
    target_kind_hint: str = "unknown"
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.target_label, "ActionIntentTargetRef.target_label", 128)
        _ensure_short_text(self.target_kind_hint, "ActionIntentTargetRef.target_kind_hint", 128)
        if not self.schema_version:
            raise ValueError("ActionIntentTargetRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ActionIntentEnvelope:
    """动作意图信封；只表达动作意图结构，不执行动作。"""

    envelope_ref: TypedRef
    intent_ref: ActionIntentRef
    intent_kind: IntentKind = IntentKind.ACTION
    status: IntentEnvelopeStatus = IntentEnvelopeStatus.PARTIAL
    action_summary: str = ""
    target_refs: tuple[ActionIntentTargetRef, ...] = field(default_factory=tuple)
    provided_fields: tuple[str, ...] = field(default_factory=tuple)
    missing_fields: tuple[str, ...] = field(default_factory=tuple)
    precondition_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    confidence: float = 0.0
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.intent_kind is not IntentKind.ACTION:
            raise ValueError("ActionIntentEnvelope.intent_kind must be ACTION")
        _ensure_short_text(self.action_summary, "ActionIntentEnvelope.action_summary")
        _ensure_short_items(self.provided_fields, "ActionIntentEnvelope.provided_fields")
        for item in self.missing_fields:
            if len(item) > 128:
                raise ValueError("ActionIntentEnvelope.missing_fields entries must be short")
        _ensure_unit_interval(self.confidence, "ActionIntentEnvelope.confidence")
        if self.advisory_only is not True:
            raise ValueError("ActionIntentEnvelope.advisory_only must remain true")
        if not self.schema_version:
            raise ValueError("ActionIntentEnvelope.schema_version cannot be empty")
