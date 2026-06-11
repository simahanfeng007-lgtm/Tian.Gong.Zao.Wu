"""最小计划桥：把显式文本任务转成受控工具计划。"""

from __future__ import annotations

import json
import re
import shlex

from .tool_invocation import ToolInvocation


class PlanBridge:
    """第一版只做可审计的显式/半显式计划，不做自由工具执行。"""

    def build_plan(self, user_message: str) -> list[ToolInvocation]:
        text = user_message.strip()
        if not text:
            return []

        if "[桌面端主机文件访问提示]" not in text and "[Runtime本地文件交接]" not in text:
            segments = _split_chain(text)
            if len(segments) > 1:
                plan: list[ToolInvocation] = []
                for segment in segments:
                    plan.extend(self.build_plan(segment))
                return plan

        lowered = text.lower()

        sha256_plan = _parse_file_sha256_task(text)
        if sha256_plan:
            return sha256_plan

        python_calc_plan = _parse_python_calculation_task(text)
        if python_calc_plan:
            return python_calc_plan

        handoff_plan = _parse_runtime_file_handoff_task(text)
        if handoff_plan:
            return handoff_plan

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

        # 有桌面桥主机路径提示时，先让 host_file_task 把“桌面/下载/文档 + 文件名”解析成
        # 工作区相对路径，再进入 document_parse / document_apply_rewrite，避免文档上下文桥
        # 只捕获裸文件名而丢失真实 host access base。
        if "[桌面端主机文件访问提示]" in text:
            host_file_plan = _parse_host_file_task(text)
            if host_file_plan:
                return host_file_plan

        if lowered.startswith("write ") or lowered.startswith("鍐欏叆 "):
            return _parse_write(text)
        if lowered.startswith("read ") or lowered.startswith("cat ") or lowered.startswith("璇诲彇 "):
            path = _tail(text, default="")
            suffix = ("." + path.rsplit(".", 1)[-1].lower()) if "." in path else ""
            tool_name = "document_parse" if suffix in _DOCUMENT_PARSE_EXTENSIONS else "read_file"
            return [ToolInvocation(tool_name, {"path": path})]

        document_context_plan = _parse_document_context_task(text)
        if document_context_plan:
            return document_context_plan

        host_file_plan = _parse_host_file_task(text)
        if host_file_plan:
            return host_file_plan
        natural_write_plan = _parse_natural_workspace_write(text)
        if natural_write_plan:
            return natural_write_plan
        if _looks_like_generic_test_task(lowered):
            return [ToolInvocation("run_python_quality_check", {"command": "pytest", "target": "."})]
        if _looks_like_generic_compile_task(lowered):
            return [ToolInvocation("run_python_quality_check", {"command": "compileall", "target": "."})]
        if _looks_like_generic_package_task(lowered):
            return [ToolInvocation("create_zip_package", {"source": ".", "target": "dist/tiangong_delivery.zip"})]
        if lowered.startswith("list ") or lowered in {"list", "ls", "列目录", "列出目录"}:
            path = _tail(text, default=".")
            return [ToolInvocation("list_dir", {"path": path})]
        if lowered.startswith("ls "):
            path = _tail(text, default=".")
            return [ToolInvocation("list_dir", {"path": path})]
        if lowered.startswith("read ") or lowered.startswith("cat ") or lowered.startswith("读取 "):
            path = _tail(text, default="")
            suffix = ("." + path.rsplit(".", 1)[-1].lower()) if "." in path else ""
            # L6.72.51：仅 docx/pdf/xlsx/pptx/csv 等真实文档容器按 read 进入 document_parse；txt/py/js 等普通文件不再被文档系统劫持。
            tool_name = "document_parse" if suffix in _DOCUMENT_PARSE_EXTENSIONS else "read_file"
            return [ToolInvocation(tool_name, {"path": path})]
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



_HOST_HINT_KEY_MAP = {
    "desktop": "desktop_relative_path",
    "downloads": "downloads_relative_path",
    "documents": "documents_relative_path",
}

_FOLDER_SYNONYMS = {
    "desktop": ("桌面", "桌面文件夹", "onedrive 桌面", "one drive 桌面", "desktop", "onedrive desktop"),
    "downloads": ("下载目录", "下载文件夹", "下载文件", "下载", "downloads", "download folder", "download"),
    "documents": ("文档目录", "文档文件夹", "文档里面", "我的文档", "documents", "my documents", "document folder"),
}

_READ_VERBS = ("读取", "读一下", "帮我读", "打开", "查看内容", "查看", "看内容", "看一下", "看下", "帮我看", "总结", "帮我总结", "分析", "解析", "read", "cat", "open", "view", "summarize", "summarise", "analyze", "analyse", "parse")
_LIST_VERBS = ("看看", "查看", "看下", "检查", "列出", "列目录", "有没有", "有什么", "扫描", "垃圾文件", "list", "ls", "inspect", "check", "show")
_DOCUMENT_PARSE_EXTENSIONS = {".docx", ".pdf", ".xlsx", ".pptx", ".csv"}
_WRITE_VERBS = ("写入", "创建", "生成", "保存", "修改", "删除", "覆盖", "打包", "发布", "新建", "移动", "重命名", "write", "create", "delete", "remove", "package", "zip", "rename", "move")


def _extract_host_hints(text: str) -> dict[str, str]:
    hints: dict[str, str] = {}
    for key, hint_key in _HOST_HINT_KEY_MAP.items():
        match = re.search(rf"(?:^|\n)\s*-?\s*{re.escape(hint_key)}\s*=\s*([^\n\r]+)", text, flags=re.IGNORECASE)
        if not match:
            continue
        value = match.group(1).strip().strip('"').strip("'")
        if value and not value.startswith("<") and _safe_relative_plan_path(value):
            hints[key] = value
    return hints


def _safe_relative_plan_path(value: str) -> bool:
    path = str(value or "").strip().replace("\\", "/")
    if not path or path.startswith("/") or path.startswith("~") or ".." in path.split("/"):
        return False
    if re.match(r"^[A-Za-z]:", path):
        return False
    return True


def _detect_host_folder(text: str) -> str:
    lowered = text.lower()
    for folder, names in _FOLDER_SYNONYMS.items():
        for name in names:
            if name.lower() in lowered:
                return folder
    return ""


def _join_relative_path(base: str, child: str) -> str:
    base_clean = base.strip().replace("\\", "/").strip("/")
    child_clean = child.strip().replace("\\", "/").strip("/")
    if not _safe_relative_plan_path(base_clean) or not _safe_relative_plan_path(child_clean):
        return base_clean
    return f"{base_clean}/{child_clean}" if child_clean else base_clean


def _extract_requested_filename(text: str) -> str:
    # 只提取明显带扩展名的文件名，避免把自然语言片段误当路径。
    patterns = (
        r"[《\"']([^《》\"'\n\r]{1,120}\.[A-Za-z0-9]{1,12})[》\"']",
        r"(?:文件|file)\s*[:：]?\s*([^\s，。；;]+\.[A-Za-z0-9]{1,12})",
        r"([^\s，。；;]+\.[A-Za-z0-9]{1,12})",
    )
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            candidate = match.group(1).strip().strip('"').strip("'")
            if _safe_relative_plan_path(candidate):
                return candidate
    return ""



def _has_any(lowered: str, words: tuple[str, ...]) -> bool:
    return any(word.lower() in lowered for word in words)


_DOCUMENT_FOLLOWUP_HINTS = (
    "刚才", "上面", "这份", "该文档", "这个文档", "文档里", "里面", "原文", "引用", "片段", "第", "页", "工作表", "sheet", "幻灯片", "slide", "document", "doc",
)
_DOCUMENT_EXPORT_VERBS = ("导出", "保存", "生成", "输出", "export", "save")
_DOCUMENT_REWRITE_VERBS = ("修改", "改写", "修订", "润色", "重写", "替换", "改成", "改为", "换成", "替换为", "替换成", "修改计划", "rewrite", "revise", "edit", "replace")
_DOCUMENT_APPLY_VERBS = ("写回", "应用修改", "保存修改", "覆盖写入", "生成修订副本", "真正修改", "执行修改", "apply", "writeback", "write back")
_DOCUMENT_ROLLBACK_VERBS = ("回滚", "撤回修改", "还原", "撤销写回", "rollback", "undo")
_DOCUMENT_QUERY_VERBS = ("查", "找", "有没有", "哪些", "总结", "分析", "解释", "追问", "引用", "第", "页", "sheet", "工作表", "slide", "幻灯片", "query", "ask")
_DOCUMENT_READ_VERBS = ("读取", "读一下", "打开", "查看", "看一下", "看下", "总结", "分析", "解析", "read", "open", "view", "summarize", "analyse", "analyze", "parse")


def _extract_document_operation_id(text: str) -> str:
    match = re.search(r"(docwrite_[0-9a-fA-F]{8,32})", text)
    return match.group(1) if match else ""


_RUNTIME_FILE_HANDOFF_RE = re.compile(
    r"附件(?P<index>\d+)\s*[:：]\s*(?P<name>.*?)\s*\|\s*runtime_local_path=(?P<path>[^\n\r]+)",
    re.IGNORECASE,
)
_RUNTIME_HANDOFF_INTENT_RE = re.compile(
    r"上传|附件|这个文件|该文件|刚才文件|读取|读一下|看一下|打开|总结|分析|解析|处理|内容|read|open|summari[sz]e|parse|inspect",
    re.IGNORECASE,
)


def _extract_runtime_file_handoffs(text: str) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for match in _RUNTIME_FILE_HANDOFF_RE.finditer(text or ""):
        name = (match.group("name") or "attachment").strip().strip("《》<>\"'“”")
        path = (match.group("path") or "").strip().strip("《》<>\"'“”")
        if not path or path.startswith("<"):
            continue
        out.append({"name": name, "path": path})
    return out


def _parse_runtime_file_handoff_task(text: str) -> list[ToolInvocation]:
    """Route uploaded/local handoff files to the actual Runtime path, not to the display filename.

    This prevents upload flows from planning ``read_file('xxx.txt')`` against the
    wrong workspace root and then reporting path_not_found.
    """
    handoffs = _extract_runtime_file_handoffs(text)
    if not handoffs:
        return []
    user_part = text.split("[Runtime本地文件交接]", 1)[0]
    if user_part.strip() and not _RUNTIME_HANDOFF_INTENT_RE.search(user_part):
        return []
    item = handoffs[-1]
    path = item["path"]
    suffix = ("." + path.rsplit(".", 1)[-1].lower()) if "." in path else ""
    if suffix in _DOCUMENT_PARSE_EXTENSIONS:
        return [ToolInvocation("document_parse", {"path": path})]
    return [ToolInvocation("read_file", {"path": path})]


def _extract_simple_replacement(text: str) -> dict[str, str]:
    patterns = (
        r"把\s*[“\"'《]?(?P<old>[^“”\"'《》\n]{2,180})[”\"'》]?\s*(?:替换成|替换为|改成|改为|换成)\s*[“\"'《]?(?P<new>[^“”\"'《》\n]{0,260})[”\"'》]?",
        r"replace\s+[\"']?(?P<old>[^\"'\n]{2,180})[\"']?\s+with\s+[\"']?(?P<new>[^\"'\n]{0,260})[\"']?",
    )
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if not match:
            continue
        old = match.group("old").strip().strip("\"'“”‘’《》<>` ：:，,。.;；")
        new = match.group("new").strip().strip("\"'“”‘’《》<>` ：:，,。.;；")
        old = re.sub(r"^.*\.(?:docx|pdf|xlsx|xlsm|pptx|csv|md|markdown|txt|html?|json|py|js|ts|tsx|jsx|css|java|cpp|c|go|rs)(?:\s*(?:里|里的|中|中的|内|里面|的))?", "", old, flags=re.IGNORECASE).strip()
        old = re.sub(r"^(?:帮我|请|把)?\s*(?:桌面|下载|文档|我的文档|desktop|downloads?|documents?)(?:的|里|里的|中|中的)?\s*", "", old, flags=re.IGNORECASE).strip()
        old = re.sub(r"^(?:这个|该|刚才|上面|这份)?(?:文档|原文|正文|内容|文件|资料)(?:中|里|里的|的)?", "", old).strip()
        old = re.sub(r"^(?:里面|里|中|的)", "", old).strip()
        new = re.sub(r"(?:并)?(?:写回|保存修改|应用修改|生成修订副本|覆盖写入|真正修改|执行修改)$", "", new).strip()
        if len(old) >= 2:
            return {"old_text": old, "new_text": new}
    return {}


def _extract_document_file_reference(text: str) -> str:
    patterns = (
        r"[《\"']([^《》\"'\n\r]{1,260}\.(?:docx|pdf|xlsx|xlsm|pptx|csv|md|markdown|txt|html?|json|py|js|ts|tsx|jsx|css|java|cpp|c|go|rs))[》\"']",
        r"((?:[A-Za-z]:[\\/])?[^\s，。；;<>|]{1,260}\.(?:docx|pdf|xlsx|xlsm|pptx|csv|md|markdown|txt|html?|json|py|js|ts|tsx|jsx|css|java|cpp|c|go|rs))",
    )
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if not match:
            continue
        candidate = match.group(1).strip().strip('"\'“”《》<>，。；;')
        if candidate:
            return candidate
    return ""


def _parse_document_context_task(text: str) -> list[ToolInvocation]:
    """L6.72.45：解析后的文档追问/导出/修改闭环路由。

    只在文档上下文意图明确时触发；普通聊天不进入任务链。
    """
    lowered = text.lower()
    path = _extract_document_file_reference(text)
    has_doc_hint = path or _has_any(lowered, _DOCUMENT_FOLLOWUP_HINTS)
    if not has_doc_hint:
        return []

    wants_export = _has_any(lowered, _DOCUMENT_EXPORT_VERBS) and ("文档" in lowered or "摘要" in lowered or "引用" in lowered or "解析" in lowered or path)
    replacement_hint = _extract_simple_replacement(text)
    doc_context_hint = ("文档" in lowered or "原文" in lowered or "这份" in lowered or "刚才" in lowered or path)
    wants_rewrite = _has_any(lowered, _DOCUMENT_REWRITE_VERBS) and doc_context_hint
    wants_apply = (_has_any(lowered, _DOCUMENT_APPLY_VERBS) or replacement_hint) and doc_context_hint
    wants_rollback = _has_any(lowered, _DOCUMENT_ROLLBACK_VERBS) and ("文档" in lowered or "写回" in lowered or "修改" in lowered or _extract_document_operation_id(text))
    wants_query = _has_any(lowered, _DOCUMENT_QUERY_VERBS) or (not path and _has_any(lowered, _DOCUMENT_FOLLOWUP_HINTS))
    wants_read = path and _has_any(lowered, _DOCUMENT_READ_VERBS)

    if wants_rollback:
        op_id = _extract_document_operation_id(text)
        args: dict[str, str] = {}
        if op_id:
            args["operation_id"] = op_id
        return [ToolInvocation("document_rollback", args)]
    if wants_apply:
        args = {"instruction": text}
        repl = replacement_hint or _extract_simple_replacement(text)
        args.update(repl)
        if path:
            args["path"] = path
        return [ToolInvocation("document_apply_rewrite", args)]
    if wants_export:
        args: dict[str, str] = {"query": text}
        if path:
            args["path"] = path
        return [ToolInvocation("document_export", args)]
    if wants_rewrite:
        args = {"instruction": text}
        if path:
            args["path"] = path
        return [ToolInvocation("document_rewrite_plan", args)]
    if path and wants_read and not wants_query:
        suffix = ("." + path.rsplit(".", 1)[-1].lower()) if "." in path else ""
        if suffix in _DOCUMENT_PARSE_EXTENSIONS or ("文档" in lowered or "解析" in lowered or "总结" in lowered):
            return [ToolInvocation("document_parse", {"path": path})]
    if wants_query:
        args = {"query": text}
        if path:
            args["path"] = path
        return [ToolInvocation("document_query", args)]
    # L6.72.51：存在路径但没有明确文档动作时不抢路由，交给 ActivationForm/Planner。
    return []


def _parse_host_file_task(text: str) -> list[ToolInvocation]:
    user_part = text.split("[桌面端主机文件访问提示]", 1)[0]
    lowered = user_part.lower()
    folder = _detect_host_folder(user_part)
    if not folder:
        return []
    hints = _extract_host_hints(text)
    base = hints.get(folder, "")
    if not base:
        # 没有桌面桥接注入的相对路径提示时，不凭空猜绝对路径。
        return []

    filename = _extract_requested_filename(user_part)
    is_read_or_list = any(verb.lower() in lowered for verb in [*_READ_VERBS, *_LIST_VERBS])
    is_write_intent = any(verb.lower() in lowered for verb in _WRITE_VERBS) or _has_any(lowered, _DOCUMENT_REWRITE_VERBS) or _has_any(lowered, _DOCUMENT_APPLY_VERBS) or bool(_extract_simple_replacement(user_part))

    if filename:
        rel_path = _join_relative_path(base, filename)
        suffix_match = re.search(r"(\.[A-Za-z0-9]{1,12})$", filename.strip())
        suffix = suffix_match.group(1).lower() if suffix_match else ""
        if suffix in _DOCUMENT_PARSE_EXTENSIONS:
            replacement_hint = _extract_simple_replacement(user_part)
            wants_apply = (_has_any(lowered, _DOCUMENT_APPLY_VERBS) or replacement_hint) and is_write_intent
            if wants_apply:
                args = {"instruction": user_part, "path": rel_path}
                args.update(replacement_hint)
                return [ToolInvocation("document_apply_rewrite", args)]
            if is_write_intent and ("文档" in lowered or "解析" in lowered or "总结" in lowered):
                return [ToolInvocation("document_rewrite_plan", {"instruction": user_part, "path": rel_path})]
            if not is_write_intent:
                return [ToolInvocation("document_parse", {"path": rel_path})]
        if any(verb.lower() in lowered for verb in _READ_VERBS):
            return [ToolInvocation("read_file", {"path": rel_path})]
        if is_write_intent:
            # 非文档写入仍交给模型计划与 QualityGate，不在自然语言桥直接落盘。
            return []
    if not is_read_or_list:
        return []
    return [ToolInvocation("list_dir", {"path": base})]


def _looks_like_generic_test_task(lowered: str) -> bool:
    return any(x in lowered for x in ("运行测试", "跑测试", "执行测试", "run tests", "run test", "pytest"))


def _looks_like_generic_compile_task(lowered: str) -> bool:
    return any(x in lowered for x in ("运行 python 检查", "python 检查", "编译检查", "compileall", "python -m compileall"))


def _looks_like_generic_package_task(lowered: str) -> bool:
    return any(x in lowered for x in ("打包项目", "项目打包", "生成交付包", "package project", "zip project"))

def _tail(text: str, default: str = "") -> str:
    try:
        parts = shlex.split(text)
    except ValueError:
        parts = text.split(maxsplit=1)
    return parts[1] if len(parts) >= 2 else default


def _parse_write(text: str) -> list[ToolInvocation]:
    # 格式：write path :: content
    if "::" not in text:
        natural = _parse_natural_workspace_write(text)
        return natural
    left, content = text.split("::", 1)
    parts = shlex.split(left)
    if len(parts) < 2:
        return []
    return [ToolInvocation("write_workspace_file", {"path": parts[1], "content": _strip_appended_runtime_context(content.lstrip())})]


def _parse_natural_workspace_write(text: str) -> list[ToolInvocation]:
    """L6.72.54 确定性回退：只解析明确文件名 + 内容的本地写入。

    该解析只支持普通工作区文件，不接管 docx/pdf 等文档容器，也不猜测用户
    未给出的内容，避免文档系统或模型计划失败时假装完成。
    """
    raw = str(text or "").strip()
    if not raw:
        return []
    lowered = raw.lower()
    if "::" in raw and (lowered.startswith("write ") or lowered.startswith("写入 ")):
        return []
    if not any(verb in lowered for verb in ("创建", "新建", "生成", "写入", "保存", "create", "write")):
        return []
    if any(marker in lowered for marker in ("docx", ".pdf", ".xlsx", ".pptx")) and not any(ext in lowered for ext in (".txt", ".md", ".json", ".csv", ".py", ".log")):
        return []
    match = re.search(r"(?P<path>[A-Za-z0-9_./\\\-一-鿿]+\.(?:txt|md|json|csv|py|log))", raw)
    if not match:
        return []
    path = match.group("path").strip().strip("\"'“”‘’")
    after = raw[match.end():].strip()
    content = ""
    content_match = re.search(r"(?:内容|正文|写成|为|是|:|：)\s*(?P<content>.+)$", after, flags=re.DOTALL)
    if content_match:
        content = content_match.group("content").strip()
    elif "::" in raw:
        content = raw.split("::", 1)[1].strip()
    else:
        # 明确创建空文件也允许，但复杂自然语言不凭空补正文。
        if any(marker in lowered for marker in ("空文件", "empty file", "blank file")):
            content = ""
        else:
            return []
    return [ToolInvocation("write_workspace_file", {"path": path, "content": _strip_appended_runtime_context(content)})]


def _strip_appended_runtime_context(content: str) -> str:
    value = str(content or "")
    for marker in ("\n\n[Runtime", "\n\n[桌面端", "\n\n[妗岄潰"):
        idx = value.find(marker)
        if idx >= 0:
            tail = value[idx:]
            if "access_scope=" in tail or "runtime_local_path=" in tail or "desktop_relative_path=" in tail:
                return value[:idx].rstrip()
    idx = value.find("\n\n[")
    if idx >= 0:
        tail = value[idx:]
        if "access_scope=" in tail or "工具 path" in tail or "runtime_local_path=" in tail:
            return value[:idx].rstrip()
    return value


_HASH_FILE_EXTENSIONS = (
    "zip", "txt", "json", "md", "py", "csv", "xlsx", "xlsm", "docx", "pdf", "png", "jpg", "jpeg", "tar", "gz", "7z"
)
_HASH_FILE_RE = re.compile(
    r"(?P<path>(?:[A-Za-z]:[\\/])?[^\s`\"'<>|]+?\.(?:"
    + "|".join(_HASH_FILE_EXTENSIONS)
    + r"))(?=$|[\s`\"'，。；;、,)\]】])",
    re.IGNORECASE,
)


def _parse_file_sha256_task(text: str) -> list[ToolInvocation]:
    lowered = text.lower()
    has_hash_word = (
        "sha256" in lowered
        or "sha-256" in lowered
        or "checksum" in lowered
        or "digest" in lowered
        or "哈希" in text
        or "摘要" in text
    )
    has_action = (
        "compute" in lowered
        or "calculate" in lowered
        or "verify" in lowered
        or "match" in lowered
        or "check" in lowered
        or "计算" in text
        or "校验" in text
        or "核对" in text
        or "算" in text
    )
    if not (has_hash_word and has_action):
        return []
    path = _extract_hash_file_path(text)
    if not path:
        return []
    return [ToolInvocation("file_sha256", {"path": path})]


def _extract_hash_file_path(text: str) -> str:
    for candidate in re.findall(r"`([^`]+)`", text):
        cleaned = _clean_path_candidate(candidate)
        if _looks_like_hash_file_path(cleaned):
            return cleaned
    for candidate in re.findall(r"[\"“”']([^\"“”']+)[\"“”']", text):
        cleaned = _clean_path_candidate(candidate)
        if _looks_like_hash_file_path(cleaned):
            return cleaned
    for match in _HASH_FILE_RE.finditer(text):
        cleaned = _clean_path_candidate(match.group("path"))
        if _looks_like_hash_file_path(cleaned):
            return cleaned
    return ""


def _clean_path_candidate(value: str) -> str:
    return str(value or "").strip().strip("`\"'“”‘’()[]{}<>，。；;、,")


def _looks_like_hash_file_path(value: str) -> bool:
    lowered = value.lower().replace("\\", "/")
    return any(lowered.endswith("." + suffix) for suffix in _HASH_FILE_EXTENSIONS)


def _parse_python_calculation_task(text: str) -> list[ToolInvocation]:
    lowered = text.lower()
    if "python" not in lowered:
        return []
    if not any(word in lowered for word in ("calculation", "calculate", "calc", "compute", "eval")) and not any(word in text for word in ("计算", "算式", "求值")):
        return []
    expr = _extract_arithmetic_expression(text)
    if not expr:
        return []
    command = ["python", "-S", "-B", "-c", f"print({expr})"]
    return [ToolInvocation("safe_command_runner", {"command": command, "cwd": ".", "timeout_sec": 30, "max_output_chars": 2000})]


def _extract_arithmetic_expression(text: str) -> str:
    patterns = (
        r"(?:for|calculate|calc|compute|eval)\s+([0-9][0-9\s+\-*/().%]*[0-9)])",
        r"(?:计算|算式|求值)\s*([0-9][0-9\s+\-*/().%]*[0-9)])",
        r"([0-9]+(?:\s*[+\-*/%]\s*[0-9]+)+)",
    )
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if not match:
            continue
        expr = match.group(1).strip()
        if re.fullmatch(r"[0-9\s+\-*/().%]+", expr):
            return expr
    return ""



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
