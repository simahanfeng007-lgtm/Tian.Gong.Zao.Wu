import pytest
from tiangong_kernel.l5_plugin_host import GENERIC_HOST_BLOCK_TOOL_ONLY, L5CapabilityReadinessMatrix, L5CapabilityReadinessMatrixValidator
from tests.l5_phase8_factories import blocked_product_matrix


def test_l5_phase8_capability_readiness_matrix_tracks_product_factory_conditionally():
    matrix = L5CapabilityReadinessMatrix()
    assert matrix.artifact_factory_ready is True
    assert L5CapabilityReadinessMatrixValidator().check(matrix)
    blocked = blocked_product_matrix()
    assert blocked.artifact_factory_ready is False
    with pytest.raises(ValueError):
        L5CapabilityReadinessMatrix(product_artifact_factory_precheck_result=GENERIC_HOST_BLOCK_TOOL_ONLY, artifact_factory_ready=True)


def test_l5_phase8_capability_readiness_matrix_rejects_empty_or_blocked_ready_matrix():
    with pytest.raises(ValueError):
        L5CapabilityReadinessMatrix(capability_kind_refs=(), readiness_rows=())
    with pytest.raises(ValueError):
        L5CapabilityReadinessMatrix(blocking_reason_refs=("block:capability",))
    with pytest.raises(ValueError):
        L5CapabilityReadinessMatrix(readiness_rows=(("ArtifactFactoryCapability", "not_ready"),))


def test_l5_phase8_product_artifact_factory_readiness_is_planning_only():
    matrix = L5CapabilityReadinessMatrix()
    readiness = dict(matrix.readiness_rows)
    assert readiness["ArtifactFactoryCapability"] == "l6_planning_only"
    assert matrix.product_artifact_factory_scope == "l6_planning_only"
    assert matrix.allow_execute_product_artifact_factory is False
    assert matrix.product_artifact_factory_no_execution_ref
    assert matrix.product_artifact_factory_no_build_ref
    assert matrix.product_artifact_factory_no_delivery_ref
