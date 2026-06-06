import inspect
from dataclasses import is_dataclass
from pathlib import Path
from typing import get_origin, get_type_hints

from tiangong_kernel.l0_primitives.resource import ResourceRef
from tiangong_kernel.l0_primitives.result import CoreResult
from tiangong_kernel.l0_primitives.retrieval import QueryRef, RetrievalEvidenceRef, RetrievalRef, RetrievalResultRef
from tiangong_kernel.l1_ports.port_result import PortResult
import tiangong_kernel.l1_ports.retrieval_ports as ports

PORT_CLASSES = [ports.RetrievalIntentPort, ports.RetrievalQueryPort, ports.RetrievalResultPort, ports.RetrievalEvidencePort, ports.RetrievalBoundaryPort, ports.RetrievalFeedbackPort]
DATA_CLASSES = [ports.RetrievalIntent, ports.RetrievalQuery, ports.RetrievalResult, ports.RetrievalEvidenceBinding, ports.RetrievalBoundary, ports.RetrievalFeedback, ports.RetrievalIntentRequest, ports.RetrievalIntentResponse, ports.RetrievalQueryRequest, ports.RetrievalQueryResponse, ports.RetrievalResultRequest, ports.RetrievalResultResponse, ports.RetrievalEvidenceRequest, ports.RetrievalEvidenceResponse, ports.RetrievalBoundaryRequest, ports.RetrievalBoundaryResponse, ports.RetrievalFeedbackRequest, ports.RetrievalFeedbackResponse]

def _return_is_result(method):
    return get_origin(get_type_hints(method)["return"]) in {CoreResult, PortResult}

def test_phase7_retrieval_ports_are_abstract():
    for port_cls in PORT_CLASSES:
        assert inspect.isabstract(port_cls)
        assert port_cls.__name__.endswith("Port")

def test_phase7_retrieval_methods_return_result_wrappers():
    for port_cls in PORT_CLASSES:
        for method_name in port_cls.__abstractmethods__:
            assert _return_is_result(getattr(port_cls, method_name))

def test_phase7_retrieval_data_objects_are_frozen_slots_dataclasses():
    for cls in DATA_CLASSES:
        assert is_dataclass(cls)
        assert cls.__dataclass_params__.frozen is True
        assert hasattr(cls, "__slots__")

def test_phase7_retrieval_reuses_l0_retrieval_refs():
    assert get_type_hints(ports.RetrievalIntent)["intent_ref"] is ResourceRef
    assert get_type_hints(ports.RetrievalQuery)["query_ref"] is QueryRef
    assert get_type_hints(ports.RetrievalResult)["result_ref"] is RetrievalResultRef
    assert get_type_hints(ports.RetrievalEvidenceBinding)["retrieval_evidence_ref"] is RetrievalEvidenceRef

def test_phase7_retrieval_ports_do_not_perform_real_search_or_rag():
    text = Path(ports.__file__).read_text(encoding="utf-8")
    forbidden = ["open(", "read_text(", "write_text(", "requests", "sqlite3", "RetrievalEngine", "CapabilityPort", "AbilityPackagePort"]
    assert [item for item in forbidden if item in text] == []
