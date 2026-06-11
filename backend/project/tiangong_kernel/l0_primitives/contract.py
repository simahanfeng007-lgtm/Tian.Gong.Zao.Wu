"""L0 合约事实语言原语。

本模块在 L0 中的职责：定义运行承诺、合约范围、满足状态、违反、版本和来源的引用事实。
本模块只表达：Actor、Goal、Plan、Effect、Skill、Tool、Adapter、Plugin、Resource 或 Artifact 的承诺边界事实。
本模块明确不做：完整合约内容保存、合约检查、策略执行、运行时强制、规则解析或流程编排。
禁止事项：不得实现合约校验算法，不得触发真实执行，不得绑定法律条款。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .identity import RefId, TypedRef


class ContractKind(str, Enum):
    """合约类别：只表达承诺类型；UNKNOWN 表示类别未知。

    BEHAVIORAL：行为；RESOURCE：资源；SECURITY：安全；PRIVACY：隐私；LIFECYCLE：生命周期；
    PLUGIN：插件；SKILL：技能；EFFECT：副作用；RECOVERY：恢复；UNKNOWN：未知兜底。
    """
    BEHAVIORAL="behavioral"; RESOURCE="resource"; SECURITY="security"; PRIVACY="privacy"; LIFECYCLE="lifecycle"; PLUGIN="plugin"; SKILL="skill"; EFFECT="effect"; RECOVERY="recovery"; UNKNOWN="unknown"

class ContractState(str, Enum):
    """合约状态：只表达承诺生命周期；UNKNOWN 表示状态未知。

    DRAFT：草稿；PROPOSED：提议；ACTIVE：活动；SATISFIED：满足；VIOLATED：违反；DEGRADED：降级；
    SUPERSEDED：被取代；REVOKED：撤销；EXPIRED：过期；ARCHIVED：归档；UNKNOWN：未知兜底。
    """
    DRAFT="draft"; PROPOSED="proposed"; ACTIVE="active"; SATISFIED="satisfied"; VIOLATED="violated"; DEGRADED="degraded"; SUPERSEDED="superseded"; REVOKED="revoked"; EXPIRED="expired"; ARCHIVED="archived"; UNKNOWN="unknown"

class ContractSatisfaction(str, Enum):
    """合约满足度：只表达满足事实；UNKNOWN 表示无法判定。

    SATISFIED：满足；PARTIALLY_SATISFIED：部分满足；UNSATISFIED：不满足；UNKNOWN：未知；NOT_APPLICABLE：不适用。
    """
    SATISFIED="satisfied"; PARTIALLY_SATISFIED="partially_satisfied"; UNSATISFIED="unsatisfied"; UNKNOWN="unknown"; NOT_APPLICABLE="not_applicable"

@dataclass(frozen=True, slots=True)
class ContractScopeRef:
    """合约范围引用。

    作用：表达合约适用的作用域、生命周期或对象边界。
    所属 L0 边界：只保存 contract_scope_id 与 scope_refs。
    不能承担的上层职责：不能判断对象是否落入范围，不能执行策略。
    字段：value 为合约范围引用 ID；scope_refs 为关联范围引用集合。
    """
    value: RefId; scope_refs: tuple[TypedRef,...]=field(default_factory=tuple); schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("ContractScopeRef.schema_version cannot be empty")

@dataclass(frozen=True, slots=True)
class ContractVersionRef:
    """合约版本引用。

    作用：表达合约版本事实引用。
    所属 L0 边界：只保存 version_id 与 previous_ref。
    不能承担的上层职责：不能做版本迁移、兼容判断或内容解析。
    字段：value 为版本引用 ID；previous_ref 为前序版本引用。
    """
    value: RefId; previous_ref: TypedRef|None=None; schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("ContractVersionRef.schema_version cannot be empty")

@dataclass(frozen=True, slots=True)
class ContractOriginRef:
    """合约来源引用。

    作用：表达合约由用户、系统、插件、策略或恢复流程产生的来源事实。
    所属 L0 边界：只保存 origin_id、origin_ref 与 evidence_refs。
    不能承担的上层职责：不能验证来源，不能生成合约内容。
    字段：value 为来源引用 ID；origin_ref 为来源对象引用。
    """
    value: RefId; origin_ref: TypedRef|None=None; evidence_refs: tuple[TypedRef,...]=field(default_factory=tuple); schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("ContractOriginRef.schema_version cannot be empty")

@dataclass(frozen=True, slots=True)
class ContractViolationRef:
    """合约违反引用。

    作用：表达合约被违反或疑似违反的事实引用。
    所属 L0 边界：只保存 violation_id、contract_ref 与 evidence_refs。
    不能承担的上层职责：不能判定违反原因，不能执行制裁或恢复。
    字段：value 为违反引用 ID；contract_ref 为合约引用；evidence_refs 为证据引用集合。
    """
    value: RefId; contract_ref: TypedRef|None=None; evidence_refs: tuple[TypedRef,...]=field(default_factory=tuple); schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("ContractViolationRef.schema_version cannot be empty")

@dataclass(frozen=True, slots=True)
class ContractRef:
    """合约引用。

    作用：表达对象在特定范围和生命周期下必须遵守的运行承诺引用。
    所属 L0 边界：只保存 contract_id、kind、state、satisfaction、scope、version 与 origin。
    不能承担的上层职责：不能保存完整合约内容，不能检查合约，不能强制执行。
    字段：value 为合约引用 ID；kind 为合约类别；state 为合约状态；satisfaction 为满足度。
    """
    value: RefId; kind: ContractKind=ContractKind.UNKNOWN; state: ContractState=ContractState.UNKNOWN; satisfaction: ContractSatisfaction=ContractSatisfaction.UNKNOWN; scope_ref: ContractScopeRef|None=None; version_ref: ContractVersionRef|None=None; origin_ref: ContractOriginRef|None=None; schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("ContractRef.schema_version cannot be empty")
