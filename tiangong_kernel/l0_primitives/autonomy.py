"""L0 自治、能动性与控制姿态事实语言原语。

本模块在 L0 中的职责：定义自治等级、能动性等级、控制模式、人类监督方式及自治/能动边界引用事实。
本模块只表达：系统在何种监督和边界下具有何种行动影响能力的事实语言。
本模块明确不做：模式切换、高权限模式、组织审批、权限策略、自动降级或界面按钮。
禁止事项：不得实现绕过安全的模式，不得执行控制模式切换，不得改变真实权限。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .identity import RefId, TypedRef


class AutonomyLevel(str, Enum):
    """自治等级：不用 A0-A5，避免与风险等级混淆；UNKNOWN 表示等级未知。

    L0_MANUAL：人工手动；L1_OBSERVE：只观察；L2_ADVISE：建议；L3_ACT_WITH_APPROVAL：审批后行动；
    L4_BOUNDED_AUTONOMY：有界自治；L5_FULL_AUTONOMY：完全自治事实标记；UNKNOWN：未知兜底。
    """
    L0_MANUAL="l0_manual"; L1_OBSERVE="l1_observe"; L2_ADVISE="l2_advise"; L3_ACT_WITH_APPROVAL="l3_act_with_approval"; L4_BOUNDED_AUTONOMY="l4_bounded_autonomy"; L5_FULL_AUTONOMY="l5_full_autonomy"; UNKNOWN="unknown"

class AgencyLevel(str, Enum):
    """能动性等级：表达被允许产生的影响范围；UNKNOWN 表示等级未知。

    G0_REASON_ONLY：仅推理；G1_READ_CONTEXT：读取上下文；G2_PROPOSE_ACTION：提出行动；G3_REQUEST_EFFECT：请求副作用；
    G4_COMMIT_REVERSIBLE：提交可逆副作用；G5_COMMIT_IRREVERSIBLE：提交不可逆副作用事实标记；UNKNOWN：未知兜底。
    """
    G0_REASON_ONLY="g0_reason_only"; G1_READ_CONTEXT="g1_read_context"; G2_PROPOSE_ACTION="g2_propose_action"; G3_REQUEST_EFFECT="g3_request_effect"; G4_COMMIT_REVERSIBLE="g4_commit_reversible"; G5_COMMIT_IRREVERSIBLE="g5_commit_irreversible"; UNKNOWN="unknown"

class OversightMode(str, Enum):
    """人类监督方式：只表达监督姿态；UNKNOWN 表示监督方式未知。

    HUMAN_IN_COMMAND：人类指挥；HUMAN_IN_THE_LOOP：人在环中；HUMAN_ON_THE_LOOP：人在环上监督；HUMAN_OUT_OF_THE_LOOP：人不在环；UNKNOWN：未知兜底。
    """
    HUMAN_IN_COMMAND="human_in_command"; HUMAN_IN_THE_LOOP="human_in_the_loop"; HUMAN_ON_THE_LOOP="human_on_the_loop"; HUMAN_OUT_OF_THE_LOOP="human_out_of_the_loop"; UNKNOWN="unknown"

class ControlModeState(str, Enum):
    """控制模式状态：只表达控制姿态生命周期；UNKNOWN 表示状态未知。

    PROPOSED：提议；ACTIVE：活动；ESCALATED：升级；DEGRADED：降级；SUSPENDED：暂停；REVOKED：撤销；EXPIRED：过期；ARCHIVED：归档；UNKNOWN：未知兜底。
    """
    PROPOSED="proposed"; ACTIVE="active"; ESCALATED="escalated"; DEGRADED="degraded"; SUSPENDED="suspended"; REVOKED="revoked"; EXPIRED="expired"; ARCHIVED="archived"; UNKNOWN="unknown"

@dataclass(frozen=True, slots=True)
class AutonomyBoundaryRef:
    """自治边界引用。

    作用：表达自治能力适用的范围边界。
    所属 L0 边界：只保存 autonomy_boundary_id 与 boundary_refs。
    不能承担的上层职责：不能执行边界判断，不能改变控制模式。
    字段：value 为自治边界引用 ID；boundary_refs 为关联边界引用集合。
    """
    value: RefId; boundary_refs: tuple[TypedRef,...]=field(default_factory=tuple); schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("AutonomyBoundaryRef.schema_version cannot be empty")

@dataclass(frozen=True, slots=True)
class AgencyBoundaryRef:
    """能动边界引用。

    作用：表达行动影响力的边界引用事实。
    所属 L0 边界：只保存 agency_boundary_id 与 boundary_refs。
    不能承担的上层职责：不能授权影响，不能执行权限策略。
    字段：value 为能动边界引用 ID；boundary_refs 为关联边界引用集合。
    """
    value: RefId; boundary_refs: tuple[TypedRef,...]=field(default_factory=tuple); schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("AgencyBoundaryRef.schema_version cannot be empty")

@dataclass(frozen=True, slots=True)
class ControlModeRef:
    """控制模式引用。

    作用：表达当前运行所采用的控制姿态引用。
    所属 L0 边界：只保存 control_mode_id、autonomy_level、agency_level、oversight_mode 与 state。
    不能承担的上层职责：不能切换模式，不能启用高权限，不能绕过安全边界。
    字段：value 为控制模式引用 ID；autonomy_level 为自治等级；agency_level 为能动性等级。
    """
    value: RefId; autonomy_level: AutonomyLevel=AutonomyLevel.UNKNOWN; agency_level: AgencyLevel=AgencyLevel.UNKNOWN; oversight_mode: OversightMode=OversightMode.UNKNOWN; state: ControlModeState=ControlModeState.UNKNOWN; autonomy_boundary_ref: AutonomyBoundaryRef|None=None; agency_boundary_ref: AgencyBoundaryRef|None=None; schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("ControlModeRef.schema_version cannot be empty")
