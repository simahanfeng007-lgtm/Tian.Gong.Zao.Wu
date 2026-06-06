from l3_phase7_builders import build_l3_phase7_objects
from tiangong_kernel.l3_orchestration import EvolutionFlowKind, ExperimentFlowKind, IterationFlowKind


def test_experiment_iteration_evolution_requests_are_refs_and_requests_only():
    objects = build_l3_phase7_objects()
    experiment = objects["experiment_request"]
    iteration = objects["iteration_request"]
    evolution = objects["evolution_request"]
    assert experiment.request_only is True
    assert iteration.request_only is True
    assert evolution.request_only is True
    assert experiment.value_score.advisory_only is True
    assert iteration.need_score.advisory_only is True
    assert evolution.pressure_score.advisory_only is True
    assert not hasattr(experiment, "run")
    assert not hasattr(iteration, "generate_patch")
    assert not hasattr(evolution, "evolve")


def test_experiment_iteration_evolution_rankings_are_stable_ordered():
    objects = build_l3_phase7_objects()
    assert objects["experiment_ranking"].candidates[0].route_kind is ExperimentFlowKind.REQUEST_DESIGN_REVIEW
    assert objects["iteration_ranking"].candidates[0].route_kind is IterationFlowKind.REQUEST_CANDIDATE_REVIEW
    assert objects["evolution_ranking"].candidates[0].route_kind is EvolutionFlowKind.REQUEST_BOUNDARY_REVIEW
    assert objects["evolution_boundary"].advisory_only is True
    assert objects["evolution_constraint"].advisory_only is True
