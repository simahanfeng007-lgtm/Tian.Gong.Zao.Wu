import copy
from l5_phase4_helpers import valid_mount, valid_state_machine


def test_phase4_objects_are_only_read_as_data():
    sm = valid_state_machine()
    mount = valid_mount()
    before = copy.deepcopy((sm, mount))
    _ = (sm.state_machine_ref, mount.mount_decl_ref)
    assert (sm, mount) == before
