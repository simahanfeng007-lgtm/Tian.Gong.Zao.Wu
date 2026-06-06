from dataclasses import replace

from l3_phase1_builders import typed
from l4_phase2_builders import (
    audit_requirement,
    build_gate_input,
    credential,
    full_permit,
    granted_boundary,
    requested_scope,
    resource_limit,
    validate,
)
from tiangong_kernel.l4_action_grounding import (
    AdapterInputEnvelope,
    AdapterMode,
    AdapterRegistry,
    AdapterSelectionRequest,
    DryRunActionAdapter,
    FakeActionAdapter,
    InMemoryActionAdapter,
    NoOpActionAdapter,
    RealActionAdapterStub,
)


def phase3_ref(offset: int, ref_type: str):
    return typed(6000 + offset, ref_type)


def accepted_permit_and_gate():
    boundary = granted_boundary()
    cred = credential()
    audit = audit_requirement()
    resource = resource_limit()
    permit = full_permit(boundary=boundary, credential=cred, audit=audit, resource=resource)
    gate_result = validate(
        build_gate_input(
            permit=permit,
            boundary=boundary,
            credential=cred,
            audit=audit,
            resource=resource,
            boundary_required=True,
            credential_required=True,
            audit_required=True,
            resource_limit_required=True,
        )
    )
    return permit, gate_result


def envelope(mode=AdapterMode.NO_OP, action_kind="generic_action", permit=None, gate_result=None, production_path=False, scope=None):
    return AdapterInputEnvelope(
        envelope_ref=phase3_ref(1, "adapter_input"),
        action_kind=action_kind,
        mode=mode,
        requested_scope=scope or requested_scope(),
        permit_ref=permit,
        gate_result=gate_result,
        production_path=production_path,
    )


def selection_request(
    mode=AdapterMode.NO_OP,
    adapter_id="",
    adapter_kind="",
    gate_result=None,
    production_path=False,
    allow_fake=False,
    allow_in_memory=False,
    allow_dry_run=False,
    allow_no_op=True,
    allow_real_stub_selection=False,
    input_envelope=None,
):
    return AdapterSelectionRequest(
        selection_ref=phase3_ref(2, "adapter_selection"),
        input_envelope=input_envelope or envelope(mode=mode, gate_result=gate_result, production_path=production_path),
        requested_mode=mode,
        requested_adapter_id=adapter_id,
        requested_adapter_kind=adapter_kind,
        gate_result=gate_result,
        production_path=production_path,
        allow_fake=allow_fake,
        allow_in_memory=allow_in_memory,
        allow_dry_run=allow_dry_run,
        allow_no_op=allow_no_op,
        allow_real_stub_selection=allow_real_stub_selection,
    )


def registry_with_default_adapters():
    registry = AdapterRegistry(phase3_ref(3, "adapter_registry"))
    adapters = (
        FakeActionAdapter(),
        InMemoryActionAdapter(),
        DryRunActionAdapter(),
        NoOpActionAdapter(),
        RealActionAdapterStub(),
    )
    results = tuple(registry.register(adapter) for adapter in adapters)
    return registry, adapters, results


def no_op_requiring_l5_adapter():
    adapter = NoOpActionAdapter()
    descriptor = replace(adapter.adapter_descriptor, requires_l5_permit=True)
    return NoOpActionAdapter(adapter_descriptor=descriptor)
