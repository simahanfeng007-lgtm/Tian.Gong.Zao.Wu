from pathlib import Path


def test_l5_phase4_code_does_not_call_real_file_reading_apis():
    root = Path("tiangong_kernel/l5_plugin_host")
    phase4_files = [root / "lifecycle_declaration.py", root / "lifecycle_validation.py", root / "lifecycle_projection.py", root / "self_healing_declaration.py"]
    blocked = ("Path.read_text(", "Path.read_bytes(", "Path.open(", "open(", "os.listdir(", "rglob(")
    for file in phase4_files:
        text = file.read_text(encoding="utf-8")
        assert not any(token in text for token in blocked)
