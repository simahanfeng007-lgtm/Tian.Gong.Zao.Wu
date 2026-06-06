import inspect
from dataclasses import is_dataclass
from pathlib import Path
from typing import get_origin, get_type_hints

from tiangong_kernel.l0_primitives.result import CoreResult
from tiangong_kernel.l0_primitives.risk import RiskRef, RiskView
from tiangong_kernel.l1_ports.port_result import PortResult
import tiangong_kernel.l1_ports.risk_ports as ports


PORT_CLASSES = [
    ports.RiskViewPort,
    ports.RiskBoundaryPort,
    ports.RiskExplainPort,
    ports.RiskEscalationHintPort,
]
DATA_CLASSES = [
    ports.RiskBoundary,
    ports.RiskViewSubmitRequest,
    ports.RiskViewSubmitResponse,
    ports.RiskViewReadRequest,
    ports.RiskViewReadResponse,
    ports.RiskBoundaryRequest,
    ports.RiskBoundaryResponse,
    ports.RiskExplainRequest,
    ports.RiskExplainResponse,
    ports.RiskEscalationHintRequest,
    ports.RiskEscalationHintResponse,
]


def _return_is_result(method):
    hint = get_type_hints(method)["return"]
    return get_origin(hint) in {CoreResult, PortResult}


def test_phase4_risk_ports_are_abstract():
    for port_cls in PORT_CLASSES:
        assert inspect.isabstract(port_cls)
        assert port_cls.__name__.endswith("Port")


def test_phase4_risk_methods_return_result_wrappers():
    for port_cls in PORT_CLASSES:
        for method_name in port_cls.__abstractmethods__:
            assert _return_is_result(getattr(port_cls, method_name))


def test_phase4_risk_data_objects_are_frozen_slots_dataclasses():
    for cls in DATA_CLASSES:
        assert is_dataclass(cls)
        assert cls.__dataclass_params__.frozen is True
        assert hasattr(cls, "__slots__")


def test_phase4_risk_requests_reuse_l0_risk_objects():
    assert get_type_hints(ports.RiskViewSubmitRequest)["risk_view"] is RiskView
    assert get_type_hints(ports.RiskViewSubmitResponse)["risk_ref"] is RiskRef
    assert get_type_hints(ports.RiskBoundary)["risk_view"] is RiskView


def test_phase4_risk_ports_do_not_define_scoring_or_ticket_logic():
    text = Path(ports.__file__).read_text(encoding="utf-8")
    forbidden = ["score_risk", "calculate_risk", "issue_ticket", "grant_lease", "Approval"]
    assert [item for item in forbidden if item in text] == []
