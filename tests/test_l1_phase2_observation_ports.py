import inspect
from dataclasses import is_dataclass
from typing import get_origin, get_type_hints

from tiangong_kernel.l0_primitives.observation import ObservationRef
from tiangong_kernel.l0_primitives.result import CoreResult
from tiangong_kernel.l0_primitives.signal import SignalRef
from tiangong_kernel.l1_ports.port_result import PortResult
import tiangong_kernel.l1_ports.observation_ports as ports


PORT_CLASSES = [
    ports.ObservationSubmitPort,
    ports.ObservationReadPort,
    ports.SignalPort,
    ports.TelemetryPort,
]
DATA_CLASSES = [
    ports.ObservationPortBoundary,
    ports.ObservationSubmitRequest,
    ports.ObservationSubmitResponse,
    ports.ObservationReadRequest,
    ports.ObservationReadResponse,
    ports.SignalSendRequest,
    ports.SignalSendResponse,
    ports.SignalReceiveRequest,
    ports.SignalReceiveResponse,
    ports.TelemetrySubmitRequest,
    ports.TelemetrySubmitResponse,
]


def _return_is_result(method):
    hint = get_type_hints(method)["return"]
    return get_origin(hint) in {CoreResult, PortResult}


def test_phase2_observation_ports_are_abstract():
    for port_cls in PORT_CLASSES:
        assert inspect.isabstract(port_cls)
        assert port_cls.__name__.endswith("Port")


def test_phase2_observation_methods_return_result_wrappers():
    for port_cls in PORT_CLASSES:
        for method_name in port_cls.__abstractmethods__:
            assert _return_is_result(getattr(port_cls, method_name))


def test_phase2_observation_data_objects_are_frozen_slots_dataclasses():
    for cls in DATA_CLASSES:
        assert is_dataclass(cls)
        assert cls.__dataclass_params__.frozen is True
        assert hasattr(cls, "__slots__")


def test_phase2_observation_and_signal_requests_use_l0_refs():
    obs_hints = get_type_hints(ports.ObservationSubmitRequest)
    sig_hints = get_type_hints(ports.SignalSendRequest)
    assert obs_hints["observation_ref"] is ObservationRef
    assert sig_hints["signal_ref"] is SignalRef
