from l5_phase3_sample_factory import complete_record, complete_snapshot, registry_namespace
from tiangong_kernel.l5_plugin_host import PluginRegistryConflictKind, PluginRegistryValidator


def test_registry_record_missing_accountability_refs_blocks_quality():
    record = complete_record(actor_ref="", scope_ref="", trace_ref="", responsibility_chain_ref="", evidence_refs=tuple())
    report = PluginRegistryValidator(validator_ref="validator:test").validate(complete_snapshot((record,)), (registry_namespace(),))
    assert any(c.kind is PluginRegistryConflictKind.RESPONSIBILITY_CHAIN_CONFLICT and c.blocking for c in report.conflicts)
