from l3_phase1_builders import typed
from l4_phase3_builders import envelope
from tiangong_kernel.l4_action_grounding import (
    ActionAdapterProtocol,
    AdapterCapabilityDescriptor,
    AdapterFailureEnvelope,
    AdapterIdentity,
    AdapterInputEnvelope,
    AdapterMode,
    AdapterOutputEnvelope,
    AdapterRiskSurfaceDescriptor,
    DryRunActionAdapter,
    NoOpActionAdapter,
    action_grounding_stable_hash,
    action_grounding_to_primitive,
)


def test_l4_phase3_adapter_protocol_is_structural():
    adapter = NoOpActionAdapter()
    assert isinstance(adapter, ActionAdapterProtocol)
    assert adapter.is_real_adapter is False
    assert adapter.is_enabled_by_default is True
    assert adapter.requires_l5_permit is False
    assert adapter.allowed_modes == (AdapterMode.NO_OP,)
    assert adapter.supports(envelope(mode=AdapterMode.NO_OP))


def test_l4_phase3_descriptor_parts_are_serializable_and_projectable():
    adapter = DryRunActionAdapter()
    descriptor = adapter.adapter_descriptor
    primitive = action_grounding_to_primitive(descriptor)
    assert primitive["identity"]["adapter_id"] == "dry_run.action_adapter"
    assert primitive["mode"] == "dry_run"
    assert action_grounding_stable_hash(descriptor)
    assert descriptor.is_structurally_complete()
    assert descriptor.capability_descriptor.structurally_supports("generic_action", "adapter_input", AdapterMode.DRY_RUN)


def test_l4_phase3_core_descriptor_objects_can_be_created():
    identity = AdapterIdentity(adapter_ref=typed(6010, "adapter"), adapter_id="x.adapter", adapter_kind="fake")
    capability = AdapterCapabilityDescriptor(
        capability_ref=typed(6011, "adapter_capability"),
        action_kinds=("generic_action",),
        supported_modes=(AdapterMode.FAKE,),
    )
    risk = AdapterRiskSurfaceDescriptor(risk_surface_ref=typed(6012, "adapter_risk"))
    assert identity.adapter_id == "x.adapter"
    assert capability.capability_only is True
    assert risk.l4_releases_risk is False


def test_l4_phase3_envelopes_are_standard_dataclasses():
    input_envelope = AdapterInputEnvelope(envelope_ref=typed(6020, "adapter_input"), action_kind="generic_action")
    output = AdapterOutputEnvelope(
        output_ref=typed(6021, "adapter_output"),
        adapter_id="no_op.action_adapter",
        adapter_kind="no_op",
        action_kind="generic_action",
        mode=AdapterMode.NO_OP,
        success=True,
    )
    failure = AdapterFailureEnvelope(
        failure_ref=typed(6022, "adapter_failure"),
        adapter_id="real_stub.action_adapter",
        adapter_kind="real_stub",
        action_kind="generic_action",
        mode=AdapterMode.REAL_STUB,
        failure_category="adapter",
        failure_code="production_disabled",
        message="disabled",
    )
    assert input_envelope.l3_controlled is True
    assert output.real_action_performed is False
    assert failure.retry_allowed_hint is False
