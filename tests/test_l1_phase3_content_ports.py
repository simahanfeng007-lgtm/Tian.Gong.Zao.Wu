import inspect
from dataclasses import is_dataclass
from typing import get_origin, get_type_hints

from tiangong_kernel.l0_primitives.artifact import ArtifactRef
from tiangong_kernel.l0_primitives.content import ContentRef, PayloadRef
from tiangong_kernel.l0_primitives.evidence import EvidenceRef
from tiangong_kernel.l0_primitives.result import CoreResult
from tiangong_kernel.l1_ports.port_result import PortResult
import tiangong_kernel.l1_ports.content_ports as ports


PORT_CLASSES = [
    ports.ContentStorePort,
    ports.ContentReadPort,
    ports.ContentWriteIntentPort,
    ports.PayloadPort,
    ports.ArtifactPort,
    ports.EvidencePort,
]
DATA_CLASSES = [
    ports.ContentPortBoundary,
    ports.ContentStoreRequest,
    ports.ContentStoreResponse,
    ports.ContentReadRequest,
    ports.ContentReadResponse,
    ports.ContentWriteIntentRequest,
    ports.ContentWriteIntentResponse,
    ports.PayloadDeclareRequest,
    ports.PayloadDeclareResponse,
    ports.ArtifactRegisterRequest,
    ports.ArtifactRegisterResponse,
    ports.EvidenceBindRequest,
    ports.EvidenceBindResponse,
]


def _return_is_result(method):
    hint = get_type_hints(method)["return"]
    return get_origin(hint) in {CoreResult, PortResult}


def test_phase3_content_ports_are_abstract():
    for port_cls in PORT_CLASSES:
        assert inspect.isabstract(port_cls)
        assert port_cls.__name__.endswith("Port")


def test_phase3_content_methods_return_result_wrappers():
    for port_cls in PORT_CLASSES:
        for method_name in port_cls.__abstractmethods__:
            assert _return_is_result(getattr(port_cls, method_name))


def test_phase3_content_data_objects_are_frozen_slots_dataclasses():
    for cls in DATA_CLASSES:
        assert is_dataclass(cls)
        assert cls.__dataclass_params__.frozen is True
        assert hasattr(cls, "__slots__")


def test_phase3_content_requests_use_l0_content_objects():
    store_hints = get_type_hints(ports.ContentStoreRequest)
    assert store_hints["content_ref"] is ContentRef
    assert get_type_hints(ports.PayloadDeclareRequest)["payload_ref"] is PayloadRef
    assert get_type_hints(ports.ArtifactRegisterRequest)["artifact_ref"] is ArtifactRef
    assert get_type_hints(ports.EvidenceBindRequest)["evidence_ref"] is EvidenceRef
