"""L2 副作用治理链状态对象。

本模块只保存权限治理与副作用安全链路的状态引用，不执行、不裁决、不提交、
不回滚、不写真实状态库。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from .base_state import L2_STATE_SCHEMA_VERSION, L2StateMetadata
from .state_identity import L2StateIdentity
from .state_status import L2StateStatus


def _ensure_true(value: bool, field_name: str) -> None:
    if value is not True:
        raise ValueError(f"{field_name} must remain true")


def _ensure_false(value: bool, field_name: str) -> None:
    if value is not False:
        raise ValueError(f"{field_name} must remain false")


@dataclass(frozen=True, slots=True)
class SideEffectGovernanceChainState:
    """副作用治理链状态，只串联安全链路引用。"""

    identity: L2StateIdentity
    status: L2StateStatus
    chain_ref: TypedRef | None = None
    action_intent_ref: TypedRef | None = None
    risk_decision_ref: TypedRef | None = None
    policy_reference_ref: TypedRef | None = None
    resource_lease_ref: TypedRef | None = None
    secret_reference_ref: TypedRef | None = None
    audit_observation_ref: TypedRef | None = None
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    summary: str = ""
    state_only: bool = True
    no_execution: bool = True
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_true(self.state_only, "SideEffectGovernanceChainState.state_only")
        _ensure_true(self.no_execution, "SideEffectGovernanceChainState.no_execution")
        if not self.schema_version:
            raise ValueError("SideEffectGovernanceChainState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class PolicyBindingState:
    """策略绑定状态，只保存策略引用。"""

    identity: L2StateIdentity
    status: L2StateStatus
    binding_ref: TypedRef | None = None
    policy_reference_ref: TypedRef | None = None
    action_intent_ref: TypedRef | None = None
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    summary: str = ""
    state_only: bool = True
    policy_decision_made: bool = False
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_true(self.state_only, "PolicyBindingState.state_only")
        _ensure_false(self.policy_decision_made, "PolicyBindingState.policy_decision_made")
        if not self.schema_version:
            raise ValueError("PolicyBindingState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ContractBindingState:
    """合同绑定状态，只保存合同引用。"""

    identity: L2StateIdentity
    status: L2StateStatus
    binding_ref: TypedRef | None = None
    contract_ref: TypedRef | None = None
    action_intent_ref: TypedRef | None = None
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    summary: str = ""
    state_only: bool = True
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_true(self.state_only, "ContractBindingState.state_only")
        if not self.schema_version:
            raise ValueError("ContractBindingState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ApprovalState:
    """审批状态，只保存审批引用，不签发确认票据。"""

    identity: L2StateIdentity
    status: L2StateStatus
    approval_ref: TypedRef | None = None
    approval_request_ref: TypedRef | None = None
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    summary: str = ""
    state_only: bool = True
    issues_ticket: bool = False
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_true(self.state_only, "ApprovalState.state_only")
        _ensure_false(self.issues_ticket, "ApprovalState.issues_ticket")
        if not self.schema_version:
            raise ValueError("ApprovalState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class HumanGateState:
    """人工门状态，只保存等待与恢复引用。"""

    identity: L2StateIdentity
    status: L2StateStatus
    human_gate_ref: TypedRef | None = None
    wait_ref: TypedRef | None = None
    resume_ref: TypedRef | None = None
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    summary: str = ""
    state_only: bool = True
    confirms_action: bool = False
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_true(self.state_only, "HumanGateState.state_only")
        _ensure_false(self.confirms_action, "HumanGateState.confirms_action")
        if not self.schema_version:
            raise ValueError("HumanGateState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class TransactionState:
    """事务状态，只保存事务引用，不提交。"""

    identity: L2StateIdentity
    status: L2StateStatus
    transaction_ref: TypedRef | None = None
    action_intent_ref: TypedRef | None = None
    compensation_ref: TypedRef | None = None
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    summary: str = ""
    state_only: bool = True
    commit_performed: bool = False
    rollback_performed: bool = False
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_true(self.state_only, "TransactionState.state_only")
        _ensure_false(self.commit_performed, "TransactionState.commit_performed")
        _ensure_false(self.rollback_performed, "TransactionState.rollback_performed")
        if not self.schema_version:
            raise ValueError("TransactionState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class CompensationState:
    """补偿状态，只保存补偿计划引用，不执行补偿。"""

    identity: L2StateIdentity
    status: L2StateStatus
    compensation_ref: TypedRef | None = None
    transaction_ref: TypedRef | None = None
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    summary: str = ""
    state_only: bool = True
    compensation_performed: bool = False
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_true(self.state_only, "CompensationState.state_only")
        _ensure_false(self.compensation_performed, "CompensationState.compensation_performed")
        if not self.schema_version:
            raise ValueError("CompensationState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class DataGovernanceState:
    """数据治理状态，只保存数据治理引用。"""

    identity: L2StateIdentity
    status: L2StateStatus
    data_governance_ref: TypedRef | None = None
    policy_reference_ref: TypedRef | None = None
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    summary: str = ""
    state_only: bool = True
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_true(self.state_only, "DataGovernanceState.state_only")
        if not self.schema_version:
            raise ValueError("DataGovernanceState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class SecretExposureGuardState:
    """密钥暴露保护状态，只保存保护引用，不解析密钥。"""

    identity: L2StateIdentity
    status: L2StateStatus
    guard_ref: TypedRef | None = None
    secret_reference_ref: TypedRef | None = None
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    summary: str = ""
    state_only: bool = True
    plain_secret_visible: bool = False
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_true(self.state_only, "SecretExposureGuardState.state_only")
        _ensure_false(self.plain_secret_visible, "SecretExposureGuardState.plain_secret_visible")
        if not self.schema_version:
            raise ValueError("SecretExposureGuardState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class PrivacyGuardState:
    """隐私保护状态，只保存隐私边界引用。"""

    identity: L2StateIdentity
    status: L2StateStatus
    guard_ref: TypedRef | None = None
    privacy_boundary_ref: TypedRef | None = None
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    summary: str = ""
    state_only: bool = True
    external_disclosure_authorized: bool = False
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_true(self.state_only, "PrivacyGuardState.state_only")
        _ensure_false(self.external_disclosure_authorized, "PrivacyGuardState.external_disclosure_authorized")
        if not self.schema_version:
            raise ValueError("PrivacyGuardState.schema_version cannot be empty")
