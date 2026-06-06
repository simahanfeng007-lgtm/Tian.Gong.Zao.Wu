from tiangong_kernel.l0_primitives.identity import RefId
from tiangong_kernel.l0_primitives.serialization import stable_json_dumps
from tiangong_kernel.l0_primitives.resource import ResourceKind, ResourceRef
from tiangong_kernel.l0_primitives.cost_budget import CostKind, CostRef
from tiangong_kernel.l0_primitives.environment import EnvironmentKind, EnvironmentRef
from tiangong_kernel.l0_primitives.location import LocationKind, LocationRef
from tiangong_kernel.l0_primitives.communication import MessageKind, MessageEnvelopeRef
from tiangong_kernel.l0_primitives.tool_adapter import ToolKind, ToolRef
from tiangong_kernel.l0_primitives.skill_capability import CapabilityKind, CapabilityRef
from tiangong_kernel.l0_primitives.component_package import PackageKind, PackageRef

def rid(prefix: str = "ref") -> RefId:
    return RefId(f"{prefix}:" + "a" * 32)

def test_phase7_objects_have_stable_json():
    objects = (
        ResourceRef(rid(), ResourceKind.ENERGY),
        CostRef(rid(), CostKind.MONEY),
        EnvironmentRef(rid(), EnvironmentKind.HOST),
        LocationRef(rid(), LocationKind.ABSTRACT),
        MessageEnvelopeRef(rid(), MessageKind.REQUEST),
        ToolRef(rid(), ToolKind.READ),
        CapabilityRef(rid(), CapabilityKind.COGNITIVE),
        PackageRef(rid(), PackageKind.CORE_PACKAGE),
    )
    for obj in objects:
        first = stable_json_dumps(obj)
        second = stable_json_dumps(obj)
        assert first == second
        assert "schema_version" in first
