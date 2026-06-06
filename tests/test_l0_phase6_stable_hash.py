from tiangong_kernel.l0_primitives.autonomy import ControlModeRef
from tiangong_kernel.l0_primitives.contract import ContractRef
from tiangong_kernel.l0_primitives.identity import RefId
from tiangong_kernel.l0_primitives.instruction import InstructionRef
from tiangong_kernel.l0_primitives.policy import PolicyRef
from tiangong_kernel.l0_primitives.privacy import PrivacyRef
from tiangong_kernel.l0_primitives.secret import SecretRef
from tiangong_kernel.l0_primitives.serialization import stable_hash
from tiangong_kernel.l0_primitives.trust import TrustBoundaryRef
from tiangong_kernel.l0_primitives.value import ValueRef

def rid(prefix: str = "ref") -> RefId:
    return RefId(f"{prefix}:" + "9" * 32)

def test_phase6_objects_have_stable_hash():
    objects = (TrustBoundaryRef(rid()), PrivacyRef(rid()), SecretRef(rid()), ContractRef(rid()), PolicyRef(rid()), InstructionRef(rid()), ControlModeRef(rid()), ValueRef(rid()))
    for obj in objects:
        digest = stable_hash(obj)
        assert digest == stable_hash(obj)
        assert len(digest) == 64
