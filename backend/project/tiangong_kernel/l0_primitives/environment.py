"""L0 执行环境、沙箱和隔离边界事实语言原语。

本模块在 L0 中的职责：定义环境、沙箱、隔离边界、环境指纹和环境能力的引用事实。
本模块只表达：执行环境处所、隔离类别、隔离等级、环境状态和可验证摘要。
本模块明确不做：真实沙箱、容器、虚拟机、浏览器自动化、网络策略或进程控制。
禁止事项：不得启动环境，不得挂载文件系统，不得控制进程或浏览器。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .identity import RefId, TypedRef


class EnvironmentKind(str, Enum):
    """环境类别：只表达执行环境类型；UNKNOWN 表示类别未知。"""
    HOST="host"; LOCAL_PROCESS="local_process"; CONTAINER="container"; MICRO_VM="micro_vm"; REMOTE_SANDBOX="remote_sandbox"; BROWSER="browser"; MOBILE="mobile"; DESKTOP="desktop"; CODE_INTERPRETER="code_interpreter"; PLUGIN_RUNTIME="plugin_runtime"; MODEL_RUNTIME="model_runtime"; UNKNOWN="unknown"
class SandboxKind(str, Enum):
    """沙箱类别：只表达隔离环境类型；UNKNOWN 表示类别未知。"""
    NONE="none"; PROCESS_SANDBOX="process_sandbox"; CONTAINER_SANDBOX="container_sandbox"; VM_SANDBOX="vm_sandbox"; BROWSER_SANDBOX="browser_sandbox"; NETWORK_SANDBOX="network_sandbox"; FILESYSTEM_SANDBOX="filesystem_sandbox"; HYBRID_SANDBOX="hybrid_sandbox"; UNKNOWN="unknown"
class IsolationLevel(str, Enum):
    """隔离等级：只表达隔离强度；UNKNOWN 表示等级未知。"""
    NONE="none"; LOW="low"; MEDIUM="medium"; HIGH="high"; STRICT="strict"; VERIFIED="verified"; UNKNOWN="unknown"
class EnvironmentState(str, Enum):
    """环境状态：只表达环境生命周期状态；UNKNOWN 表示状态未知。"""
    CREATED="created"; INITIALIZING="initializing"; READY="ready"; ACTIVE="active"; DEGRADED="degraded"; QUARANTINED="quarantined"; SUSPENDED="suspended"; TERMINATING="terminating"; TERMINATED="terminated"; UNKNOWN="unknown"
@dataclass(frozen=True, slots=True)
class EnvironmentRef:
    """环境引用。作用：表达 Actor、Effect、ToolRef、AdapterRef、Run 或 Transaction 所处执行环境；所属 L0 边界：只保存 environment_id、kind、state；不能启动或控制环境。"""
    value: RefId; kind: EnvironmentKind=EnvironmentKind.UNKNOWN; state: EnvironmentState=EnvironmentState.UNKNOWN; scope_ref: TypedRef|None=None; schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("EnvironmentRef.schema_version cannot be empty")
@dataclass(frozen=True, slots=True)
class SandboxRef:
    """沙箱引用。作用：表达受隔离、受限制、可控制的执行环境引用；所属 L0 边界：只保存 sandbox_id、kind、environment_ref；不能创建沙箱。"""
    value: RefId; kind: SandboxKind=SandboxKind.UNKNOWN; environment_ref: EnvironmentRef|None=None; schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("SandboxRef.schema_version cannot be empty")
@dataclass(frozen=True, slots=True)
class IsolationBoundaryRef:
    """隔离边界引用。作用：表达环境与宿主、网络、文件系统、凭证、外部资源之间的隔离边界；所属 L0 边界：只保存 boundary_id 与 level；不能配置隔离策略。"""
    value: RefId; level: IsolationLevel=IsolationLevel.UNKNOWN; environment_ref: EnvironmentRef|None=None; schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("IsolationBoundaryRef.schema_version cannot be empty")
@dataclass(frozen=True, slots=True)
class EnvironmentFingerprint:
    """环境指纹。作用：表达执行环境的可验证摘要；所属 L0 边界：只保存 digest 和 algorithm；不能验证签名或扫描环境。"""
    digest: str; algorithm: str="sha256"; schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.digest: raise ValueError("EnvironmentFingerprint.digest cannot be empty")
        if not self.schema_version: raise ValueError("EnvironmentFingerprint.schema_version cannot be empty")
@dataclass(frozen=True, slots=True)
class EnvironmentCapabilityRef:
    """环境能力引用。作用：表达环境具备或暴露的能力引用；所属 L0 边界：只保存 capability_id 与 environment_ref；不能调用能力。"""
    value: RefId; environment_ref: EnvironmentRef|None=None; capability_ref: TypedRef|None=None; schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("EnvironmentCapabilityRef.schema_version cannot be empty")
