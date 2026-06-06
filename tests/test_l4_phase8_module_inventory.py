import pytest

from l4_phase8_builders import module_inventory, phase8_ref
from tiangong_kernel.l4_execution import L4ModuleInventory


def test_l4_phase8_module_inventory_is_static_only():
    inventory = module_inventory()
    phases = {phase for phase, _, _ in inventory.module_items}

    assert "phase1_base" in phases
    assert "phase8_closure" in phases
    assert inventory.inventory_only is True
    assert inventory.creates_runtime_registry is False
    assert inventory.loads_plugins is False
    assert inventory.schedules_components is False


def test_l4_phase8_module_inventory_rejects_runtime_registry_flags():
    with pytest.raises(ValueError):
        L4ModuleInventory(inventory_ref=phase8_ref(100, "inventory"), creates_runtime_registry=True)
