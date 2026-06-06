import inspect
from dataclasses import is_dataclass
from typing import get_origin, get_type_hints

from tiangong_kernel.l0_primitives.result import CoreResult
from tiangong_kernel.l1_ports.port_result import PortResult
import tiangong_kernel.l1_ports.infrastructure_ports as ports


PORT_CLASSES = [
    ports.ClockPort,
    ports.IdGeneratorPort,
    ports.SerializationPort,
    ports.HashPort,
    ports.LoggerPort,
]
REQUEST_RESPONSE_BOUNDARY_CLASSES = [
    ports.InfrastructurePortBoundary,
    ports.ClockQueryRequest,
    ports.ClockQueryResponse,
    ports.IdGenerationRequest,
    ports.IdGenerationResponse,
    ports.SerializationRequest,
    ports.SerializationResponse,
    ports.DeserializationRequest,
    ports.DeserializationResponse,
    ports.HashRequest,
    ports.HashResponse,
    ports.LogSubmitRequest,
    ports.LogSubmitResponse,
]


def _return_is_result(method):
    hint = get_type_hints(method)["return"]
    return get_origin(hint) in {CoreResult, PortResult}


def test_phase2_infrastructure_ports_are_abstract():
    for port_cls in PORT_CLASSES:
        assert inspect.isabstract(port_cls)
        assert port_cls.__name__.endswith("Port")


def test_phase2_infrastructure_methods_return_result_wrappers():
    for port_cls in PORT_CLASSES:
        for method_name in port_cls.__abstractmethods__:
            assert _return_is_result(getattr(port_cls, method_name))


def test_phase2_infrastructure_data_objects_are_frozen_slots_dataclasses():
    for cls in REQUEST_RESPONSE_BOUNDARY_CLASSES:
        assert is_dataclass(cls)
        assert cls.__dataclass_params__.frozen is True
        assert hasattr(cls, "__slots__")


def test_phase2_infrastructure_uses_l0_refs_and_trace():
    hints = get_type_hints(ports.ClockPort.query_time)
    assert hints["request"] is ports.ClockQueryRequest
    assert hints["trace"].__name__ == "TraceContext"
    assert get_origin(hints["return"]) is PortResult
