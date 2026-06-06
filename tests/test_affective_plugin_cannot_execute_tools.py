from dataclasses import fields

from tiangong_kernel.l5_plugin_host import AffectivePluginMountDeclaration, AffectiveL6HandoffRef, L5L6HandoffFreeze


_EXECUTABLE_FIELD_NAMES = {
    "handler",
    "endpoint",
    "callable_ref",
    "module_path",
    "import_path",
    "entry_point",
    "tool_schema",
    "function_schema",
    "plugin_instance",
}


def test_affective_plugin_cannot_execute_tools():
    mount = AffectivePluginMountDeclaration()
    field_names = {item.name for item in fields(mount)}
    assert not (_EXECUTABLE_FIELD_NAMES & field_names)
    assert mount.no_direct_tool_call_ref
    assert mount.no_direct_l4_adapter_ref
    assert mount.no_live_execution_ref


def test_affective_l6_handoff_forbids_direct_tool_or_adapter_call():
    handoff = AffectiveL6HandoffRef()
    assert "forbid:affective_direct_tool_call" in handoff.forbidden_misuse_refs
    assert "forbid:affective_direct_l4_adapter_call" in handoff.forbidden_misuse_refs
    final_handoff = L5L6HandoffFreeze()
    assert "forbid:affective_direct_tool_call" in final_handoff.l6_forbidden_misuse_refs
    assert "forbid:affective_direct_l4_adapter_call" in final_handoff.l6_forbidden_misuse_refs
