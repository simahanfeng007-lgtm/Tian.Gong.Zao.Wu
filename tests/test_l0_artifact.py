import tiangong_kernel.l0_primitives.artifact as module
from phase8_helpers import assert_enum_values, assert_module_dataclasses
from tiangong_kernel.l0_primitives.artifact import ArtifactKind, ArtifactState


def test_l0_artifact_objects_construct_freeze_serialize_hash_and_enum_values():
    assert_module_dataclasses(module)
    assert_enum_values(ArtifactKind, {'TEXT': 'text', 'DATASET': 'dataset'})
    assert_enum_values(ArtifactState, {'OBSERVED': 'observed', 'DELETED': 'deleted'})
