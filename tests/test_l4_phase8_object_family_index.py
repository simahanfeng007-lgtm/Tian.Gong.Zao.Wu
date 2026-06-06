import pytest

from l4_phase8_builders import object_family_index, phase8_ref, public_export_map
from tiangong_kernel.l4_execution import L4ObjectFamilyIndex, L4PublicExportMap


def test_l4_phase8_object_family_and_export_maps_are_indexes_only():
    family_index = object_family_index()
    export_map = public_export_map()

    families = {name for name, _ in family_index.family_items}
    exports = {name for name, _ in export_map.export_items}

    assert "base_execution" in families
    assert "transaction_resource_concurrency_replay_refs" in families
    assert "L4ModuleInventory" in exports
    assert family_index.index_only is True
    assert family_index.duplicates_existing_objects is False
    assert family_index.mutates_previous_phase_interfaces is False
    assert export_map.map_only is True
    assert export_map.exposes_real_adapter_execution is False
    assert export_map.exposes_permission_decision is False
    assert export_map.exposes_l6_service is False


def test_l4_phase8_index_and_export_map_reject_overreach_flags():
    with pytest.raises(ValueError):
        L4ObjectFamilyIndex(object_family_index_ref=phase8_ref(110, "family_index"), duplicates_existing_objects=True)
    with pytest.raises(ValueError):
        L4PublicExportMap(export_map_ref=phase8_ref(111, "export_map"), exposes_l6_service=True)
