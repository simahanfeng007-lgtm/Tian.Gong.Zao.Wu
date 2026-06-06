from tiangong_kernel.l5_plugin_host import L5Phase3RegressionEvidenceIndex


def test_regression_evidence_index_tracks_phase1_phase2():
    index = L5Phase3RegressionEvidenceIndex(
        index_ref="regression:l5_phase3",
        l0_l4_regression_summary="clean",
        l5_phase1_modified_refs=("tiangong_kernel/l5_plugin_host/registry_snapshot.py",),
        l5_phase2_modified_refs=("tiangong_kernel/l5_plugin_host/__init__.py",),
        evidence_refs=("evidence:regression",),
    )
    assert index.no_live_action_preserved
    assert index.l5_phase1_modified_refs
