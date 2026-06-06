"""L0 Skill 与能力引用事实语言原语。

本模块在 L0 中的职责：定义可复用程序性能力、认知能力或安全恢复能力的引用事实。
本模块只表达：Skill 引用、能力引用、能力类别、状态、来源、风险和版本引用。
本模块明确不做：能力选择、组合、执行、库管理、工具绑定、安全扫描或市场分发。
禁止事项：不得执行 Skill，不得选择能力，不得生成能力，不得绑定工具。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .identity import RefId, TypedRef


class CapabilityKind(str, Enum):
    """能力类别：只表达能力用途类型；UNKNOWN 表示类别未知。"""
    PROCEDURAL="procedural"; COGNITIVE="cognitive"; OPERATIONAL="operational"; RECOVERY="recovery"; SAFETY="safety"; LEARNING="learning"; COMMUNICATION="communication"; UNKNOWN="unknown"
class CapabilityState(str, Enum):
    """能力状态：只表达能力引用生命周期；UNKNOWN 表示状态未知。"""
    DISCOVERED="discovered"; REGISTERED="registered"; AVAILABLE="available"; REQUESTED="requested"; AUTHORIZED="authorized"; ACTIVE="active"; DEPRECATED="deprecated"; QUARANTINED="quarantined"; REVOKED="revoked"; ARCHIVED="archived"; UNKNOWN="unknown"
@dataclass(frozen=True, slots=True)
class SkillRef:
    """Skill 引用。作用：表达可复用做事方法引用；所属 L0 边界：只保存 skill_id、origin_ref 与 version_ref；不能保存完整 Skill 内容或执行流程。"""
    value: RefId; origin_ref: TypedRef|None=None; version_ref: TypedRef|None=None; schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("SkillRef.schema_version cannot be empty")
@dataclass(frozen=True, slots=True)
class CapabilityOriginRef:
    """能力来源引用。作用：表达能力来源事实；所属 L0 边界：只保存 capability_origin_id 与 evidence_refs；不能发现或生成能力。"""
    value: RefId; evidence_refs: tuple[TypedRef,...]=field(default_factory=tuple); schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("CapabilityOriginRef.schema_version cannot be empty")
@dataclass(frozen=True, slots=True)
class CapabilityRiskRef:
    """能力风险引用。作用：表达能力风险事实引用；所属 L0 边界：只保存 capability_risk_id 与 risk_ref；不能评分或裁决风险。"""
    value: RefId; risk_ref: TypedRef|None=None; schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("CapabilityRiskRef.schema_version cannot be empty")
@dataclass(frozen=True, slots=True)
class CapabilityVersionRef:
    """能力版本引用。作用：表达能力版本引用；所属 L0 边界：只保存 capability_version_id 与 capability_ref；不能升级能力。"""
    value: RefId; capability_ref: TypedRef|None=None; schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("CapabilityVersionRef.schema_version cannot be empty")
@dataclass(frozen=True, slots=True)
class CapabilityRef:
    """能力引用。作用：表达可复用的程序性能力或做事方法引用；所属 L0 边界：只保存 capability_id、kind、state、skill_ref、origin_ref、risk_ref 和 version_ref；不能执行、组合或选择能力。"""
    value: RefId; kind: CapabilityKind=CapabilityKind.UNKNOWN; state: CapabilityState=CapabilityState.UNKNOWN; skill_ref: SkillRef|None=None; origin_ref: CapabilityOriginRef|None=None; risk_ref: CapabilityRiskRef|None=None; version_ref: CapabilityVersionRef|None=None; schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("CapabilityRef.schema_version cannot be empty")
