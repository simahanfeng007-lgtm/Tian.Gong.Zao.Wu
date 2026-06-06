import inspect
from dataclasses import is_dataclass
from pathlib import Path
from typing import get_origin, get_type_hints

from tiangong_kernel.l0_primitives.policy import PolicyRef
from tiangong_kernel.l0_primitives.result import CoreResult
from tiangong_kernel.l1_ports.port_result import PortResult
import tiangong_kernel.l1_ports.policy_ports as ports


PORT_CLASSES = [
    ports.PolicyReferencePort,
    ports.PolicyLookupPort,
    ports.PolicyBoundaryPort,
    ports.PolicyExplainPort,
]
DATA_CLASSES = [
    ports.PolicyBoundary,
    ports.PolicyReferenceRequest,
    ports.PolicyReferenceResponse,
    ports.PolicyLookupRequest,
    ports.PolicyLookupResponse,
    ports.PolicyBoundaryRequest,
    ports.PolicyBoundaryResponse,
    ports.PolicyExplainRequest,
    ports.PolicyExplainResponse,
]


def _return_is_result(method):
    hint = get_type_hints(method)["return"]
    return get_origin(hint) in {CoreResult, PortResult}


def test_phase4_policy_ports_are_abstract():
    for port_cls in PORT_CLASSES:
        assert inspect.isabstract(port_cls)
        assert port_cls.__name__.endswith("Port")


def test_phase4_policy_methods_return_result_wrappers():
    for port_cls in PORT_CLASSES:
        for method_name in port_cls.__abstractmethods__:
            assert _return_is_result(getattr(port_cls, method_name))


def test_phase4_policy_data_objects_are_frozen_slots_dataclasses():
    for cls in DATA_CLASSES:
        assert is_dataclass(cls)
        assert cls.__dataclass_params__.frozen is True
        assert hasattr(cls, "__slots__")


def test_phase4_policy_requests_use_l0_policy_ref():
    assert get_type_hints(ports.PolicyReferenceRequest)["policy_ref"] is PolicyRef
    assert get_type_hints(ports.PolicyBoundary)["policy_ref"] is PolicyRef
    assert get_type_hints(ports.PolicyExplainResponse)["policy_ref"] is PolicyRef


def test_phase4_policy_ports_have_no_real_policy_lookup_calls():
    text = Path(ports.__file__).read_text(encoding="utf-8")
    forbidden = ["sqlite3", "requests", "httpx", "urlopen", "open(", "read_text(", "write_text("]
    assert [item for item in forbidden if item in text] == []
