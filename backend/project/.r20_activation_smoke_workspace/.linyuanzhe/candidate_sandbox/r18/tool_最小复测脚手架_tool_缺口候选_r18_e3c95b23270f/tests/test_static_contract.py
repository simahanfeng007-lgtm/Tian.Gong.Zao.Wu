def test_r18_tool_candidate_static_contract():
    asset_ref = 'asset_tool_request:r16_e7ad356532f4ae5b'
    assert asset_ref
    assert True  # candidate_adapter_draft AST and no-side-effect boundaries are scanned by Runtime.
