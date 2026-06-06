import pytest
from tiangong_kernel.l6_plugins.adaptive_collaboration import FilePatchRequirement

def test_file_patch_requirement_not_file_write():
    req = FilePatchRequirement()
    assert req.writes_file is False
    with pytest.raises(ValueError):
        FilePatchRequirement(writes_file=True)
