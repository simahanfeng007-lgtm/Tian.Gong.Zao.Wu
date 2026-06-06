"""L2 外部适配器与沙箱状态对象。"""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from .base_state import L2_STATE_SCHEMA_VERSION, L2StateMetadata
from .state_identity import L2StateIdentity
from .state_status import L2StateStatus


@dataclass(frozen=True, slots=True)
class ExternalActionState:
    """外部动作状态，绑定适配器、沙箱、凭证、预算和审计引用。"""

    identity: L2StateIdentity
    status: L2StateStatus
    action_ref: TypedRef | None = None
    surface: str = "unknown"
    adapter_state_ref: TypedRef | None = None
    sandbox_state_ref: TypedRef | None = None
    credential_binding_state_ref: TypedRef | None = None
    resource_budget_state_ref: TypedRef | None = None
    effect_result_state_ref: TypedRef | None = None
    audit_evidence_state_ref: TypedRef | None = None
    recovery_state_ref: TypedRef | None = None
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION


@dataclass(frozen=True, slots=True)
class AdapterState:
    """适配器状态，只记录适配表面和模式提示。"""

    identity: L2StateIdentity
    status: L2StateStatus
    adapter_ref: TypedRef | None = None
    surface: str = "unknown"
    mode_hint: str = "disabled"
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION


@dataclass(frozen=True, slots=True)
class SandboxPolicyState:
    """沙箱策略状态，记录挂载、工作目录、网络、环境和资源策略引用。"""

    identity: L2StateIdentity
    status: L2StateStatus
    policy_ref: TypedRef | None = None
    mount_policy_ref: TypedRef | None = None
    workdir_policy_ref: TypedRef | None = None
    network_policy_ref: TypedRef | None = None
    env_policy_ref: TypedRef | None = None
    process_policy_ref: TypedRef | None = None
    resource_limit_ref: TypedRef | None = None
    credential_policy_ref: TypedRef | None = None
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION


SandboxContextState = SandboxPolicyState
CredentialBindingState = ExternalActionState
ResourceBudgetConsumptionState = ExternalActionState
EffectResultState = ExternalActionState
AuditEvidenceState = ExternalActionState
RecoveryState = ExternalActionState
