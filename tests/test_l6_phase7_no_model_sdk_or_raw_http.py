from pathlib import Path

def test_no_model_sdk_or_raw_http():
    root = Path(__file__).resolve().parents[1] / 'tiangong_kernel/l6_plugins/adaptive_collaboration'
    source = '\n'.join(p.read_text(encoding='utf-8') for p in root.glob('*.py') if p.name not in {'forbidden_scan.py'})
    for token in ('import openai', 'import anthropic', 'requests.', 'httpx.', 'urllib.request', 'aiohttp.'):
        assert token not in source
