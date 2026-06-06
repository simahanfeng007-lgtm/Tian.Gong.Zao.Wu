import pytest

from tiangong_kernel.l5_plugin_host import (
    L5NoL6ImplementationGuarantee,
    L5NoLegacyRuntimeGuarantee,
    L5NoLiveExternalActionGuarantee,
    L5NoLowerLayerMutationGuarantee,
)


def test_guarantees_accept_only_safe_false_flags():
    assert L5NoL6ImplementationGuarantee(guarantee_ref="guarantee:no_l6").l6_business_logic_present is False
    assert L5NoLiveExternalActionGuarantee(guarantee_ref="guarantee:no_live").live_external_action_present is False
    assert L5NoLowerLayerMutationGuarantee(guarantee_ref="guarantee:no_lower").lower_layer_mutation_present is False
    assert L5NoLegacyRuntimeGuarantee(guarantee_ref="guarantee:no_legacy").legacy_main_chain_present is False


def test_guarantees_reject_unsafe_true_flags():
    with pytest.raises(ValueError):
        L5NoL6ImplementationGuarantee(guarantee_ref="guarantee:no_l6", l6_business_logic_present=True)
    with pytest.raises(ValueError):
        L5NoLiveExternalActionGuarantee(guarantee_ref="guarantee:no_live", live_external_action_present=True)
    with pytest.raises(ValueError):
        L5NoLowerLayerMutationGuarantee(guarantee_ref="guarantee:no_lower", lower_layer_mutation_present=True)
    with pytest.raises(ValueError):
        L5NoLegacyRuntimeGuarantee(guarantee_ref="guarantee:no_legacy", legacy_main_chain_present=True)
