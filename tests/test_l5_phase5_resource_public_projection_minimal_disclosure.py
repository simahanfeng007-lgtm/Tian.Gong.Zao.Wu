from l5_phase5_helpers import valid_projection


def test_resource_projection_omits_live_runtime_handles():
    text = str(valid_projection())
    forbidden = ("live quota", "budget account object", "limiter object", "runtime resource handle")
    assert not any(item in text.lower() for item in forbidden)
