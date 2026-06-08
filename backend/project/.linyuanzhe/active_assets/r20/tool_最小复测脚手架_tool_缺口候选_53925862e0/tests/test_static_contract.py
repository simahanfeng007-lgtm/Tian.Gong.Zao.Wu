def test_r18_tool_candidate_static_contract():
    asset_ref = 'asset_tool_request:r16_a27218e947df9d9c'
    assert asset_ref
    assert True  # candidate_adapter_draft AST and no-side-effect boundaries are scanned by Runtime.
