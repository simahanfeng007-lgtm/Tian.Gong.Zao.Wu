from __future__ import annotations

from tiangong_kernel.l0_primitives.identity import RefId, TypedRef
from tiangong_kernel.l1_ports.math_engine_contract_ports import ConfidenceValue, ScoreResult, ScoreValue, UncertaintyValue
from tiangong_kernel.l2_state.math_model_governance_state import ScoringSnapshotState
from tiangong_kernel.l2_state.state_identity import L2StateIdentity, L2StateKind
from tiangong_kernel.l2_state.state_status import L2StateStatus, L2StateStatusKind
from tiangong_kernel.l3_orchestration.math_model_engine_flow import MathScoringFlow
from tiangong_kernel.l4_action_grounding.math_model_adapter import DeterministicLocalScoreAdapter


def _ref(suffix: int, ref_type: str = "math_chain") -> TypedRef:
    return TypedRef(RefId(f"ref:{suffix:032x}"), ref_type)


def test_math_model_l1_l2_l3_l4_chain_remains_ref_only_and_disabled() -> None:
    score_result = ScoreResult(score=ScoreValue(0.4), confidence=ConfidenceValue(0.7), uncertainty=UncertaintyValue(0.3))
    state = ScoringSnapshotState(
        identity=L2StateIdentity(_ref(1, "l2_state"), L2StateKind.MATH),
        status=L2StateStatus(L2StateStatusKind.DECLARED),
        score=score_result.score.value,
        confidence=score_result.confidence.value,
        uncertainty=score_result.uncertainty.value,
    )
    flow = MathScoringFlow(score_result_refs=(_ref(2, "score_result"),), fallback_used=True)
    invocation = DeterministicLocalScoreAdapter().run_disabled(_ref(3, "request"))

    assert score_result.advisory_only is True
    assert state.no_execution is True
    assert flow.disabled_safe is True
    assert flow.no_final_decision is True
    assert invocation.disabled is True
    assert invocation.action_enabled is False
