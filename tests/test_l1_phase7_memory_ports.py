import inspect
from dataclasses import is_dataclass
from pathlib import Path
from typing import get_origin, get_type_hints

from tiangong_kernel.l0_primitives.content import ContentRef
from tiangong_kernel.l0_primitives.memory import MemoryRef, MemoryTraceRef
from tiangong_kernel.l0_primitives.result import CoreResult
from tiangong_kernel.l1_ports.port_result import PortResult
import tiangong_kernel.l1_ports.memory_ports as ports

PORT_CLASSES = [ports.MemoryReferencePort, ports.MemoryWriteIntentPort, ports.MemoryReadIntentPort, ports.MemoryTracePort, ports.MemoryPromotionHintPort, ports.MemoryRetentionBoundaryPort, ports.ForgettingIntentPort]
DATA_CLASSES = [ports.MemoryReference, ports.MemoryWriteIntent, ports.MemoryReadIntent, ports.MemoryTraceBinding, ports.MemoryPromotionHint, ports.MemoryRetentionBoundary, ports.ForgettingIntent, ports.MemoryReferenceRequest, ports.MemoryReferenceResponse, ports.MemoryWriteIntentRequest, ports.MemoryWriteIntentResponse, ports.MemoryReadIntentRequest, ports.MemoryReadIntentResponse, ports.MemoryTraceRequest, ports.MemoryTraceResponse, ports.MemoryPromotionHintRequest, ports.MemoryPromotionHintResponse, ports.MemoryRetentionBoundaryRequest, ports.MemoryRetentionBoundaryResponse, ports.ForgettingIntentRequest, ports.ForgettingIntentResponse]


def _return_is_result(method):
    hint = get_type_hints(method)["return"]
    return get_origin(hint) in {CoreResult, PortResult}


def test_phase7_memory_ports_are_abstract():
    for port_cls in PORT_CLASSES:
        assert inspect.isabstract(port_cls)
        assert port_cls.__name__.endswith("Port")


def test_phase7_memory_methods_return_result_wrappers():
    for port_cls in PORT_CLASSES:
        for method_name in port_cls.__abstractmethods__:
            assert _return_is_result(getattr(port_cls, method_name))


def test_phase7_memory_data_objects_are_frozen_slots_dataclasses():
    for cls in DATA_CLASSES:
        assert is_dataclass(cls)
        assert cls.__dataclass_params__.frozen is True
        assert hasattr(cls, "__slots__")


def test_phase7_memory_reuses_l0_memory_and_content_refs():
    assert get_type_hints(ports.MemoryReference)["memory_ref"] is MemoryRef
    assert get_type_hints(ports.MemoryReference)["content_ref"] == ContentRef | None
    assert get_type_hints(ports.MemoryTraceBinding)["trace_ref"] is MemoryTraceRef
    assert get_type_hints(ports.ForgettingIntent)["memory_ref"] == MemoryRef | None


def test_phase7_memory_ports_do_not_perform_real_memory_actions():
    text = Path(ports.__file__).read_text(encoding="utf-8")
    forbidden = ["open(", "read_text(", "write_text(", "sqlite3", "requests", "MemoryManager", "CapabilityPort", "AbilityPackagePort"]
    assert [item for item in forbidden if item in text] == []
