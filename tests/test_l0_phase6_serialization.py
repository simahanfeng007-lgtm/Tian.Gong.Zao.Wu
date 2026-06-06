from tiangong_kernel.l0_primitives.autonomy import AutonomyLevel, ControlModeRef
from tiangong_kernel.l0_primitives.contract import ContractKind, ContractRef
from tiangong_kernel.l0_primitives.identity import RefId
from tiangong_kernel.l0_primitives.instruction import InstructionKind, InstructionRef
from tiangong_kernel.l0_primitives.policy import PolicyKind, PolicyRef
from tiangong_kernel.l0_primitives.privacy import DataClass, PrivacyRef
from tiangong_kernel.l0_primitives.secret import SecretKind, SecretRef
from tiangong_kernel.l0_primitives.serialization import stable_json_dumps
from tiangong_kernel.l0_primitives.trust import TrustBoundaryKind, TrustBoundaryRef
from tiangong_kernel.l0_primitives.value import ValueKind, ValueRef

def rid(prefix: str = "ref") -> RefId:
    return RefId(f"{prefix}:" + "8" * 32)

def test_phase6_objects_have_stable_json():
    objects = (
        TrustBoundaryRef(rid(), TrustBoundaryKind.SANDBOX),
        PrivacyRef(rid(), DataClass.PERSONAL),
        SecretRef(rid(), SecretKind.API_KEY),
        ContractRef(rid(), ContractKind.SECURITY),
        PolicyRef(rid(), PolicyKind.PRIVACY),
        InstructionRef(rid(), InstructionKind.USER_REQUEST),
        ControlModeRef(rid(), AutonomyLevel.L2_ADVISE),
        ValueRef(rid(), ValueKind.SAFETY),
    )
    for obj in objects:
        first = stable_json_dumps(obj)
        second = stable_json_dumps(obj)
        assert first == second
        assert "schema_version" in first
