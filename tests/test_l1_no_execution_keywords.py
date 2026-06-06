from pathlib import Path

L1_DIR = Path(__file__).resolve().parents[1] / "tiangong_kernel" / "l1_ports"
FORBIDDEN_TEXT = {
    "CapabilityPort",
    "AbilityPackagePort",
    "CapabilityDeclaration",
    "AgentFacingPort",
    "ModelFacingPort",
    "AgentVisiblePort",
    "ShenShu",
    "Shenshu",
    "神枢",
    "PluginHost",
    "OpenAI",
    "Docker",
    "execute_plan",
    "run_loop",
    "model.call",
    "tool.call",
    "asyncio.create_task",
    "threading.Thread",
    "multiprocessing",
}


def test_l1_has_no_old_chain_or_real_execution_keywords():
    violations = []
    for path in L1_DIR.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        for item in FORBIDDEN_TEXT:
            if item in text:
                violations.append((path.name, item))
    assert violations == []
