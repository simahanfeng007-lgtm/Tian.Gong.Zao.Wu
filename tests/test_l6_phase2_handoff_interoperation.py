import pytest

from tiangong_kernel.l6_plugins.common import (
    AckEnvelope,
    ActorCollaborationBoundaryContract,
    AggregationEnvelope,
    HandoffEnvelopeContract,
    InteroperationBoundaryCheck,
    NackEnvelope,
    PluginInteroperationBoundaryContract,
    ResultReturnEnvelope,
    VersionedPluginHandoffEnvelope,
)


def test_handoff_is_not_authorization_or_auto_merge_or_direct_call():
    handoff = VersionedPluginHandoffEnvelope()
    assert handoff.handoff_is_auto_merge is False
    assert handoff.handoff_is_execution_authorization is False
    assert handoff.has_quality_evidence is True
    with pytest.raises(ValueError):
        VersionedPluginHandoffEnvelope(transfers_authorization=True)
    with pytest.raises(ValueError):
        VersionedPluginHandoffEnvelope(auto_merge_allowed=True)
    with pytest.raises(ValueError):
        VersionedPluginHandoffEnvelope(direct_target_plugin_call=True)
    with pytest.raises(ValueError):
        VersionedPluginHandoffEnvelope(bypasses_l3_l5=True)
    with pytest.raises(ValueError):
        VersionedPluginHandoffEnvelope(writes_state=True)


def test_result_return_requires_parent_handoff_and_never_auto_merges():
    result = ResultReturnEnvelope(parent_handoff_ref="handoff:l6_parent")
    assert result.no_auto_merge is True
    with pytest.raises(ValueError):
        ResultReturnEnvelope(parent_handoff_ref="")
    with pytest.raises(ValueError):
        ResultReturnEnvelope(no_auto_merge=False)


def test_ack_is_receipt_only_and_nack_requires_reasoned_evidence():
    ack = AckEnvelope()
    assert ack.starts_work is False
    assert ack.means_success is False
    assert ack.grants_authorization is False
    with pytest.raises(ValueError):
        AckEnvelope(starts_work=True)
    with pytest.raises(ValueError):
        AckEnvelope(means_success=True)
    with pytest.raises(ValueError):
        AckEnvelope(grants_authorization=True)
    nack = NackEnvelope()
    assert nack.rejection_reason_ref
    assert nack.rejection_evidence_refs


def test_aggregation_and_handoff_contract_do_not_merge():
    assert AggregationEnvelope().auto_merge is False
    assert HandoffEnvelopeContract().auto_merge_allowed is False
    with pytest.raises(ValueError):
        AggregationEnvelope(auto_merge=True)
    with pytest.raises(ValueError):
        HandoffEnvelopeContract(auto_merge_allowed=True)


def test_interoperation_boundary_allows_only_envelope_modes():
    contract = PluginInteroperationBoundaryContract()
    assert contract.envelope_only is True
    assert contract.cross_plugin_direct_import_allowed is False
    assert contract.cross_plugin_direct_call_allowed is False
    assert contract.cross_plugin_state_write_allowed is False
    assert contract.parallel_runtime_allowed is False
    with pytest.raises(ValueError):
        PluginInteroperationBoundaryContract(cross_plugin_direct_import_allowed=True)
    with pytest.raises(ValueError):
        PluginInteroperationBoundaryContract(cross_plugin_direct_call_allowed=True)
    with pytest.raises(ValueError):
        PluginInteroperationBoundaryContract(cross_plugin_state_write_allowed=True)
    with pytest.raises(ValueError):
        PluginInteroperationBoundaryContract(parallel_runtime_allowed=True)


def test_interoperation_check_blocks_p0_p1_and_requires_evidence_chain():
    assert InteroperationBoundaryCheck().passed is True
    assert InteroperationBoundaryCheck(p0_count=1).passed is False
    assert InteroperationBoundaryCheck(p1_count=1).passed is False


def test_actor_collaboration_requires_handoff_and_result_return():
    contract = ActorCollaborationBoundaryContract()
    assert contract.collaboration_requires_handoff is True
    assert contract.collaboration_requires_result_return is True
    with pytest.raises(ValueError):
        ActorCollaborationBoundaryContract(collaboration_requires_handoff=False)
    with pytest.raises(ValueError):
        ActorCollaborationBoundaryContract(collaboration_requires_result_return=False)
