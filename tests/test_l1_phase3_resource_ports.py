import inspect
from dataclasses import is_dataclass
from typing import get_origin, get_type_hints

from tiangong_kernel.l0_primitives.cost_budget import BudgetRef, QuotaRef, RateLimitRef
from tiangong_kernel.l0_primitives.resource import ResourceRef
from tiangong_kernel.l0_primitives.result import CoreResult
from tiangong_kernel.l1_ports.port_result import PortResult
import tiangong_kernel.l1_ports.resource_ports as ports


PORT_CLASSES = [
    ports.ResourcePort,
    ports.BudgetPort,
    ports.QuotaPort,
    ports.RateLimitPort,
    ports.ResourceReservationPort,
]
DATA_CLASSES = [
    ports.ResourcePortBoundary,
    ports.ResourceDeclareRequest,
    ports.ResourceDeclareResponse,
    ports.BudgetCheckRequest,
    ports.BudgetCheckResponse,
    ports.QuotaCheckRequest,
    ports.QuotaCheckResponse,
    ports.RateLimitCheckRequest,
    ports.RateLimitCheckResponse,
    ports.ResourceReservationRequest,
    ports.ResourceReservationResponse,
]


def _return_is_result(method):
    hint = get_type_hints(method)["return"]
    return get_origin(hint) in {CoreResult, PortResult}


def test_phase3_resource_ports_are_abstract():
    for port_cls in PORT_CLASSES:
        assert inspect.isabstract(port_cls)
        assert port_cls.__name__.endswith("Port")


def test_phase3_resource_methods_return_result_wrappers():
    for port_cls in PORT_CLASSES:
        for method_name in port_cls.__abstractmethods__:
            assert _return_is_result(getattr(port_cls, method_name))


def test_phase3_resource_data_objects_are_frozen_slots_dataclasses():
    for cls in DATA_CLASSES:
        assert is_dataclass(cls)
        assert cls.__dataclass_params__.frozen is True
        assert hasattr(cls, "__slots__")


def test_phase3_resource_requests_use_l0_resource_budget_objects():
    assert get_type_hints(ports.ResourceDeclareRequest)["resource_ref"] is ResourceRef
    assert get_type_hints(ports.BudgetCheckRequest)["budget_ref"] is BudgetRef
    assert get_type_hints(ports.QuotaCheckRequest)["quota_ref"] is QuotaRef
    assert get_type_hints(ports.RateLimitCheckRequest)["rate_limit_ref"] is RateLimitRef
