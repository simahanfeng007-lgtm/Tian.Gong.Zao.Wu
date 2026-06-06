import pytest

from l4_phase8_builders import no_legacy_main_chain_guarantee, phase8_ref
from tiangong_kernel.l4_execution import L4NoLegacyRuntimeGuarantee


def test_l4_phase8_no_legacy_main_chain_guarantee_covers_legacy_symbols():
    guarantee = no_legacy_main_chain_guarantee()

    expected = {
        "Run" + "time",
        "\u795e\u67a2",
        "Ability" + "Package",
        "Capability" + "Port",
        "Ability" + "Package" + "Port",
    }
    assert expected.issubset(set(guarantee.forbidden_symbols))
    assert guarantee.restores_legacy_main_chain is False
    assert guarantee.restores_ability_package is False
    assert guarantee.restores_capability_port is False
    assert guarantee.creates_old_router is False


def test_l4_phase8_no_legacy_main_chain_guarantee_rejects_restore_flags():
    with pytest.raises(ValueError):
        L4NoLegacyRuntimeGuarantee(guarantee_ref=phase8_ref(170, "no_legacy"), restores_legacy_main_chain=True)
