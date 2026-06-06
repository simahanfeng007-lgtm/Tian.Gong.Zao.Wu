import tiangong_kernel.l0_primitives.namespace as module
from phase8_helpers import assert_enum_values, assert_module_dataclasses
from tiangong_kernel.l0_primitives.namespace import NamespaceKind, RegistryKind, NameState


def test_l0_namespace_objects_construct_freeze_serialize_hash_and_enum_values():
    assert_module_dataclasses(module)
    assert_enum_values(NamespaceKind, {'CORE': 'core', 'EXTERNAL': 'external'})
    assert_enum_values(RegistryKind, {'TYPE_REGISTRY': 'type_registry', 'RESOURCE_REGISTRY': 'resource_registry'})
    assert_enum_values(NameState, {'RESERVED': 'reserved', 'ARCHIVED': 'archived'})
