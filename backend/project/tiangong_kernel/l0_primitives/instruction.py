"""L0 指令与治理指令事实语言原语。

本模块在 L0 中的职责：定义观察到的指令、指令来源、权力等级、优先级、状态、冲突和治理指令引用事实。
本模块只表达：系统、开发者、用户、插件、外部内容、模型建议或恢复流程提出的指令事实。
本模块明确不做：提示词模板、消息拼接、指令优先级仲裁、注入检测或上下文装配。
禁止事项：不得保存系统提示内容，不得构建模型输入，不得实现指令冲突裁决算法。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .identity import RefId, TypedRef


class InstructionKind(str, Enum):
    """指令类别：只表达指令事实类型；UNKNOWN 表示类别未知。

    SYSTEM_POLICY：系统政策；DEVELOPER_RULE：开发者规则；USER_REQUEST：用户请求；USER_CONSTRAINT：用户约束；
    PLUGIN_DIRECTIVE：插件指令；TOOL_OBSERVATION：工具观察；EXTERNAL_CONTENT：外部内容；MODEL_SUGGESTION：模型建议；RECOVERY_DIRECTIVE：恢复指令；UNKNOWN：未知兜底。
    """
    SYSTEM_POLICY="system_policy"; DEVELOPER_RULE="developer_rule"; USER_REQUEST="user_request"; USER_CONSTRAINT="user_constraint"; PLUGIN_DIRECTIVE="plugin_directive"; TOOL_OBSERVATION="tool_observation"; EXTERNAL_CONTENT="external_content"; MODEL_SUGGESTION="model_suggestion"; RECOVERY_DIRECTIVE="recovery_directive"; UNKNOWN="unknown"

class InstructionAuthority(str, Enum):
    """指令权力等级：只表达来源权威级别；UNKNOWN 表示权威未知。

    ROOT：根级；SYSTEM：系统；DEVELOPER：开发者；USER：用户；PLUGIN：插件；MODEL：模型；EXTERNAL：外部；NONE：无权威；UNKNOWN：未知兜底。
    """
    ROOT="root"; SYSTEM="system"; DEVELOPER="developer"; USER="user"; PLUGIN="plugin"; MODEL="model"; EXTERNAL="external"; NONE="none"; UNKNOWN="unknown"

class InstructionState(str, Enum):
    """指令状态：只表达指令生命周期；UNKNOWN 表示状态未知。

    OBSERVED：已观察；CLASSIFIED：已分类；ACTIVE：活动；CONFLICTED：冲突；SUPERSEDED：被取代；REJECTED：已拒绝；EXPIRED：过期；ARCHIVED：归档；UNKNOWN：未知兜底。
    """
    OBSERVED="observed"; CLASSIFIED="classified"; ACTIVE="active"; CONFLICTED="conflicted"; SUPERSEDED="superseded"; REJECTED="rejected"; EXPIRED="expired"; ARCHIVED="archived"; UNKNOWN="unknown"

@dataclass(frozen=True, slots=True)
class InstructionSource:
    """指令来源。

    作用：表达指令来自 Actor、系统、用户、插件、外部内容或恢复流程的来源引用。
    所属 L0 边界：只保存 source_ref 与 authority。
    不能承担的上层职责：不能读取来源内容，不能判定来源可信性。
    字段：source_ref 为来源引用；authority 为指令权力等级。
    """
    source_ref: TypedRef|None=None; authority: InstructionAuthority=InstructionAuthority.UNKNOWN; schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("InstructionSource.schema_version cannot be empty")

@dataclass(frozen=True, slots=True)
class InstructionPriority:
    """指令优先级。

    作用：表达指令优先级数值事实。
    所属 L0 边界：只保存 priority 数值，不做排序或仲裁。
    不能承担的上层职责：不能解决指令冲突，不能覆盖其他指令。
    字段：priority 为优先级值，数值越大仅表示更高事实标记。
    """
    priority: int=0; schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("InstructionPriority.schema_version cannot be empty")

@dataclass(frozen=True, slots=True)
class InstructionConflictRef:
    """指令冲突引用。

    作用：表达多个指令之间存在冲突的引用事实。
    所属 L0 边界：只保存 conflict_id 与 instruction_refs。
    不能承担的上层职责：不能仲裁冲突，不能重排优先级。
    字段：value 为冲突引用 ID；instruction_refs 为冲突指令引用集合。
    """
    value: RefId; instruction_refs: tuple[TypedRef,...]=field(default_factory=tuple); schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("InstructionConflictRef.schema_version cannot be empty")

@dataclass(frozen=True, slots=True)
class DirectiveRef:
    """治理指令引用。

    作用：表达具有更强约束力的系统性指令或治理指令引用。
    所属 L0 边界：只保存 directive_id、authority 与 source。
    不能承担的上层职责：不能生成提示词，不能执行治理，不能裁决冲突。
    字段：value 为治理指令引用 ID；authority 为权力等级；source 为来源事实。
    """
    value: RefId; authority: InstructionAuthority=InstructionAuthority.UNKNOWN; source: InstructionSource|None=None; schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("DirectiveRef.schema_version cannot be empty")

@dataclass(frozen=True, slots=True)
class InstructionRef:
    """指令引用。

    作用：表达某个来源提出并被识别出的指令事实。
    所属 L0 边界：只保存 instruction_id、kind、authority、source、priority、state 与 conflict_ref。
    不能承担的上层职责：不能保存完整提示词内容，不能拼接模型消息，不能做指令仲裁。
    字段：value 为指令引用 ID；kind 为指令类别；authority 为指令权力等级。
    """
    value: RefId; kind: InstructionKind=InstructionKind.UNKNOWN; authority: InstructionAuthority=InstructionAuthority.UNKNOWN; source: InstructionSource|None=None; priority: InstructionPriority|None=None; state: InstructionState=InstructionState.UNKNOWN; conflict_ref: InstructionConflictRef|None=None; directive_ref: DirectiveRef|None=None; schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("InstructionRef.schema_version cannot be empty")
