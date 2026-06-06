from l5_phase3_sample_factory import complete_record, complete_snapshot, registry_key
from tiangong_kernel.l5_plugin_host import PluginRegistryConflictKind, PluginRegistryNamespace, PluginRegistryValidator


def test_frozen_archive_duplicate_without_revision_distinction_reports_namespace_collision():
    first = complete_record(registry_record_ref="record:first")
    second = complete_record(registry_record_ref="record:second", registry_key=registry_key(version_ref="version:2"), manifest_hash="b"*64, manifest_digest_value="b"*64, plugin_version_ref="version:2")
    namespace = PluginRegistryNamespace(namespace_id="namespace:user_declared", namespace_kind="archive", uniqueness_policy="frozen_archive")
    report = PluginRegistryValidator(validator_ref="validator:test").validate(complete_snapshot((first, second)), (namespace,))
    assert any(c.kind is PluginRegistryConflictKind.NAMESPACE_COLLISION for c in report.conflicts)
