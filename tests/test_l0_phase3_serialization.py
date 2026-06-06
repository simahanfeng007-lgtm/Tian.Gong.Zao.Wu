from tiangong_kernel.l0_primitives.action import ActionIntent, ActionKind, ActionRef
from tiangong_kernel.l0_primitives.actor import ActorKind, ActorRef
from tiangong_kernel.l0_primitives.decision import Decision, DecisionKind, DecisionRef
from tiangong_kernel.l0_primitives.effect import EffectIntent, EffectKind, EffectRef
from tiangong_kernel.l0_primitives.goal import GoalKind, GoalRef, GoalState
from tiangong_kernel.l0_primitives.grant_lease import GrantKind, GrantRef, LeaseRef, LeaseStatus
from tiangong_kernel.l0_primitives.identity import RefId
from tiangong_kernel.l0_primitives.plan import PlanKind, PlanRef, PlanState
from tiangong_kernel.l0_primitives.risk import RiskLevel, RiskRef, RiskView
from tiangong_kernel.l0_primitives.scope import CoreScope, ScopeKind, ScopeRef
from tiangong_kernel.l0_primitives.serialization import stable_json_dumps, to_primitive
from tiangong_kernel.l0_primitives.time import Timestamp


def test_phase3_objects_have_canonical_json_forms():
    actor = ActorRef(RefId("actor:" + "7" * 32), ActorKind.MODEL)
    scope_ref = ScopeRef(RefId("scope:" + "8" * 32), ScopeKind.RUN)
    scope = CoreScope(scope_ref, ScopeKind.RUN)
    goal = GoalRef(RefId("goal:" + "9" * 32), GoalKind.RECOVERY, GoalState.ACTIVE)
    plan = PlanRef(RefId("plan:" + "a" * 32), PlanKind.SEQUENTIAL, PlanState.APPROVED)
    action = ActionIntent(ActionRef(RefId("action:" + "b" * 32), ActionKind.FINAL), ActionKind.FINAL)
    effect = EffectIntent(EffectRef(RefId("effect:" + "c" * 32), EffectKind.READ), EffectKind.READ)
    decision = Decision(DecisionRef(RefId("decision:" + "d" * 32), DecisionKind.ALLOW), DecisionKind.ALLOW, Timestamp(3))
    risk = RiskView(RiskRef(RefId("risk:" + "e" * 32), RiskLevel.A1_LOW), RiskLevel.A1_LOW)
    grant = GrantRef(RefId("grant:" + "f" * 32), GrantKind.USER)
    lease = LeaseRef(RefId("lease:" + "1" * 32), LeaseStatus.ISSUED, grant)
    payload = (actor, scope, goal, plan, action, effect, decision, risk, lease)
    primitive = to_primitive(payload)
    assert primitive[0]["kind"] == "model"
    assert primitive[4]["kind"] == "final"
    assert primitive[8]["status"] == "issued"
    assert stable_json_dumps(payload) == stable_json_dumps(payload)
