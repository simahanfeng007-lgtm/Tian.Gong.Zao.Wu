"""L0 证据引用事实语言原语。

本模块在 L0 中的职责：定义支撑事实、判断、裁决、恢复、验证或审计的证据引用。
本模块只表达：证据引用、证据类别、摘要、状态与来源引用。
本模块明确不做：证据采集、证据验证、内容解析、日志扫描或外部取证。
禁止事项：不得读取真实材料，不得验证真实证据，不得连接外部系统。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .identity import RefId, TypedRef

class EvidenceKind(str, Enum):
    """证据类别：表达证据来源类型；UNKNOWN 表示来源未知。"""
    EVENT_EVIDENCE="event_evidence"; OBSERVATION_EVIDENCE="observation_evidence"; ARTIFACT_EVIDENCE="artifact_evidence"; METRIC_EVIDENCE="metric_evidence"; SIGNAL_EVIDENCE="signal_evidence"; HUMAN_EVIDENCE="human_evidence"; TOOL_OUTPUT_EVIDENCE="tool_output_evidence"; TEST_RESULT_EVIDENCE="test_result_evidence"; AUDIT_EVIDENCE="audit_evidence"; UNKNOWN="unknown"

class EvidenceState(str, Enum):
    """证据状态：表达证据治理阶段；UNKNOWN 表示状态未知。"""
    PROPOSED="proposed"; COLLECTED="collected"; VERIFIED="verified"; QUESTIONED="questioned"; REJECTED="rejected"; EXPIRED="expired"; REDACTED="redacted"; ARCHIVED="archived"; UNKNOWN="unknown"

@dataclass(frozen=True, slots=True)
class EvidenceDigest:
    """证据摘要。

    作用：表达证据摘要引用或摘要值对象。
    所属 L0 边界：只保存 algorithm 与 digest，不读取或校验证据内容。
    不能承担的上层职责：不能采集证据，不能判断证据真伪。
    字段：algorithm 为摘要算法名；digest 为摘要文本。
    """
    algorithm: str="sha256"; digest: str=""; schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.algorithm: raise ValueError("EvidenceDigest.algorithm cannot be empty")
        if not self.schema_version: raise ValueError("EvidenceDigest.schema_version cannot be empty")

@dataclass(frozen=True, slots=True)
class EvidenceSourceRef:
    """证据来源引用。作用：表达证据来源引用事实；所属 L0 边界：只保存 source_id 与 origin_ref；不能访问来源。字段：value 为来源引用 ID。"""
    value: RefId; origin_ref: TypedRef|None=None; schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("EvidenceSourceRef.schema_version cannot be empty")

@dataclass(frozen=True, slots=True)
class EvidenceRef:
    """证据引用。

    作用：表达用于支撑事实、判断、裁决、恢复、验证或审计的证据引用。
    所属 L0 边界：只保存 evidence_id、kind、state、digest 与 source_ref。
    不能承担的上层职责：不能保存大内容体，不能执行证据验证或外部取证。
    字段：value 为 evidence_id；kind 为证据类别；state 为证据状态。
    """
    value: RefId; kind: EvidenceKind=EvidenceKind.UNKNOWN; state: EvidenceState=EvidenceState.UNKNOWN; digest: EvidenceDigest|None=None; source_ref: EvidenceSourceRef|None=None; schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("EvidenceRef.schema_version cannot be empty")
