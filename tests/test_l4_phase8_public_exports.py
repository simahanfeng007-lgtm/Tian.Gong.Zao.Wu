from tiangong_kernel import l4_execution
from tiangong_kernel.l4_execution import (
    L4BoundaryInvariantSuite,
    L4FinalFreezeReadinessReport,
    L4ModuleInventory,
    L4PublicExportMap,
    L4ToL5HandoffEnvelope,
    L4ToL6AdapterRequirement,
)


def test_l4_phase8_public_exports_are_importable():
    expected = {
        "L4ModuleInventory",
        "L4PublicExportMap",
        "L4BoundaryInvariantSuite",
        "L4ToL5HandoffEnvelope",
        "L4ToL6AdapterRequirement",
        "L4FinalFreezeReadinessReport",
    }

    assert expected.issubset(set(l4_execution.__all__))
    assert L4ModuleInventory is not None
    assert L4PublicExportMap is not None
    assert L4BoundaryInvariantSuite is not None
    assert L4ToL5HandoffEnvelope is not None
    assert L4ToL6AdapterRequirement is not None
    assert L4FinalFreezeReadinessReport is not None
