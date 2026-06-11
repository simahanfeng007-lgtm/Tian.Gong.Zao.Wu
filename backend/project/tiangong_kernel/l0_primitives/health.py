"""L0 健康、活性与稳态事实语言原语。

本模块在 L0 中的职责：定义系统、主体、运行、插件、资源、环境、记忆、产物或副作用的健康事实引用。
本模块只表达：健康引用、健康信号引用、活性引用、稳态引用、稳定区间、偏离稳态、压力、损伤、恢复后健康引用。
本模块明确不做：健康评分、监控采集、自愈触发、节律模型、降级决策、恢复决策或自治等级调整。
禁止事项：不得采集指标，不得触发恢复，不得调用外部系统，不得计算系统生命分。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .identity import RefId, TypedRef
from .time import TimeRange


class HealthState(str, Enum):
    """健康状态枚举：只表达健康事实状态；UNKNOWN 表示未知或未判定。

    HEALTHY：健康；WATCH：观察；DEGRADED：降级；UNSTABLE：不稳定；CRITICAL：临界；
    RECOVERING：恢复中；FAILED：失败；UNKNOWN：未知兜底。
    """

    HEALTHY = "healthy"
    WATCH = "watch"
    DEGRADED = "degraded"
    UNSTABLE = "unstable"
    CRITICAL = "critical"
    RECOVERING = "recovering"
    FAILED = "failed"
    UNKNOWN = "unknown"


class VitalityKind(str, Enum):
    """活性类型枚举：只标记生命体运行能力维度；UNKNOWN 表示未知或暂不归类。

    STRUCTURAL_INTEGRITY：结构完整性；EXECUTION_CAPACITY：执行容量；RESOURCE_BALANCE：资源平衡；MEMORY_CONTINUITY：记忆连续性；
    FORGETTING_CLEANLINESS：遗忘洁净度；SELF_CONTINUITY：自我连续性；ADAPTATION_CAPACITY：适应能力；RECOVERY_CAPACITY：恢复能力；
    TRUST_INTEGRITY：信任完整性；UNKNOWN：未知兜底。
    """

    STRUCTURAL_INTEGRITY = "structural_integrity"
    EXECUTION_CAPACITY = "execution_capacity"
    RESOURCE_BALANCE = "resource_balance"
    MEMORY_CONTINUITY = "memory_continuity"
    FORGETTING_CLEANLINESS = "forgetting_cleanliness"
    SELF_CONTINUITY = "self_continuity"
    ADAPTATION_CAPACITY = "adaptation_capacity"
    RECOVERY_CAPACITY = "recovery_capacity"
    TRUST_INTEGRITY = "trust_integrity"
    UNKNOWN = "unknown"


class VitalityState(str, Enum):
    """活性状态枚举：只表达生命变量当前活性状态；UNKNOWN 表示未知或未判定。

    STRONG：强；NORMAL：正常；WEAKENED：弱化；DAMAGED：受损；RECOVERING：恢复中；COLLAPSED：坍塌；UNKNOWN：未知兜底。
    """

    STRONG = "strong"
    NORMAL = "normal"
    WEAKENED = "weakened"
    DAMAGED = "damaged"
    RECOVERING = "recovering"
    COLLAPSED = "collapsed"
    UNKNOWN = "unknown"


class HomeostasisState(str, Enum):
    """稳态状态枚举：只表达生命变量是否处于稳定区间；UNKNOWN 表示未知或未判定。

    WITHIN_RANGE：区间内；DRIFTING：漂移中；OUT_OF_RANGE：区间外；COMPENSATING：补偿中；FAILED：稳态失败；UNKNOWN：未知兜底。
    """

    WITHIN_RANGE = "within_range"
    DRIFTING = "drifting"
    OUT_OF_RANGE = "out_of_range"
    COMPENSATING = "compensating"
    FAILED = "failed"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class StabilityRange:
    """稳定区间。

    作用：表达某个生命变量或运行变量的稳定范围。
    所属 L0 边界：只保存 label、lower_bound、upper_bound、time_range 和 unit。
    不能承担的上层职责：不能计算健康状态，不能触发降级或恢复。
    字段：label 为变量名称；lower_bound/upper_bound 为稳定区间上下界。
    """

    label: str = "unknown"
    lower_bound: float | None = None
    upper_bound: float | None = None
    unit: str = "unitless"
    time_range: TimeRange | None = None
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.label:
            raise ValueError("StabilityRange.label cannot be empty")
        if not self.unit:
            raise ValueError("StabilityRange.unit cannot be empty")
        if self.lower_bound is not None and self.upper_bound is not None and self.upper_bound < self.lower_bound:
            raise ValueError("StabilityRange.upper_bound cannot be lower than lower_bound")
        if not self.schema_version:
            raise ValueError("StabilityRange.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class HealthSignalRef:
    """健康信号引用。

    作用：表达某条健康相关信号的引用事实。
    所属 L0 边界：只保存 signal_id、signal_ref 和 evidence_refs。
    不能承担的上层职责：不能采集信号，不能聚合指标，不能判断健康等级。
    字段：value 为健康信号引用 ID；signal_ref 为底层信号事实引用。
    """

    value: RefId
    signal_ref: TypedRef | None = None
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("HealthSignalRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class VitalityRef:
    """活性引用。

    作用：表达生命体运行能力、活性、连续性和适应能力的事实引用。
    所属 L0 边界：只保存 vitality_id、kind、state、subject_ref 和 evidence_refs。
    不能承担的上层职责：不能计算活性分，不能调整自治等级。
    字段：value 为活性引用 ID；kind 为活性类型；state 为活性状态。
    """

    value: RefId
    kind: VitalityKind = VitalityKind.UNKNOWN
    state: VitalityState = VitalityState.UNKNOWN
    subject_ref: TypedRef | None = None
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("VitalityRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class HomeostasisRef:
    """稳态引用。

    作用：表达系统维持内部稳定区间的事实引用。
    所属 L0 边界：只保存 homeostasis_id、state、stability_range 和 subject_ref。
    不能承担的上层职责：不能执行补偿，不能计算稳态控制动作。
    字段：value 为稳态引用 ID；stability_range 为稳定区间事实。
    """

    value: RefId
    state: HomeostasisState = HomeostasisState.UNKNOWN
    stability_range: StabilityRange | None = None
    subject_ref: TypedRef | None = None
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("HomeostasisRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class StabilityDeviationRef:
    """稳态偏离引用。

    作用：表达某个生命变量或运行变量偏离稳定区间的事实引用。
    所属 L0 边界：只保存 deviation_id、range_ref、observed_value 和 evidence_refs。
    不能承担的上层职责：不能计算偏离等级，不能触发恢复流程。
    字段：observed_value 为观测值；range_ref 为稳定区间引用。
    """

    value: RefId
    range_ref: TypedRef | None = None
    observed_value: float | None = None
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("StabilityDeviationRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class StressRef:
    """压力源引用。

    作用：表达系统、主体、资源或环境承受压力的来源事实引用。
    所属 L0 边界：只保存 stress_id、source_ref、target_ref 和 intensity。
    不能承担的上层职责：不能采集压力，不能计算压力模型，不能触发降级。
    字段：intensity 为 0 到 1 的压力强度事实。
    """

    value: RefId
    source_ref: TypedRef | None = None
    target_ref: TypedRef | None = None
    intensity: float = 0.0
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not 0.0 <= self.intensity <= 1.0:
            raise ValueError("StressRef.intensity must be between 0 and 1")
        if not self.schema_version:
            raise ValueError("StressRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class DamageRef:
    """损伤引用。

    作用：表达结构、运行、记忆、资源、信任或恢复能力受损的事实引用。
    所属 L0 边界：只保存 damage_id、target_ref、severity 和 evidence_refs。
    不能承担的上层职责：不能执行修复，不能评估完整根因。
    字段：severity 为 0 到 1 的损伤程度事实。
    """

    value: RefId
    target_ref: TypedRef | None = None
    severity: float = 0.0
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not 0.0 <= self.severity <= 1.0:
            raise ValueError("DamageRef.severity must be between 0 and 1")
        if not self.schema_version:
            raise ValueError("DamageRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class RecoveryHealthRef:
    """恢复后健康引用。

    作用：表达恢复动作完成后系统或对象健康状态的引用事实。
    所属 L0 边界：只保存 recovery_health_id、health_ref、recovery_ref 和 evidence_refs。
    不能承担的上层职责：不能执行恢复，不能验证恢复效果。
    字段：health_ref 为健康引用；recovery_ref 为恢复路径或恢复结果引用。
    """

    value: RefId
    health_ref: TypedRef | None = None
    recovery_ref: TypedRef | None = None
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("RecoveryHealthRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class HealthRef:
    """健康引用。

    作用：表达系统、主体、运行、插件、资源、环境、记忆、产物或副作用的健康事实引用。
    所属 L0 边界：只保存 health_id、state、subject_ref、signal_refs、vitality_ref、homeostasis_ref 等引用事实。
    不能承担的上层职责：不能评分，不能监控采集，不能触发自愈或降级。
    字段：value 为健康引用 ID；state 为健康状态；subject_ref 为被观察对象引用。
    """

    value: RefId
    state: HealthState = HealthState.UNKNOWN
    subject_ref: TypedRef | None = None
    signal_refs: tuple[HealthSignalRef, ...] = field(default_factory=tuple)
    vitality_ref: VitalityRef | None = None
    homeostasis_ref: HomeostasisRef | None = None
    deviation_ref: StabilityDeviationRef | None = None
    stress_ref: StressRef | None = None
    damage_ref: DamageRef | None = None
    recovery_health_ref: RecoveryHealthRef | None = None
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("HealthRef.schema_version cannot be empty")
