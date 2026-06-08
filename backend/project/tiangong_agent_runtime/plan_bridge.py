"""最小计划桥：把显式文本任务转成受控工具计划。"""

from __future__ import annotations

import json
import shlex

from .tool_invocation import ToolInvocation


class PlanBridge:
    """第一版只做可审计的显式/半显式计划，不做自由工具执行。"""

    def build_plan(self, user_message: str) -> list[ToolInvocation]:
        text = user_message.strip()
        if not text:
            return []

        segments = _split_chain(text)
        if len(segments) > 1:
            plan: list[ToolInvocation] = []
            for segment in segments:
                plan.extend(self.build_plan(segment))
            return plan

        lowered = text.lower()

        # 显式工具 JSON/DSL 以后再扩展；当前支持 CLI 风格短命令与 && / 换行多步骤链。
        if (
            lowered.startswith("p0-system2-build")
            or lowered.startswith("p0-system-two-build")
            or lowered.startswith("l6.39")
            or lowered.startswith("l6_39")
            or lowered.startswith("p0 接入二")
            or lowered.startswith("p0系统接入二")
            or lowered.startswith("p0 系统接入二")
            or "memory / audit / recovery / qualitygate" in lowered
            or "memory/audit/recovery/qualitygate" in lowered
            or ("memory" in lowered and "audit" in lowered and "recovery" in lowered and ("qualitygate" in lowered or "quality gate" in lowered or "质量门" in lowered))
            or ("记忆" in lowered and "审计" in lowered and "恢复" in lowered and "质量门" in lowered)
        ):
            notes = _tail(text, default="")
            return [
                ToolInvocation("build_recovery_coordination", {"notes": notes, "max_items": 8, "step_budget": 10}),
                ToolInvocation("build_l6_39_memory_integration", {"notes": notes, "max_items": 8}),
                ToolInvocation("build_l6_39_audit_integration", {"notes": notes, "max_events": 24}),
                ToolInvocation("build_l6_39_recovery_integration", {"notes": notes, "max_items": 8}),
                ToolInvocation("build_l6_39_quality_gate_integration", {"notes": notes}),
                ToolInvocation("build_l6_39_p0_integration", {"notes": notes}),
            ]
        if (
            lowered.startswith("p0-system-build")
            or lowered.startswith("l6.38")
            or lowered.startswith("l6_38")
            or lowered.startswith("p0 接入")
            or lowered.startswith("p0系统接入")
            or lowered.startswith("p0 系统接入")
            or "provider / budget / skill / handoff" in lowered
            or "provider/budget/skill/handoff" in lowered
            or ("provider" in lowered and "budget" in lowered and "skill" in lowered and "handoff" in lowered)
        ):
            notes = _tail(text, default="")
            return [
                ToolInvocation("build_provider_adaptation", {"path": ".", "notes": notes}),
                ToolInvocation("synthesize_experience_candidates", {"notes": notes, "max_candidates": 8}),
                ToolInvocation("queue_skill_candidates", {"notes": notes, "max_items": 8}),
                ToolInvocation("build_l6_38_provider_integration", {"notes": notes, "requested_call_mode": "dry_run"}),
                ToolInvocation("build_l6_38_budget_snapshot", {"notes": notes, "max_steps": 10, "planned_steps": 4}),
                ToolInvocation("build_l6_38_skill_integration", {"notes": notes, "max_items": 8}),
                ToolInvocation("build_l6_38_handoff_integration", {"notes": notes, "max_subtasks": 3}),
                ToolInvocation("build_l6_38_p0_integration", {"notes": notes}),
            ]
        if (
            lowered.startswith("planner-context")
            or lowered.startswith("planner context")
            or lowered.startswith("planner-context-build")
            or lowered.startswith("统一 planner")
            or lowered.startswith("统一planner")
            or lowered.startswith("planner 接入")
            or lowered.startswith("l6.31")
            or "unifiedplannercontext" in lowered
            or "统一 planner" in lowered
            or "统一planner" in lowered
            or ("planner" in lowered and ("接入" in lowered or "收口" in lowered or "上下文" in lowered))
        ):
            notes = _tail(text, default="")
            return [
                ToolInvocation("build_shell_system_mount", {"notes": notes}),
                ToolInvocation("build_learning_convergence", {"notes": notes, "max_items": 16}),
                ToolInvocation("build_recovery_coordination", {"notes": notes, "max_items": 16, "step_budget": 20}),
                ToolInvocation("build_delivery_standardization", {"path": ".", "notes": notes}),
                ToolInvocation("build_provider_adaptation", {"path": ".", "notes": notes}),
                ToolInvocation("build_governance_execution", {"notes": notes, "max_items": 16}),
                ToolInvocation("build_planner_context", {"notes": notes, "max_items": 16, "task_id": "l6_31_unified_planner"}),
            ]

        if lowered.startswith("scan ") or lowered in {"scan", "扫描项目", "项目扫描", "inspect project", "project scan"}:
            path = _tail(text, default=".")
            return [ToolInvocation("scan_project", {"path": path})]
        if lowered.startswith("diagnose ") or lowered in {"diagnose", "诊断", "工程诊断", "诊断项目", "project diagnose"}:
            path = _tail(text, default=".")
            return [ToolInvocation("scan_project", {"path": path}), ToolInvocation("diagnose_project", {"path": path})]
        if (
            lowered.startswith("governance-build")
            or lowered.startswith("governance")
            or lowered.startswith("governance-execution")
            or lowered.startswith("治理执行力化")
            or lowered.startswith("治理护栏")
            or lowered.startswith("l6.30")
            or "治理执行力化" in lowered
            or "a0-a4" in lowered and "a5" in lowered
            or ("治理" in lowered and ("执行力" in lowered or "护栏" in lowered or "快车道" in lowered))
        ):
            notes = _tail(text, default="")
            return [
                ToolInvocation("build_recovery_coordination", {"notes": notes, "max_items": 12, "step_budget": 20}),
                ToolInvocation("build_governance_execution", {"notes": notes, "max_items": 12}),
            ]

        if (
            lowered.startswith("recovery-build")
            or lowered.startswith("recovery")
            or lowered.startswith("long-chain-recovery")
            or lowered.startswith("自修复联动")
            or lowered.startswith("恢复协调")
            or lowered.startswith("l6.29")
            or "自修复 + 多智能体 + 预算" in lowered
            or "恢复协调" in lowered
            or ("自修复" in lowered and ("多智能体" in lowered or "预算" in lowered or "续接" in lowered))
        ):
            notes = _tail(text, default="")
            return [
                ToolInvocation("build_learning_convergence", {"notes": notes, "max_items": 12}),
                ToolInvocation("build_recovery_coordination", {"notes": notes, "max_items": 12, "step_budget": 20}),
            ]

        if (
            lowered.startswith("learning-converge")
            or lowered.startswith("learning convergence")
            or lowered.startswith("经验合流")
            or lowered.startswith("学习合流")
            or lowered.startswith("skill-tool-converge")
            or lowered.startswith("l6.28")
            or "经验 / skill / tool" in lowered
            or "经验 skill tool" in lowered
            or "skill/tool 合流" in lowered
            or "执行合流" in lowered
            or ("合流" in lowered and ("经验" in lowered or "skill" in lowered or "tool" in lowered or "工具" in lowered))
        ):
            notes = _tail(text, default="")
            return [
                ToolInvocation("synthesize_experience_candidates", {"notes": notes, "max_candidates": 18}),
                ToolInvocation("queue_skill_candidates", {"notes": notes, "max_items": 18}),
                ToolInvocation("queue_tool_production_requests", {"notes": notes, "max_items": 18}),
                ToolInvocation("build_execution_exoskeleton", {"notes": notes, "max_items": 18}),
                ToolInvocation("build_learning_convergence", {"notes": notes, "max_items": 18}),
                ToolInvocation("learning_asset_contract_normalize", {"notes": notes, "max_items": 24}),
                ToolInvocation("learning_asset_contract_validate", {}),
            ]

        if (
            lowered.startswith("provider-build")
            or lowered.startswith("provider")
            or lowered.startswith("model-provider")
            or lowered.startswith("模型provider")
            or lowered.startswith("模型 provider")
            or lowered.startswith("provider适配")
            or lowered.startswith("l6.27")
            or "provider 适配" in lowered
            or "provider适配" in lowered
            or "真实 provider" in lowered
        ):
            path = _tail(text, default=".")
            return [ToolInvocation("build_provider_adaptation", {"path": path, "notes": text})]

        if (
            lowered.startswith("delivery-standard")
            or lowered.startswith("delivery standard")
            or lowered.startswith("交付链标准化")
            or lowered.startswith("标准化交付")
            or lowered.startswith("标准交付链")
            or lowered.startswith("l6.26")
            or "交付链标准化" in lowered
        ):
            path = _tail(text, default=".")
            return [ToolInvocation("build_delivery_standardization", {"path": path, "notes": text})]

        if (
            lowered.startswith("repair-plan")
            or lowered.startswith("project-repair")
            or lowered.startswith("工程修复计划")
            or lowered.startswith("项目修复计划")
            or lowered.startswith("l6.25")
            or "patchplan" in lowered
            or "工程修复外壳" in lowered
        ):
            path = _tail(text, default=".")
            return [
                ToolInvocation("scan_project", {"path": path}),
                ToolInvocation("run_python_quality_check", {"command": "compileall", "target": path}),
                ToolInvocation("diagnose_project", {"path": path}),
                ToolInvocation("build_project_repair_plan", {"path": path, "notes": text, "max_targets": 12}),
            ]

        if lowered.startswith("repair-loop") or lowered.startswith("repair loop") or "修复循环" in lowered:
            path = _tail(text, default=".") if lowered.startswith("repair") else "."
            return [
                ToolInvocation("scan_project", {"path": path}),
                ToolInvocation("run_python_quality_check", {"command": "compileall", "target": path}),
                ToolInvocation("run_python_quality_check", {"command": "pytest", "target": path}),
                ToolInvocation("diagnose_project", {"path": path}),
                ToolInvocation("write_workspace_file", {"path": "reports/l6_17_repair_loop_note.md", "content": "# L6.17 修复循环记录\n\n请查看 Runtime 运行报告和诊断摘要。\n"}),
            ]


        if (
            lowered.startswith("asset-adapter")
            or lowered.startswith("learning-asset-adapter")
            or lowered.startswith("adapter-template")
            or lowered.startswith("学习资产adapter")
            or lowered.startswith("学习资产 adapter")
            or lowered.startswith("adapter 模板")
            or ("adapter" in lowered and ("模板" in lowered or "template" in lowered) and ("asset" in lowered or "学习资产" in lowered))
        ):
            return _parse_learning_asset_adapter(text)

        if (
            lowered.startswith("asset-activate")
            or lowered.startswith("learning-asset-activate")
            or lowered.startswith("toolskill-activate")
            or lowered.startswith("学习资产激活")
            or lowered.startswith("候选激活")
            or lowered.startswith("注册激活")
            or lowered.startswith("激活资产")
            or ("激活" in lowered and ("候选" in lowered or "tool" in lowered or "skill" in lowered or "工具" in lowered or "学习资产" in lowered))
            or ("注册" in lowered and "可用" in lowered and ("tool" in lowered or "skill" in lowered or "工具" in lowered or "候选" in lowered))
        ):
            return _parse_learning_asset_activation(text)


        if (
            lowered.startswith("asset-release")
            or lowered.startswith("candidate-release")
            or lowered.startswith("learning-asset-release")
            or lowered.startswith("toolskill-release")
            or lowered.startswith("候选发布")
            or lowered.startswith("发布门")
            or lowered.startswith("注册申请")
            or ("发布门" in lowered and ("候选" in lowered or "tool" in lowered or "skill" in lowered or "工具" in lowered))
            or ("注册申请" in lowered and ("候选" in lowered or "tool" in lowered or "skill" in lowered or "工具" in lowered))
        ):
            return _parse_learning_asset_release_gate(text)

        if (
            lowered.startswith("asset-candidate-sandbox")
            or lowered.startswith("candidate-sandbox")
            or lowered.startswith("learning-asset-candidate-sandbox")
            or lowered.startswith("toolskill-candidate-sandbox")
            or lowered.startswith("候选包沙箱")
            or lowered.startswith("候选沙箱")
            or ("候选包" in lowered and "沙箱" in lowered)
            or ("真实" in lowered and "沙箱" in lowered and ("tool" in lowered or "skill" in lowered or "工具" in lowered or "候选" in lowered))
        ):
            return _parse_learning_asset_candidate_sandbox(text)

        if (
            lowered.startswith("asset-sandbox")
            or lowered.startswith("learning-asset-sandbox")
            or lowered.startswith("toolskill-sandbox")
            or lowered.startswith("沙箱对齐")
            or lowered.startswith("资产沙箱")
            or lowered.startswith("工具沙箱")
            or ("沙箱" in lowered and ("对齐" in lowered or "找找" in lowered) and ("asset" in lowered or "tool" in lowered or "skill" in lowered or "工具" in lowered or "资产" in lowered or "统一" in lowered))
        ):
            return _parse_learning_asset_sandbox(text)

        if (
            lowered.startswith("asset-contract")
            or lowered.startswith("learning-asset")
            or lowered.startswith("future-asset")
            or lowered.startswith("学习资产契约")
            or lowered.startswith("统一资产契约")
            or lowered.startswith("toolskill-contract")
            or "tool/skill 格式" in lowered
            or "tool 和 skill 格式" in lowered
            or "tool和skill格式" in lowered
            or "统一 tool" in lowered and "skill" in lowered
            or "自主学习" in lowered and "skill" in lowered and "tool" in lowered and ("统一" in lowered or "格式" in lowered)
            or "经验" in lowered and "skill" in lowered and "tool" in lowered and ("统一" in lowered or "格式" in lowered)
        ):
            return _parse_learning_asset_contract(text)

        if (
            lowered.startswith("runtime-tools")
            or lowered.startswith("runtime tools")
            or lowered.startswith("tool-registry")
            or lowered.startswith("tool registry")
            or lowered.startswith("工具注册表")
            or lowered.startswith("注册表对齐")
            or lowered.startswith("skill对齐")
            or lowered.startswith("skill 对齐")
            or "注册表对齐" in lowered
            or "skill对齐" in lowered
            or "skill 对齐" in lowered
            or "llm 实操" in lowered
            or "llm实操" in lowered
            or "工具对齐" in lowered
        ):
            return _parse_runtime_tools(text)

        if (
            lowered.startswith("v1-import")
            or lowered.startswith("v1 import")
            or lowered.startswith("v1导入")
            or lowered.startswith("v1 导入")
            or lowered.startswith("去重导入")
            or lowered.startswith("纯净导入")
            or "v1 去重" in lowered
            or "v1去重" in lowered
        ):
            return _parse_v1_import(text)

        if (
            lowered.startswith("code-x")
            or lowered.startswith("codex")
            or lowered.startswith("code x")
            or lowered.startswith("代码外骨骼")
            or "用 code-x" in lowered
            or "用codex" in lowered
            or "用 code x" in lowered
        ):
            return _parse_code_x(text)
        if lowered.startswith("list ") or lowered in {"list", "ls", "列目录", "列出目录"}:
            path = _tail(text, default=".")
            return [ToolInvocation("list_dir", {"path": path})]
        if lowered.startswith("ls "):
            path = _tail(text, default=".")
            return [ToolInvocation("list_dir", {"path": path})]
        if lowered.startswith("read ") or lowered.startswith("cat ") or lowered.startswith("读取 "):
            path = _tail(text, default="")
            return [ToolInvocation("read_file", {"path": path})]
        if lowered.startswith("write ") or lowered.startswith("写入 "):
            return _parse_write(text)
        if lowered.startswith("compileall") or lowered.startswith("python -m compileall") or "跑 compileall" in lowered:
            target = _tail(text, default=".") if lowered.startswith("compileall") else "."
            return [ToolInvocation("run_python_quality_check", {"command": "compileall", "target": target})]
        if lowered.startswith("pytest") or lowered.startswith("python -m pytest") or "跑 pytest" in lowered:
            target = _tail(text, default=".") if lowered.startswith("pytest") else "."
            return [ToolInvocation("run_python_quality_check", {"command": "pytest", "target": target})]
        if lowered.startswith("zip ") or lowered.startswith("打包 "):
            parts = shlex.split(text)
            source = parts[1] if len(parts) >= 2 else "."
            target = parts[2] if len(parts) >= 3 else "dist/tiangong_delivery.zip"
            return [ToolInvocation("create_zip_package", {"source": source, "target": target})]
        if lowered.startswith("release ") or lowered.startswith("发布 "):
            parts = shlex.split(text)
            target = parts[1] if len(parts) >= 2 else "dist/l6_19_release_bundle.zip"
            source = parts[2] if len(parts) >= 3 else "."
            return [ToolInvocation("create_release_bundle", {"source": source, "target": target})]
        if (
            lowered.startswith("shell-mount")
            or lowered.startswith("shell mount")
            or lowered.startswith("系统壳装")
            or lowered.startswith("壳装系统")
            or lowered.startswith("十八系统")
            or lowered.startswith("18系统")
            or "壳装" in lowered
            or "十八系统" in lowered
            or "18 个系统" in lowered
            or "18个系统" in lowered
        ):
            notes = _tail(text, default="")
            return [ToolInvocation("build_shell_system_mount", {"notes": notes})]

        if (
            lowered.startswith("exoskeleton")
            or lowered.startswith("外骨骼")
            or lowered.startswith("执行外骨骼")
            or lowered.startswith("llm外骨骼")
            or lowered.startswith("llm 外骨骼")
            or "外骨骼" in lowered
            or "执行力压缩" in lowered
        ):
            notes = _tail(text, default="")
            return [
                ToolInvocation("synthesize_experience_candidates", {"notes": notes, "max_candidates": 12}),
                ToolInvocation("queue_skill_candidates", {"notes": notes, "max_items": 12}),
                ToolInvocation("queue_tool_production_requests", {"notes": notes, "max_items": 12}),
                ToolInvocation("build_execution_exoskeleton", {"notes": notes, "max_items": 12}),
            ]
        if (
            lowered.startswith("tool-request")
            or lowered.startswith("tool request")
            or lowered.startswith("工具生产请求")
            or lowered.startswith("工具请求")
            or lowered.startswith("工具缺口入队")
            or ("工具" in lowered and ("生产请求" in lowered or "沙箱" in lowered or "验证前置" in lowered or "缺口入队" in lowered))
        ):
            notes = _tail(text, default="")
            return [
                ToolInvocation("synthesize_experience_candidates", {"notes": notes, "max_candidates": 20}),
                ToolInvocation("queue_tool_production_requests", {"notes": notes, "max_items": 20}),
            ]
        if (
            lowered.startswith("skill-queue")
            or lowered.startswith("技能候选入队")
            or lowered.startswith("技能版本化")
            or lowered.startswith("skill review")
            or ("技能" in lowered and ("审阅队列" in lowered or "入队" in lowered or "版本化" in lowered))
        ):
            notes = _tail(text, default="")
            return [
                ToolInvocation("synthesize_experience_candidates", {"notes": notes, "max_candidates": 20}),
                ToolInvocation("queue_skill_candidates", {"notes": notes, "max_items": 20}),
            ]
        if (
            lowered.startswith("reflect ")
            or lowered.startswith("experience ")
            or lowered.startswith("沉淀经验")
            or lowered.startswith("经验沉淀")
            or "总结经验" in lowered
            or "转化成技能" in lowered
            or "转化成工具" in lowered
        ):
            notes = _tail(text, default="")
            if lowered.startswith("沉淀经验") or lowered.startswith("经验沉淀"):
                notes = text.split(maxsplit=1)[1] if len(text.split(maxsplit=1)) > 1 else ""
            return [ToolInvocation("synthesize_experience_candidates", {"notes": notes})]
        return []


def _tail(text: str, default: str = "") -> str:
    try:
        parts = shlex.split(text)
    except ValueError:
        parts = text.split(maxsplit=1)
    return parts[1] if len(parts) >= 2 else default


def _parse_write(text: str) -> list[ToolInvocation]:
    # 格式：write path :: content
    if "::" not in text:
        return []
    left, content = text.split("::", 1)
    parts = shlex.split(left)
    if len(parts) < 2:
        return []
    return [ToolInvocation("write_workspace_file", {"path": parts[1], "content": content.lstrip()})]



def _split_chain(text: str) -> list[str]:
    """按安全的轻量分隔符拆分多步骤任务。

    支持换行和 `&&`。`;` 暂不作为默认分隔符，避免中文正文或 Windows 路径误切。
    """
    normalized = text.replace("\r\n", "\n")
    pieces: list[str] = []
    for line in normalized.split("\n"):
        for part in line.split(" && "):
            item = part.strip()
            if item:
                pieces.append(item)
    return pieces


def _parse_code_x(text: str) -> list[ToolInvocation]:
    """Code-X explicit DSL for usable Runtime registration.

    Supported examples:
    - code-x status
    - code-x skill
    - code-x readiness
    - code-x v1-audit
    - code-x smoke .
    - code-x repo-map .
    - code-x locate "bug description"
    - code-x search "symbol or behavior"
    - code-x pytest tests
    - code-x snapshot
    - code-x changed
    - code-x package . dist/code_x_delivery.zip
    - code-x tool <tool_name> {json_args}
    """
    try:
        parts = shlex.split(text)
    except ValueError:
        parts = text.split()
    if not parts:
        return []
    if len(parts) >= 2 and parts[0].lower() == "code" and parts[1].lower() == "x":
        parts = ["code-x"] + parts[2:]
    if len(parts) == 1:
        return [ToolInvocation("code_x_runtime_status", {})]
    cmd = parts[1].lower().replace("_", "-")
    tail = parts[2:]
    if cmd in {"status", "tools", "tool-list", "可用", "状态"}:
        return [ToolInvocation("code_x_runtime_status", {})]
    if cmd in {"skill", "guide", "workflow", "使用", "技能", "工作流"}:
        task_type = tail[0] if tail else "auto"
        phase = tail[1] if len(tail) > 1 else ""
        return [ToolInvocation("code_x_skill_guide", {"task_type": task_type, "phase": phase})]
    if cmd in {"readiness", "world-class", "world", "世界级", "能力确认"}:
        return [ToolInvocation("code_x_world_class_readiness_check", {})]
    if cmd in {"v1-audit", "import-audit", "导入审计", "v1审计"}:
        return [ToolInvocation("code_x_v1_import_audit", {})]
    if cmd in {"smoke", "check", "体检", "联调"}:
        return [ToolInvocation("code_x_smoke_workflow", {"path": tail[0] if tail else "."})]
    if cmd in {"repo-map", "repo", "map", "scan", "工程感知"}:
        return [ToolInvocation("repo_map", {"workspace_root": tail[0] if tail else "."})]
    if cmd in {"tree", "file-tree"}:
        return [ToolInvocation("file_tree_scan", {"workspace_root": tail[0] if tail else "."})]
    if cmd in {"rules", "project-rules"}:
        return [ToolInvocation("project_rules_reader", {"repo_root": tail[0] if tail else "."})]
    if cmd in {"fix", "repair", "bugfix", "修复", "修bug", "改bug"}:
        issue_text = " ".join(tail)
        return [
            ToolInvocation("code_x_skill_guide", {"task_type": "bug_fix", "phase": "start"}),
            ToolInvocation("project_rules_reader", {"repo_root": "."}),
            ToolInvocation("repo_map", {"workspace_root": "."}),
            ToolInvocation("issue_to_file_localizer", {"issue_text": issue_text}),
            ToolInvocation("workspace_snapshot", {}),
            ToolInvocation("patch_plan_generator", {"issue": issue_text}),
        ]
    if cmd in {"locate", "localize", "定位"}:
        return [ToolInvocation("issue_to_file_localizer", {"issue_text": " ".join(tail)})]
    if cmd in {"search", "semantic-search", "语义搜索"}:
        return [ToolInvocation("semantic_code_search", {"query": " ".join(tail)})]
    if cmd in {"symbols", "symbol"}:
        file_path = tail[0] if tail else "."
        query = " ".join(tail[1:]) if len(tail) > 1 else ""
        return [ToolInvocation("file_to_symbol_localizer", {"file_path": file_path, "query": query})]
    if cmd in {"pytest", "test", "测试"}:
        return [ToolInvocation("pytest_runner", {"test_path": tail[0] if tail else None})]
    if cmd in {"quality", "python-quality", "compile", "compileall"}:
        return [ToolInvocation("python_quality_runner", {})]
    if cmd in {"env", "probe", "环境"}:
        return [ToolInvocation("environment_probe", {})]
    if cmd in {"static", "static-analyzer", "静态检查"}:
        return [ToolInvocation("static_analyzer", {})]
    if cmd in {"snapshot", "快照"}:
        return [ToolInvocation("workspace_snapshot", {})]
    if cmd in {"changed", "changed-files", "变更"}:
        return [ToolInvocation("changed_files_index", {})]
    if cmd in {"package", "pack", "打包"}:
        include = [tail[0]] if tail else ["."]
        target = tail[1] if len(tail) > 1 else "dist/code_x_delivery.zip"
        return [ToolInvocation("code_x_package_workflow", {"include_paths": include, "output_zip": target})]
    if cmd == "tool" and tail:
        tool_name = tail[0]
        args: dict = {}
        if len(tail) > 1:
            raw = " ".join(tail[1:])
            try:
                parsed = json.loads(raw)
                if isinstance(parsed, dict):
                    args = parsed
            except json.JSONDecodeError:
                args = _parse_loose_object(raw) or {"query": raw, "issue_text": raw, "log_text": raw}
        return [ToolInvocation(tool_name, args)]
    return [ToolInvocation("code_x_runtime_status", {"unrecognized_command": cmd, "raw": text})]


def _parse_v1_import(text: str) -> list[ToolInvocation]:
    """v1 clean import explicit DSL."""
    try:
        parts = shlex.split(text)
    except ValueError:
        parts = text.split()
    if not parts:
        return []
    if len(parts) >= 2 and parts[0].lower() == "v1" and parts[1].lower() in {"import", "导入"}:
        parts = ["v1-import"] + parts[2:]
    if parts and parts[0] in {"v1导入", "去重导入", "纯净导入"}:
        parts = ["v1-import"] + parts[1:]
    if len(parts) == 1:
        return [ToolInvocation("v1_clean_import_status", {})]
    cmd = parts[1].lower().replace("_", "-")
    tail = parts[2:]
    joined = " ".join(tail)
    if cmd in {"status", "状态", "tools", "tool-list"}:
        return [ToolInvocation("v1_clean_import_status", {})]
    if cmd in {"audit", "import-audit", "dedupe", "审计", "去重"}:
        return [ToolInvocation("v1_clean_import_audit", {})]
    if cmd in {"guide", "skill", "usage", "使用", "指南"}:
        return [ToolInvocation("v1_clean_import_guide", {"domain": tail[0] if tail else "all"})]
    if cmd in {"search", "file-search", "全文搜索", "搜索"}:
        return [ToolInvocation("workspace_text_search", {"query": joined})]
    if cmd in {"conversation", "chat", "history", "会话", "历史"}:
        return [ToolInvocation("conversation_history_search", {"query": joined})]
    if cmd in {"task", "zuoye", "homework", "抄作业", "作业"}:
        return [ToolInvocation("task_pattern_search", {"query": joined})]
    if cmd in {"experience", "mentor", "skill-search", "经验", "传帮带"}:
        return [ToolInvocation("experience_mentor_search", {"query": joined})]
    if cmd in {"document", "doc", "extract", "文档", "提取"}:
        return [ToolInvocation("document_text_extract", {"path": tail[0] if tail else ""})]
    if cmd in {"readability", "web-readability", "html", "网页可读性"}:
        return [ToolInvocation("web_readability_extract", {"html_or_text": joined})]
    if cmd in {"learning", "learn", "master", "学习", "学习精通"}:
        return [ToolInvocation("learning_master_plan", {"goal": joined})]
    if cmd in {"tool-skill", "toolskill", "asset", "production", "工具生产", "skill生产", "资产"}:
        return [ToolInvocation("tool_skill_blueprint", {"goal": joined})]
    return [ToolInvocation("v1_clean_import_status", {"unrecognized_command": cmd, "raw": text})]



def _parse_learning_asset_adapter(text: str) -> list[ToolInvocation]:
    """R21 practical learned adapter template DSL.

    Supported examples:
    - asset-adapter guide
    - asset-adapter templates
    - asset-adapter normalize pure_transform
    - asset-adapter validate schema_contract_check
    - asset-adapter smoke all
    - asset-adapter drill
    """
    try:
        parts = shlex.split(text)
    except ValueError:
        parts = text.split()
    if not parts:
        return [ToolInvocation("learning_asset_adapter_guide", {})]
    first = parts[0].lower()
    if len(parts) >= 2 and first in {"asset", "learning", "adapter"} and parts[1].lower() in {"adapter", "template", "模板"}:
        parts = ["asset-adapter"] + parts[2:]
    if first in {"学习资产adapter", "学习资产", "adapter模板", "adapter"}:
        parts = ["asset-adapter"] + parts[1:]
    if len(parts) == 1:
        return [ToolInvocation("learning_asset_adapter_guide", {})]
    cmd = parts[1].lower().replace("_", "-")
    tail = parts[2:]
    template_id = tail[0] if tail else "all"
    notes = " ".join(tail[1:] if tail else []) or text
    if cmd in {"guide", "help", "schema", "指南", "格式"}:
        return [ToolInvocation("learning_asset_adapter_guide", {})]
    if cmd in {"templates", "template", "list", "模板", "列表"}:
        return [ToolInvocation("learning_asset_adapter_template_list", {})]
    if cmd in {"normalize", "normalise", "归一化", "生成"}:
        return [ToolInvocation("learning_asset_adapter_template_normalize", {"template_id": template_id if template_id != "all" else "auto", "notes": notes})]
    if cmd in {"validate", "check", "校验", "验证"}:
        return [ToolInvocation("learning_asset_adapter_template_validate", {"template_id": template_id if template_id != "all" else "auto", "notes": notes})]
    if cmd in {"smoke", "test", "测试", "体检"}:
        return [ToolInvocation("learning_asset_adapter_template_smoke", {"template_id": template_id})]
    if cmd in {"drill", "simulate", "full", "all", "演练", "全链", "模拟"}:
        return [
            ToolInvocation("learning_asset_adapter_guide", {}),
            ToolInvocation("learning_asset_adapter_template_list", {}),
            ToolInvocation("learning_asset_adapter_template_smoke", {"template_id": "all"}),
            ToolInvocation("learning_asset_adapter_drill", {"notes": notes}),
            ToolInvocation("learning_asset_activation_smoke", {"sample_args": {"query": notes, "goal": "r21 adapter activation smoke"}}),
            ToolInvocation("runtime_tool_alignment_check", {"include_cards": True}),
            ToolInvocation("runtime_llm_operational_drill", {}),
        ]
    return [
        ToolInvocation("learning_asset_adapter_guide", {"unrecognized_command": cmd, "raw": text}),
        ToolInvocation("learning_asset_adapter_template_list", {}),
    ]


def _parse_learning_asset_activation(text: str) -> list[ToolInvocation]:
    """R20 learning asset activation DSL.

    Supported examples:
    - asset-activate guide
    - asset-activate apply
    - asset-activate status
    - asset-activate smoke
    - asset-activate drill pytest missing tests
    - asset-activate call <learned_tool_name> {json_args}
    """
    try:
        parts = shlex.split(text)
    except ValueError:
        parts = text.split()
    if not parts:
        return [ToolInvocation("learning_asset_activation_guide", {})]
    first = parts[0].lower()
    if len(parts) >= 2 and first in {"asset", "learning", "toolskill"} and parts[1].lower() in {"activate", "activation", "激活"}:
        parts = ["asset-activate"] + parts[2:]
    if first in {"学习资产激活", "候选激活", "注册激活", "激活资产"}:
        parts = ["asset-activate"] + parts[1:]
    if len(parts) == 1:
        return [ToolInvocation("learning_asset_activation_guide", {})]
    cmd = parts[1].lower().replace("_", "-")
    tail = parts[2:]
    notes = " ".join(tail) or text
    if cmd in {"guide", "schema", "help", "指南", "格式"}:
        return [ToolInvocation("learning_asset_activation_guide", {})]
    if cmd in {"status", "list", "active", "状态", "列表", "可用"}:
        return [ToolInvocation("learning_asset_activation_status", {})]
    if cmd in {"apply", "activate", "register", "release", "注册", "激活", "应用"}:
        return [ToolInvocation("learning_asset_activation_apply", {"notes": notes})]
    if cmd in {"smoke", "check", "test", "测试", "体检"}:
        return [ToolInvocation("learning_asset_activation_smoke", {"sample_args": {"query": notes, "goal": "r20 activation smoke"}})]
    if cmd in {"call", "tool", "调用"} and tail:
        tool_name = tail[0]
        args: dict = {}
        if len(tail) > 1:
            raw = " ".join(tail[1:])
            try:
                parsed = json.loads(raw)
                args = parsed if isinstance(parsed, dict) else {"value": parsed}
            except json.JSONDecodeError:
                args = _parse_loose_object(raw) or {"query": raw, "goal": raw, "notes": raw}
        return [ToolInvocation(tool_name, args)]
    if cmd in {"drill", "simulate", "full", "all", "演练", "全链", "模拟"}:
        return [
            ToolInvocation("learning_asset_activation_guide", {}),
            ToolInvocation("synthesize_experience_candidates", {"notes": notes, "max_candidates": 12}),
            ToolInvocation("queue_skill_candidates", {"notes": notes, "max_items": 12}),
            ToolInvocation("queue_tool_production_requests", {"notes": notes, "max_items": 12}),
            ToolInvocation("learning_asset_contract_normalize", {"notes": notes, "max_items": 24}),
            ToolInvocation("learning_asset_contract_validate", {}),
            ToolInvocation("learning_asset_sandbox_align", {"notes": notes}),
            ToolInvocation("learning_asset_sandbox_validate", {"notes": notes}),
            ToolInvocation("learning_asset_candidate_sandbox_build", {"notes": notes, "max_items": 12}),
            ToolInvocation("learning_asset_candidate_sandbox_validate", {"notes": notes}),
            ToolInvocation("learning_asset_candidate_sandbox_review", {"notes": notes}),
            ToolInvocation("learning_asset_release_gate_check", {"notes": notes}),
            ToolInvocation("learning_asset_activation_apply", {"notes": notes}),
            ToolInvocation("learning_asset_activation_smoke", {"sample_args": {"query": notes, "goal": "r20 activation drill"}}),
            ToolInvocation("runtime_tool_alignment_check", {"include_cards": True}),
            ToolInvocation("runtime_llm_operational_drill", {}),
        ]
    return [
        ToolInvocation("learning_asset_activation_guide", {"unrecognized_command": cmd, "raw": text}),
        ToolInvocation("learning_asset_activation_status", {}),
    ]


def _parse_learning_asset_release_gate(text: str) -> list[ToolInvocation]:
    """R19 execution-first candidate release gate DSL.

    Supported examples:
    - asset-release guide
    - asset-release gate
    - asset-release drill pytest missing tests
    """
    try:
        parts = shlex.split(text)
    except ValueError:
        parts = text.split()
    if not parts:
        return [ToolInvocation("learning_asset_release_gate_guide", {})]
    first = parts[0].lower()
    if len(parts) >= 2 and first in {"asset", "candidate", "learning", "toolskill"} and parts[1].lower() in {"release", "发布", "发布门"}:
        parts = ["asset-release"] + parts[2:]
    if first in {"候选发布", "发布门", "注册申请", "候选注册"}:
        parts = ["asset-release"] + parts[1:]
    if len(parts) == 1:
        return [ToolInvocation("learning_asset_release_gate_guide", {})]
    cmd = parts[1].lower().replace("_", "-")
    tail = parts[2:]
    notes = " ".join(tail) or text
    if cmd in {"guide", "status", "schema", "指南", "状态", "格式"}:
        return [ToolInvocation("learning_asset_release_gate_guide", {})]
    if cmd in {"gate", "check", "release", "registration", "request", "注册", "申请", "发布门", "质量门"}:
        return [ToolInvocation("learning_asset_release_gate_check", {"notes": notes})]
    if cmd in {"drill", "simulate", "full", "all", "演练", "全链", "模拟"}:
        return [
            ToolInvocation("learning_asset_release_gate_guide", {}),
            ToolInvocation("synthesize_experience_candidates", {"notes": notes, "max_candidates": 12}),
            ToolInvocation("queue_skill_candidates", {"notes": notes, "max_items": 12}),
            ToolInvocation("queue_tool_production_requests", {"notes": notes, "max_items": 12}),
            ToolInvocation("learning_asset_contract_normalize", {"notes": notes, "max_items": 24}),
            ToolInvocation("learning_asset_contract_validate", {}),
            ToolInvocation("learning_asset_sandbox_align", {"notes": notes}),
            ToolInvocation("learning_asset_sandbox_validate", {"notes": notes}),
            ToolInvocation("learning_asset_candidate_sandbox_build", {"notes": notes, "max_items": 12}),
            ToolInvocation("learning_asset_candidate_sandbox_validate", {"notes": notes}),
            ToolInvocation("learning_asset_candidate_sandbox_review", {"notes": notes}),
            ToolInvocation("learning_asset_release_gate_check", {"notes": notes}),
        ]
    return [
        ToolInvocation("learning_asset_release_gate_guide", {"unrecognized_command": cmd, "raw": text}),
        ToolInvocation("learning_asset_release_gate_check", {"notes": notes}),
    ]


def _parse_learning_asset_candidate_sandbox(text: str) -> list[ToolInvocation]:
    """R18 Tool/Skill candidate package production sandbox DSL.

    Supported examples:
    - asset-candidate-sandbox guide
    - asset-candidate-sandbox build pytest missing tests
    - asset-candidate-sandbox validate
    - asset-candidate-sandbox review
    - asset-candidate-sandbox drill pytest missing tests
    """
    try:
        parts = shlex.split(text)
    except ValueError:
        parts = text.split()
    if not parts:
        return [ToolInvocation("learning_asset_candidate_sandbox_guide", {})]
    first = parts[0].lower()
    if len(parts) >= 3 and first in {"asset", "learning", "toolskill"} and parts[1].lower() in {"candidate", "候选"} and parts[2].lower() in {"sandbox", "沙箱"}:
        parts = ["asset-candidate-sandbox"] + parts[3:]
    if len(parts) >= 2 and first in {"candidate", "候选包", "候选"} and parts[1].lower() in {"sandbox", "沙箱"}:
        parts = ["asset-candidate-sandbox"] + parts[2:]
    if first in {"候选包沙箱", "候选沙箱", "真实沙箱"}:
        parts = ["asset-candidate-sandbox"] + parts[1:]
    if len(parts) == 1:
        notes = text
        return [
            ToolInvocation("learning_asset_candidate_sandbox_guide", {}),
            ToolInvocation("synthesize_experience_candidates", {"notes": notes, "max_candidates": 12}),
            ToolInvocation("queue_skill_candidates", {"notes": notes, "max_items": 12}),
            ToolInvocation("queue_tool_production_requests", {"notes": notes, "max_items": 12}),
            ToolInvocation("learning_asset_contract_normalize", {"notes": notes, "max_items": 24}),
            ToolInvocation("learning_asset_contract_validate", {}),
            ToolInvocation("learning_asset_sandbox_align", {"notes": notes}),
            ToolInvocation("learning_asset_sandbox_validate", {"notes": notes}),
            ToolInvocation("learning_asset_candidate_sandbox_build", {"notes": notes, "max_items": 12}),
            ToolInvocation("learning_asset_candidate_sandbox_validate", {"notes": notes}),
            ToolInvocation("learning_asset_candidate_sandbox_review", {"notes": notes}),
        ]
    cmd = parts[1].lower().replace("_", "-")
    tail = parts[2:]
    notes = " ".join(tail) or text
    if cmd in {"guide", "status", "schema", "指南", "状态", "格式"}:
        return [ToolInvocation("learning_asset_candidate_sandbox_guide", {})]
    if cmd in {"build", "produce", "materialize", "生成", "生产", "落盘"}:
        return [ToolInvocation("learning_asset_candidate_sandbox_build", {"notes": notes, "max_items": 12})]
    if cmd in {"validate", "check", "smoke", "scan", "校验", "验证", "扫描"}:
        return [ToolInvocation("learning_asset_candidate_sandbox_validate", {"notes": notes})]
    if cmd in {"review", "registration", "gate", "审阅", "注册审阅"}:
        return [ToolInvocation("learning_asset_candidate_sandbox_review", {"notes": notes})]
    if cmd in {"drill", "simulate", "full", "all", "演练", "全链", "模拟"}:
        return [
            ToolInvocation("learning_asset_candidate_sandbox_guide", {}),
            ToolInvocation("synthesize_experience_candidates", {"notes": notes, "max_candidates": 12}),
            ToolInvocation("queue_skill_candidates", {"notes": notes, "max_items": 12}),
            ToolInvocation("queue_tool_production_requests", {"notes": notes, "max_items": 12}),
            ToolInvocation("learning_asset_contract_normalize", {"notes": notes, "max_items": 24}),
            ToolInvocation("learning_asset_contract_validate", {}),
            ToolInvocation("learning_asset_sandbox_align", {"notes": notes}),
            ToolInvocation("learning_asset_sandbox_validate", {"notes": notes}),
            ToolInvocation("learning_asset_candidate_sandbox_build", {"notes": notes, "max_items": 12}),
            ToolInvocation("learning_asset_candidate_sandbox_validate", {"notes": notes}),
            ToolInvocation("learning_asset_candidate_sandbox_review", {"notes": notes}),
        ]
    return [
        ToolInvocation("learning_asset_candidate_sandbox_guide", {"unrecognized_command": cmd, "raw": text}),
        ToolInvocation("learning_asset_candidate_sandbox_build", {"notes": notes, "max_items": 12}),
        ToolInvocation("learning_asset_candidate_sandbox_validate", {"notes": notes}),
        ToolInvocation("learning_asset_candidate_sandbox_review", {"notes": notes}),
    ]


def _parse_learning_asset_sandbox(text: str) -> list[ToolInvocation]:
    """R17 Tool/Skill asset sandbox alignment DSL.

    Supported examples:
    - asset-sandbox guide
    - asset-sandbox align
    - asset-sandbox validate
    - asset-sandbox drill pytest missing tests
    """
    try:
        parts = shlex.split(text)
    except ValueError:
        parts = text.split()
    if not parts:
        return [ToolInvocation("learning_asset_sandbox_guide", {})]
    first = parts[0].lower()
    if len(parts) >= 2 and first in {"asset", "learning", "toolskill"} and parts[1].lower() in {"sandbox", "沙箱"}:
        parts = ["asset-sandbox"] + parts[2:]
    if first in {"沙箱对齐", "资产沙箱", "工具沙箱"}:
        parts = ["asset-sandbox"] + parts[1:]
    if len(parts) == 1:
        notes = text
        return [
            ToolInvocation("learning_asset_sandbox_guide", {}),
            ToolInvocation("synthesize_experience_candidates", {"notes": notes, "max_candidates": 12}),
            ToolInvocation("queue_skill_candidates", {"notes": notes, "max_items": 12}),
            ToolInvocation("queue_tool_production_requests", {"notes": notes, "max_items": 12}),
            ToolInvocation("learning_asset_contract_normalize", {"notes": notes, "max_items": 24}),
            ToolInvocation("learning_asset_contract_validate", {}),
            ToolInvocation("learning_asset_sandbox_align", {"notes": notes}),
            ToolInvocation("learning_asset_sandbox_validate", {"notes": notes}),
        ]
    cmd = parts[1].lower().replace("_", "-")
    tail = parts[2:]
    notes = " ".join(tail) or text
    if cmd in {"guide", "status", "schema", "指南", "状态", "格式"}:
        return [ToolInvocation("learning_asset_sandbox_guide", {})]
    if cmd in {"align", "alignment", "对齐", "映射"}:
        return [ToolInvocation("learning_asset_sandbox_align", {"notes": notes})]
    if cmd in {"validate", "check", "校验", "验证", "复核"}:
        return [ToolInvocation("learning_asset_sandbox_validate", {"notes": notes})]
    if cmd in {"drill", "simulate", "full", "all", "演练", "全链", "模拟"}:
        return [
            ToolInvocation("learning_asset_sandbox_guide", {}),
            ToolInvocation("synthesize_experience_candidates", {"notes": notes, "max_candidates": 12}),
            ToolInvocation("queue_skill_candidates", {"notes": notes, "max_items": 12}),
            ToolInvocation("queue_tool_production_requests", {"notes": notes, "max_items": 12}),
            ToolInvocation("learning_asset_contract_normalize", {"notes": notes, "max_items": 24}),
            ToolInvocation("learning_asset_contract_validate", {}),
            ToolInvocation("learning_asset_sandbox_align", {"notes": notes}),
            ToolInvocation("learning_asset_sandbox_validate", {"notes": notes}),
        ]
    return [
        ToolInvocation("learning_asset_sandbox_guide", {"unrecognized_command": cmd, "raw": text}),
        ToolInvocation("learning_asset_sandbox_align", {"notes": notes}),
        ToolInvocation("learning_asset_sandbox_validate", {"notes": notes}),
    ]


def _parse_learning_asset_contract(text: str) -> list[ToolInvocation]:
    """Future autonomous-learning Tool/Skill asset contract DSL.

    Supported examples:
    - asset-contract guide
    - asset-contract normalize
    - asset-contract validate
    - asset-contract drill
    """
    try:
        parts = shlex.split(text)
    except ValueError:
        parts = text.split()
    if not parts:
        return [ToolInvocation("learning_asset_contract_guide", {})]
    first = parts[0].lower()
    if len(parts) >= 2 and first in {"asset", "learning", "future"} and parts[1].lower() in {"contract", "asset"}:
        parts = ["asset-contract"] + parts[2:]
    if first in {"学习资产契约", "统一资产契约", "toolskill-contract"}:
        parts = ["asset-contract"] + parts[1:]
    if len(parts) == 1:
        return [
            ToolInvocation("learning_asset_contract_guide", {}),
            ToolInvocation("learning_asset_contract_normalize", {"notes": text, "max_items": 24}),
            ToolInvocation("learning_asset_contract_validate", {}),
        ]
    cmd = parts[1].lower().replace("_", "-")
    tail = parts[2:]
    notes = " ".join(tail)
    if cmd in {"guide", "status", "schema", "指南", "格式", "标准"}:
        return [ToolInvocation("learning_asset_contract_guide", {})]
    if cmd in {"normalize", "normalise", "align", "归一", "归一化", "对齐"}:
        return [ToolInvocation("learning_asset_contract_normalize", {"notes": notes, "max_items": 24})]
    if cmd in {"validate", "check", "校验", "验证"}:
        return [ToolInvocation("learning_asset_contract_validate", {})]
    if cmd in {"drill", "simulate", "full", "all", "演练", "全链", "模拟"}:
        return [
            ToolInvocation("synthesize_experience_candidates", {"notes": notes or text, "max_candidates": 12}),
            ToolInvocation("queue_skill_candidates", {"notes": notes or text, "max_items": 12}),
            ToolInvocation("queue_tool_production_requests", {"notes": notes or text, "max_items": 12}),
            ToolInvocation("learning_asset_contract_normalize", {"notes": notes or text, "max_items": 24}),
            ToolInvocation("learning_asset_contract_validate", {}),
        ]
    return [
        ToolInvocation("learning_asset_contract_guide", {"unrecognized_command": cmd, "raw": text}),
        ToolInvocation("learning_asset_contract_normalize", {"notes": text, "max_items": 24}),
        ToolInvocation("learning_asset_contract_validate", {}),
    ]


def _parse_runtime_tools(text: str) -> list[ToolInvocation]:
    """Global Runtime tool registry/Skill alignment DSL.

    Supported examples:
    - runtime-tools align
    - runtime-tools drill
    - runtime-tools guide
    - runtime-tools tool <tool_name> {json_args}
    """
    try:
        parts = shlex.split(text)
    except ValueError:
        parts = text.split()
    if not parts:
        return [ToolInvocation("runtime_tool_alignment_check", {})]
    # Normalize Chinese / spaced aliases to a stable pseudo command.
    first = parts[0].lower()
    if len(parts) >= 2 and first == "runtime" and parts[1].lower() == "tools":
        parts = ["runtime-tools"] + parts[2:]
    if first in {"工具注册表", "注册表对齐", "skill对齐", "skill", "工具对齐"}:
        parts = ["runtime-tools"] + parts[1:]
    if len(parts) == 1:
        return [ToolInvocation("runtime_tool_alignment_check", {})]
    cmd = parts[1].lower().replace("_", "-")
    tail = parts[2:]
    if cmd in {"align", "alignment", "status", "check", "guide", "skill", "registry", "对齐", "状态", "指南", "注册表"}:
        return [ToolInvocation("runtime_tool_alignment_check", {})]
    if cmd in {"drill", "simulate", "simulation", "llm", "实操", "演练", "模拟"}:
        return [ToolInvocation("runtime_llm_operational_drill", {})]
    if cmd == "tool" and tail:
        tool_name = tail[0]
        args: dict = {}
        if len(tail) > 1:
            raw = " ".join(tail[1:])
            try:
                parsed = json.loads(raw)
                if isinstance(parsed, dict):
                    args = parsed
                else:
                    args = {"value": parsed}
            except json.JSONDecodeError:
                args = _parse_loose_object(raw) or {"query": raw, "notes": raw, "text": raw, "analysis": raw}
        return [ToolInvocation(tool_name, args)]
    return [ToolInvocation("runtime_tool_alignment_check", {"unrecognized_command": cmd, "raw": text})]



def _parse_loose_object(raw: str) -> dict | None:
    """Parse shlex-stripped JSON like {query:after reload} for CLI ergonomics."""
    text = raw.strip()
    if not (text.startswith("{") and text.endswith("}") and ":" in text):
        return None
    inner = text[1:-1].strip()
    if not inner:
        return {}
    result: dict[str, str] = {}
    for part in inner.split(","):
        if ":" not in part:
            return None
        key, value = part.split(":", 1)
        key = key.strip().strip("'\"")
        value = value.strip().strip("'\"")
        if not key:
            return None
        result[key] = value
    return result
