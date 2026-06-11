"""L0 产物引用事实语言原语。

本模块在 L0 中的职责：定义系统生成、接收、修改、引用、交付或归档的实体产物引用事实。
本模块只表达：产物引用、类型、状态、摘要、版本、位置、来源与完整性引用。
本模块明确不做：真实产物处理、打包、构建、存储访问或格式转换。
禁止事项：不得接触真实文件、不得处理二进制内容、不得分发产物。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .identity import RefId, TypedRef

class ArtifactKind(str, Enum):
    """产物类别：表达产物的事实类型；UNKNOWN 表示类别未知或暂不可归类。

    TEXT：文本；CODE：代码；PATCH：补丁；BINARY：二进制；DOCUMENT：文档；IMAGE：图像；AUDIO：音频；VIDEO：视频；ARCHIVE：归档包；LOG：日志；CHECKPOINT：检查点；REPORT：报告；MODEL_OUTPUT：模型输出；CONFIG：配置；PLUGIN_PACKAGE：插件包；SKILL_PACKAGE：技能包；DATASET：数据集；UNKNOWN：未知兜底。
    """
    TEXT="text"; CODE="code"; PATCH="patch"; BINARY="binary"; DOCUMENT="document"; IMAGE="image"; AUDIO="audio"; VIDEO="video"; ARCHIVE="archive"; LOG="log"; CHECKPOINT="checkpoint"; REPORT="report"; MODEL_OUTPUT="model_output"; CONFIG="config"; PLUGIN_PACKAGE="plugin_package"; SKILL_PACKAGE="skill_package"; DATASET="dataset"; UNKNOWN="unknown"

class ArtifactState(str, Enum):
    """产物状态：表达产物生命周期事实；UNKNOWN 表示状态未知。"""
    OBSERVED="observed"; CREATED="created"; MODIFIED="modified"; VALIDATED="validated"; SIGNED="signed"; DELIVERED="delivered"; ARCHIVED="archived"; QUARANTINED="quarantined"; DEPRECATED="deprecated"; DELETED="deleted"; UNKNOWN="unknown"

@dataclass(frozen=True, slots=True)
class ArtifactDigest:
    """产物摘要。

    作用：表达产物摘要引用或摘要值对象。
    所属 L0 边界：只保存 algorithm 与 digest 文本，不计算摘要。
    不能承担的上层职责：不能读取产物内容，不能校验真实文件。
    字段：algorithm 为摘要算法名；digest 为摘要文本。
    """
    algorithm: str = "sha256"; digest: str = ""; schema_version: str = "0.1"
    def __post_init__(self)->None:
        if not self.algorithm: raise ValueError("ArtifactDigest.algorithm cannot be empty")
        if not self.schema_version: raise ValueError("ArtifactDigest.schema_version cannot be empty")

@dataclass(frozen=True, slots=True)
class ArtifactRef:
    """产物引用。

    作用：表达系统生成、接收、修改、保存、引用、交付或归档的实体产物引用。
    所属 L0 边界：只保存 artifact_id、kind、state 与关联引用。
    不能承担的上层职责：不能生成、读取、打包、转换或分发真实产物。
    字段：value 为 artifact_id；kind 为产物类别；state 为产物状态。
    """
    value: RefId; kind: ArtifactKind=ArtifactKind.UNKNOWN; state: ArtifactState=ArtifactState.UNKNOWN; digest: ArtifactDigest|None=None; evidence_refs: tuple[TypedRef,...]=field(default_factory=tuple); schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("ArtifactRef.schema_version cannot be empty")

@dataclass(frozen=True, slots=True)
class ArtifactVersionRef:
    """产物版本引用。作用：表达产物版本引用事实；所属 L0 边界：只保存 version_id 与 artifact_ref；不能管理版本库。字段：value 为版本引用 ID。"""
    value: RefId; artifact_ref: ArtifactRef|None=None; version_label: str=""; schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("ArtifactVersionRef.schema_version cannot be empty")

@dataclass(frozen=True, slots=True)
class ArtifactLocationRef:
    """产物位置引用。作用：表达产物位置引用事实；所属 L0 边界：只保存 location_id 与 artifact_ref；不能访问存储。字段：value 为位置引用 ID。"""
    value: RefId; artifact_ref: ArtifactRef|None=None; location_ref: TypedRef|None=None; schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("ArtifactLocationRef.schema_version cannot be empty")

@dataclass(frozen=True, slots=True)
class ArtifactProvenanceRef:
    """产物来源引用。作用：表达产物流转来源引用；所属 L0 边界：只保存 provenance_id 与 artifact_ref；不能追取外部来源。字段：value 为来源引用 ID。"""
    value: RefId; artifact_ref: ArtifactRef|None=None; provenance_ref: TypedRef|None=None; schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("ArtifactProvenanceRef.schema_version cannot be empty")

@dataclass(frozen=True, slots=True)
class ArtifactIntegrityRef:
    """产物完整性引用。作用：表达产物完整性引用事实；所属 L0 边界：只保存 integrity_id、artifact_ref 与 digest；不能验证真实完整性。字段：value 为完整性引用 ID。"""
    value: RefId; artifact_ref: ArtifactRef|None=None; digest: ArtifactDigest|None=None; schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("ArtifactIntegrityRef.schema_version cannot be empty")
