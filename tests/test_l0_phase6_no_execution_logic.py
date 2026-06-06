import ast
from dataclasses import fields, is_dataclass
from pathlib import Path

PHASE6_MODULES = {"trust.py", "privacy.py", "secret.py", "contract.py", "policy.py", "instruction.py", "autonomy.py", "value.py"}
L0_DIR = Path(__file__).resolve().parents[1] / "tiangong_kernel" / "l0_primitives"
FORBIDDEN_CLASS_NAMES = {"Runtime", "ToolExecutor", "PluginHost", "ModelClient", "MemorySystem", "ForgettingSystem", "SelfHealingSystem", "HealthMonitor", "PolicyEngine", "SecurityEngine", "PrivacyEngine"}
FORBIDDEN_FUNCTION_NAMES = {"authenticate", "verify_signature", "encrypt", "decrypt", "zero_trust_engine", "detect_pii", "comply_gdpr", "erase_user_data", "redact_content", "read_env", "check_contract", "enforce_contract", "execute_policy", "evaluate_policy", "allow", "deny", "rule_engine", "dsl_parser", "build_prompt", "resolve_instruction_conflict", "detect_prompt_injection", "switch_mode", "enable_wushuang", "disable_safety", "bypass", "reward_model", "optimize_utility", "moral_reasoner", "preference_learning", "execute", "run"}
FORBIDDEN_FIELD_NAMES = {"executor", "client", "callback", "callable", "socket", "connection", "file_handle", "process", "resource_handle", "database", "transport", "mutable_object", "real_handle", "secret_value", "token_value", "private_key_value"}
FORBIDDEN_TEXT_TOKENS = {"ToolExecutor", "PluginHost", "ModelClient", "MemorySystem", "ForgettingSystem", "SelfHealingSystem", "HealthMonitor", "PolicyEngine", "SecurityEngine", "PrivacyEngine", "secret_value", "token_value", "private_key_value", "read_env", "vault", "zero_trust_engine", "detect_pii", "comply_gdpr", "erase_user_data", "redact_content", "check_contract", "enforce_contract", "execute_policy", "evaluate_policy", "rule_engine", "dsl_parser", "build_prompt", "resolve_instruction_conflict", "detect_prompt_injection", "switch_mode", "enable_wushuang", "disable_safety", "bypass", "reward_model", "optimize_utility", "moral_reasoner", "preference_learning"}

def test_phase6_modules_do_not_define_upper_layer_classes_or_flow_functions():
    violations = []
    for path in sorted(L0_DIR.glob("*.py")):
        if path.name not in PHASE6_MODULES:
            continue
        text = path.read_text(encoding="utf-8")
        for token in FORBIDDEN_TEXT_TOKENS:
            if token in text:
                violations.append((path.name, "text", token))
        tree = ast.parse(text, filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name in FORBIDDEN_CLASS_NAMES:
                violations.append((path.name, "class", node.name))
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in FORBIDDEN_FUNCTION_NAMES:
                violations.append((path.name, "function", node.name))
    assert violations == []

def test_phase6_ref_dataclasses_do_not_hold_runtime_handles():
    import tiangong_kernel.l0_primitives.autonomy as autonomy
    import tiangong_kernel.l0_primitives.contract as contract
    import tiangong_kernel.l0_primitives.instruction as instruction
    import tiangong_kernel.l0_primitives.policy as policy
    import tiangong_kernel.l0_primitives.privacy as privacy
    import tiangong_kernel.l0_primitives.secret as secret
    import tiangong_kernel.l0_primitives.trust as trust
    import tiangong_kernel.l0_primitives.value as value
    violations = []
    for module in (trust, privacy, secret, contract, policy, instruction, autonomy, value):
        for obj in module.__dict__.values():
            if isinstance(obj, type) and obj.__module__ == module.__name__ and obj.__name__.endswith("Ref") and is_dataclass(obj):
                for field in fields(obj):
                    if field.name in FORBIDDEN_FIELD_NAMES:
                        violations.append((obj.__name__, field.name))
    assert violations == []
