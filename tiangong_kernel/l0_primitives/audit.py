"""L0 审计、追责与完整性链事实语言原语。

本模块在 L0 中的职责：定义审计轨迹、责任、可追责关系、防篡改依据、完整性链与审计发现引用。
本模块只表达：审计相关引用事实和覆盖范围事实。
本模块明确不做：审计系统实现、报告产出、合规判断、外部取证或材料落地。
禁止事项：不得写入审计材料，不得连接外部审计系统，不得执行密码学流程。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .identity import RefId, TypedRef

class ResponsibilityKind(str, Enum):
    """责任类别：表达事实链中的责任角色；UNKNOWN 表示责任角色未知。"""
    ORIGINATOR="originator"; APPROVER="approver"; EXECUTOR="executor"; DELEGATOR="delegator"; ADAPTER="adapter"; POLICY="policy"; RECOVERY="recovery"; OBSERVER="observer"; UNKNOWN="unknown"
class AuditCoverageKind(str, Enum):
    """审计覆盖类别：表达被审计覆盖的生命周期片段；UNKNOWN 表示覆盖未知。"""
    INPUT="input"; CONTEXT="context"; DECISION="decision"; POLICY_CHECK="policy_check"; EFFECT_REQUEST="effect_request"; EFFECT_EXECUTION="effect_execution"; RESULT="result"; RECOVERY="recovery"; ARTIFACT="artifact"; LIFECYCLE="lifecycle"; UNKNOWN="unknown"
class AuditFindingKind(str, Enum):
    """审计发现类别：表达审计缺口或风险类型；UNKNOWN 表示发现类型未知。"""
    MISSING_EVIDENCE="missing_evidence"; BROKEN_CHAIN="broken_chain"; POLICY_GAP="policy_gap"; UNATTRIBUTED_ACTION="unattributed_action"; INCOMPLETE_LIFECYCLE="incomplete_lifecycle"; TAMPER_RISK="tamper_risk"; RECOVERY_GAP="recovery_gap"; UNKNOWN="unknown"

@dataclass(frozen=True, slots=True)
class AuditRef:
    """审计引用。作用：表达一次审计事实的总引用；所属 L0 边界：只保存 audit_id 与 scope_ref；不能生成审计报告。字段：value 为 audit_id。"""
    value: RefId; scope_ref: TypedRef|None=None; schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("AuditRef.schema_version cannot be empty")
@dataclass(frozen=True, slots=True)
class AuditTrailRef:
    """审计轨迹引用。作用：表达事件、决策、副作用、证据、来源与责任链构成的审计轨迹引用；所属 L0 边界：只保存 trail_id 与关联引用；不能持久化轨迹。字段：value 为 audit_trail_id。"""
    value: RefId; audit_ref: AuditRef|None=None; related_refs: tuple[TypedRef,...]=field(default_factory=tuple); schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("AuditTrailRef.schema_version cannot be empty")
@dataclass(frozen=True, slots=True)
class AuditEventRef:
    """审计事件引用。作用：表达被纳入审计的事件引用；所属 L0 边界：只保存 audit_event_id 与 event_ref；不能扫描事件流。字段：value 为审计事件引用 ID。"""
    value: RefId; event_ref: TypedRef|None=None; trail_ref: AuditTrailRef|None=None; schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("AuditEventRef.schema_version cannot be empty")
@dataclass(frozen=True, slots=True)
class ResponsibilityRef:
    """责任引用。作用：表达主体对事实、动作或结果的责任角色；所属 L0 边界：只保存 responsibility_id、kind 与 actor_ref；不能裁定责任。字段：kind 为责任类别。"""
    value: RefId; kind: ResponsibilityKind=ResponsibilityKind.UNKNOWN; actor_ref: TypedRef|None=None; target_ref: TypedRef|None=None; schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("ResponsibilityRef.schema_version cannot be empty")
@dataclass(frozen=True, slots=True)
class AccountabilityRef:
    """可追责关系引用。作用：表达 Actor、系统、插件、工具、策略或外部主体对某事实、动作或结果的可追责关系引用；所属 L0 边界：只保存 accountability_id 与 responsibility_ref；不能执行追责流程。字段：value 为追责引用 ID。"""
    value: RefId; responsibility_ref: ResponsibilityRef|None=None; evidence_refs: tuple[TypedRef,...]=field(default_factory=tuple); schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("AccountabilityRef.schema_version cannot be empty")
@dataclass(frozen=True, slots=True)
class TamperEvidenceRef:
    """防篡改依据引用。作用：表达审计材料具备防篡改或可验证完整性的事实引用；所属 L0 边界：只保存 tamper_evidence_id 与 digest_ref；不能执行签名或加密。字段：value 为防篡改依据引用 ID。"""
    value: RefId; digest_ref: TypedRef|None=None; evidence_refs: tuple[TypedRef,...]=field(default_factory=tuple); schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("TamperEvidenceRef.schema_version cannot be empty")
@dataclass(frozen=True, slots=True)
class IntegrityChainRef:
    """完整性链引用。作用：表达事件、证据、产物、检查点之间的摘要链引用；所属 L0 边界：只保存 integrity_chain_id 与 node_refs；不能落地真实链。字段：node_refs 为链节点引用集合。"""
    value: RefId; node_refs: tuple[TypedRef,...]=field(default_factory=tuple); schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("IntegrityChainRef.schema_version cannot be empty")
@dataclass(frozen=True, slots=True)
class AuditCoverageRef:
    """审计覆盖引用。作用：表达审计是否覆盖输入、决策、执行、结果、恢复、归档等阶段；所属 L0 边界：只保存 coverage_id 与 kind；不能评估合规性。字段：kind 为覆盖类别。"""
    value: RefId; kind: AuditCoverageKind=AuditCoverageKind.UNKNOWN; target_ref: TypedRef|None=None; schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("AuditCoverageRef.schema_version cannot be empty")
@dataclass(frozen=True, slots=True)
class AuditFindingRef:
    """审计发现引用。作用：表达审计发现的问题、缺口或风险事实引用；所属 L0 边界：只保存 finding_id、kind 与 evidence_refs；不能生成处置建议。字段：kind 为审计发现类别。"""
    value: RefId; kind: AuditFindingKind=AuditFindingKind.UNKNOWN; evidence_refs: tuple[TypedRef,...]=field(default_factory=tuple); schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("AuditFindingRef.schema_version cannot be empty")
