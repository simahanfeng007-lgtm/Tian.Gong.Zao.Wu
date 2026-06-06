from dataclasses import FrozenInstanceError
import pytest
from tiangong_kernel.l0_primitives.identity import RefId
from tiangong_kernel.l0_primitives.serialization import stable_json_dumps, stable_hash

def rid(prefix: str = "ref") -> RefId:
    return RefId(f"{prefix}:" + "9" * 32)

def assert_frozen(obj):
    with pytest.raises(FrozenInstanceError):
        obj.schema_version = "x"

def assert_stable(obj):
    assert stable_json_dumps(obj) == stable_json_dumps(obj)
    assert stable_hash(obj) == stable_hash(obj)

from tiangong_kernel.l0_primitives.tool_adapter import ToolRef, AdapterRef, ToolKind, AdapterKind, ToolState, ToolVersionRef, AdapterVersionRef

def test_tool_adapter_objects_construct_freeze_serialize_hash_and_enum_values():
    tv = ToolVersionRef(rid())
    av = AdapterVersionRef(rid())
    tool = ToolRef(rid(), ToolKind.SEARCH, ToolState.AVAILABLE, tv)
    adapter = AdapterRef(rid(), AdapterKind.MCP_ADAPTER, ToolState.REGISTERED, av)
    assert ToolKind.COMPUTATION.value == "computation"
    assert AdapterKind.GATEWAY_ADAPTER.value == "gateway_adapter"
    assert ToolState.QUARANTINED.value == "quarantined"
    for obj in (tv, av, tool, adapter):
        assert_frozen(obj); assert_stable(obj)
