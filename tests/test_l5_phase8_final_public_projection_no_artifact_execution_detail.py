import pytest
from tiangong_kernel.l5_plugin_host import L5FinalPublicProjection


def test_l5_phase8_final_public_projection_no_artifact_execution_detail():
    with pytest.raises(ValueError):
        L5FinalPublicProjection(production_mount_readiness_summary=(("build_command", "python build.py"),))
