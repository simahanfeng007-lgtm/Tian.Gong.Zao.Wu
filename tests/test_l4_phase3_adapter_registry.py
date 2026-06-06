from dataclasses import replace

from l4_phase3_builders import phase3_ref, registry_with_default_adapters
from tiangong_kernel.l4_action_grounding import (
    AdapterFailureKind,
    AdapterRegistry,
    AdapterRegistryProjection,
    FakeActionAdapter,
    NoOpActionAdapter,
    RealActionAdapterStub,
)


def test_l4_phase3_registry_registers_safe_adapters_and_projects_snapshot():
    registry, adapters, results = registry_with_default_adapters()
    assert all(result.registered for result in results)
    snapshot = registry.snapshot(phase3_ref(10, "adapter_registry_snapshot"))
    assert len(snapshot.entries) == len(adapters)
    projection = AdapterRegistryProjection.from_snapshot(phase3_ref(11, "adapter_registry_projection"), snapshot)
    assert "real_stub.action_adapter" in projection.real_stub_adapter_ids
    assert "fake.action_adapter" in projection.test_only_adapter_ids


def test_l4_phase3_registry_rejects_duplicate_adapter_id():
    registry = AdapterRegistry(phase3_ref(20, "adapter_registry"))
    assert registry.register(NoOpActionAdapter()).registered is True
    duplicate = registry.register(NoOpActionAdapter())
    assert duplicate.registered is False
    assert duplicate.failure.failure_kind is AdapterFailureKind.DUPLICATE_ADAPTER_ID


def test_l4_phase3_registry_rejects_malformed_descriptor():
    adapter = NoOpActionAdapter()
    bad_descriptor = replace(adapter.adapter_descriptor, capability_descriptor=None)
    result = AdapterRegistry(phase3_ref(30, "adapter_registry")).register(NoOpActionAdapter(adapter_descriptor=bad_descriptor))
    assert result.registered is False
    assert result.failure.failure_kind is AdapterFailureKind.MALFORMED_DESCRIPTOR


def test_l4_phase3_registry_rejects_test_only_production_descriptor():
    adapter = FakeActionAdapter()
    bad_descriptor = replace(adapter.adapter_descriptor, production_enabled=True)
    result = AdapterRegistry(phase3_ref(40, "adapter_registry")).register(FakeActionAdapter(adapter_descriptor=bad_descriptor))
    assert result.registered is False
    assert result.failure.failure_kind is AdapterFailureKind.TEST_ONLY_MODE


def test_l4_phase3_registry_rejects_real_stub_enabled_by_default():
    adapter = RealActionAdapterStub()
    bad_descriptor = replace(adapter.adapter_descriptor, enabled_by_default=True)
    result = AdapterRegistry(phase3_ref(50, "adapter_registry")).register(RealActionAdapterStub(adapter_descriptor=bad_descriptor))
    assert result.registered is False
    assert result.failure.failure_kind is AdapterFailureKind.DISABLED_BY_DEFAULT
