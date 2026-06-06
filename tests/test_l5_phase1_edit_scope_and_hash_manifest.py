from dataclasses import FrozenInstanceError

import pytest

from tiangong_kernel.l5_plugin_host import L5Phase1EditablePathScope, L5Phase1HashManifestRecord


def test_edit_scope_defaults_to_l5_phase1_whitelist():
    scope = L5Phase1EditablePathScope(scope_ref="edit_scope:phase1")
    assert "tiangong_kernel/l5_plugin_host/" in scope.allowed_prefixes
    assert "tests/test_l5_phase1_" in scope.allowed_prefixes
    assert "docs/l5_phase1_" in scope.allowed_prefixes
    with pytest.raises(FrozenInstanceError):
        scope.allowed_prefixes = ()


def test_hash_manifest_record_is_data_only_and_frozen():
    record = L5Phase1HashManifestRecord(
        record_ref="hash_record:l0_identity",
        path="tiangong_kernel/l0_primitives/identity.py",
        sha256="a" * 64,
        layer="L0",
        summary="开发前基线记录。",
    )
    assert record.layer == "L0"
    with pytest.raises(FrozenInstanceError):
        record.sha256 = "b" * 64
