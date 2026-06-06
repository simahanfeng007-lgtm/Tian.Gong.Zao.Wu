from tiangong_kernel.l6_plugins.final_closure import L6StageInventory

def test_stage_inventory_complete():
    inv = L6StageInventory()
    assert inv.phase_count == 7
    assert len(inv.phase_refs) == 7
    assert inv.freeze_candidate_flag is True
