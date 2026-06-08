"""Code-X runtime skill guide and import audit tools.

Pure v2-native metadata helpers. They expose the Code-X workflow to the LLM
without executing v1 code, importing v1 modules, or changing Runtime state.
"""
from __future__ import annotations

from typing import Any, Mapping


def _hint(next_tool: str, reason: str, confidence: float = 0.9) -> dict[str, Any]:
    return {"next_tool": next_tool, "reason": reason, "confidence": confidence}



def _tool_usage_cards() -> list[dict[str, Any]]:
    """Return compact LLM-facing usage cards for the high-leverage Code-X tools."""
    return [
        {
            "tool": "project_rules_reader",
            "when_to_use": "开始任何真实仓库任务前，先读取项目局部规则与约束。",
            "required_inputs": {"repo_root": "workspace 根目录，默认 ."},
            "output_expectation": "返回项目规则文件、约束线索、建议遵守事项。",
            "next_action": "repo_map",
        },
        {
            "tool": "repo_map",
            "when_to_use": "首次接触仓库、定位前、重构前、打包前。",
            "required_inputs": {"workspace_root": "workspace 根目录，默认 .", "max_files": "可选扫描上限"},
            "output_expectation": "返回文件概览、技术栈、入口、测试映射、next_action_hint。",
            "next_action": "issue_to_file_localizer 或 semantic_code_search",
        },
        {
            "tool": "issue_to_file_localizer",
            "when_to_use": "用户给出 bug、报错、需求描述，需要先定位候选文件。",
            "required_inputs": {"issue_text": "问题描述/报错日志/需求文本"},
            "output_expectation": "返回候选文件、置信度、定位依据。",
            "next_action": "file_to_symbol_localizer 或 symbol_to_line_localizer",
        },
        {
            "tool": "semantic_code_search",
            "when_to_use": "用户描述行为或语义，但没有明确文件名/符号名。",
            "required_inputs": {"query": "要搜索的行为、符号或错误语义"},
            "output_expectation": "返回语义匹配片段与候选文件。",
            "next_action": "affected_area_detector",
        },
        {
            "tool": "workspace_snapshot",
            "when_to_use": "任何写入 workspace 前必须调用。",
            "required_inputs": {"label": "可选快照标签"},
            "output_expectation": "返回快照 id、快照路径、可恢复范围。",
            "next_action": "patch_plan_generator",
        },
        {
            "tool": "patch_plan_generator",
            "when_to_use": "定位完成后、写入前，生成可审阅修复计划。",
            "required_inputs": {"issue": "问题描述", "target_files": "可选候选文件列表"},
            "output_expectation": "返回 patch 目标、风险点、编辑策略。",
            "next_action": "edit_unit_planner",
        },
        {
            "tool": "edit_unit_planner",
            "when_to_use": "把 patch 计划拆成 create/replace/append/delete 等可执行 edit_units。",
            "required_inputs": {"patch_plan": "patch_plan_generator 的计划或 LLM 裁决后的计划"},
            "output_expectation": "返回可传给 workspace_patch_applier 的 edit_units。",
            "next_action": "conflict_detector",
        },
        {
            "tool": "conflict_detector",
            "when_to_use": "写入前检查路径、覆盖、冲突和高风险编辑。",
            "required_inputs": {"edit_units": "待写入 edit_units"},
            "output_expectation": "返回冲突/风险判断。",
            "next_action": "unified_diff_generator 或 workspace_patch_applier",
        },
        {
            "tool": "workspace_patch_applier",
            "when_to_use": "LLM 审阅计划并裁决后，真实写入 workspace。",
            "required_inputs": {"edit_units": "通过冲突检查的 edit_units"},
            "output_expectation": "返回已改文件、before/after hash、写入证据。",
            "next_action": "python_quality_runner / pytest_runner / build_runner",
        },
        {
            "tool": "python_quality_runner",
            "when_to_use": "Python 项目 patch 后优先运行 compileall/基础质量检查。",
            "required_inputs": {"target": "可选目标路径，默认 workspace"},
            "output_expectation": "返回 exit code、stdout/stderr 摘要、失败类型线索。",
            "next_action": "pytest_runner 或 failure_attribution_analyzer",
        },
        {
            "tool": "pytest_runner",
            "when_to_use": "存在 pytest 测试或用户要求跑测试时。",
            "required_inputs": {"test_path": "可选测试路径，默认自动探测"},
            "output_expectation": "返回测试结果、失败输出、next_action_hint。",
            "next_action": "failure_attribution_analyzer if failed; changed_files_index if passed",
        },
        {
            "tool": "failure_attribution_analyzer",
            "when_to_use": "任何验证失败、命令失败、测试失败后必须先归因。",
            "required_inputs": {"log_text": "失败日志/测试输出/异常栈"},
            "output_expectation": "返回失败分类、根因候选、建议修复方向。",
            "next_action": "repair_loop_planner",
        },
        {
            "tool": "repair_loop_planner",
            "when_to_use": "归因后决定二次修复、降级、回滚或交接。",
            "required_inputs": {"failure_analysis": "失败归因结果", "attempt": "当前修复轮次"},
            "output_expectation": "返回下一轮修复策略与轮次限制。",
            "next_action": "next_patch_generator",
        },
        {
            "tool": "restore_checkpoint",
            "when_to_use": "patch 错误、A5 阻断、验证不可恢复、用户要求回滚。",
            "required_inputs": {"snapshot_id": "workspace_snapshot 返回的快照 id"},
            "output_expectation": "返回恢复结果和残留变更。",
            "next_action": "handoff_digest",
        },
        {
            "tool": "handoff_digest",
            "when_to_use": "任务完成、失败收口、超轮次、准备新窗口续接。",
            "required_inputs": {"task": "任务描述", "results": "关键证据/测试/变更摘要"},
            "output_expectation": "返回可复制续接摘要。",
            "next_action": "zip_delivery_packager when delivery is needed",
        },
        {
            "tool": "zip_delivery_packager",
            "when_to_use": "用户要求交付 zip 或阶段包。",
            "required_inputs": {"include_paths": "要打包路径", "output_zip": "输出 zip 路径"},
            "output_expectation": "返回 zip 路径、hash、文件清单。",
            "next_action": "handoff_digest",
        },
    ]


def _phase_to_next_action() -> dict[str, dict[str, Any]]:
    """Expose deterministic next-action hints so the LLM does not stall between tools."""
    return {
        "start": _hint("project_rules_reader", "先读项目规则，再建立 repo_map。"),
        "rules_read": _hint("repo_map", "规则读取后建立仓库地图。"),
        "mapped": _hint("issue_to_file_localizer", "仓库地图完成后进入问题定位。"),
        "located": _hint("workspace_snapshot", "定位完成且准备写入前创建快照。"),
        "snapshot_ready": _hint("patch_plan_generator", "快照完成后生成 patch 计划。"),
        "planned": _hint("edit_unit_planner", "patch 计划需拆成可执行 edit_units。"),
        "edit_units_ready": _hint("conflict_detector", "写入前必须检查冲突与覆盖风险。"),
        "conflict_clear": _hint("workspace_patch_applier", "冲突检查通过后由 LLM 裁决是否写入。"),
        "patched": _hint("python_quality_runner", "写入后必须验证。"),
        "validation_failed": _hint("failure_attribution_analyzer", "验证失败后先归因，不要停止。"),
        "failure_attributed": _hint("repair_loop_planner", "归因后规划二次修复。"),
        "validated": _hint("changed_files_index", "验证通过后汇总变更。"),
        "ready_to_deliver": _hint("handoff_digest", "交付前生成 handoff 摘要。"),
    }

def code_x_skill_guide(task_type: str = "auto", current_state: Mapping[str, Any] | None = None, phase: str = "") -> dict[str, Any]:
    """Return the LLM-facing Code-X usage skill.

    This is intentionally instruction-only. It helps the LLM choose the right
    chain; all real effects still go through registered Code-X tools.
    """
    state = dict(current_state or {})
    normalized_task = (task_type or "auto").strip().lower()
    normalized_phase = (phase or state.get("phase") or "start").strip().lower()
    recipes = {
        "bug_fix": [
            "code_x_skill_guide",
            "project_rules_reader",
            "repo_map",
            "issue_to_file_localizer",
            "file_to_symbol_localizer",
            "symbol_to_line_localizer",
            "workspace_snapshot",
            "patch_plan_generator",
            "edit_unit_planner",
            "conflict_detector",
            "unified_diff_generator",
            "workspace_patch_applier",
            "python_quality_runner or pytest_runner/build_runner",
            "failure_attribution_analyzer if validation failed",
            "repair_loop_planner + next_patch_generator for second repair",
            "changed_files_index",
            "handoff_digest",
        ],
        "import_error": [
            "repo_map",
            "test_failure_trace_mapper",
            "issue_to_file_localizer",
            "import_error_analyzer",
            "affected_area_detector",
            "workspace_snapshot",
            "patch_plan_generator",
            "workspace_patch_applier",
            "python_quality_runner",
            "pytest_runner",
            "handoff_digest",
        ],
        "feature_add": [
            "project_rules_reader",
            "repo_map",
            "semantic_code_search",
            "affected_area_detector",
            "test_design_subagent",
            "workspace_snapshot",
            "patch_plan_generator",
            "edit_unit_planner",
            "workspace_patch_applier",
            "pytest_runner/build_runner",
            "review_subagent",
            "changed_files_index",
            "handoff_digest",
        ],
        "refactor": [
            "repo_map",
            "dependency_graph",
            "call_graph",
            "affected_area_detector",
            "refactor_review_subagent",
            "workspace_snapshot",
            "patch_plan_generator",
            "workspace_patch_applier",
            "pytest_runner/build_runner/typecheck_runner",
            "changed_files_index",
            "handoff_digest",
        ],
        "frontend": [
            "repo_map",
            "stack_detector",
            "semantic_code_search",
            "frontend_visual_subagent",
            "test_design_subagent",
            "workspace_snapshot",
            "patch_plan_generator",
            "workspace_patch_applier",
            "npm_test_runner/build_runner/lint_runner",
            "frontend_visual_subagent",
            "handoff_digest",
        ],
        "handoff": [
            "changed_files_index",
            "task_digest",
            "handoff_digest",
            "delivery_candidate_packager",
            "zip_delivery_packager",
        ],
    }
    selected = recipes.get(normalized_task) or recipes["bug_fix"]
    if normalized_phase in {"failed", "validation_failed", "test_failed"}:
        next_hint = _hint("failure_attribution_analyzer", "验证失败后先归因，再决定二次修复、降级、回滚或交接。")
    elif normalized_phase in {"patched", "edited", "after_patch"}:
        next_hint = _hint("python_quality_runner", "Patch 已落地后必须验证；Python 项目先跑 compileall/pytest，其他栈按 build/lint/typecheck。")
    elif normalized_phase in {"located", "planned"}:
        next_hint = _hint("workspace_snapshot", "写入前先创建快照，再应用 patch。")
    else:
        next_hint = _hint("repo_map", "任何代码任务先建立压缩仓库地图，避免盲改。")
    return {
        "status": "ok",
        "summary": "Code-X Skill 已就绪：LLM 应按 读项目→定位→计划→快照→Patch→验证→失败归因→二修/回滚→打包→Handoff 的闭环使用工具。",
        "skill_id": "skill.code_x_execution_workflow",
        "authority_model": {
            "llm": "主脑、工程判断者、最终裁决者",
            "code_x": "代码执行外骨骼装甲",
            "planner": "动作建议器，不得夺权",
            "subagents": "证据型侦察/测试/审查/迁移助手，不得直接提交主 patch",
        },
        "trigger_words": [
            "修 bug", "代码修复", "跑测试", "失败归因", "二次修复", "重构", "新增功能", "打包交付",
            "code-x", "codex", "代码外骨骼", "repo map", "patch", "pytest", "handoff",
        ],
        "default_chain": selected,
        "recipes": recipes,
        "tool_choice_rules": [
            "未读项目：先 repo_map / project_rules_reader / stack_detector。",
            "只有报错日志：先 test_failure_trace_mapper / failure_attribution_analyzer，再定位文件。",
            "要写入：先 workspace_snapshot，再 patch_plan_generator + edit_unit_planner + conflict_detector。",
            "已改文件：必须 python_quality_runner / pytest_runner / build_runner / lint_runner / typecheck_runner 至少选一种验证。",
            "验证失败：failure_attribution_analyzer → repair_loop_planner → next_patch_generator；普通任务最多 3 轮，长链最多 6 轮。",
            "无法继续：restore_checkpoint 或 handoff_digest，不允许静默失败。",
        ],
        "command_shortcuts": {
            "status": "code-x status",
            "skill": "code-x skill",
            "readiness": "code-x readiness",
            "v1_audit": "code-x v1-audit",
            "fix": "code-x fix \"问题描述\"",
            "smoke": "code-x smoke .",
            "repo_map": "code-x repo-map .",
            "locate": "code-x locate \"问题描述或报错日志\"",
            "search": "code-x search \"符号或行为\"",
            "snapshot": "code-x snapshot",
            "changed": "code-x changed",
            "quality": "code-x quality",
            "pytest": "code-x pytest tests",
            "package": "code-x package src dist/code_x_delivery.zip",
            "raw_tool": "code-x tool <tool_name> {json_args}",
        },
        "tool_usage_cards": _tool_usage_cards(),
        "phase_to_next_action": _phase_to_next_action(),
        "safety_and_execution": {
            "A0_A4": "默认允许并审计",
            "A5": "硬阻断：密钥外传、大规模删除、系统目录破坏、生产环境修改、恶意命令",
            "never_lock": ["rollback", "handoff", "state_recover", "lease_extend"],
        },
        "current_state": state,
        "next_action_hint": next_hint,
    }


def code_x_world_class_readiness_check() -> dict[str, Any]:
    """Assess Code-X against current frontier coding-agent capability classes."""
    matrix = [
        {"axis": "repo understanding", "status": "present", "evidence": ["repo_map", "symbol_index", "dependency_graph", "call_graph"]},
        {"axis": "plan before edit", "status": "present", "evidence": ["patch_plan_generator", "edit_unit_planner", "conflict_detector"]},
        {"axis": "workspace write", "status": "present", "evidence": ["workspace_patch_applier", "before_after_hash", "patch_manifest"]},
        {"axis": "validation loop", "status": "present", "evidence": ["python_quality_runner", "pytest_runner", "npm_test_runner", "build_runner", "lint_runner", "typecheck_runner"]},
        {"axis": "failure repair", "status": "present", "evidence": ["failure_attribution_analyzer", "repair_loop_planner", "next_patch_generator"]},
        {"axis": "rollback/delivery", "status": "present", "evidence": ["workspace_snapshot", "restore_checkpoint", "zip_delivery_packager"]},
        {"axis": "subagent evidence", "status": "present", "evidence": ["code_research_subagent", "test_design_subagent", "review_subagent", "security_review_subagent"]},
        {"axis": "LLM usage skill", "status": "present", "evidence": ["code_x_skill_guide", "skill.code_x_execution_workflow"]},
        {"axis": "large benchmark proof", "status": "not_yet_proven", "evidence": ["R13A mini smoke passed", "no public SWE-bench/SWE-bench Pro run yet"]},
        {"axis": "IDE-grade interactive UX", "status": "partial", "evidence": ["frontend projection smoke passed", "new desktop UI not yet fully exercised"]},
    ]
    return {
        "status": "ok",
        "summary": "Code-X 已达到世界级代码代理的结构能力门槛，但尚不能宣称已实证超越 Claude Code/Codex；还需大型真实仓库和长链 benchmark。",
        "judgement": {
            "structural_world_class": True,
            "runtime_usable": True,
            "benchmark_world_class_proven": False,
            "reason": "已具备读库、定位、patch、验证、失败归因、二修、回滚、交付、子代理和 Skill；但缺少 SWE-bench/Pro 级公开实测。",
        },
        "matrix": matrix,
        "required_next_proof": [
            "真实中型仓库 20+ issue smoke",
            "多语言仓库验证：Python/Node/前端/混合项目",
            "长链 6 轮 repair loop 轨迹回放",
            "SWE-bench-like 去污染 fixture 扩容",
            "新前端端到端可视化 smoke",
        ],
        "next_action_hint": _hint("code_x_skill_guide", "继续把 LLM 使用 Skill 注入默认工作流，然后扩展真实仓库评测。"),
    }


def code_x_v1_import_audit() -> dict[str, Any]:
    """Report which v1 semantics have been rebuilt and which v1 assets remain out of scope."""
    rows = [
        {"v1_source": "daima_luoji_gongju.py", "status": "semantics_rebuilt", "v2_mapping": ["repo_map", "symbol_index", "dependency_graph", "patch_plan_generator", "failure_attribution_analyzer", "handoff_digest"], "note": "核心代码生产链语义已重建；未复制源码。"},
        {"v1_source": "daima_zhixing_gongju.py", "status": "semantics_rebuilt", "v2_mapping": ["python_quality_runner", "pytest_runner", "safe_command_runner"], "note": "执行器语义已重建；未复用 v1 执行沙箱。"},
        {"v1_source": "zhongduan_adapter.py", "status": "semantics_rebuilt", "v2_mapping": ["safe_command_runner", "build_runner", "lint_runner", "typecheck_runner", "command_capability_probe"], "note": "终端能力语义已重建；未复用 v1 shell adapter。"},
        {"v1_source": "wenjian_gongju.py", "status": "semantics_rebuilt", "v2_mapping": ["workspace_patch_applier", "changed_files_index", "before_after_hash", "rollback_plan", "zip_delivery_packager"], "note": "文件链语义已重建；未导入 v1 文件实现。"},
        {"v1_source": "tiangong_gongju_zhuce.py", "status": "metadata_lessons_only", "v2_mapping": ["RuntimeToolRegistry", "ToolDescriptor", "code_x_runtime_adapters"], "note": "只吸收元数据经验；v1 registry 必须抛弃。"},
        {"v1_source": "tiangong_ziwo_diedai.py", "status": "lessons_only", "v2_mapping": ["patch_manifest", "restore_checkpoint", "code_x_world_class_readiness_check"], "note": "只吸收复盘/回滚经验；未引入自改 loop。"},
        {"v1_source": "tiangong_shenshu_zhudong_qudong.py", "status": "lessons_only", "v2_mapping": ["next_action_hint", "code_x_skill_guide", "repair_loop_planner"], "note": "主动性变为 LLM 续航提示；未引入后台 loop。"},
        {"v1_source": "xuexi_jingtong_gongju.py", "status": "not_imported_in_codex", "v2_mapping": [], "note": "属于学习精通系统，不属于 Code-X；需要单独 L6.70.x 学习工具纯净重建。"},
        {"v1_source": "wendang_tiqu_gongju.py / wendang_tiqu_adapter.py", "status": "not_imported_in_codex", "v2_mapping": [], "note": "属于文档提取系统；应单独做文档链，不混入 Code-X。"},
        {"v1_source": "tiangong_wangye_gongju.py / wangye_keduxing_adapter.py", "status": "not_imported_in_codex", "v2_mapping": [], "note": "属于网页/搜索读取系统；应单独接入 Provider/搜索链。"},
        {"v1_source": "jietu_adapter.py / shenzhuakuai_gongju.py", "status": "not_imported_in_codex", "v2_mapping": [], "note": "属于截图/桌面观察/视觉链；可作为前端视觉子能力后续强化。"},
        {"v1_source": "chuanbangdai_gongju.py / tool_skill_shengchan_gongju.py", "status": "not_imported_in_codex", "v2_mapping": [], "note": "属于工具/技能生产系统；应单独进入 Tool-Skill 生产链。"},
        {"v1_source": "huihua_sousuo_gongju.py / zuoye_sousuo_gongju.py", "status": "not_imported_in_codex", "v2_mapping": [], "note": "属于会话/作业搜索；不应混入代码生产链。"},
    ]
    return {
        "status": "ok",
        "summary": "v1 Code-X 必需代码生产链语义已导入；v1 其他非代码工具未导入，需分系统单独纯净重建。",
        "code_x_essential_semantics_imported": True,
        "all_v1_tools_imported": False,
        "rows": rows,
        "redline": [
            "未复制 v1 源码", "未 import v1 模块", "未复用 v1 registry/executor/terminal/provider/self-iteration", "未引入后台 loop",
        ],
        "next_action_hint": _hint("code_x_world_class_readiness_check", "确认 Code-X 结构能力后，再规划 v1 非代码工具分系统导入。"),
    }
