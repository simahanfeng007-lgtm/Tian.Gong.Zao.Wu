import inspect
from dataclasses import is_dataclass
from pathlib import Path
from typing import get_origin, get_type_hints

from tiangong_kernel.l0_primitives.context import ContextBoundary, ContextRef, ContextWindow
from tiangong_kernel.l0_primitives.result import CoreResult
from tiangong_kernel.l1_ports.model_ports import ModelContextView
from tiangong_kernel.l1_ports.port_result import PortResult
import tiangong_kernel.l1_ports.context_ports as ports

PORT_CLASSES = [ports.ContextReferencePort, ports.ContextWindowPort, ports.ContextAssemblyIntentPort, ports.ContextBoundaryPort, ports.ContextCompressionHintPort, ports.ContextCarryoverPort]
DATA_CLASSES = [ports.ContextReference, ports.ContextWindowBoundary, ports.ContextAssemblyIntent, ports.ContextUsageBoundary, ports.ContextCompressionHint, ports.ContextCarryover, ports.ContextReferenceRequest, ports.ContextReferenceResponse, ports.ContextWindowRequest, ports.ContextWindowResponse, ports.ContextAssemblyIntentRequest, ports.ContextAssemblyIntentResponse, ports.ContextBoundaryRequest, ports.ContextBoundaryResponse, ports.ContextCompressionHintRequest, ports.ContextCompressionHintResponse, ports.ContextCarryoverRequest, ports.ContextCarryoverResponse]

def _return_is_result(method):
    return get_origin(get_type_hints(method)["return"]) in {CoreResult, PortResult}

def test_phase7_context_ports_are_abstract():
    for port_cls in PORT_CLASSES:
        assert inspect.isabstract(port_cls)
        assert port_cls.__name__.endswith("Port")

def test_phase7_context_methods_return_result_wrappers():
    for port_cls in PORT_CLASSES:
        for method_name in port_cls.__abstractmethods__:
            assert _return_is_result(getattr(port_cls, method_name))

def test_phase7_context_data_objects_are_frozen_slots_dataclasses():
    for cls in DATA_CLASSES:
        assert is_dataclass(cls)
        assert cls.__dataclass_params__.frozen is True
        assert hasattr(cls, "__slots__")

def test_phase7_context_reuses_l0_context_and_phase6_model_context_view():
    assert get_type_hints(ports.ContextReference)["context_ref"] is ContextRef
    assert get_type_hints(ports.ContextWindowBoundary)["boundary"] == ContextBoundary | None
    assert get_type_hints(ports.ContextUsageBoundary)["boundary"] == ContextBoundary | None
    assert get_type_hints(ports.ContextAssemblyIntent)["model_context_view"] == ModelContextView | None

def test_phase7_context_ports_do_not_perform_real_context_assembly():
    text = Path(ports.__file__).read_text(encoding="utf-8")
    forbidden = ["open(", "read_text(", "write_text(", "ContextService", "RetrievalEngine", "CapabilityPort", "AbilityPackagePort"]
    assert [item for item in forbidden if item in text] == []
