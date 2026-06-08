"""R21 activation-ready learned Tool adapter.

Generated from template: doc_skill_production
Boundary: deterministic argument-only processing; no external side effects.
"""
from __future__ import annotations

import json
import re
import statistics
from typing import Any

TEMPLATE_ID = 'doc_skill_production'


def candidate_adapter_draft(arguments: dict[str, Any]) -> dict[str, Any]:
    args = dict(arguments or {})
    if TEMPLATE_ID == "pure_transform":
        return _pure_transform(args)
    if TEMPLATE_ID == "schema_contract_check":
        return _schema_contract_check(args)
    if TEMPLATE_ID == "project_diagnostic":
        return _project_diagnostic(args)
    if TEMPLATE_ID == "doc_skill_production":
        return _doc_skill_production(args)
    if TEMPLATE_ID == "experience_reuse":
        return _experience_reuse(args)
    return _ok("未知模板，已降级为参数回显。", {"arguments": args})


def _ok(summary: str, data: dict[str, Any], status: str = "ok") -> dict[str, Any]:
    data["arguments"] = data.get("arguments", {})
    return {"status": status, "output_summary": summary, "data": data}


def _as_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if value in (None, ""):
        return []
    return [value]


def _as_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _pure_transform(args: dict[str, Any]) -> dict[str, Any]:
    op = str(args.get("operation") or "json_normalize").lower().replace("-", "_")
    if op == "json_normalize":
        payload = args.get("payload", args.get("data", args))
        text = json.dumps(payload, ensure_ascii=False, sort_keys=True)
        return _ok("JSON 已归一化。", {"normalized_json": text, "key_count": len(payload) if isinstance(payload, dict) else 0, "arguments": args})
    if op == "markdown_table":
        rows = _as_list(args.get("rows") or args.get("items"))
        fields = [str(x) for x in _as_list(args.get("fields"))]
        if not fields and rows and isinstance(rows[0], dict):
            fields = sorted(str(k) for k in rows[0].keys())
        header = "| " + " | ".join(fields or ["value"]) + " |"
        sep = "| " + " | ".join("---" for _ in (fields or ["value"])) + " |"
        body = []
        for row in rows:
            if isinstance(row, dict):
                body.append("| " + " | ".join(str(row.get(f, "")) for f in fields) + " |")
            else:
                body.append("| " + str(row) + " |")
        return _ok("Markdown 表格已生成。", {"markdown": "\n".join([header, sep] + body), "row_count": len(rows), "arguments": args})
    if op == "field_extract":
        payload = args.get("payload", {})
        fields = [str(x) for x in _as_list(args.get("fields"))]
        extracted = {f: payload.get(f) for f in fields} if isinstance(payload, dict) else {}
        return _ok("字段已提取。", {"fields": extracted, "arguments": args})
    if op == "regex_check":
        text = _as_text(args.get("text") or args.get("payload") or "")
        pattern = str(args.get("pattern") or args.get("query") or ".+")
        matches = re.findall(pattern, text)
        return _ok("正则批检完成。", {"matched": bool(matches), "match_count": len(matches), "matches": matches[:20], "arguments": args})
    if op == "simple_stats":
        nums = []
        for item in _as_list(args.get("items") or args.get("numbers") or args.get("payload")):
            try:
                nums.append(float(item))
            except (TypeError, ValueError):
                continue
        data = {"count": len(nums), "arguments": args}
        if nums:
            data.update({"sum": sum(nums), "mean": statistics.fmean(nums), "min": min(nums), "max": max(nums)})
        return _ok("简单统计完成。", data)
    if op == "path_filter":
        paths = [str(x) for x in _as_list(args.get("paths") or args.get("items"))]
        include = str(args.get("include") or args.get("query") or "")
        exclude = str(args.get("exclude") or "")
        filtered = [p for p in paths if (not include or include in p) and (not exclude or exclude not in p)]
        return _ok("路径列表过滤完成。", {"paths": filtered, "count": len(filtered), "arguments": args})
    return _ok("未知转换操作，已返回原始参数。", {"arguments": args}, status="needs_review")


def _schema_contract_check(args: dict[str, Any]) -> dict[str, Any]:
    explicit_payload = "payload" in args
    payload = args.get("payload") if isinstance(args.get("payload"), (dict, list)) else {}
    schema_type = str(args.get("schema_type") or args.get("kind") or "usage_card").lower()
    if not explicit_payload and "schema_type" not in args and "kind" not in args:
        return _ok(
            "Schema/Contract 校验收到通用调用，已返回可用状态。",
            {"schema_type": schema_type, "valid": True, "missing_fields": [], "arguments": args, "generic_call": True},
        )
    required_map = {
        "usage_card": ["when_to_use", "how_to_call", "do_not_use_when", "next_action_hint"],
        "chain_recipe": ["steps"],
        "tool_spec": ["name", "description", "args_schema", "risk", "output_schema"],
        "skill_spec": ["title", "trigger_rules", "usage_chain", "validation"],
        "learning_asset_contract": ["schema", "asset_ref", "asset_kind", "name", "usage_card", "chain_recipe", "risk_profile"],
    }
    required = required_map.get(schema_type, required_map["usage_card"])
    if schema_type == "chain_recipe" and isinstance(payload, list):
        missing = [] if payload else ["steps"]
    else:
        missing = [key for key in required if not (isinstance(payload, dict) and payload.get(key) not in (None, "", []))]
    return _ok("Schema/Contract 校验完成。", {"schema_type": schema_type, "valid": not missing, "missing_fields": missing, "arguments": args}, status="ok" if not missing else "needs_review")


def _project_diagnostic(args: dict[str, Any]) -> dict[str, Any]:
    text = " ".join(_as_text(args.get(k)) for k in ("log_text", "repo_map", "file_tree", "changed_files", "goal") if args.get(k) is not None)
    low = text.lower()
    findings = []
    next_tool = "diagnose_project"
    if "importerror" in low or "cannot import" in low:
        findings.append("import error：优先检查符号名、导出路径和循环导入。")
        next_tool = "import_error_analyzer"
    if "failed" in low or "assert" in low or "pytest" in low:
        findings.append("测试失败：先映射失败测试到受影响文件，再生成最小补丁。")
        next_tool = "test_failure_analyzer"
    if "missing" in low and "test" in low:
        findings.append("缺失测试：需要补最小复测用例或 fallback smoke。")
        next_tool = "patch_plan_generator"
    if not findings:
        findings.append("未发现明确失败特征；建议先跑 repo_map/file_tree_scan 或质量检查。")
    return _ok("项目诊断输入摘要已分析。", {"findings": findings, "risk_flags": [], "next_action_hint": {"next_tool": next_tool, "reason": "由 LLM 决定是否进入 Code-X 定位/补丁/验证链。"}, "arguments": args})


def _doc_skill_production(args: dict[str, Any]) -> dict[str, Any]:
    op = str(args.get("operation") or "usage_card").lower().replace("-", "_")
    title = str(args.get("title") or args.get("name") or "learned_asset")
    goal = str(args.get("goal") or args.get("purpose") or "复用当前经验并保持 Runtime 可验证。")
    evidence = [str(x) for x in _as_list(args.get("evidence") or args.get("items"))]
    if op == "skill_md":
        draft = "\n".join([f"# {title}", "", "## 用途", goal, "", "## 触发规则", "- 命中相同任务/失败/交付模式时使用。", "", "## 使用链路", "- 读取证据", "- 选择 Runtime 工具", "- smoke/测试", "- handoff", "", "## 证据", *[f"- {x}" for x in evidence]])
    elif op == "release_note":
        draft = "\n".join([f"# Release Note: {title}", "", f"- 目标：{goal}", f"- 证据数：{len(evidence)}", "- 下一步：运行 smoke 与 runtime alignment。"])
    elif op == "engineer_handoff_prompt":
        draft = "\n".join(["你现在接手临渊者 Code-X 工程任务。", f"目标：{goal}", "边界：LLM 主脑、工具外骨骼、A5 才硬拦。", "下一步：读结构、跑 smoke、修失败、打包交付。"])
    elif op == "handoff_summary":
        draft = f"{title}：{goal}；证据={len(evidence)}；下一步=验证/回滚/交付。"
    else:
        draft = json.dumps({"title": title, "when_to_use": goal, "how_to_call": "runtime-tools tool <learned_tool_name> {json_args}", "do_not_use_when": "A5/凭证/裸外部副作用", "next_action_hint": "smoke 后进入 handoff"}, ensure_ascii=False, indent=2)
    return _ok("文档/Skill 辅助草案已生成。", {"operation": op, "draft": draft, "arguments": args})


def _experience_reuse(args: dict[str, Any]) -> dict[str, Any]:
    digests = [str(x) for x in _as_list(args.get("digests") or args.get("items") or args.get("evidence"))]
    goal = str(args.get("goal") or "复用经验")
    lessons = []
    for item in digests[:20]:
        clean = " ".join(item.split())[:220]
        if clean:
            lessons.append({"summary": clean, "reusable_condition": "相同错误/链路/交付模式再次出现。"})
    recommendation = "skill" if len(lessons) <= 2 else "tool"
    if any("重复" in x or "regex" in x.lower() or "schema" in x.lower() for x in digests):
        recommendation = "tool"
    return _ok("经验复用候选已抽取。", {"goal": goal, "lessons": lessons, "recommendations": [{"asset_kind": recommendation, "reason": "可复用且可验证。"}], "arguments": args})
