import pytest

from l4_phase5_builders import phase5_ref
from tiangong_kernel.l4_action_grounding import SideEffectDescriptor, SideEffectKind


def test_l4_phase5_side_effect_descriptor_describes_but_does_not_authorize():
    descriptor = SideEffectDescriptor(
        side_effect_ref=phase5_ref(101, "side_effect"),
        effect_kinds=(
            SideEffectKind.READ_ONLY,
            SideEffectKind.WRITE,
            SideEffectKind.DELETE,
            SideEffectKind.NETWORK_SEND,
            SideEffectKind.PROCESS_SPAWN,
            SideEffectKind.UI_INPUT,
        ),
        summary="broad descriptor for tests",
    )

    assert SideEffectKind.DELETE in descriptor.effect_kinds
    assert descriptor.descriptor_only is True
    assert descriptor.authorizes_action is False
    assert descriptor.performs_side_effect is False


def test_l4_phase5_side_effect_descriptor_rejects_authorization():
    with pytest.raises(ValueError):
        SideEffectDescriptor(
            side_effect_ref=phase5_ref(102, "side_effect"),
            effect_kinds=(SideEffectKind.WRITE,),
            authorizes_action=True,
        )
