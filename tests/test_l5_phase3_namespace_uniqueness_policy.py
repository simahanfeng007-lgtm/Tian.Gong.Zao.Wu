from l5_phase3_sample_factory import complete_record, complete_snapshot, registry_key, registry_namespace
from tiangong_kernel.l5_plugin_host import PluginRegistryConflictKind, PluginRegistryValidator


def test_explicit_alias_policy_requires_alias_or_channel_for_multi_version():
    first = complete_record(registry_record_ref="record:first", alias_ref="", channel_ref="")
    second = complete_record(registry_record_ref="record:second", registry_key=registry_key(version_ref="version:2"), manifest_hash="b"*64, manifest_digest_value="b"*64, plugin_version_ref="version:2", alias_ref="", channel_ref="")
    report = PluginRegistryValidator(validator_ref="validator:test").validate(complete_snapshot((first, second)), (registry_namespace(policy="explicit_alias_required"),))
    assert any(c.kind is PluginRegistryConflictKind.DUPLICATE_PLUGIN_ID for c in report.conflicts)
