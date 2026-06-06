from l5_phase4_helpers import valid_mount


def test_mount_declaration_has_no_model_or_tool_release_fields():
    mount = valid_mount()
    forbidden = ("skill_id", "tool_name", "tool_schema", "model_visible_name", "function_schema", "tool_release_ref", "execution_endpoint", "handler_name")
    assert all(not hasattr(mount, name) for name in forbidden)
