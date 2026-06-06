import inspect
from dataclasses import is_dataclass
from typing import get_origin, get_type_hints

from tiangong_kernel.l0_primitives.audit import AuditRef
from tiangong_kernel.l0_primitives.evidence import EvidenceRef
from tiangong_kernel.l0_primitives.result import CoreResult
from tiangong_kernel.l1_ports.port_result import PortResult
import tiangong_kernel.l1_ports.audit_ports as ports


PORT_CLASSES = [
    ports.AuditAppendPort,
    ports.AuditReadPort,
    ports.EvidenceAttachPort,
]
DATA_CLASSES = [
    ports.AuditPortBoundary,
    ports.AuditAppendRequest,
    ports.AuditAppendResponse,
    ports.AuditReadRequest,
    ports.AuditReadResponse,
    ports.EvidenceAttachRequest,
    ports.EvidenceAttachResponse,
]


def _return_is_result(method):
    hint = get_type_hints(method)["return"]
    return get_origin(hint) in {CoreResult, PortResult}


def test_phase2_audit_ports_are_abstract():
    for port_cls in PORT_CLASSES:
        assert inspect.isabstract(port_cls)
        assert port_cls.__name__.endswith("Port")


def test_phase2_audit_methods_return_result_wrappers():
    for port_cls in PORT_CLASSES:
        for method_name in port_cls.__abstractmethods__:
            assert _return_is_result(getattr(port_cls, method_name))


def test_phase2_audit_data_objects_are_frozen_slots_dataclasses():
    for cls in DATA_CLASSES:
        assert is_dataclass(cls)
        assert cls.__dataclass_params__.frozen is True
        assert hasattr(cls, "__slots__")


def test_phase2_audit_requests_use_l0_audit_and_evidence_refs():
    audit_hints = get_type_hints(ports.AuditAppendRequest)
    evidence_hints = get_type_hints(ports.EvidenceAttachRequest)
    assert audit_hints["audit_ref"] is AuditRef
    assert evidence_hints["evidence_ref"] is EvidenceRef
