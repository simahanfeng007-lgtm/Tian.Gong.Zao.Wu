import inspect
from dataclasses import is_dataclass
from typing import get_origin, get_type_hints

from tiangong_kernel.l0_primitives.environment import EnvironmentRef, SandboxRef
from tiangong_kernel.l0_primitives.location import LocationRef
from tiangong_kernel.l0_primitives.observation import ObservationRef
from tiangong_kernel.l0_primitives.result import CoreResult
from tiangong_kernel.l1_ports.port_result import PortResult
import tiangong_kernel.l1_ports.environment_ports as ports


PORT_CLASSES = [
    ports.EnvironmentPort,
    ports.SandboxPort,
    ports.LocationResolverPort,
    ports.RuntimeContextPort,
    ports.EnvironmentObservationPort,
]
DATA_CLASSES = [
    ports.EnvironmentPortBoundary,
    ports.EnvironmentDescribeRequest,
    ports.EnvironmentDescribeResponse,
    ports.SandboxBoundaryRequest,
    ports.SandboxBoundaryResponse,
    ports.LocationResolveRequest,
    ports.LocationResolveResponse,
    ports.RuntimeContextDeclareRequest,
    ports.RuntimeContextDeclareResponse,
    ports.EnvironmentObservationRequest,
    ports.EnvironmentObservationResponse,
]


def _return_is_result(method):
    hint = get_type_hints(method)["return"]
    return get_origin(hint) in {CoreResult, PortResult}


def test_phase3_environment_ports_are_abstract():
    for port_cls in PORT_CLASSES:
        assert inspect.isabstract(port_cls)
        assert port_cls.__name__.endswith("Port")


def test_phase3_environment_methods_return_result_wrappers():
    for port_cls in PORT_CLASSES:
        for method_name in port_cls.__abstractmethods__:
            assert _return_is_result(getattr(port_cls, method_name))


def test_phase3_environment_data_objects_are_frozen_slots_dataclasses():
    for cls in DATA_CLASSES:
        assert is_dataclass(cls)
        assert cls.__dataclass_params__.frozen is True
        assert hasattr(cls, "__slots__")


def test_phase3_environment_requests_use_l0_environment_objects():
    assert get_type_hints(ports.EnvironmentDescribeRequest)["environment_ref"] is EnvironmentRef
    assert get_type_hints(ports.SandboxBoundaryRequest)["sandbox_ref"] is SandboxRef
    assert get_type_hints(ports.LocationResolveRequest)["location_ref"] is LocationRef
    assert get_type_hints(ports.EnvironmentObservationRequest)["observation_ref"] is ObservationRef
