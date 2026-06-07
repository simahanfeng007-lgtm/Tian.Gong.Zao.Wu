"""Fake observation/evidence/audit references for L4 phase 6 tests."""

from __future__ import annotations

from dataclasses import dataclass

from .adapter_failure import new_adapter_typed_ref
from .execution_audit_ref import ExecutionAuditRef
from .execution_evidence_ref import ExecutionEvidenceRef
from .execution_observation_ref import ExecutionObservationRef


@dataclass(frozen=True, slots=True)
class FakeObservationReferenceFactory:
    """Test helper only; it creates refs and samples no real source."""

    test_only: bool = True

    def observation_ref(self, action_ref) -> ExecutionObservationRef:
        return ExecutionObservationRef(
            observation_ref=new_adapter_typed_ref("execution_observation"),
            action_ref=action_ref,
            samples_real_observation=False,
        )

    def evidence_ref(self, action_ref) -> ExecutionEvidenceRef:
        return ExecutionEvidenceRef(
            evidence_ref=new_adapter_typed_ref("execution_evidence"),
            action_ref=action_ref,
            stores_real_evidence=False,
        )

    def audit_ref(self, action_ref) -> ExecutionAuditRef:
        return ExecutionAuditRef(
            audit_ref=new_adapter_typed_ref("execution_audit"),
            action_ref=action_ref,
            writes_real_audit=False,
            writes_audit_store=False,
        )
