from pathlib import Path


def test_l3_run_loop_flow_source_has_no_external_execution_keywords():
    source = Path("tiangong_kernel/l3_orchestration/orchestration_flow.py").read_text(encoding="utf-8")
    forbidden = (
        "open(",
        "subprocess",
        "requests",
        "httpx",
        "urllib",
        "sqlite",
        "socket",
        "os.system",
        "Popen",
        "eval(",
        "exec(",
        "write_text",
        "read_text",
        "Path(",
        "plugin_host",
        "AbilityPackage",
        "CapabilityPort",
        "AbilityPackagePort",
        "AbilityRouter",
        "AbilityExecutor",
    )
    for token in forbidden:
        assert token not in source
