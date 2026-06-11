"""L4 phase 8 closure exports.

This package is a static closure and handoff layer. It does not execute actions,
decide boundaries, implement L5, implement L6, or restore any legacy main chain.
"""

from ._common import (
    L4_ACTION_SURFACES,
    L4_BOUNDARY_SURFACES,
    L4_EXECUTION_CLOSURE_SCHEMA_VERSION,
    L4_L6_SURFACES,
    L4_PHASES,
    L5_PLUGIN_HOST_SURFACES,
    LEGACY_MAIN_CHAIN_SYMBOLS,
)
from .l4_boundary_invariant_suite import L4BoundaryInvariantSuite
from .l4_closure_projection import L4ClosureProjection
from .l4_component_registry_summary import L4ComponentRegistrySummary
from .l4_final_freeze_readiness import L4FinalFreezeReadinessReport
from .l4_final_quality_checklist import L4FinalQualityChecklist
from .l4_module_inventory import L4ModuleInventory
from .l4_no_boundary_bypass_guarantee import L4NoBoundaryBypassGuarantee
from .l4_no_l6_implementation_guarantee import L4NoL6ImplementationGuarantee
from .l4_no_legacy_runtime_guarantee import L4NoLegacyRuntimeGuarantee
from .l4_no_live_action_guarantee import L4NoLiveActionGuarantee
from .l4_object_family_index import L4ObjectFamilyIndex
from .l4_phase8_invariants import (
    L4Phase8Invariant,
    NoDirectL5L6ProgressionInvariant,
    NoPhase8LiveActionInvariant,
    NoSkipL4QualityGateInvariant,
)
from .l4_public_export_map import L4PublicExportMap
from .l4_to_l5_audit_summary import L4ToL5ExecutionAuditSummary
from .l4_to_l5_boundary_feedback import L4ToL5BoundaryFeedback
from .l4_to_l5_handoff import L4ToL5HandoffEnvelope
from .l4_to_l5_plugin_host_handoff import L4ToL5PluginHostHandoffEnvelope
from .l4_to_l5_permit_consumption import L4ToL5PermitConsumptionSummary
from .l4_quality_gate_handoff import L4QualityGateHandoffEnvelope
from .l4_test_evidence_index import L4TestEvidenceIndex
from .l4_regression_evidence_index import L4RegressionEvidenceIndex
from .l4_to_l5_quality_gate_summary import L4ToL5QualityGateSummary
from .l4_to_l6_validation_evaluation_requirement import (
    L4ToL6EvaluationRequirement,
    L4ToL6RegressionRequirement,
    L4ToL6ValidationRequirement,
)
from .l4_to_l5_audit_chain_handoff import L4ToL5AuditChainHandoff
from .l4_to_l5_version_switch_requirement import L4ToL5VersionSwitchRequirement
from .l4_to_l6_migration_switch_requirement import L4ToL6MigrationSwitchRequirement
from .l4_to_l5_resource_concurrency_summary import L4ToL5ConcurrencySummary, L4ToL5ResourceBudgetSummary
from .l4_to_l5_self_evolution_requirement import L4ToL5SelfEvolutionBoundaryRequirement, L4ToL5SelfEvolutionPermitRequirement
from .l4_to_l6_adapter_requirement import L4ToL6AdapterRequirement
from .l4_to_l6_execution_service_need import L4ToL6ExecutionServiceNeed
from .l4_to_l6_forgetting_sink_requirement import L4ToL6ForgettingSinkRequirement
from .l4_to_l6_memory_sink_requirement import L4ToL6MemorySinkRequirement
from .l4_to_l6_observation_requirement import L4ToL6ObservationRequirement
from .l4_to_l6_recovery_requirement import L4ToL6RecoveryRequirement
from .l4_to_l6_replay_requirement import L4ToL6ReplayRequirement
from .l4_to_l6_self_evolution_requirement import (
    L4ToL6EvolutionCommitRequirement,
    L4ToL6EvolutionValidationRequirement,
    L4ToL6PostCommitObservationRequirement,
    L4ToL6SelfLearningSinkRequirement,
)


__all__ = (
    "L4_ACTION_SURFACES",
    "L4_BOUNDARY_SURFACES",
    "L4_EXECUTION_CLOSURE_SCHEMA_VERSION",
    "L4_L6_SURFACES",
    "L4_PHASES",
    "L5_PLUGIN_HOST_SURFACES",
    "LEGACY_MAIN_CHAIN_SYMBOLS",
    "L4BoundaryInvariantSuite",
    "L4ClosureProjection",
    "L4ComponentRegistrySummary",
    "L4FinalFreezeReadinessReport",
    "L4FinalQualityChecklist",
    "L4ModuleInventory",
    "L4NoBoundaryBypassGuarantee",
    "L4NoL6ImplementationGuarantee",
    "L4NoLegacyRuntimeGuarantee",
    "L4NoLiveActionGuarantee",
    "L4ObjectFamilyIndex",
    "L4Phase8Invariant",
    "NoDirectL5L6ProgressionInvariant",
    "NoPhase8LiveActionInvariant",
    "NoSkipL4QualityGateInvariant",
    "L4PublicExportMap",
    "L4ToL5BoundaryFeedback",
    "L4ToL5ConcurrencySummary",
    "L4ToL5ExecutionAuditSummary",
    "L4ToL5HandoffEnvelope",
    "L4ToL5PluginHostHandoffEnvelope",
    "L4ToL5PermitConsumptionSummary",
    "L4QualityGateHandoffEnvelope",
    "L4TestEvidenceIndex",
    "L4RegressionEvidenceIndex",
    "L4ToL5QualityGateSummary",
    "L4ToL6ValidationRequirement",
    "L4ToL6EvaluationRequirement",
    "L4ToL6RegressionRequirement",
    "L4ToL5AuditChainHandoff",
    "L4ToL5VersionSwitchRequirement",
    "L4ToL6MigrationSwitchRequirement",
    "L4ToL5ResourceBudgetSummary",
    "L4ToL5SelfEvolutionBoundaryRequirement",
    "L4ToL5SelfEvolutionPermitRequirement",
    "L4ToL6AdapterRequirement",
    "L4ToL6ExecutionServiceNeed",
    "L4ToL6ForgettingSinkRequirement",
    "L4ToL6MemorySinkRequirement",
    "L4ToL6ObservationRequirement",
    "L4ToL6RecoveryRequirement",
    "L4ToL6ReplayRequirement",
    "L4ToL6EvolutionCommitRequirement",
    "L4ToL6EvolutionValidationRequirement",
    "L4ToL6PostCommitObservationRequirement",
    "L4ToL6SelfLearningSinkRequirement",
)
