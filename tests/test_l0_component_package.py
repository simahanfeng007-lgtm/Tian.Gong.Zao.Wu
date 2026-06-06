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

from tiangong_kernel.l0_primitives.component_package import ComponentRef, ComponentKind, ComponentState, ModuleRef, ModuleKind, ModuleState, PackageRef, PackageKind, PackageState, PackageDigest, PackageVersionRef, ComponentInterfaceRef, ComponentBoundaryRef

def test_component_package_objects_construct_freeze_serialize_hash_and_enum_values():
    digest = PackageDigest("abc")
    boundary = ComponentBoundaryRef(rid())
    interface = ComponentInterfaceRef(rid())
    component = ComponentRef(rid(), ComponentKind.CORE_COMPONENT, ComponentState.AVAILABLE, boundary)
    module = ModuleRef(rid(), ModuleKind.PYTHON_MODULE, ModuleState.REGISTERED, component)
    version = PackageVersionRef(rid())
    package = PackageRef(rid(), PackageKind.CORE_PACKAGE, PackageState.AVAILABLE, digest, version, (module,))
    assert ComponentKind.UI_COMPONENT.value == "ui_component"
    assert ModuleKind.DOCUMENTATION_MODULE.value == "documentation_module"
    assert PackageKind.DISTRIBUTION_PACKAGE.value == "distribution_package"
    for obj in (digest, boundary, interface, component, module, version, package):
        assert_frozen(obj); assert_stable(obj)
