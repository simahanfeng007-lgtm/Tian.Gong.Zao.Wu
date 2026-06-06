from tiangong_kernel.l5_plugin_host import (
    AFFECTIVE_CAPABILITY_KIND_REFS,
    AFFECTIVE_PLUGIN_KIND_REF,
    AffectiveCapabilityDeclaration,
    AffectivePluginMountDeclaration,
    Phase7AffectivePluginMountDeclaration,
    PluginGenericHostPrecheckReport,
    PluginHostBoundaryGateValidator,
    affective_declaration_digest,
    has_affective_live_locator,
)


def test_affective_plugin_mount_is_declarative():
    mount = AffectivePluginMountDeclaration()
    assert mount.plugin_kind_ref == AFFECTIVE_PLUGIN_KIND_REF
    assert set(AFFECTIVE_CAPABILITY_KIND_REFS) <= set(mount.capability_kind_refs)
    assert mount.declaration_not_authorization_ref
    assert mount.l6_planning_only_ref
    assert mount.no_live_execution_ref
    assert not has_affective_live_locator(mount)
    assert mount.declaration_digest == affective_declaration_digest(mount, ("declaration_digest",))


def test_phase7_affective_mount_validates_as_generic_non_tool_plugin():
    mount = Phase7AffectivePluginMountDeclaration()
    report = PluginHostBoundaryGateValidator().check(mount, precheck=PluginGenericHostPrecheckReport())
    assert report.p0_count == 0
    assert report.p1_count == 0
    assert report.passed is True


def test_affective_capability_declaration_is_not_tool_plugin_pseudo_schema():
    capability = AffectiveCapabilityDeclaration()
    assert capability.plugin_kind_ref == AFFECTIVE_PLUGIN_KIND_REF
    assert "ToolPlugin" not in capability.plugin_kind_ref
    assert not hasattr(capability, "tool_schema")
    assert not hasattr(capability, "function_schema")
