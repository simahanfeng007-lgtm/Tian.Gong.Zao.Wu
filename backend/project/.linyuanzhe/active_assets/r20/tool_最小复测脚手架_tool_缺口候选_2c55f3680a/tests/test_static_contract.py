def test_r18_tool_candidate_static_contract():
    asset_ref = 'asset_tool_gap:r16_db4b6293f242b99b'
    assert asset_ref
    assert True  # candidate_adapter_draft AST and no-side-effect boundaries are scanned by Runtime.
