from dataclasses import FrozenInstanceError

from tiangong_kernel.l0_primitives.identity import RefId
from tiangong_kernel.l0_primitives.scope import BoundaryRef, CoreScope, ScopeBoundary, ScopeKind, ScopeRef
from tiangong_kernel.l0_primitives.serialization import stable_hash, stable_json_dumps


def test_scope_objects_construction_immutability_serialization_hash_and_enum_values():
    scope_ref = ScopeRef(RefId("scope:" + "2" * 32), ScopeKind.RUN)
    boundary_ref = BoundaryRef(RefId("boundary:" + "3" * 32), "run_boundary")
    boundary = ScopeBoundary(boundary_ref, scope_ref, "main")
    item = CoreScope(scope_ref, ScopeKind.RUN, boundary_refs=(boundary_ref,))
    assert boundary.scope_ref == scope_ref
    try:
        item.kind = ScopeKind.GLOBAL
    except FrozenInstanceError:
        pass
    else:
        raise AssertionError("CoreScope allowed mutation")
    assert '"kind":"run"' in stable_json_dumps(item)
    assert len(stable_hash((boundary, item))) == 64
    assert [member.value for member in ScopeKind] == [
        "global",
        "workspace",
        "session",
        "run",
        "step",
        "actor",
        "resource",
        "environment",
        "unknown",
    ]
