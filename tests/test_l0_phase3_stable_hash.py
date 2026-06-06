from tiangong_kernel.l0_primitives.action import ActionIntent, ActionKind, ActionRef, ActionState
from tiangong_kernel.l0_primitives.effect import EffectIntent, EffectKind, EffectRef, EffectState
from tiangong_kernel.l0_primitives.identity import RefId
from tiangong_kernel.l0_primitives.risk import RiskLevel, RiskRef, RiskView
from tiangong_kernel.l0_primitives.serialization import stable_hash


def test_phase3_stable_hash_is_repeatable_and_sensitive_to_fact_changes():
    action_a = ActionIntent(ActionRef(RefId("action:" + "2" * 32), ActionKind.NOOP), ActionKind.NOOP, ActionState.PROPOSED)
    action_b = ActionIntent(ActionRef(RefId("action:" + "2" * 32), ActionKind.NOOP), ActionKind.NOOP, ActionState.COMPLETED)
    assert stable_hash(action_a) == stable_hash(action_a)
    assert stable_hash(action_a) != stable_hash(action_b)


def test_phase3_hash_handles_nested_effect_and_risk_facts():
    effect = EffectIntent(EffectRef(RefId("effect:" + "3" * 32), EffectKind.OBSERVE), EffectKind.OBSERVE, EffectState.PROPOSED)
    risk = RiskView(RiskRef(RefId("risk:" + "4" * 32), RiskLevel.A0_SAFE), RiskLevel.A0_SAFE)
    assert len(stable_hash((effect, risk))) == 64
