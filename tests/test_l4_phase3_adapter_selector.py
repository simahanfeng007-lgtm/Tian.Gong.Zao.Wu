from l4_phase2_builders import mismatched_scope
from l4_phase3_builders import accepted_permit_and_gate, envelope, no_op_requiring_l5_adapter, phase3_ref, registry_with_default_adapters, selection_request
from tiangong_kernel.l4_action_grounding import AdapterFailureKind, AdapterMode, AdapterRegistry, AdapterSelector


def test_l4_phase3_selector_selects_safe_modes_structurally():
    registry, _, _ = registry_with_default_adapters()
    selector = AdapterSelector()

    no_op = selector.select(selection_request(mode=AdapterMode.NO_OP, allow_no_op=True), registry)
    fake = selector.select(
        selection_request(mode=AdapterMode.FAKE, allow_fake=True, allow_no_op=False, input_envelope=envelope(mode=AdapterMode.FAKE)),
        registry,
    )
    dry_run = selector.select(
        selection_request(mode=AdapterMode.DRY_RUN, allow_dry_run=True, allow_no_op=False, input_envelope=envelope(mode=AdapterMode.DRY_RUN)),
        registry,
    )

    assert no_op.structure_selected is True
    assert fake.selected_adapter_id == "fake.action_adapter"
    assert dry_run.selected_adapter_kind == "dry_run"
    assert no_op.l4_authorized_action is False


def test_l4_phase3_selector_rejects_test_only_in_production_path():
    registry, _, _ = registry_with_default_adapters()
    request = selection_request(
        mode=AdapterMode.FAKE,
        allow_fake=True,
        allow_no_op=False,
        production_path=True,
        input_envelope=envelope(mode=AdapterMode.FAKE, production_path=True),
    )
    result = AdapterSelector().select(request, registry)
    assert result.structure_selected is False
    assert result.failure.failure_kind is AdapterFailureKind.TEST_ONLY_MODE


def test_l4_phase3_selector_rejects_l5_required_without_gate():
    registry = AdapterRegistry(phase3_ref(60, "adapter_registry"))
    registry.register(no_op_requiring_l5_adapter())
    result = AdapterSelector().select(selection_request(mode=AdapterMode.NO_OP, allow_no_op=True), registry)
    assert result.structure_selected is False
    assert result.failure.failure_kind is AdapterFailureKind.PERMIT_REQUIRED


def test_l4_phase3_selector_rejects_scope_mismatch_after_gate():
    permit, gate_result = accepted_permit_and_gate()
    registry = AdapterRegistry(phase3_ref(70, "adapter_registry"))
    registry.register(no_op_requiring_l5_adapter())
    request = selection_request(
        mode=AdapterMode.NO_OP,
        allow_no_op=True,
        gate_result=gate_result,
        input_envelope=envelope(mode=AdapterMode.NO_OP, permit=permit, gate_result=gate_result, scope=mismatched_scope()),
    )
    result = AdapterSelector().select(request, registry)
    assert result.structure_selected is False
    assert result.failure.failure_kind is AdapterFailureKind.SCOPE_MISMATCH


def test_l4_phase3_selector_never_enables_real_stub_even_with_gate():
    permit, gate_result = accepted_permit_and_gate()
    registry, _, _ = registry_with_default_adapters()
    request = selection_request(
        mode=AdapterMode.REAL_STUB,
        allow_no_op=False,
        allow_real_stub_selection=True,
        gate_result=gate_result,
        input_envelope=envelope(mode=AdapterMode.REAL_STUB, permit=permit, gate_result=gate_result),
    )
    result = AdapterSelector().select(request, registry)
    assert result.structure_selected is False
    assert result.failure.failure_kind is AdapterFailureKind.PRODUCTION_DISABLED
