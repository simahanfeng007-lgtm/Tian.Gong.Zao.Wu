def test_l2_phase1_package_and_modules_importable():
    import tiangong_kernel.l2_state as l2_state
    from tiangong_kernel.l2_state import base_state
    from tiangong_kernel.l2_state import state_boundary
    from tiangong_kernel.l2_state import state_delta
    from tiangong_kernel.l2_state import state_identity
    from tiangong_kernel.l2_state import state_invariant
    from tiangong_kernel.l2_state import state_snapshot
    from tiangong_kernel.l2_state import state_status

    assert l2_state.L2_STATE_SCHEMA_VERSION == "0.1"
    assert base_state.L2StateRecord
    assert state_identity.L2StateIdentity
    assert state_status.L2StateStatus
    assert state_boundary.L2StateBoundary
    assert state_snapshot.L2StateSnapshot
    assert state_delta.L2StateDelta
    assert state_invariant.L2StateInvariant


def test_l2_phase1_public_exports_are_stable():
    import tiangong_kernel.l2_state as l2_state

    expected = {
        "L2_STATE_SCHEMA_VERSION",
        "L2BoundaryStatusKind",
        "L2DeltaEntry",
        "L2DeltaKind",
        "L2InvariantCheck",
        "L2InvariantStatusKind",
        "L2SnapshotSummary",
        "L2StateBoundary",
        "L2StateDelta",
        "L2StateIdentity",
        "L2StateInvariant",
        "L2StateKind",
        "L2StateMetadata",
        "L2StateRecord",
        "L2StateSnapshot",
        "L2StateStatus",
        "L2StateStatusKind",
    }
    assert expected <= set(l2_state.__all__)
