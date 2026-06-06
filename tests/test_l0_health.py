from dataclasses import FrozenInstanceError

from tiangong_kernel.l0_primitives.health import (
    DamageRef,
    HealthRef,
    HealthSignalRef,
    HealthState,
    HomeostasisRef,
    HomeostasisState,
    RecoveryHealthRef,
    StabilityDeviationRef,
    StabilityRange,
    StressRef,
    VitalityKind,
    VitalityRef,
    VitalityState,
)
from tiangong_kernel.l0_primitives.identity import RefId, TypedRef
from tiangong_kernel.l0_primitives.serialization import stable_hash, stable_json_dumps


def rid(prefix: str = "ref") -> RefId:
    return RefId(f"{prefix}:" + "5" * 32)


def tref(kind: str = "health") -> TypedRef:
    return TypedRef(rid("ref"), kind)


def test_health_objects_construct_immutable_and_stable():
    signal = HealthSignalRef(rid(), signal_ref=tref("signal"))
    range_ = StabilityRange(label="latency", lower_bound=0.0, upper_bound=1.0)
    vitality = VitalityRef(rid(), kind=VitalityKind.EXECUTION_CAPACITY, state=VitalityState.NORMAL, subject_ref=tref("run"))
    homeostasis = HomeostasisRef(rid(), state=HomeostasisState.WITHIN_RANGE, stability_range=range_, subject_ref=tref("run"))
    deviation = StabilityDeviationRef(rid(), range_ref=tref("range"), observed_value=0.2)
    stress = StressRef(rid(), source_ref=tref("source"), target_ref=tref("target"), intensity=0.4)
    damage = DamageRef(rid(), target_ref=tref("target"), severity=0.1)
    recovery = RecoveryHealthRef(rid(), health_ref=tref("health"), recovery_ref=tref("recovery"))
    health = HealthRef(
        rid(),
        state=HealthState.HEALTHY,
        subject_ref=tref("run"),
        signal_refs=(signal,),
        vitality_ref=vitality,
        homeostasis_ref=homeostasis,
        deviation_ref=deviation,
        stress_ref=stress,
        damage_ref=damage,
        recovery_health_ref=recovery,
    )
    assert "healthy" in stable_json_dumps(health)
    assert stable_hash(health) == stable_hash(health)
    try:
        health.state = HealthState.FAILED
    except FrozenInstanceError:
        pass
    else:
        raise AssertionError("HealthRef allowed mutation")


def test_health_enum_values_are_stable():
    assert HealthState.HEALTHY.value == "healthy"
    assert HealthState.WATCH.value == "watch"
    assert HealthState.DEGRADED.value == "degraded"
    assert HealthState.UNSTABLE.value == "unstable"
    assert HealthState.CRITICAL.value == "critical"
    assert HealthState.RECOVERING.value == "recovering"
    assert HealthState.FAILED.value == "failed"
    assert HealthState.UNKNOWN.value == "unknown"
    assert VitalityKind.STRUCTURAL_INTEGRITY.value == "structural_integrity"
    assert VitalityKind.EXECUTION_CAPACITY.value == "execution_capacity"
    assert VitalityKind.RESOURCE_BALANCE.value == "resource_balance"
    assert VitalityKind.MEMORY_CONTINUITY.value == "memory_continuity"
    assert VitalityKind.FORGETTING_CLEANLINESS.value == "forgetting_cleanliness"
    assert VitalityKind.SELF_CONTINUITY.value == "self_continuity"
    assert VitalityKind.ADAPTATION_CAPACITY.value == "adaptation_capacity"
    assert VitalityKind.RECOVERY_CAPACITY.value == "recovery_capacity"
    assert VitalityKind.TRUST_INTEGRITY.value == "trust_integrity"
    assert VitalityKind.UNKNOWN.value == "unknown"
    assert HomeostasisState.WITHIN_RANGE.value == "within_range"
    assert HomeostasisState.DRIFTING.value == "drifting"
    assert HomeostasisState.OUT_OF_RANGE.value == "out_of_range"
    assert HomeostasisState.COMPENSATING.value == "compensating"
    assert HomeostasisState.FAILED.value == "failed"
    assert HomeostasisState.UNKNOWN.value == "unknown"
    assert VitalityState.STRONG.value == "strong"
    assert VitalityState.NORMAL.value == "normal"
    assert VitalityState.WEAKENED.value == "weakened"
    assert VitalityState.DAMAGED.value == "damaged"
    assert VitalityState.RECOVERING.value == "recovering"
    assert VitalityState.COLLAPSED.value == "collapsed"
    assert VitalityState.UNKNOWN.value == "unknown"
