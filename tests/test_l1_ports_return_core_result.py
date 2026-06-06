from typing import get_args, get_origin, get_type_hints

from tiangong_kernel.l0_primitives.result import CoreResult
from tiangong_kernel.l1_ports.base import BasePort
from tiangong_kernel.l1_ports.port_result import PortResult


def _returns_core_result(method_name: str) -> bool:
    hints = get_type_hints(getattr(BasePort, method_name))
    return_hint = hints["return"]
    return get_origin(return_hint) is CoreResult


def test_base_port_description_methods_return_core_result():
    assert _returns_core_result("describe_boundary")
    assert _returns_core_result("describe_health")
    assert _returns_core_result("describe_lifecycle")


def test_port_result_wraps_l0_core_result():
    hints = get_type_hints(PortResult)
    core_hint = hints["core_result"]
    assert get_origin(core_hint) is CoreResult
    assert get_args(core_hint) != ()
