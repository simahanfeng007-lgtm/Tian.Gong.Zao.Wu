"""L2 插件宿主状态占位对象。"""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from .base_state import L2_STATE_SCHEMA_VERSION, L2StateMetadata
from .state_identity import L2StateIdentity
from .state_status import L2StateStatus


@dataclass(frozen=True, slots=True)
class L2PluginStateBase:
    """插件状态基类，只保存引用和证据，不加载插件或写注册表。"""

    identity: L2StateIdentity
    status: L2StateStatus
    plugin_ref: TypedRef | None = None
    manifest_ref: TypedRef | None = None
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    metadata: L2StateMetadata | None = None
    state_only: bool = True
    loads_plugin: bool = False
    writes_registry: bool = False
    schema_version: str = L2_STATE_SCHEMA_VERSION


L2PluginManifestState = L2PluginStateBase
L2PluginRegistrationState = L2PluginStateBase
L2PluginLifecycleState = L2PluginStateBase
L2PluginIsolationState = L2PluginStateBase
L2PluginMountState = L2PluginStateBase
L2PluginDependencyState = L2PluginStateBase
L2PluginHealthState = L2PluginStateBase
L2PluginQuarantineState = L2PluginStateBase
L2PluginRollbackState = L2PluginStateBase
L2PluginAuditBindingState = L2PluginStateBase
