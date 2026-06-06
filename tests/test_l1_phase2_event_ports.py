import inspect
from dataclasses import is_dataclass
from typing import get_origin, get_type_hints

from tiangong_kernel.l0_primitives.event import CoreEvent, EventRef
from tiangong_kernel.l0_primitives.result import CoreResult
from tiangong_kernel.l1_ports.port_result import PortResult
import tiangong_kernel.l1_ports.event_ports as ports


PORT_CLASSES = [
    ports.EventAppendPort,
    ports.EventReadPort,
    ports.EventStreamPort,
    ports.EventQueryPort,
]
DATA_CLASSES = [
    ports.EventPortBoundary,
    ports.EventAppendRequest,
    ports.EventAppendResponse,
    ports.EventReadRequest,
    ports.EventReadResponse,
    ports.EventStreamRequest,
    ports.EventStreamResponse,
    ports.EventQueryRequest,
    ports.EventQueryResponse,
]


def _return_is_result(method):
    hint = get_type_hints(method)["return"]
    return get_origin(hint) in {CoreResult, PortResult}


def test_phase2_event_ports_are_abstract():
    for port_cls in PORT_CLASSES:
        assert inspect.isabstract(port_cls)
        assert port_cls.__name__.endswith("Port")


def test_phase2_event_methods_return_result_wrappers():
    for port_cls in PORT_CLASSES:
        for method_name in port_cls.__abstractmethods__:
            assert _return_is_result(getattr(port_cls, method_name))


def test_phase2_event_data_objects_are_frozen_slots_dataclasses():
    for cls in DATA_CLASSES:
        assert is_dataclass(cls)
        assert cls.__dataclass_params__.frozen is True
        assert hasattr(cls, "__slots__")


def test_phase2_event_requests_use_l0_event_objects():
    hints = get_type_hints(ports.EventAppendRequest)
    assert hints["event"] is CoreEvent
    response_hints = get_type_hints(ports.EventAppendResponse)
    assert response_hints["event_ref"] is EventRef
