"""L0 政策、规范与治理域事实语言原语。

本模块在 L0 中的职责：定义可被引用的治理政策、规范事实、治理域、政策冲突和执行模式引用。
本模块只表达：安全、隐私、资源、生命周期、工具使用、人类审批等治理事实的引用语言。
本模块明确不做：规则引擎、合规判断、治理流程执行、实际通过或拒绝算法。
禁止事项：不得解析策略文本，不得执行规则，不得输出最终授权裁决。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .identity import RefId, TypedRef


class PolicyKind(str, Enum):
    """政策类别：只表达治理政策类型；UNKNOWN 表示类别未知。

    SAFETY：安全；SECURITY：安保；PRIVACY：隐私；RESOURCE：资源；LIFECYCLE：生命周期；TOOL_USE：工具使用；
    DATA_GOVERNANCE：数据治理；HUMAN_APPROVAL：人工审批；PLUGIN_GOVERNANCE：插件治理；RECOVERY：恢复；UNKNOWN：未知兜底。
    """
    SAFETY="safety"; SECURITY="security"; PRIVACY="privacy"; RESOURCE="resource"; LIFECYCLE="lifecycle"; TOOL_USE="tool_use"; DATA_GOVERNANCE="data_governance"; HUMAN_APPROVAL="human_approval"; PLUGIN_GOVERNANCE="plugin_governance"; RECOVERY="recovery"; UNKNOWN="unknown"

class NormKind(str, Enum):
    """规范类别：只表达规范性事实类型；UNKNOWN 表示类别未知。

    OBLIGATION：义务；PERMISSION：许可；PROHIBITION：禁止；RECOMMENDATION：建议；EXCEPTION：例外；UNKNOWN：未知兜底。
    """
    OBLIGATION="obligation"; PERMISSION="permission"; PROHIBITION="prohibition"; RECOMMENDATION="recommendation"; EXCEPTION="exception"; UNKNOWN="unknown"

class PolicyState(str, Enum):
    """政策状态：只表达政策生命周期；UNKNOWN 表示状态未知。

    DRAFT：草稿；ACTIVE：活动；SUSPENDED：暂停；SUPERSEDED：被取代；DEPRECATED：弃用；REVOKED：撤销；ARCHIVED：归档；UNKNOWN：未知兜底。
    """
    DRAFT="draft"; ACTIVE="active"; SUSPENDED="suspended"; SUPERSEDED="superseded"; DEPRECATED="deprecated"; REVOKED="revoked"; ARCHIVED="archived"; UNKNOWN="unknown"

class GovernanceDomain(str, Enum):
    """治理域：只表达治理归属区域；UNKNOWN 表示治理域未知。

    CORE：核心；RUNTIME：运行；MEMORY：记忆；FORGETTING：遗忘；EFFECT：副作用；RESOURCE：资源；
    PRIVACY：隐私；TRUST：信任；PLUGIN：插件；ARTIFACT：产物；UNKNOWN：未知兜底。
    """
    CORE="core"; RUNTIME="runtime"; MEMORY="memory"; FORGETTING="forgetting"; EFFECT="effect"; RESOURCE="resource"; PRIVACY="privacy"; TRUST="trust"; PLUGIN="plugin"; ARTIFACT="artifact"; UNKNOWN="unknown"

@dataclass(frozen=True, slots=True)
class NormRef:
    """规范引用。

    作用：表达义务、许可、禁止、建议或例外等规范性事实。
    所属 L0 边界：只保存 norm_id、kind 与 source_ref。
    不能承担的上层职责：不能执行规范，不能裁决冲突，不能绑定法律条款。
    字段：value 为规范引用 ID；kind 为规范类别；source_ref 为来源引用。
    """
    value: RefId; kind: NormKind=NormKind.UNKNOWN; source_ref: TypedRef|None=None; schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("NormRef.schema_version cannot be empty")

@dataclass(frozen=True, slots=True)
class GovernanceRef:
    """治理域引用。

    作用：表达某个政策、合约、裁决、风险、插件或执行路径所属治理域。
    所属 L0 边界：只保存 governance_id、domain 与 target_ref。
    不能承担的上层职责：不能执行治理流程，不能生成治理策略。
    字段：value 为治理引用 ID；domain 为治理域；target_ref 为目标对象引用。
    """
    value: RefId; domain: GovernanceDomain=GovernanceDomain.UNKNOWN; target_ref: TypedRef|None=None; schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("GovernanceRef.schema_version cannot be empty")

@dataclass(frozen=True, slots=True)
class PolicyConflictRef:
    """政策冲突引用。

    作用：表达多条政策或规范之间存在冲突的引用事实。
    所属 L0 边界：只保存 conflict_id 与 conflict_refs。
    不能承担的上层职责：不能仲裁冲突，不能排序优先级，不能修改政策。
    字段：value 为冲突引用 ID；conflict_refs 为冲突对象引用集合。
    """
    value: RefId; conflict_refs: tuple[TypedRef,...]=field(default_factory=tuple); schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("PolicyConflictRef.schema_version cannot be empty")

@dataclass(frozen=True, slots=True)
class EnforcementModeRef:
    """执行模式引用。

    作用：表达政策被如何约束或引用的模式事实。
    所属 L0 边界：只保存 enforcement_mode_id 与 policy_ref。
    不能承担的上层职责：不能实际执行政策，不能做通过或拒绝裁决。
    字段：value 为执行模式引用 ID；policy_ref 为政策引用。
    """
    value: RefId; policy_ref: TypedRef|None=None; schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("EnforcementModeRef.schema_version cannot be empty")

@dataclass(frozen=True, slots=True)
class PolicyRef:
    """政策引用。

    作用：表达可被运行时或治理层引用的政策事实。
    所属 L0 边界：只保存 policy_id、kind、state、norm_refs、governance_ref 与 conflict_ref。
    不能承担的上层职责：不能解析策略、不能执行规则、不能产出最终通过或拒绝结论。
    字段：value 为治理政策引用 ID；kind 为政策类别；state 为政策状态。
    """
    value: RefId; kind: PolicyKind=PolicyKind.UNKNOWN; state: PolicyState=PolicyState.UNKNOWN; norm_refs: tuple[NormRef,...]=field(default_factory=tuple); governance_ref: GovernanceRef|None=None; conflict_ref: PolicyConflictRef|None=None; enforcement_mode_ref: EnforcementModeRef|None=None; schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("PolicyRef.schema_version cannot be empty")
