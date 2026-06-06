import inspect
from dataclasses import is_dataclass
from pathlib import Path
from typing import get_origin, get_type_hints

from tiangong_kernel.l0_primitives.decision import Decision, DecisionRef
from tiangong_kernel.l0_primitives.result import CoreResult
from tiangong_kernel.l1_ports.port_result import PortResult
import tiangong_kernel.l1_ports.decision_ports as ports


PORT_CLASSES = [
    ports.DecisionReferencePort,
    ports.DecisionRecordPort,
    ports.DecisionBoundaryPort,
    ports.DecisionFeedbackPort,
]
DATA_CLASSES = [
    ports.DecisionBoundary,
    ports.DecisionReferenceRequest,
    ports.DecisionReferenceResponse,
    ports.DecisionRecordRequest,
    ports.DecisionRecordResponse,
    ports.DecisionBoundaryRequest,
    ports.DecisionBoundaryResponse,
    ports.DecisionFeedbackRequest,
    ports.DecisionFeedbackResponse,
]


def _return_is_result(method):
    hint = get_type_hints(method)["return"]
    return get_origin(hint) in {CoreResult, PortResult}


def test_phase4_decision_ports_are_abstract():
    for port_cls in PORT_CLASSES:
        assert inspect.isabstract(port_cls)
        assert port_cls.__name__.endswith("Port")


def test_phase4_decision_methods_return_result_wrappers():
    for port_cls in PORT_CLASSES:
        for method_name in port_cls.__abstractmethods__:
            assert _return_is_result(getattr(port_cls, method_name))


def test_phase4_decision_data_objects_are_frozen_slots_dataclasses():
    for cls in DATA_CLASSES:
        assert is_dataclass(cls)
        assert cls.__dataclass_params__.frozen is True
        assert hasattr(cls, "__slots__")


def test_phase4_decision_requests_reuse_l0_decision_objects():
    assert get_type_hints(ports.DecisionReferenceRequest)["decision_ref"] is DecisionRef
    assert get_type_hints(ports.DecisionRecordRequest)["decision"] is Decision
    assert get_type_hints(ports.DecisionBoundary)["decision_ref"] is DecisionRef


def test_phase4_decision_ports_do_not_define_real_decision_algorithm():
    text = Path(ports.__file__).read_text(encoding="utf-8")
    forbidden = ["decide_allow", "decide_block", "approve", "deny", "execute", "ToolExecutor"]
    assert [item for item in forbidden if item in text] == []
