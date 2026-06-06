import pytest
from dataclasses import replace

from l4_phase3_builders import envelope, phase3_ref
from tiangong_kernel.l4_action_grounding import (
    AdapterCannotBypassL3Invariant,
    AdapterCannotBypassL5Invariant,
    AdapterCannotHoldPlainCredentialInvariant,
    AdapterCannotImplementL6SubsystemInvariant,
    AdapterInputEnvelope,
    AdapterMode,
    FakeActionAdapter,
    FakeAdapterNeverProductionInvariant,
    NoRealAdapterActivationWithoutL5Invariant,
    RealActionAdapterStub,
)


def test_l4_phase3_real_adapter_activation_invariant_keeps_stub_disabled():
    invariant = NoRealAdapterActivationWithoutL5Invariant(phase3_ref(80, "adapter_invariant"))
    real_stub = RealActionAdapterStub()
    assert invariant.is_satisfied_by_descriptor(real_stub.adapter_descriptor)


def test_l4_phase3_fake_adapter_never_production_invariant_detects_bad_descriptor():
    invariant = FakeAdapterNeverProductionInvariant(phase3_ref(81, "adapter_invariant"))
    fake = FakeActionAdapter()
    bad_descriptor = replace(fake.adapter_descriptor, production_enabled=True)
    assert invariant.is_satisfied_by_descriptor(fake.adapter_descriptor)
    assert invariant.is_satisfied_by_descriptor(bad_descriptor) is False


def test_l4_phase3_plain_credential_and_l3_bypass_are_blocked_at_envelope_boundary():
    credential_invariant = AdapterCannotHoldPlainCredentialInvariant(phase3_ref(82, "adapter_invariant"))
    l3_invariant = AdapterCannotBypassL3Invariant(phase3_ref(83, "adapter_invariant"))
    safe = envelope(mode=AdapterMode.NO_OP)
    assert credential_invariant.is_satisfied_by_envelope(safe)
    assert l3_invariant.is_satisfied_by_envelope(safe)
    with pytest.raises(ValueError):
        AdapterInputEnvelope(envelope_ref=phase3_ref(84, "adapter_input"), action_kind="generic_action", contains_plain_credential=True)
    with pytest.raises(ValueError):
        AdapterInputEnvelope(envelope_ref=phase3_ref(85, "adapter_input"), action_kind="generic_action", l3_controlled=False)


def test_l4_phase3_l5_and_l6_invariants_are_declared():
    l5_invariant = AdapterCannotBypassL5Invariant(phase3_ref(86, "adapter_invariant"))
    l6_invariant = AdapterCannotImplementL6SubsystemInvariant(phase3_ref(87, "adapter_invariant"))
    assert l5_invariant.is_satisfied_by_descriptor(RealActionAdapterStub().adapter_descriptor)
    assert l6_invariant.implements_l6_subsystem is False
    with pytest.raises(ValueError):
        AdapterCannotImplementL6SubsystemInvariant(phase3_ref(88, "adapter_invariant"), implements_l6_subsystem=True)
