"""L4 动作落地层第一阶段公共导出。

本包是 LLM action grounding 的承载层：接收 L3 表达的动作请求，缺少未来 L5
许可引用时默认拒绝，并用 fake/dry-run/no-op 返回模拟或拒绝 envelope。
本包不是执行智能体，不选择 Skill，不调用模型或工具，不执行文件、网络、终端或桌面动作。
"""

from .context import ActionGroundingContext
from .adapter_capability import AdapterCapabilityDescriptor
from .adapter_descriptor import AdapterDescriptor, AdapterIdentity
from .adapter_disabled import AdapterDisabledReason, AdapterDisabledReasonKind
from .adapter_dry_run import DryRunActionAdapter, DryRunAdapter
from .adapter_envelope import AdapterExecutionEnvelope, AdapterFailureEnvelope, AdapterInputEnvelope, AdapterObservationHint, AdapterOutputEnvelope
from .adapter_failure import (
    AdapterCapabilityMismatchFailure,
    AdapterDisabledByDefaultFailure,
    AdapterDuplicateIdFailure,
    AdapterFailure,
    AdapterFailureKind,
    AdapterInvariantViolationFailure,
    AdapterMalformedDescriptorFailure,
    AdapterModeMismatchFailure,
    AdapterNotFoundFailure,
    AdapterPermitRequiredFailure,
    AdapterProductionDisabledFailure,
    AdapterScopeMismatchFailure,
    AdapterSelectionFailure,
    AdapterTestOnlyModeFailure,
)
from .adapter_fake import FakeActionAdapter, FakeAdapter
from .adapter_in_memory import InMemoryActionAdapter, InMemoryAdapter
from .adapter_invariant import (
    AdapterCannotBypassL3Invariant,
    AdapterCannotBypassL5Invariant,
    AdapterCannotHoldPlainCredentialInvariant,
    AdapterCannotImplementL6SubsystemInvariant,
    FakeAdapterNeverProductionInvariant,
    NoRealAdapterActivationWithoutL5Invariant,
)
from .adapter_mode import AdapterExecutionMode, AdapterMode, AdapterModePolicy, ExecutionAdapterMode
from .adapter_no_op import NoOpActionAdapter, NoOpAdapter
from .adapter_normalization import AdapterFailureNormalizer, AdapterResultNormalizer
from .adapter_projection import AdapterProjection, AdapterRegistryProjection
from .adapter_protocol import ActionAdapterProtocol, ExecutionAdapterProtocol
from .adapter_real_stub import RealActionAdapterStub, RealAdapterStub
from .adapter_registry import AdapterRegistry, AdapterRegistryEntry, AdapterRegistryRegistrationResult, AdapterRegistrySnapshot
from .adapter_risk_surface import AdapterRiskSurfaceDescriptor
from .adapter_selection import AdapterSelectionRequest, AdapterSelectionResult
from .adapter_selector import AdapterSelector
from .adapter_status import AdapterStatus, AdapterStatusKind
from .action_failure_return_envelope import ActionFailureReturnEnvelope
from .audit_requirement import AuditRequirementRef
from .action_outcome_envelope import ActionOutcomeEnvelope
from .action_result_return_envelope import ActionResultReturnEnvelope
from .boundary_feedback_ref import BoundaryFeedbackRef
from .boundary_failure import BoundaryDeniedFailure, BoundaryExpiredFailure, BoundaryMissingFailure, BoundaryScopeMismatchFailure
from .boundary_ref import (
    BoundaryDecisionRef,
    BoundaryDecisionStatus,
    ConfirmationTicketRef,
    LeaseRef,
    PermissionGrantRef,
    PolicyDecisionRef,
    RiskReviewRef,
)
from .credential_ref import CredentialHandleRef
from .cancellation_timeout_fake import FakeCancellationTimeoutHelper
from .disabled import ExecutionDisabledByDefaultFailure
from .desktop_action_failure import DesktopActionFailure, DesktopActionFailureKind
from .desktop_action_port import DesktopActionAdapterPort
from .desktop_action_request import DesktopActionRequest
from .desktop_action_result import DesktopActionResult
from .desktop_dry_run_adapter import DryRunDesktopAdapter
from .desktop_fake_adapter import FakeDesktopAdapter
from .dry_run import DryRunActionGroundingRunner, NoOpActionGroundingRunner
from .error import ActionGroundingError, ActionGroundingErrorKind
from .execution_audit_ref import ExecutionAuditRef
from .execution_cancellation import ExecutionCancellationRequest, ExecutionCancellationResult, ExecutionCancellationStatus
from .execution_evidence_ref import ExecutionEvidenceRef
from .execution_observation_ref import ExecutionObservationRef
from .execution_resource_usage import ExecutionResourceUsage
from .execution_resume_ref import ExecutionResumeRef
from .execution_retry_advice import ExecutionRetryAdviceRef
from .execution_return_projection import ExecutionReturnProjection
from .execution_rollback_hint import ExecutionRollbackHintRef
from .execution_timeout import ExecutionTimeoutFailure, ExecutionTimeoutPolicyRef
from .execution_trace_ref import ExecutionTraceRef
from .external_action_disabled import ExternalActionDisabledByDefault
from .external_action_envelope import DesktopActionEnvelope, ExternalActionEnvelope, FileActionEnvelope, NetworkActionEnvelope, TerminalActionEnvelope
from .external_action_invariant import (
    A5LikeHardSafetyInvariant,
    ExternalActionHardSafetyInvariant,
    ExternalActionRequiresL5PermitInvariant,
    NoRealDesktopControlInvariant,
    NoRealFileSystemMutationInvariant,
    NoRealNetworkAccessInvariant,
    NoRealShellExecutionInvariant,
)
from .external_action_normalization import ExternalActionNormalization
from .external_action_risk_surface import ExternalActionRiskSurface
from .external_action_scope import ExternalActionScope, ExternalActionSurface
from .external_no_op_adapter import NoOpDesktopAdapter, NoOpFileAdapter, NoOpNetworkAdapter, NoOpTerminalAdapter
from .external_real_disabled_stub import (
    DisabledRealDesktopAdapterStub,
    DisabledRealFileAdapterStub,
    DisabledRealNetworkAdapterStub,
    DisabledRealTerminalAdapterStub,
)
from .failure import ActionGroundingFailure, ActionGroundingFailureKind
from .failure_category import FailureCategory
from .failure_recoverability_hint import FailureRecoverabilityHint
from .failure_severity import FailureSeverity
from .fake import FakeActionGroundingRunner
from .fake_boundary_permit import FakeBoundaryPermitForTestOnly, FakePermitIssuerForTestOnly, SyntheticBoundaryDecisionForTestOnly
from .file_action_failure import FileActionFailure, FileActionFailureKind
from .file_action_port import FileActionAdapterPort
from .file_action_request import FileActionRequest
from .file_action_result import FileActionResult
from .file_dry_run_adapter import DryRunFileAdapter
from .file_fake_adapter import FakeFileAdapter
from .gate_input import ActionGroundingGateInput, ExecutionGateInput
from .gate_result import (
    ActionGroundingBoundaryRequirement,
    ActionGroundingGateResult,
    ActionGroundingPermitRequirement,
    ExecutionGateResult,
)
from .gate_validator import ActionGroundingGateValidator, ExecutionGateValidator
from .identity import ActionGroundingIdentity, ActionGroundingObjectKind, L4_ACTION_GROUNDING_SCHEMA_VERSION
from .invariant import (
    ActionGroundingInvariant,
    ActionGroundingInvariantKind,
    BoundaryPermitRequiredInvariant,
    NoL4AutonomousExecutionInvariant,
    NoLiveExecutionWithoutL5Invariant,
)
from .l5_ports import (
    L5AuditSinkPort,
    L5BoundaryFeedbackPort,
    L5BoundaryRecheckPort,
    L5CredentialResolverPort,
    L5PermitConsumptionReporterPort,
    L5PermitValidatorPort,
    L5ResourceBudgetPort,
)
from .l3_intent_binding import L3IntentBinding
from .l3_replan_suggestion_ref import L3ReplanSuggestionRef
from .model_action_failure import ModelActionFailure, ModelActionFailureKind
from .model_action_port import ModelActionAdapterPort
from .model_action_request import ModelActionRequest
from .model_action_result import ModelActionResult
from .model_dry_run_adapter import DryRunModelAdapter
from .model_fake_adapter import FakeModelAdapter
from .model_tool_disabled_stub import DisabledRealModelToolAdapterStub
from .model_tool_normalization import ModelToolNormalization
from .network_action_failure import NetworkActionFailure, NetworkActionFailureKind
from .network_action_port import NetworkActionAdapterPort
from .network_action_request import NetworkActionRequest
from .network_action_result import NetworkActionResult
from .network_dry_run_adapter import DryRunNetworkAdapter
from .network_fake_adapter import FakeNetworkAdapter
from .observation_reference_fake import FakeObservationReferenceFactory
from .observation_return_envelope import ObservationReturnEnvelope
from .permit_expiry import PermitExpiry
from .permit_failure import (
    AuditRequirementMissingFailure,
    CredentialScopeMismatchFailure,
    CredentialUnavailableFailure,
    LeaseUnavailableFailure,
    PermitDeniedFailure,
    PermitExpiredFailure,
    PermitFailure,
    PermitFailureKind,
    PermitMalformedFailure,
    PermitMissingFailure,
    PermitScopeMismatchFailure,
    PermitTestOnlyMisuseFailure,
    ResourceLimitExceededFailure,
    ResourceLimitUnavailableFailure,
)
from .permit_invariant import (
    NoL4AuditWriterInvariant,
    NoL4CredentialResolverInvariant,
    NoL4PermissionDecisionInvariant,
    NoL4RiskDecisionInvariant,
    NoL4TicketIssuerInvariant,
    NoLiveActionWithoutL5PermitInvariant,
    TestOnlyPermitNeverProductionInvariant,
)
from .permit_ref import (
    ActionPermitRef,
    ExecutionPermitRef,
    PermitActionRef,
    PermitConsumptionRef,
    PermitEnvironmentRef,
    PermitIssuerRef,
    PermitSubjectRef,
)
from .permit_scope import PermitScope
from .permit_validation import PermitValidationReason, PermitValidationResult, PermitValidationStatus, PermitValidationTrace
from .phase6_invariants import (
    NoAuditWriteInL4Invariant,
    NoL2StateWriteFromReturnInvariant,
    NoPermitIssuanceInL4Invariant,
    NoRealObservationInL4Invariant,
    NoRetryRecoveryRollbackInL4Invariant,
    Phase6Invariant,
)
from .projection import ActionGroundingProjection
from .recovery_requirement_ref import RecoveryRequirementRef
from .request_intake import ActionRequestIntake, ActionRequestIntakeSummary
from .resource_limit_ref import ResourceLimitRef
from .resource_usage_descriptor import ResourceUsageDescriptor
from .result import ActionGroundingResult, ActionGroundingResultKind
from .result_failure_normalization import FailureNormalizationFailure, ResultNormalizationFailure
from .reversibility_descriptor import ReversibilityDescriptor, ReversibilityKind
from .serialization import (
    ActionGroundingSerialization,
    action_grounding_stable_hash,
    action_grounding_stable_json,
    action_grounding_to_primitive,
)
from .session import ActionGroundingSession
from .status import ActionGroundingMode, ActionGroundingStatus, ActionGroundingStatusKind
from .step import ActionGroundingStep
from .side_effect_descriptor import SideEffectDescriptor, SideEffectKind
from .terminal_action_failure import TerminalActionFailure, TerminalActionFailureKind
from .terminal_action_port import TerminalActionAdapterPort
from .terminal_action_request import TerminalActionRequest
from .terminal_action_result import TerminalActionResult
from .terminal_dry_run_adapter import DryRunTerminalAdapter
from .terminal_fake_adapter import FakeTerminalAdapter
from .tool_action_failure import ToolActionFailure, ToolActionFailureKind
from .tool_action_port import ToolActionAdapterPort
from .tool_action_request import ToolActionRequest
from .tool_action_result import ToolActionResult
from .tool_argument_envelope import ToolArgumentEnvelope
from .tool_call_envelope import ToolCallEnvelope
from .tool_dry_run_adapter import DryRunToolAdapter
from .tool_failure_envelope import ToolFailureEnvelope
from .tool_fake_adapter import FakeToolAdapter
from .tool_group_action_context import ToolGroupActionContext
from .tool_result_envelope import ToolResultEnvelope
from .concurrency_scope import ConcurrencyScope
from .execution_checkpoint_ref import ExecutionCheckpointRef
from .execution_commit_intent import ExecutionCommitIntent
from .execution_determinism_hint import DeterminismKind, ExecutionDeterminismHint
from .execution_idempotency_hint import ExecutionIdempotencyHint, IdempotencyKind
from .execution_isolation_context import ExecutionIsolationContext
from .execution_lock_ref import ExecutionLockRef
from .execution_operational_summary import ExecutionOperationalSummary
from .execution_reconciliation_advice import ExecutionReconciliationAdvice
from .execution_replay_summary import ExecutionReplaySummary
from .execution_rollback_intent import ExecutionRollbackIntent
from .execution_side_effect_summary import ExecutionSideEffectSummary
from .execution_snapshot_ref import ExecutionSnapshotRef
from .execution_transaction_ref import ExecutionTransactionRef
from .execution_transaction_scope import ExecutionTransactionScope
from .l4_to_l5_resource_feedback import L4ToL5ResourceFeedback
from .l4_to_l6_recovery_replay_requirement import L4ToL6RecoveryReplayRequirement
from .l5_concurrency_budget_port import L5ConcurrencyBudgetPort
from .l5_resource_budget_port import L5ResourceBudgetPort as L5Phase7ResourceBudgetPort
from .l6_recovery_service_port import L6RecoveryServicePort
from .l6_replay_service_port import L6ReplayServicePort
from .phase7_invariants import (
    ConcurrencyScopeIsNotSchedulerInvariant,
    LockRefIsNotRealLockInvariant,
    NoCommitOrRollbackAuthorizationInL4Invariant,
    NoConcurrencyAuthorizationInL4Invariant,
    NoResourceBudgetAllocationInL4Invariant,
    Phase7Invariant,
    ReplaySummaryContainsNoPlainCredentialInvariant,
    ResourceBudgetRefIsNotAllocationInvariant,
    RollbackIntentIsNotRollbackInvariant,
    TransactionRefIsNotCommitInvariant,
)
from .resource_budget_consumption_summary import ResourceBudgetConsumptionSummary
from .resource_budget_failure import ResourceBudgetExhaustedFailure
from .resource_budget_ref import ResourceBudgetRef
from .resource_usage_report import ResourceUsageReport
from .transaction_resource_dry_run import DryRunTransactionResourceSupport
from .transaction_resource_fake import FakeTransactionResourceSupport
from .transaction_resource_noop import NoOpTransactionResourceSupport


__all__ = (
    "ActionGroundingContext",
    "ActionAdapterProtocol",
    "AdapterCannotBypassL3Invariant",
    "AdapterCannotBypassL5Invariant",
    "AdapterCannotHoldPlainCredentialInvariant",
    "AdapterCannotImplementL6SubsystemInvariant",
    "AdapterCapabilityDescriptor",
    "AdapterCapabilityMismatchFailure",
    "AdapterDescriptor",
    "AdapterDisabledByDefaultFailure",
    "AdapterDisabledReason",
    "AdapterDisabledReasonKind",
    "AdapterDuplicateIdFailure",
    "AdapterExecutionEnvelope",
    "AdapterExecutionMode",
    "AdapterFailure",
    "AdapterFailureEnvelope",
    "AdapterFailureKind",
    "AdapterFailureNormalizer",
    "AdapterIdentity",
    "AdapterInputEnvelope",
    "AdapterInvariantViolationFailure",
    "AdapterMalformedDescriptorFailure",
    "AdapterMode",
    "AdapterModeMismatchFailure",
    "AdapterModePolicy",
    "AdapterNotFoundFailure",
    "AdapterObservationHint",
    "AdapterOutputEnvelope",
    "AdapterPermitRequiredFailure",
    "AdapterProductionDisabledFailure",
    "AdapterProjection",
    "AdapterRegistry",
    "AdapterRegistryEntry",
    "AdapterRegistryProjection",
    "AdapterRegistryRegistrationResult",
    "AdapterRegistrySnapshot",
    "AdapterResultNormalizer",
    "AdapterRiskSurfaceDescriptor",
    "AdapterScopeMismatchFailure",
    "AdapterSelectionFailure",
    "AdapterSelectionRequest",
    "AdapterSelectionResult",
    "AdapterSelector",
    "AdapterStatus",
    "AdapterStatusKind",
    "AdapterTestOnlyModeFailure",
    "ActionGroundingBoundaryRequirement",
    "ActionGroundingError",
    "ActionGroundingErrorKind",
    "ActionGroundingFailure",
    "ActionGroundingFailureKind",
    "ActionGroundingIdentity",
    "ActionGroundingInvariant",
    "ActionGroundingInvariantKind",
    "ActionGroundingMode",
    "ActionGroundingObjectKind",
    "ActionGroundingProjection",
    "ActionGroundingGateInput",
    "ActionGroundingGateResult",
    "ActionGroundingGateValidator",
    "ActionGroundingPermitRequirement",
    "ActionGroundingResult",
    "ActionGroundingResultKind",
    "ActionGroundingSerialization",
    "ActionGroundingSession",
    "ActionGroundingStatus",
    "ActionGroundingStatusKind",
    "ActionGroundingStep",
    "ActionRequestIntake",
    "ActionRequestIntakeSummary",
    "ActionPermitRef",
    "AuditRequirementMissingFailure",
    "AuditRequirementRef",
    "BoundaryDecisionRef",
    "BoundaryDecisionStatus",
    "BoundaryDeniedFailure",
    "BoundaryExpiredFailure",
    "BoundaryMissingFailure",
    "BoundaryScopeMismatchFailure",
    "BoundaryPermitRequiredInvariant",
    "ConfirmationTicketRef",
    "CredentialHandleRef",
    "CredentialScopeMismatchFailure",
    "CredentialUnavailableFailure",
    "A5LikeHardSafetyInvariant",
    "DesktopActionAdapterPort",
    "DesktopActionEnvelope",
    "DesktopActionFailure",
    "DesktopActionFailureKind",
    "DesktopActionRequest",
    "DesktopActionResult",
    "DisabledRealDesktopAdapterStub",
    "DisabledRealFileAdapterStub",
    "DisabledRealNetworkAdapterStub",
    "DisabledRealTerminalAdapterStub",
    "DryRunActionGroundingRunner",
    "DryRunDesktopAdapter",
    "DryRunFileAdapter",
    "DryRunNetworkAdapter",
    "DryRunTerminalAdapter",
    "ExecutionDisabledByDefaultFailure",
    "ExecutionAdapterMode",
    "ExecutionAdapterProtocol",
    "ExecutionGateInput",
    "ExecutionGateResult",
    "ExecutionGateValidator",
    "ExecutionPermitRef",
    "FakeActionGroundingRunner",
    "FakeActionAdapter",
    "FakeAdapter",
    "FakeAdapterNeverProductionInvariant",
    "FakeDesktopAdapter",
    "FakeFileAdapter",
    "FakeModelAdapter",
    "FakeNetworkAdapter",
    "FakeTerminalAdapter",
    "FakeToolAdapter",
    "FakeBoundaryPermitForTestOnly",
    "FakePermitIssuerForTestOnly",
    "L4_ACTION_GROUNDING_SCHEMA_VERSION",
    "L5AuditSinkPort",
    "L5BoundaryFeedbackPort",
    "L5BoundaryRecheckPort",
    "L5CredentialResolverPort",
    "L5PermitConsumptionReporterPort",
    "L5PermitValidatorPort",
    "L5ResourceBudgetPort",
    "LeaseRef",
    "LeaseUnavailableFailure",
    "NoL4AuditWriterInvariant",
    "NoL4AutonomousExecutionInvariant",
    "NoL4CredentialResolverInvariant",
    "NoL4PermissionDecisionInvariant",
    "NoL4RiskDecisionInvariant",
    "NoL4TicketIssuerInvariant",
    "NoLiveActionWithoutL5PermitInvariant",
    "NoLiveExecutionWithoutL5Invariant",
    "NoOpDesktopAdapter",
    "NoOpFileAdapter",
    "NoOpNetworkAdapter",
    "NoOpTerminalAdapter",
    "NoRealDesktopControlInvariant",
    "NoRealFileSystemMutationInvariant",
    "NoRealNetworkAccessInvariant",
    "NoRealShellExecutionInvariant",
    "NoRealAdapterActivationWithoutL5Invariant",
    "NoOpActionAdapter",
    "NoOpAdapter",
    "NoOpActionGroundingRunner",
    "PermitActionRef",
    "PermitConsumptionRef",
    "PermitDeniedFailure",
    "PermitEnvironmentRef",
    "PermitExpiredFailure",
    "PermitExpiry",
    "PermitFailure",
    "PermitFailureKind",
    "PermitIssuerRef",
    "PermitMalformedFailure",
    "PermitMissingFailure",
    "PermitScope",
    "PermitScopeMismatchFailure",
    "PermitSubjectRef",
    "PermitTestOnlyMisuseFailure",
    "PermitValidationReason",
    "PermitValidationResult",
    "PermitValidationStatus",
    "PermitValidationTrace",
    "PermissionGrantRef",
    "PolicyDecisionRef",
    "ResourceLimitExceededFailure",
    "ResourceLimitRef",
    "ResourceLimitUnavailableFailure",
    "ResourceUsageDescriptor",
    "RiskReviewRef",
    "RealActionAdapterStub",
    "RealAdapterStub",
    "DryRunActionAdapter",
    "DryRunAdapter",
    "InMemoryActionAdapter",
    "InMemoryAdapter",
    "L3IntentBinding",
    "SyntheticBoundaryDecisionForTestOnly",
    "ModelActionAdapterPort",
    "ModelActionFailure",
    "ModelActionFailureKind",
    "ModelActionRequest",
    "ModelActionResult",
    "ModelToolNormalization",
    "ExternalActionDisabledByDefault",
    "ExternalActionEnvelope",
    "ExternalActionHardSafetyInvariant",
    "ExternalActionNormalization",
    "ExternalActionRequiresL5PermitInvariant",
    "ExternalActionRiskSurface",
    "ExternalActionScope",
    "ExternalActionSurface",
    "FileActionAdapterPort",
    "FileActionEnvelope",
    "FileActionFailure",
    "FileActionFailureKind",
    "FileActionRequest",
    "FileActionResult",
    "NetworkActionAdapterPort",
    "NetworkActionEnvelope",
    "NetworkActionFailure",
    "NetworkActionFailureKind",
    "NetworkActionRequest",
    "NetworkActionResult",
    "DisabledRealModelToolAdapterStub",
    "DryRunModelAdapter",
    "DryRunToolAdapter",
    "ReversibilityDescriptor",
    "ReversibilityKind",
    "SideEffectDescriptor",
    "SideEffectKind",
    "TerminalActionAdapterPort",
    "TerminalActionEnvelope",
    "TerminalActionFailure",
    "TerminalActionFailureKind",
    "TerminalActionRequest",
    "TerminalActionResult",
    "ToolActionAdapterPort",
    "ToolActionFailure",
    "ToolActionFailureKind",
    "ToolActionRequest",
    "ToolActionResult",
    "ToolArgumentEnvelope",
    "ToolCallEnvelope",
    "ToolFailureEnvelope",
    "ToolGroupActionContext",
    "ToolResultEnvelope",
    "ActionFailureReturnEnvelope",
    "ActionOutcomeEnvelope",
    "ActionResultReturnEnvelope",
    "BoundaryFeedbackRef",
    "ExecutionAuditRef",
    "ExecutionCancellationRequest",
    "ExecutionCancellationResult",
    "ExecutionCancellationStatus",
    "ExecutionEvidenceRef",
    "ExecutionObservationRef",
    "ExecutionResourceUsage",
    "ExecutionResumeRef",
    "ExecutionRetryAdviceRef",
    "ExecutionReturnProjection",
    "ExecutionRollbackHintRef",
    "ExecutionTimeoutFailure",
    "ExecutionTimeoutPolicyRef",
    "ExecutionTraceRef",
    "FailureCategory",
    "FailureRecoverabilityHint",
    "FailureNormalizationFailure",
    "FailureSeverity",
    "FakeCancellationTimeoutHelper",
    "FakeObservationReferenceFactory",
    "L3ReplanSuggestionRef",
    "NoAuditWriteInL4Invariant",
    "NoL2StateWriteFromReturnInvariant",
    "NoPermitIssuanceInL4Invariant",
    "NoRealObservationInL4Invariant",
    "NoRetryRecoveryRollbackInL4Invariant",
    "ObservationReturnEnvelope",
    "Phase6Invariant",
    "RecoveryRequirementRef",
    "ResultNormalizationFailure",
    "ConcurrencyScope",
    "ConcurrencyScopeIsNotSchedulerInvariant",
    "DeterminismKind",
    "DryRunTransactionResourceSupport",
    "ExecutionCheckpointRef",
    "ExecutionCommitIntent",
    "ExecutionDeterminismHint",
    "ExecutionIdempotencyHint",
    "ExecutionIsolationContext",
    "ExecutionLockRef",
    "ExecutionOperationalSummary",
    "ExecutionReconciliationAdvice",
    "ExecutionReplaySummary",
    "ExecutionRollbackIntent",
    "ExecutionSideEffectSummary",
    "ExecutionSnapshotRef",
    "ExecutionTransactionRef",
    "ExecutionTransactionScope",
    "FakeTransactionResourceSupport",
    "IdempotencyKind",
    "L4ToL5ResourceFeedback",
    "L4ToL6RecoveryReplayRequirement",
    "L5ConcurrencyBudgetPort",
    "L5Phase7ResourceBudgetPort",
    "L6RecoveryServicePort",
    "L6ReplayServicePort",
    "LockRefIsNotRealLockInvariant",
    "NoCommitOrRollbackAuthorizationInL4Invariant",
    "NoConcurrencyAuthorizationInL4Invariant",
    "NoOpTransactionResourceSupport",
    "NoResourceBudgetAllocationInL4Invariant",
    "Phase7Invariant",
    "ReplaySummaryContainsNoPlainCredentialInvariant",
    "ResourceBudgetConsumptionSummary",
    "ResourceBudgetExhaustedFailure",
    "ResourceBudgetRef",
    "ResourceBudgetRefIsNotAllocationInvariant",
    "ResourceUsageReport",
    "RollbackIntentIsNotRollbackInvariant",
    "TransactionRefIsNotCommitInvariant",
    "TestOnlyPermitNeverProductionInvariant",
    "action_grounding_stable_hash",
    "action_grounding_stable_json",
    "action_grounding_to_primitive",
)

# 数学模型发动机最小兼容补丁：L4 仅预留禁用态数学适配器。
from .math_adapter_descriptor import (
    MathAdapterDescriptor,
    MathAdapterInvocationRef,
    build_math_adapter_descriptor,
    disabled_math_adapter_invocation,
)
from .math_adapter_protocol import MathAdapterProtocol
from .python_math_adapter import PythonMathAdapter
from .external_scoring_adapter import ExternalScoringAdapter
from .local_model_scoring_adapter import LocalModelScoringAdapter
from .llm_judge_adapter import LLMJudgeAdapter
from .statistics_adapter import StatisticsAdapter
from .custom_formula_adapter import CustomFormulaAdapter
from .model_evaluation_adapter import ModelEvaluationAdapter
from .optional_third_party_math_adapter_descriptor import OptionalThirdPartyMathAdapterDescriptor

__all__ = __all__ + (
    "MathAdapterDescriptor",
    "MathAdapterInvocationRef",
    "build_math_adapter_descriptor",
    "disabled_math_adapter_invocation",
    "MathAdapterProtocol",
    "PythonMathAdapter",
    "ExternalScoringAdapter",
    "LocalModelScoringAdapter",
    "LLMJudgeAdapter",
    "StatisticsAdapter",
    "CustomFormulaAdapter",
    "ModelEvaluationAdapter",
    "OptionalThirdPartyMathAdapterDescriptor",
)

# Skill 直显与 ToolGroup 释放链路专项补丁：只读视图和链路索引。
from .released_tool_schema_view import ModelVisibleReleasedToolView, ReleasedToolSchemaView
from .skill_tool_release_session_context import SkillToolReleaseSessionContext, ToolResultReturnContext
from .skill_tool_release_chain_index import SkillToolReleaseChainIndex
from .safety_chain_ref import L3SafetyChainRef, SafetyChainValidationResult, SideEffectSafetyPreconditionRef
from .cognitive_sink_hint import ActionResultCognitiveSinkHint
from .self_healing_handoff import L4FailureRecoveryRequirementBundle, L4PostRecoveryValidationRequirement, L4SelfHealingHandoffRef
from .context_safety_projection import (
    L4ContextSafetyProjection,
    L4ModelOutputContextProjection,
    L4ObservationBeliefWorldProjection,
    L4ToolOutputContextProjection,
)
from .math_model_adapter import (
    AdapterTelemetryCollector,
    BaseMathModelAdapter,
    DeterministicLocalScoreAdapter,
    ExternalModelAdapter,
    FallbackAdapter,
    ReplayAdapter,
    ShadowAdapter,
)

__all__ = __all__ + (
    "ModelVisibleReleasedToolView",
    "ReleasedToolSchemaView",
    "SkillToolReleaseSessionContext",
    "ToolResultReturnContext",
    "SkillToolReleaseChainIndex",
    "L3SafetyChainRef",
    "SafetyChainValidationResult",
    "SideEffectSafetyPreconditionRef",
    "ActionResultCognitiveSinkHint",
    "L4FailureRecoveryRequirementBundle",
    "L4PostRecoveryValidationRequirement",
    "L4SelfHealingHandoffRef",
    "L4ContextSafetyProjection",
    "L4ModelOutputContextProjection",
    "L4ObservationBeliefWorldProjection",
    "L4ToolOutputContextProjection",
    "AdapterTelemetryCollector",
    "BaseMathModelAdapter",
    "DeterministicLocalScoreAdapter",
    "ExternalModelAdapter",
    "FallbackAdapter",
    "ReplayAdapter",
    "ShadowAdapter",
)

# L4 L5/L6 preflight specialty patches: ref-only surfaces, audit chain,
# sandbox contract, data governance, version switch, and communication handoff.
from .audit_chain_binding import L4ActionAuditChain
from .sandbox_policy_ref import (
    SandboxAuditPolicyRef,
    SandboxCredentialPolicyRef,
    SandboxEnvPolicyRef,
    SandboxExecutionContextRef,
    SandboxMountPolicyRef,
    SandboxNetworkPolicyRef,
    SandboxPolicyRef,
    SandboxProcessPolicyRef,
    SandboxRecoveryPolicyRef,
    SandboxResourceLimitRef,
    SandboxWorkdirPolicyRef,
)
from .external_surface_contract import (
    EXTERNAL_SURFACE_CONTRACT_REGISTRY,
    HIGH_RISK_EXTERNAL_ACTION_SURFACES,
    REQUIRED_EXTERNAL_ACTION_SURFACES,
    DisabledExternalSurfaceAdapterStub,
    ExternalSurfaceActionFailure,
    ExternalSurfaceActionRequest,
    ExternalSurfaceActionResult,
)
from .version_switch_requirement import (
    AdapterSchemaMigrationRequirement,
    AdapterVersionCompatibilityRequirement,
    HotSwitchExecutionRequirementRef,
    L4VersionSwitchRequirement,
    OldEventReplayRequirement,
    PostSwitchObservationRequirement,
    PreSwitchCheckpointRequirement,
    SwitchRollbackExecutionRequirement,
)
from .data_governance_ref import CredentialRevocationSignalRef, DataGovernanceRefBundle
from .communication_handoff_binding import CommunicationEnvelopeBinding, HandoffActionBinding, HandoffReturnBinding

__all__ = __all__ + (
    "L4ActionAuditChain",
    "SandboxAuditPolicyRef",
    "SandboxCredentialPolicyRef",
    "SandboxEnvPolicyRef",
    "SandboxExecutionContextRef",
    "SandboxMountPolicyRef",
    "SandboxNetworkPolicyRef",
    "SandboxPolicyRef",
    "SandboxProcessPolicyRef",
    "SandboxRecoveryPolicyRef",
    "SandboxResourceLimitRef",
    "SandboxWorkdirPolicyRef",
    "EXTERNAL_SURFACE_CONTRACT_REGISTRY",
    "HIGH_RISK_EXTERNAL_ACTION_SURFACES",
    "REQUIRED_EXTERNAL_ACTION_SURFACES",
    "DisabledExternalSurfaceAdapterStub",
    "ExternalSurfaceActionFailure",
    "ExternalSurfaceActionRequest",
    "ExternalSurfaceActionResult",
    "AdapterSchemaMigrationRequirement",
    "AdapterVersionCompatibilityRequirement",
    "HotSwitchExecutionRequirementRef",
    "L4VersionSwitchRequirement",
    "OldEventReplayRequirement",
    "PostSwitchObservationRequirement",
    "PreSwitchCheckpointRequirement",
    "SwitchRollbackExecutionRequirement",
    "CredentialRevocationSignalRef",
    "DataGovernanceRefBundle",
    "CommunicationEnvelopeBinding",
    "HandoffActionBinding",
    "HandoffReturnBinding",
)

# Five-model provider adapter hotfix3 public exports.
from .model_provider_adapter import (
    MIMO_API_SURFACES,
    DeepSeekV4CapabilityProfile,
    DeepSeekV4DisabledStub,
    DeepSeekV4ErrorMapper,
    DeepSeekV4LiveAdapterSkeleton,
    DeepSeekV4ProviderDescriptor,
    DeepSeekV4ReasoningMapper,
    DeepSeekV4RequestMapper,
    DeepSeekV4ResponseMapper,
    DeepSeekV4StreamMapper,
    DeepSeekV4ToolCallMapper,
    GLM51CapabilityProfile,
    GLM51DisabledStub,
    GLM51ErrorMapper,
    GLM51LiveAdapterSkeleton,
    GLM51ProviderDescriptor,
    GLM51RequestMapper,
    GLM51ResponseMapper,
    GLM51StreamMapper,
    GLM51StructuredOutputMapper,
    GLM51ThinkingModeMapper,
    GLM51ToolCallMapper,
    GPT55CapabilityProfile,
    GPT55DisabledStub,
    GPT55ErrorMapper,
    GPT55LiveAdapterSkeleton,
    GPT55MultimodalMapper,
    GPT55ProviderDescriptor,
    GPT55ReasoningMapper,
    GPT55RequestMapper,
    GPT55ResponseMapper,
    GPT55StreamMapper,
    GPT55StructuredOutputMapper,
    GPT55ToolCallMapper,
    MiMoApiSurfaceDescriptor,
    MiMoCapabilityProfile,
    MiMoDisabledStub,
    MiMoErrorMapper,
    MiMoLiveAdapterSkeleton,
    MiMoLocalAdapterSkeleton,
    MiMoLongContextGuard,
    MiMoMultimodalMapper,
    MiMoOrdinaryApiRequestMapper,
    MiMoProviderDescriptor,
    MiMoRequestMapper,
    MiMoResponseMapper,
    MiMoStreamMapper,
    MiMoTokenPlanRequestMapper,
    MiMoToolCallMapper,
    MiniMaxM3CapabilityProfile,
    MiniMaxM3DisabledStub,
    MiniMaxM3ErrorMapper,
    MiniMaxM3LiveAdapterSkeleton,
    MiniMaxM3LongContextGuard,
    MiniMaxM3MultimodalMapper,
    MiniMaxM3ProviderDescriptor,
    MiniMaxM3RequestMapper,
    MiniMaxM3ResponseMapper,
    MiniMaxM3StreamMapper,
    MiniMaxM3ToolCallMapper,
    ModelProviderAdapterDescriptor,
    ModelProviderAdapterProtocol,
    ModelProviderAdapterRegistry,
    ModelProviderAuditEnvelope,
    ModelProviderBudgetEnvelope,
    ModelProviderCapabilityProfile,
    ModelProviderCredentialHandleRef,
    ModelProviderFailureEnvelope,
    ModelProviderPolicyEnvelope,
    ModelProviderRequestMapper,
    ModelProviderResponseMapper,
    ModelProviderStreamMapper,
    ModelProviderToolCallMapper,
    ProviderFactsheet,
    all_provider_factsheets,
    build_default_disabled_registry,
    descriptor_for,
    mimo_api_surface_descriptors,
    provider_capability_matrix,
    provider_endpoint_matrix,
    provider_error_taxonomy_matrix,
    provider_factsheet_deepseek_v4,
    provider_factsheet_glm_5_1,
    provider_factsheet_gpt_5_5,
    provider_factsheet_mimo,
    provider_factsheet_minimax_m3,
    provider_feature_gap_matrix,
    provider_risk_surface_matrix,
)

__all__ = __all__ + (
    "MIMO_API_SURFACES",
    "ProviderFactsheet",
    "ModelProviderAdapterProtocol",
    "ModelProviderAdapterRegistry",
    "ModelProviderAdapterDescriptor",
    "ModelProviderCapabilityProfile",
    "ModelProviderRequestMapper",
    "ModelProviderResponseMapper",
    "ModelProviderStreamMapper",
    "ModelProviderToolCallMapper",
    "ModelProviderBudgetEnvelope",
    "ModelProviderAuditEnvelope",
    "ModelProviderPolicyEnvelope",
    "ModelProviderCredentialHandleRef",
    "ModelProviderFailureEnvelope",
    "DeepSeekV4ProviderDescriptor",
    "MiMoProviderDescriptor",
    "GLM51ProviderDescriptor",
    "MiniMaxM3ProviderDescriptor",
    "GPT55ProviderDescriptor",
    "DeepSeekV4CapabilityProfile",
    "MiMoCapabilityProfile",
    "GLM51CapabilityProfile",
    "MiniMaxM3CapabilityProfile",
    "GPT55CapabilityProfile",
    "DeepSeekV4RequestMapper",
    "MiMoRequestMapper",
    "MiMoTokenPlanRequestMapper",
    "MiMoOrdinaryApiRequestMapper",
    "GLM51RequestMapper",
    "MiniMaxM3RequestMapper",
    "GPT55RequestMapper",
    "MiMoApiSurfaceDescriptor",
    "mimo_api_surface_descriptors",
    "DeepSeekV4DisabledStub",
    "MiMoDisabledStub",
    "GLM51DisabledStub",
    "MiniMaxM3DisabledStub",
    "GPT55DisabledStub",
    "DeepSeekV4LiveAdapterSkeleton",
    "MiMoLiveAdapterSkeleton",
    "MiMoLocalAdapterSkeleton",
    "GLM51LiveAdapterSkeleton",
    "MiniMaxM3LiveAdapterSkeleton",
    "GPT55LiveAdapterSkeleton",
    "all_provider_factsheets",
    "provider_capability_matrix",
    "provider_endpoint_matrix",
    "provider_feature_gap_matrix",
    "provider_risk_surface_matrix",
    "provider_error_taxonomy_matrix",
    "descriptor_for",
    "build_default_disabled_registry",
)
