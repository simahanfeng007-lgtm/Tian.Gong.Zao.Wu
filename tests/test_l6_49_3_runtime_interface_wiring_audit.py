from __future__ import annotations

import ast
from pathlib import Path

from tiangong_agent_runtime.memory_math_core import MemoryCategory, MemoryLevel
from tiangong_agent_runtime.memory_store_bridge import MemoryRecord, MemoryStoreBridge
from tiangong_agent_runtime.runtime_entry import RuntimeEntry


PROJECT_ROOTS = ("tiangong_agent_runtime", "tiangong_agent_shell", "tiangong_kernel")


def test_runtime_live_interfaces_are_all_connected(tmp_path: Path) -> None:
    store = MemoryStoreBridge(tmp_path / "memory.jsonl")
    store.add_candidate(
        MemoryRecord(
            memory_id="mem_interface_bug_runtime_wiring",
            memory_level=MemoryLevel.L3,
            memory_category=MemoryCategory.PROCEDURAL,
            sanitized_summary="接口 bug Runtime 接线 情志 遗忘 生命周期 四路径 预算 Planner 消费层 回归验证",
            evidence_refs=("test:l6_49_3_runtime_interface_wiring",),
            confidence_score=0.92,
            importance_score=0.88,
            task_relevance_score=0.95,
            reuse_count=2,
            success_count=2,
            last_accessed_at=1.0,
            half_life_seconds=60.0,
        )
    )
    runtime = RuntimeEntry(memory_store=store)

    runtime.run_text("请检查接口 bug，确认情志、遗忘、生命周期、四路径、预算和 Planner 消费层是否接活")
    snapshot = runtime.interface_wiring_snapshot()

    assert snapshot["no_second_runtime"] is True
    assert snapshot["no_direct_tool_call"] is True
    assert snapshot["no_kernel_mutation"] is True

    affective = snapshot["affective"]
    assert affective["turn_count"] == 1
    assert affective["has_previous_state"] is True
    assert affective["no_tool_dispatch"] is True

    memory_recall = snapshot["memory_recall"]
    assert memory_recall["memory_store_attached"] is True
    assert memory_recall["last_error"] == ""
    assert memory_recall["route"] is not None
    assert memory_recall["route"]["hints"], "MemoryRecallRouter 必须被 Runtime 真实调用"
    assert memory_recall["no_long_term_write"] is True
    assert memory_recall["no_memory_delete"] is True

    forgetting = snapshot["forgetting_review"]
    assert forgetting["memory_store_attached"] is True
    assert forgetting["last_error"] == ""
    assert forgetting["review_count"] >= 1, "ForgetReviewRouter.review(record, vector) 必须被 Runtime 正确签名调用"
    assert forgetting["no_physical_delete"] is True

    budget = snapshot["budget_low_friction"]
    assert budget["runtime_projection_only"] is True
    assert budget["no_budget_mutation"] is True
    assert budget["a0_a4_low_friction_preserved"] is True
    assert budget["a5_hard_boundary_preserved"] is True

    lifecycle = snapshot["lifecycle"]
    assert lifecycle["bundle"] is not None, "LifecycleCoordinator.build_bundle 必须被 Runtime 接活"
    assert lifecycle["bundle"]["no_direct_execution"] is True
    assert lifecycle["bundle"]["no_patch_apply"] is True
    assert lifecycle["bundle"]["no_hot_switch"] is True

    four_path = snapshot["four_path"]
    assert four_path["report"] is not None, "FourPathContextRouter.build 必须被 Runtime 接活"
    assert four_path["report"]["context_pack"]["memory_hint_count"] >= 1
    assert four_path["report"]["context_pack"]["lifecycle_hint_count"] >= 1
    assert four_path["no_model_dispatch"] is True

    planner_consumption = snapshot["planner_unified_consumption"]
    assert planner_consumption["report"] is not None, "PlannerUnifiedConsumptionBridge.consume 必须被 Runtime 接活"
    assert planner_consumption["report"]["context_hint"]["source_context_digest"]
    assert planner_consumption["no_tool_dispatch"] is True


def test_runtime_affective_state_accumulates_across_turns(tmp_path: Path) -> None:
    store = MemoryStoreBridge(tmp_path / "memory.jsonl")
    runtime = RuntimeEntry(memory_store=store)

    runtime.run_text("第一轮：接口风险和 bug 复核")
    first = runtime.affective_runtime_snapshot()
    runtime.run_text("第二轮：继续复核接口风险和回滚路径")
    second = runtime.affective_runtime_snapshot()

    assert first["turn_count"] == 1
    assert second["turn_count"] == 2
    assert second["has_previous_state"] is True
    assert first["state"] != second["state"], "previous_state 必须跨 turn 累积，不能每轮归零"


def test_source_interface_calls_have_no_obvious_signature_mismatch() -> None:
    """轻量 AST 接口体检：覆盖 runtime/shell/kernel 源码内的显式项目调用。"""
    roots = [Path(root) for root in PROJECT_ROOTS]
    py_files = [p for root in roots for p in root.rglob("*.py") if "__pycache__" not in p.parts]
    modules = {p: ".".join(p.with_suffix("").parts) for p in py_files}
    functions: dict[str, ast.FunctionDef] = {}
    classes: dict[str, ast.ClassDef] = {}
    methods: dict[str, ast.FunctionDef] = {}
    inits: dict[str, ast.FunctionDef] = {}

    for p, mod in modules.items():
        tree = ast.parse(p.read_text(encoding="utf-8"))
        for node in tree.body:
            if isinstance(node, ast.FunctionDef):
                functions[f"{mod}.{node.name}"] = node
            elif isinstance(node, ast.ClassDef):
                classes[f"{mod}.{node.name}"] = node
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        methods[f"{mod}.{node.name}.{item.name}"] = item
                        if item.name == "__init__":
                            inits[f"{mod}.{node.name}"] = item

    def signature(node: ast.FunctionDef, *, skip_self: bool = False) -> tuple[set[str], bool, int | None]:
        args = list(node.args.posonlyargs) + list(node.args.args)
        if skip_self and args and args[0].arg in {"self", "cls"}:
            args = args[1:]
        positional = {arg.arg for arg in args}
        kwonly = {arg.arg for arg in node.args.kwonlyargs}
        accepts_kwargs = node.args.kwarg is not None
        max_positional = None if node.args.vararg is not None else len(args)
        return positional | kwonly, accepts_kwargs, max_positional

    findings: list[str] = []
    for p, mod in modules.items():
        tree = ast.parse(p.read_text(encoding="utf-8"))
        imported: dict[str, str] = {}
        for key in functions | classes:
            if key.startswith(mod + "."):
                imported[key.rsplit(".", 1)[1]] = key
        for node in tree.body:
            if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith(("tiangong_agent_runtime", "tiangong_agent_shell", "tiangong_kernel")):
                for alias in node.names:
                    imported[alias.asname or alias.name] = node.module + "." + alias.name
        for call in (node for node in ast.walk(tree) if isinstance(node, ast.Call)):
            target = None
            skip_self = False
            if isinstance(call.func, ast.Name):
                resolved = imported.get(call.func.id)
                if resolved in functions:
                    target = functions[resolved]
                elif resolved in classes and resolved in inits:
                    target = inits[resolved]
                    skip_self = True
            if target is None:
                continue
            allowed, accepts_kwargs, max_pos = signature(target, skip_self=skip_self)
            if max_pos is not None and len(call.args) > max_pos:
                findings.append(f"{p}:{call.lineno} positional {len(call.args)}>{max_pos} for {call.func.id}")
            if not accepts_kwargs:
                bad = [kw.arg for kw in call.keywords if kw.arg is not None and kw.arg not in allowed]
                if bad:
                    findings.append(f"{p}:{call.lineno} unexpected keyword {bad} for {call.func.id}")

    assert not findings
