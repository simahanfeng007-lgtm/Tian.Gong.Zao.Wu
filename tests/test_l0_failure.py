from dataclasses import FrozenInstanceError, fields

from tiangong_kernel.l0_primitives.identity import RefId, TypedRef
from tiangong_kernel.l0_primitives.serialization import stable_hash, stable_json_dumps
from tiangong_kernel.l0_primitives.time import TimeRange, Timestamp


def rid(prefix: str = "ref") -> RefId:
    return RefId(f"{prefix}:" + "1" * 32)


def tref(kind: str = "sample") -> TypedRef:
    return TypedRef(rid("ref"), kind)


def assert_value_object(obj):
    dumped = stable_json_dumps(obj)
    digest = stable_hash(obj)
    assert isinstance(dumped, str)
    assert isinstance(digest, str)
    assert len(digest) == 64
    field_name = fields(obj)[0].name
    try:
        setattr(obj, field_name, getattr(obj, field_name))
    except FrozenInstanceError:
        pass
    else:
        raise AssertionError(f"{type(obj).__name__} allowed mutation")

from tiangong_kernel.l0_primitives.failure import (
    CriticalStepRef,
    DiagnosisConfidence,
    FailureEvidenceRef,
    FailureKind,
    FailureRef,
    FailureSeverity,
    FailureState,
    FaultKind,
    FaultRef,
    FaultScope,
    RecoveryDiagnosisRef,
    RootCauseRef,
)


def test_failure_objects_construct_and_serialize():
    failure = FailureRef(rid(), FailureKind.EFFECT_FAILURE, FailureState.DETECTED, FailureSeverity.HIGH)
    scope = FaultScope(tref("scope"), "run")
    fault = FaultRef(rid(), FaultKind.AUTHORIZATION_FAULT, scope)
    confidence = DiagnosisConfidence(0.75)
    step = CriticalStepRef(rid(), "proposal")
    root = RootCauseRef(rid(), "boundary")
    evidence = FailureEvidenceRef(rid(), "event")
    diagnosis = RecoveryDiagnosisRef(rid(), failure, (fault,), confidence, step, root, (evidence,))
    for obj in (failure, scope, fault, confidence, step, root, evidence, diagnosis):
        assert_value_object(obj)


def test_failure_enum_values_are_stable():
    assert [item.value for item in FailureKind] == ["goal_failure", "plan_failure", "effect_failure", "tool_failure", "adapter_failure", "policy_failure", "memory_failure", "context_failure", "resource_failure", "contract_failure", "recovery_failure", "unknown"]
    assert [item.value for item in FaultKind] == ["model_reasoning_fault", "context_boundary_fault", "authorization_fault", "tool_invocation_fault", "adapter_compatibility_fault", "dependency_fault", "environment_fault", "state_transition_fault", "schema_version_fault", "resource_exhaustion_fault", "external_service_fault", "unknown"]
    assert [item.value for item in FailureState] == ["detected", "diagnosing", "diagnosed", "recovery_planned", "recovering", "recovered", "unrecoverable", "escalated", "archived", "unknown"]
    assert [item.value for item in FailureSeverity] == ["low", "medium", "high", "critical", "unknown"]
