import pytest

from tiangong_kernel.l6_plugins.mind import *


def test_attention_focus_is_not_interrupt_command():
    assert AttentionMindState().attention_is_interrupt is False
    assert AttentionProjection().is_interrupt_command is False
    assert FocusPriorityScore().interrupts_task is False
    with pytest.raises(ValueError):
        AttentionMindState(attention_is_interrupt=True)
    with pytest.raises(ValueError):
        AttentionProjection(is_interrupt_command=True)
    with pytest.raises(ValueError):
        FocusPriorityScore(interrupts_task=True)
