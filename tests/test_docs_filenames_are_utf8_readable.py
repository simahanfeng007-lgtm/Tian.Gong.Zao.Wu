from pathlib import Path


def test_new_five_model_docs_have_readable_utf8_names():
    bad_markers = "Σ╖╡Θτµ┐Åöï║₧╕╣╜"
    five_model_docs = [p for p in Path("docs").iterdir() if p.is_file() and ("五模型" in p.name or "五大模型" in p.name)]
    assert five_model_docs
    assert all(not any(marker in p.name for marker in bad_markers) for p in five_model_docs)
