from tiangong_kernel.l0_primitives.identity import RefId
from tiangong_kernel.l0_primitives.serialization import stable_hash
from tiangong_kernel.l0_primitives.resource import ResourceKind, ResourceRef
from tiangong_kernel.l0_primitives.cost_budget import CostKind, CostRef
from tiangong_kernel.l0_primitives.environment import EnvironmentKind, EnvironmentRef
from tiangong_kernel.l0_primitives.location import LocationKind, LocationRef
from tiangong_kernel.l0_primitives.communication import MessageKind, MessageEnvelopeRef
from tiangong_kernel.l0_primitives.tool_adapter import ToolKind, ToolRef
from tiangong_kernel.l0_primitives.skill_capability import CapabilityKind, CapabilityRef
from tiangong_kernel.l0_primitives.component_package import PackageKind, PackageRef

def rid(prefix: str = "ref") -> RefId:
    return RefId(f"{prefix}:" + "b" * 32)

def test_phase7_objects_have_stable_hash():
    objects = (ResourceRef(rid(), ResourceKind.TIME), CostRef(rid(), CostKind.TIME), EnvironmentRef(rid(), EnvironmentKind.DESKTOP), LocationRef(rid(), LocationKind.LOCAL), MessageEnvelopeRef(rid(), MessageKind.RESULT), ToolRef(rid(), ToolKind.SEARCH), CapabilityRef(rid(), CapabilityKind.SAFETY), PackageRef(rid(), PackageKind.SKILL_PACKAGE))
    for obj in objects:
        assert stable_hash(obj) == stable_hash(obj)
        assert len(stable_hash(obj)) == 64
