from pathlib import Path

def test_no_tool_shell_file_network_call():
    root = Path(__file__).resolve().parents[1] / 'tiangong_kernel/l6_plugins/adaptive_collaboration'
    source = '\n'.join(p.read_text(encoding='utf-8') for p in root.glob('*.py') if p.name not in {'forbidden_scan.py'})
    for token in ('subprocess', 'os.system', 'shell=True', 'socket.', 'Path.write_text', 'Path.unlink'):
        assert token not in source
