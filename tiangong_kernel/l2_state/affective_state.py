"""L2 情感与情志状态对象，记录情感底色、临时情感、欲望倾向、总色彩、表达倾向、行为倾向和边界事实。

本模块位于 L2 状态层，只记录情感系统可交接状态，服务工程生命体把表达倾向和行为倾向作为可审查状态输入。
本模块不实现情感生成算法，不实现欲望算法，不根据情感产生执行命令，不调用模型或工具，也不提升权限或绕过边界。
本模块为后续 L6 情感子系统实现、L3 倾向排序、L5 边界审查提供状态入口；情志层只给表达和倾向，不给执行令。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef

from .base_state import L2_STATE_SCHEMA_VERSION, L2StateMetadata
from .state_boundary import L2StateBoundary
from .state_identity import L2StateIdentity
from .state_status import L2StateStatus


class EmotionKind(str, Enum):
    """情感类型枚举。

    作用：记录喜、怒、忧、思、悲、恐、惊以及平静、好奇、紧迫、谨慎、坚持等情感类别。
    边界：只做情感分类，不生成情感，不判断用户人格，不触发动作。
    """

    JOY = "joy"
    ANGER = "anger"
    WORRY = "worry"
    THOUGHTFULNESS = "thoughtfulness"
    SADNESS = "sadness"
    FEAR = "fear"
    SURPRISE = "surprise"
    CALM = "calm"
    CURIOSITY = "curiosity"
    URGENCY = "urgency"
    CAUTION = "caution"
    PERSISTENCE = "persistence"
    UNKNOWN = "unknown"


class DesireTendencyKind(str, Enum):
    """欲望倾向类型枚举。

    作用：记录探索、保护、成就、沟通、学习、稳定、修复、创造等做事倾向类别。
    边界：只表达倾向，不产生执行命令，不选择 Skill，不释放工具。
    """

    EXPLORATION = "exploration"
    PROTECTION = "protection"
    ACHIEVEMENT = "achievement"
    COMMUNICATION = "communication"
    LEARNING = "learning"
    STABILITY = "stability"
    REPAIR = "repair"
    CREATION = "creation"
    UNKNOWN = "unknown"


class AffectiveBoundaryStatus(str, Enum):
    """情志边界状态枚举。

    作用：记录情志状态对表达、倾向、边界、权限和动作链的约束状态。
    边界：不执行真实裁决，不写入授权，不改变边界结果。
    """

    DECLARED = "declared"
    ENFORCED_BY_BOUNDARY = "enforced_by_boundary"
    NEEDS_REVIEW = "needs_review"
    BLOCKED = "blocked"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class EmotionBaseState:
    """情感底色状态。

    作用：记录稳定情感底色权重、稳定度、来源引用、摘要和时间事实。
    边界：不生成情感底色，不学习情感偏好，不记录过度个人敏感信息。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    base_id: TypedRef | None = None
    emotion_weights: tuple[tuple[str, float], ...] = field(default_factory=tuple)
    stability: float = 0.0
    source_ref: TypedRef | None = None
    summary: str = ""
    created_at: str = ""
    updated_at: str = ""
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not 0.0 <= self.stability <= 1.0:
            raise ValueError("EmotionBaseState.stability must be between 0.0 and 1.0")
        for key, value in self.emotion_weights:
            if not key:
                raise ValueError("EmotionBaseState emotion weight key cannot be empty")
            if not 0.0 <= value <= 1.0:
                raise ValueError("EmotionBaseState emotion weight value must be between 0.0 and 1.0")
        if len(self.summary) > 512:
            raise ValueError("EmotionBaseState.summary must be a short summary")
        if not self.schema_version:
            raise ValueError("EmotionBaseState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class EmotionTransientState:
    """临时情感状态。

    作用：记录一次临时情感的类型、强度、衰减提示、来源、置信度、边界状态和摘要。
    边界：不计算衰减，不生成情感，不触发模型或工具动作。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    transient_id: TypedRef | None = None
    emotion_kind: EmotionKind = EmotionKind.UNKNOWN
    intensity: float = 0.0
    decay_hint: float = 0.0
    source_ref: TypedRef | None = None
    confidence: float = 0.0
    boundary_status: L2StateBoundary | None = None
    summary: str = ""
    created_at: str = ""
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not 0.0 <= self.intensity <= 1.0:
            raise ValueError("EmotionTransientState.intensity must be between 0.0 and 1.0")
        if self.decay_hint < 0.0:
            raise ValueError("EmotionTransientState.decay_hint cannot be negative")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("EmotionTransientState.confidence must be between 0.0 and 1.0")
        if len(self.summary) > 512:
            raise ValueError("EmotionTransientState.summary must be a short summary")
        if not self.schema_version:
            raise ValueError("EmotionTransientState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class DesireTendencyState:
    """欲望倾向状态。

    作用：记录做事倾向类型、强度、优先提示、来源、置信度、边界状态和摘要。
    边界：不执行动作，不提升权限，不选择 Skill，不释放工具。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    desire_id: TypedRef | None = None
    tendency_kind: DesireTendencyKind = DesireTendencyKind.UNKNOWN
    intensity: float = 0.0
    priority_hint: float = 0.0
    source_ref: TypedRef | None = None
    confidence: float = 0.0
    boundary_status: L2StateBoundary | None = None
    summary: str = ""
    created_at: str = ""
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not 0.0 <= self.intensity <= 1.0:
            raise ValueError("DesireTendencyState.intensity must be between 0.0 and 1.0")
        if not 0.0 <= self.priority_hint <= 1.0:
            raise ValueError("DesireTendencyState.priority_hint must be between 0.0 and 1.0")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("DesireTendencyState.confidence must be between 0.0 and 1.0")
        if len(self.summary) > 512:
            raise ValueError("DesireTendencyState.summary must be a short summary")
        if not self.schema_version:
            raise ValueError("DesireTendencyState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ExpressionBiasState:
    """表达倾向状态。

    作用：记录温度、清晰度、简洁度、鼓励、谨慎语气和直接度权重。
    边界：只影响表达倾向，不影响执行权限，不改变边界状态。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    expression_bias_id: TypedRef | None = None
    warmth_weight: float = 0.0
    clarity_weight: float = 0.0
    brevity_weight: float = 0.0
    encouragement_weight: float = 0.0
    caution_tone_weight: float = 0.0
    directness_weight: float = 0.0
    summary: str = ""
    created_at: str = ""
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        weights = (
            self.warmth_weight,
            self.clarity_weight,
            self.brevity_weight,
            self.encouragement_weight,
            self.caution_tone_weight,
            self.directness_weight,
        )
        if any(not 0.0 <= value <= 1.0 for value in weights):
            raise ValueError("ExpressionBiasState weights must be between 0.0 and 1.0")
        if len(self.summary) > 512:
            raise ValueError("ExpressionBiasState.summary must be a short summary")
        if not self.schema_version:
            raise ValueError("ExpressionBiasState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ActionBiasState:
    """行为倾向状态。

    作用：记录探索、谨慎、坚持、修复、学习、稳定和确认偏好权重。
    边界：只为后续排序提供倾向输入，不产生执行令，不越过边界或动作层。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    action_bias_id: TypedRef | None = None
    exploration_weight: float = 0.0
    caution_weight: float = 0.0
    persistence_weight: float = 0.0
    repair_weight: float = 0.0
    learning_weight: float = 0.0
    stability_weight: float = 0.0
    confirmation_preference_weight: float = 0.0
    summary: str = ""
    created_at: str = ""
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        weights = (
            self.exploration_weight,
            self.caution_weight,
            self.persistence_weight,
            self.repair_weight,
            self.learning_weight,
            self.stability_weight,
            self.confirmation_preference_weight,
        )
        if any(not 0.0 <= value <= 1.0 for value in weights):
            raise ValueError("ActionBiasState weights must be between 0.0 and 1.0")
        if len(self.summary) > 512:
            raise ValueError("ActionBiasState.summary must be a short summary")
        if not self.schema_version:
            raise ValueError("ActionBiasState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class AffectiveColorState:
    """情感总色彩状态。

    作用：记录情感底色引用、临时情感引用、欲望引用、表达倾向引用、行为倾向引用、总强度、稳定提示、置信度和摘要。
    边界：不合成真实情感，不改变执行链，不覆盖架构边界。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    color_id: TypedRef | None = None
    base_ref: TypedRef | None = None
    transient_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    desire_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    expression_bias_ref: TypedRef | None = None
    action_bias_ref: TypedRef | None = None
    total_intensity: float = 0.0
    stability_hint: float = 0.0
    confidence: float = 0.0
    summary: str = ""
    created_at: str = ""
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not 0.0 <= self.total_intensity <= 1.0:
            raise ValueError("AffectiveColorState.total_intensity must be between 0.0 and 1.0")
        if not 0.0 <= self.stability_hint <= 1.0:
            raise ValueError("AffectiveColorState.stability_hint must be between 0.0 and 1.0")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("AffectiveColorState.confidence must be between 0.0 and 1.0")
        if len(self.summary) > 512:
            raise ValueError("AffectiveColorState.summary must be a short summary")
        if not self.schema_version:
            raise ValueError("AffectiveColorState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class AffectiveBoundaryState:
    """情志边界状态。

    作用：记录情志引用集合以及不得执行、不得覆盖边界审查、不得覆盖动作层、不得访问秘密、不得提升权限等约束事实。
    边界：不执行真实裁决，不生成确认，不改变权限。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    boundary_id: TypedRef | None = None
    affective_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    cannot_execute: bool = True
    cannot_override_l5: bool = True
    cannot_override_l4: bool = True
    cannot_access_secret: bool = True
    cannot_raise_permission: bool = True
    boundary_status: AffectiveBoundaryStatus = AffectiveBoundaryStatus.UNKNOWN
    summary: str = ""
    created_at: str = ""
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if len(self.summary) > 512:
            raise ValueError("AffectiveBoundaryState.summary must be a short summary")
        if not self.schema_version:
            raise ValueError("AffectiveBoundaryState.schema_version cannot be empty")
