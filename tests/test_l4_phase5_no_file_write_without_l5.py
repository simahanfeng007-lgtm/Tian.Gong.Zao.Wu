from l4_phase5_builders import file_request
from tiangong_kernel.l4_action_grounding import DisabledRealFileAdapterStub, NoRealFileSystemMutationInvariant


def test_l4_phase5_no_file_write_without_l5_permit():
    request = file_request()
    failure = DisabledRealFileAdapterStub().prepare_file_action(request)
    invariant = NoRealFileSystemMutationInvariant(invariant_ref=request.request_ref)

    assert request.permit_ref is None
    assert failure.real_file_read is False
    assert failure.real_file_mutation is False
    assert invariant.live_action_allowed is False
