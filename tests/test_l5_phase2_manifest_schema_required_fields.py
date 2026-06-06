from tiangong_kernel.l5_plugin_host import PHASE2_REQUIRED_MANIFEST_FIELDS, PluginManifestSchema


def test_manifest_schema_contains_core_phase2_required_fields():
    schema = PluginManifestSchema(schema_ref="schema:l5_phase2")
    required = set(schema.required_fields)
    for name in (
        "plugin_id",
        "plugin_name",
        "plugin_kind",
        "schema_version",
        "manifest_version",
        "entry_ref",
        "package_ref",
        "mount_surfaces",
        "permission_decl",
        "resource_decl",
        "credential_decl",
        "data_governance_decl",
        "audit_decl",
        "version_decl",
        "rollback_decl",
        "compatibility_decl",
        "manifest_hash",
    ):
        assert name in required
    assert tuple(schema.required_fields) == PHASE2_REQUIRED_MANIFEST_FIELDS
