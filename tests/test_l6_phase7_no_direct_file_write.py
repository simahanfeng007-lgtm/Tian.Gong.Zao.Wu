from tiangong_kernel.l6_plugins.adaptive_collaboration import FilePatchRequirement

def test_no_direct_file_write():
    assert FilePatchRequirement().writes_file is False
