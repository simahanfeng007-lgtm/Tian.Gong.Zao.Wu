import tiangong_kernel.l0_primitives.relation as module
from phase8_helpers import assert_enum_values, assert_module_dataclasses
from tiangong_kernel.l0_primitives.relation import RelationKind, RelationDirection, RelationState, DependencyKind, DependencyState


def test_l0_relation_objects_construct_freeze_serialize_hash_and_enum_values():
    assert_module_dataclasses(module)
    assert_enum_values(RelationKind, {'USES': 'uses', 'INVALIDATES': 'invalidates'})
    assert_enum_values(RelationDirection, {'DIRECTED': 'directed', 'UNDIRECTED': 'undirected'})
    assert_enum_values(RelationState, {'PROPOSED': 'proposed', 'ARCHIVED': 'archived'})
    assert_enum_values(DependencyKind, {'RUNTIME': 'runtime', 'TRUST': 'trust'})
    assert_enum_values(DependencyState, {'ACTIVE': 'active', 'REVOKED': 'revoked'})
