import tiangong_kernel.l0_primitives.versioning as module
from phase8_helpers import assert_enum_values, assert_module_dataclasses
from tiangong_kernel.l0_primitives.versioning import MigrationKind, CompatibilityLevel, VersionState


def test_l0_versioning_objects_construct_freeze_serialize_hash_and_enum_values():
    assert_module_dataclasses(module)
    assert_enum_values(MigrationKind, {'UPCAST': 'upcast', 'DEPRECATION': 'deprecation'})
    assert_enum_values(CompatibilityLevel, {'BACKWARD_COMPATIBLE': 'backward_compatible', 'BREAKING_CHANGE': 'breaking_change'})
    assert_enum_values(VersionState, {'DRAFT': 'draft', 'MIGRATING': 'migrating'})
