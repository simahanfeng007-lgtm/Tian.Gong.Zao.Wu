from tiangong_kernel.l5_plugin_host import L5Phase1InvariantSuite, L5PublicExportMap, evaluate_phase1_responsibility_fields


def test_requirement_traceability_has_minimum_phase1_invariant_coverage():
    suite = L5Phase1InvariantSuite(
        suite_ref="invariant_suite:phase1",
        evidence_refs=("evidence:tests",),
        summary="覆盖宿主底座、数据壳、handoff refs、越界禁令、导出、序列化。",
    )
    required = set(suite.required_invariants)
    assert "manifest_view_is_data_only" in required
    assert "registry_snapshot_is_immutable" in required
    assert "no_live_external_action" in required
    assert "audit_evidence_refs_only" in required


def test_responsibility_readiness_blocks_when_required_refs_missing():
    readiness = evaluate_phase1_responsibility_fields(
        readiness_ref="readiness:missing",
        observed_fields=("actor_ref", "scope_ref"),
        evidence_refs=("evidence:readiness",),
    )
    assert readiness.complete is False
    assert "trace_ref" in readiness.missing_fields


def test_public_export_map_can_hold_requirement_surface_refs():
    export_map = L5PublicExportMap(
        export_map_ref="export_map:requirements",
        safe_exports=("PluginManifestView", "PluginRegistrySnapshot", "PluginHostReadinessSummary"),
        blocked_exports=("plugin_loader",),
    )
    assert "plugin_loader" in export_map.blocked_exports
