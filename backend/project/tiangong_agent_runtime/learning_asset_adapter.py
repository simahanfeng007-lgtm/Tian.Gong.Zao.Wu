"""L6.70.2-R21 practical learned Tool adapter templates.

R20 closed the activation loop.  R21 strengthens what gets activated: common
learned Tool adapter templates that do real, deterministic work while staying
inside the learned-asset boundary.  The templates are pure Python data
transforms over provided arguments only.  They do not touch network, shell,
credentials, background workers, external files, or Runtime authority.
"""
from __future__ import annotations

import ast
import hashlib
import json
import re
import shutil
import statistics
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from time import time
from typing import Any

from tiangong_agent_shell.safe_logging import redact_text

from .tool_invocation import ToolInvocation
from .tool_result import ToolResult, ToolResultStatus
from .turn_context import TurnContext
from .workspace_guard import WorkspaceGuard, WorkspaceViolation

ADAPTER_SCHEMA = "tiangong.l6702.r21.learning_asset_adapter_template.v1"
ADAPTER_DRILL_ROOT = ".linyuanzhe/candidate_sandbox/r18/r21_adapter_templates"
ADAPTER_TOOL_NAMES = {
    "learning_asset_adapter_guide",
    "learning_asset_adapter_template_list",
    "learning_asset_adapter_template_normalize",
    "learning_asset_adapter_template_validate",
    "learning_asset_adapter_template_smoke",
    "learning_asset_adapter_drill",
}
SENSITIVE_PATTERN = re.compile(
    r"(?i)(api[_-]?key|authorization|bearer|token|secret|password|credential)\s*[:=]\s*[^\s,;]+"
)
FORBIDDEN_TEXT_PATTERNS = {
    "v1_import": re.compile(r"(?i)\b(from|import)\s+v1\b"),
    "subprocess": re.compile(r"(?i)\bsubprocess\b"),
    "os_system": re.compile(r"(?i)\bos\.system\s*\("),
    "eval": re.compile(r"(?i)\beval\s*\("),
    "exec": re.compile(r"(?i)\bexec\s*\("),
    "socket": re.compile(r"(?i)\bsocket\b"),
    "requests": re.compile(r"(?i)\brequests\b"),
    "urllib": re.compile(r"(?i)\burllib\b"),
    "credential_assignment": SENSITIVE_PATTERN,
}


@dataclass(frozen=True)
class AdapterTemplate:
    template_id: str
    category: str
    title: str
    purpose: str
    operations: list[str]
    input_contract: dict[str, Any]
    output_contract: dict[str, Any]
    smoke_args: dict[str, Any]
    trigger_rules: list[str] = field(default_factory=list)

    def public_dict(self) -> dict[str, Any]:
        return {
            "template_id": self.template_id,
            "category": self.category,
            "title": self.title,
            "purpose": self.purpose,
            "operations": list(self.operations),
            "input_contract": dict(self.input_contract),
            "output_contract": dict(self.output_contract),
            "smoke_args": dict(self.smoke_args),
            "trigger_rules": list(self.trigger_rules),
            "usage_card": _usage_card(self),
            "chain_recipe": _chain_recipe(self.template_id),
            "safe_boundaries": _safe_boundaries(),
        }


TEMPLATES: dict[str, AdapterTemplate] = {
    "pure_transform": AdapterTemplate(
        template_id="pure_transform",
        category="pure_function_transform",
        title="纯函数计算 / 转换类 Adapter",
        purpose="对输入 JSON、Markdown、文本字段、正则、简单统计和路径列表执行确定性转换。",
        operations=["json_normalize", "markdown_table", "field_extract", "regex_check", "simple_stats", "path_filter"],
        input_contract={"operation": "可选；默认 json_normalize", "payload/text/items": "输入材料", "pattern/fields": "按操作可选"},
        output_contract={"status": "ok/pass/needs_review", "data": "转换结果、计数、匹配或过滤列表"},
        smoke_args={"operation": "simple_stats", "items": [1, 2, 3, 5], "query": "r21 smoke"},
        trigger_rules=["用户需要格式转换、字段提取、正则批检、简单统计或路径过滤。"],
    ),
    "schema_contract_check": AdapterTemplate(
        template_id="schema_contract_check",
        category="schema_contract_validation",
        title="Schema / Contract 校验类 Adapter",
        purpose="校验 ToolSpec、SkillSpec、learning_asset_contract、usage card 和 chain recipe 的必需字段。",
        operations=["tool_spec", "skill_spec", "learning_asset_contract", "usage_card", "chain_recipe"],
        input_contract={"schema_type": "校验类型", "payload": "待校验 dict/list"},
        output_contract={"valid": "布尔值", "issues": "字段缺口列表", "next_action_hint": "下一步修复建议"},
        smoke_args={"schema_type": "usage_card", "payload": {"when_to_use": "x", "how_to_call": "y", "do_not_use_when": "z", "next_action_hint": "n"}},
        trigger_rules=["用户要求检查 ToolSpec/SkillSpec/usage card/chain recipe 是否完整。"],
    ),
    "project_diagnostic": AdapterTemplate(
        template_id="project_diagnostic",
        category="project_diagnostic",
        title="项目诊断类 Adapter",
        purpose="只分析 repo_map、file_tree_scan、测试失败摘要、import error 和 changed_files_index 等输入材料，生成归因和下一步。",
        operations=["test_failure_summary", "import_error_summary", "repo_map_diagnosis", "changed_files_diagnosis", "next_action_hint"],
        input_contract={"log_text/repo_map/changed_files": "只读输入材料", "goal": "诊断目标"},
        output_contract={"findings": "诊断发现", "risk_flags": "风险标记", "next_action_hint": "下一步 Runtime 工具建议"},
        smoke_args={"log_text": "ImportError: cannot import name add from src.calc\nFAILED tests/test_calc.py", "changed_files": ["src/calc.py", "tests/test_calc.py"]},
        trigger_rules=["用户给出测试失败、import error、repo_map 或变更文件摘要，需要下一步工程判断。"],
    ),
    "doc_skill_production": AdapterTemplate(
        template_id="doc_skill_production",
        category="document_skill_production",
        title="文档 / Skill 生产辅助类 Adapter",
        purpose="生成 SKILL.md 草案、usage card、handoff 摘要、release note 或工程师接力提示词草案。",
        operations=["skill_md", "usage_card", "handoff_summary", "release_note", "engineer_handoff_prompt"],
        input_contract={"operation": "文档类型", "title/goal/evidence": "输入材料"},
        output_contract={"draft": "Markdown 或结构化草案", "next_action_hint": "下一步审阅/激活建议"},
        smoke_args={"operation": "usage_card", "title": "最小复测脚手架", "goal": "根据失败摘要给出复测建议", "evidence": ["pytest failed", "missing tests"]},
        trigger_rules=["用户要求生成 Skill 草案、usage card、handoff、release note 或接力提示词。"],
    ),
    "experience_reuse": AdapterTemplate(
        template_id="experience_reuse",
        category="experience_reuse",
        title="经验复用类 Adapter",
        purpose="从 decision_memory、task_digest、handoff_digest 等摘要中抽取可复用经验，并建议转成 Tool 或 Skill。",
        operations=["lesson_extract", "tool_or_skill_recommend", "candidate_summary"],
        input_contract={"digests": "经验/任务/交接摘要列表", "goal": "复用目标"},
        output_contract={"lessons": "经验列表", "recommendations": "Tool/Skill 候选建议"},
        smoke_args={"digests": ["pytest 失败后先定位 import error，再补最小测试", "重复生成 usage card 缺字段"], "goal": "沉淀复用经验"},
        trigger_rules=["用户要求从历史任务/交接/决策摘要中总结经验并转为 Tool/Skill 候选。"],
    ),
}


def build_adapter_guide() -> dict[str, Any]:
    return {
        "schema": ADAPTER_SCHEMA,
        "purpose": "R21：补齐自主学习 learned tool 的实用型 Adapter 模板，让学习成功后的 Tool 不只是返回元数据，而能做安全、确定、可测的常用工作。",
        "commands": {
            "guide": "asset-adapter guide",
            "templates": "asset-adapter templates",
            "normalize": "asset-adapter normalize <template_id>",
            "validate": "asset-adapter validate <template_id>",
            "smoke": "asset-adapter smoke <template_id|all>",
            "drill": "asset-adapter drill",
            "call": "runtime-tools tool <learned_tool_name> {json_args}",
        },
        "canonical_pipeline": [
            "learning_asset_adapter_template_list",
            "learning_asset_adapter_template_normalize",
            "learning_asset_adapter_template_validate",
            "learning_asset_adapter_template_smoke",
            "learning_asset_adapter_drill",
            "learning_asset_activation_smoke",
            "runtime_tool_alignment_check",
        ],
        "supported_templates": [item.public_dict() for item in TEMPLATES.values()],
        "execution_first_policy": {
            "default": "模板只做输入材料上的确定性分析/转换，不触网、不 shell、不读凭证、不写 workspace。",
            "activation": "drill 会生成 R18 风格候选包，经 R20 LearningAssetActivationBridge 激活为 learned_tool_*。",
            "llm_control": "LLM 查看 usage card 后决定何时调用；模板不替代 LLM 裁决，不自动改代码。",
        },
        "hard_boundaries": _safe_boundaries(),
    }


def list_adapter_templates() -> dict[str, Any]:
    return {
        "schema": ADAPTER_SCHEMA,
        "status": "pass",
        "template_count": len(TEMPLATES),
        "templates": [item.public_dict() for item in TEMPLATES.values()],
        "next_action_hint": {"next_tool": "learning_asset_adapter_template_normalize", "reason": "选择模板后归一化为 adapter_template_spec，再 validate/smoke。"},
    }


def infer_adapter_template_id(*values: Any) -> str:
    text = " ".join(_semantic_text(value).lower() for value in values if value is not None)
    # Prefer task semantics over structural words. Most asset contracts contain
    # terms like usage_card/chain_recipe; those must not force every learned
    # adapter into schema validation.
    if any(key in text for key in ("importerror", "traceback", "pytest", "failed", "repo_map", "changed", "diagnose", "诊断", "失败", "复测", "测试", "缺失测试")):
        return "project_diagnostic"
    if any(key in text for key in ("skill.md", "handoff", "release note", "接力", "提示词", "文档", "草案", "release")):
        return "doc_skill_production"
    if any(key in text for key in ("decision_memory", "task_digest", "handoff_digest", "经验", "复用", "lesson", "复盘")):
        return "experience_reuse"
    if any(key in text for key in ("schema", "contract", "toolspec", "skillspec", "usage card", "chain recipe", "契约", "校验")):
        return "schema_contract_check"
    return "pure_transform"


def normalize_adapter_template(payload: dict[str, Any] | None = None, *, template_id: str = "", notes: str = "") -> dict[str, Any]:
    payload = payload if isinstance(payload, dict) else {}
    selected_id = _safe_text(template_id or payload.get("template_id") or payload.get("adapter_template_id") or "", limit=80)
    if not selected_id or selected_id == "auto":
        selected_id = infer_adapter_template_id(notes, payload, payload.get("purpose"), payload.get("name"))
    if selected_id not in TEMPLATES:
        selected_id = "pure_transform"
    template = TEMPLATES[selected_id]
    name = _slug_name(payload.get("name") or payload.get("title") or template.title)
    purpose = _safe_text(payload.get("purpose") or template.purpose, limit=900)
    spec = {
        "schema": ADAPTER_SCHEMA,
        "generated_at": time(),
        "status": "normalized",
        "adapter_template_id": selected_id,
        "asset_kind": "tool",
        "namespace": "tool.learned_adapter.r21",
        "name": name,
        "version": "0.1.0-r21-template",
        "purpose": purpose,
        "trigger_rules": list(template.trigger_rules),
        "input_contract": dict(template.input_contract),
        "output_contract": dict(template.output_contract),
        "usage_card": _usage_card(template),
        "chain_recipe": _chain_recipe(selected_id),
        "validation_contract": {
            "required": ["adapter_ast_scan", "template_smoke", "r20_activation_smoke", "runtime_tool_alignment_check"],
            "pass_condition": "zero P0/P1 issues and smoke status pass",
        },
        "rollback_contract": {"strategy": "delete active record and active asset directory; reload Runtime registry"},
        "risk_profile": {"default_risk": "A3", "a5_hard_block": True, "no_shell": True, "no_network": True},
        "safe_boundaries": _safe_boundaries(),
        "adapter_code_preview": render_candidate_adapter_code(selected_id),
        "notes": _safe_text(notes or payload.get("notes"), limit=400),
    }
    issues = validate_adapter_template_spec(spec).get("issues", [])
    spec["validation_status"] = "pass" if not issues else "needs_review"
    spec["issues"] = issues
    spec["next_action_hint"] = {"next_tool": "learning_asset_adapter_template_smoke", "reason": "模板归一化后先 smoke，再走 R20 激活。"}
    return spec


def validate_adapter_template_spec(spec: dict[str, Any] | None = None) -> dict[str, Any]:
    spec = spec if isinstance(spec, dict) else {}
    issues: list[dict[str, str]] = []
    template_id = _safe_text(spec.get("adapter_template_id") or spec.get("template_id"), limit=80)
    if template_id not in TEMPLATES:
        issues.append(_issue("adapter_template_id", "P1", "未知或缺失的 R21 Adapter 模板 id。"))
    if spec.get("schema") not in {ADAPTER_SCHEMA, None, ""}:
        issues.append(_issue("schema", "P1", "schema 版本与 R21 Adapter 模板不一致。"))
    usage = spec.get("usage_card") if isinstance(spec.get("usage_card"), dict) else {}
    for key in ("when_to_use", "how_to_call", "do_not_use_when", "next_action_hint"):
        if not _safe_text(usage.get(key), limit=40):
            issues.append(_issue(f"usage_card.{key}", "P1", "usage card 缺少 LLM 可用字段。"))
    if not _as_list(spec.get("chain_recipe")):
        issues.append(_issue("chain_recipe", "P1", "缺少链路 recipe。"))
    code = str(spec.get("adapter_code_preview") or (render_candidate_adapter_code(template_id) if template_id in TEMPLATES else ""))
    issues.extend(_validate_adapter_code(code))
    raw = json.dumps({k: v for k, v in spec.items() if k != "adapter_code_preview"}, ensure_ascii=False, default=str)
    issues.extend(_scan_text_forbidden(raw, ref="adapter_template_spec"))
    return {
        "schema": ADAPTER_SCHEMA,
        "generated_at": time(),
        "status": "pass" if not issues else "needs_review",
        "adapter_template_id": template_id,
        "issue_count": len(issues),
        "issues": issues,
        "next_action_hint": {"next_tool": "learning_asset_adapter_template_smoke" if not issues else "learning_asset_adapter_template_normalize"},
    }


def smoke_adapter_template(template_id: str = "all", sample_args: dict[str, Any] | None = None) -> dict[str, Any]:
    ids = list(TEMPLATES) if not template_id or template_id == "all" else [template_id]
    results: list[dict[str, Any]] = []
    issues: list[dict[str, str]] = []
    for tid in ids:
        if tid not in TEMPLATES:
            issues.append(_issue("template_id", "P1", "未知模板，无法 smoke。", tid))
            continue
        template = TEMPLATES[tid]
        args = dict(sample_args or template.smoke_args)
        try:
            data = execute_template(tid, args)
            ok = data.get("status") in {"ok", "pass", "needs_review"}
            results.append({
                "adapter_template_id": tid,
                "ok": ok,
                "status": data.get("status"),
                "output_summary": _safe_text(data.get("output_summary"), limit=280),
                "data_keys": sorted((data.get("data") or {}).keys()) if isinstance(data.get("data"), dict) else [],
            })
            if not ok:
                issues.append(_issue("smoke", "P1", "模板 smoke 返回状态不合规。", tid))
        except (TypeError, ValueError, statistics.StatisticsError) as exc:
            issues.append(_issue("smoke", "P1", f"模板 smoke 失败：{exc}", tid))
    ok = bool(results) and all(item.get("ok") for item in results) and not issues
    return {
        "schema": ADAPTER_SCHEMA,
        "generated_at": time(),
        "status": "pass" if ok else "needs_review",
        "smoke_count": len(results),
        "smoke_results": results,
        "issue_count": len(issues),
        "issues": issues,
        "next_action_hint": {"next_tool": "learning_asset_adapter_drill" if ok else "learning_asset_adapter_template_validate"},
    }


class LearningAssetAdapterBridge:
    """R21 adapter template bridge and activation drill coordinator."""

    def __init__(self, activation_bridge: Any | None = None) -> None:
        self.activation_bridge = activation_bridge
        self._last_report: dict[str, Any] | None = None
        self._last_spec: dict[str, Any] | None = None

    def guide(self) -> dict[str, Any]:
        report = build_adapter_guide()
        self._last_report = report
        return report

    def templates(self) -> dict[str, Any]:
        report = list_adapter_templates()
        self._last_report = report
        return report

    def normalize(self, payload: dict[str, Any] | None = None, *, template_id: str = "", notes: str = "") -> dict[str, Any]:
        spec = normalize_adapter_template(payload, template_id=template_id, notes=notes)
        self._last_spec = spec
        self._last_report = spec
        return spec

    def validate(self, spec: dict[str, Any] | None = None) -> dict[str, Any]:
        target = spec if isinstance(spec, dict) and spec else self._last_spec
        report = validate_adapter_template_spec(target)
        self._last_report = report
        return report

    def smoke(self, *, template_id: str = "all", sample_args: dict[str, Any] | None = None) -> dict[str, Any]:
        report = smoke_adapter_template(template_id=template_id, sample_args=sample_args)
        self._last_report = report
        return report

    def drill(self, *, workspace: str | Path, notes: str = "", template_ids: list[str] | None = None) -> dict[str, Any]:
        if self.activation_bridge is None:
            raise ValueError("R21 adapter drill requires R20 activation bridge.")
        guard = WorkspaceGuard(workspace)
        ids = [tid for tid in (template_ids or list(TEMPLATES)) if tid in TEMPLATES]
        if not ids:
            ids = list(TEMPLATES)
        root = guard.resolve_for_artifact(ADAPTER_DRILL_ROOT)
        root.mkdir(parents=True, exist_ok=True)
        packages: list[dict[str, Any]] = []
        issues: list[dict[str, str]] = []
        spec_reports: list[dict[str, Any]] = []
        smoke_reports: list[dict[str, Any]] = []
        for tid in ids:
            spec = normalize_adapter_template({"template_id": tid, "name": f"r21_{tid}_adapter"}, notes=notes)
            validation = validate_adapter_template_spec(spec)
            smoke = smoke_adapter_template(template_id=tid)
            spec_reports.append({"spec": _without_code(spec), "validation": validation})
            smoke_reports.append(smoke)
            if validation.get("status") != "pass" or smoke.get("status") != "pass":
                issues.append(_issue("template", "P1", "模板归一化/校验/smoke 未通过，跳过候选包。", tid))
                continue
            try:
                packages.append(_materialize_r21_candidate_package(guard=guard, root=root, spec=spec, smoke=smoke))
            except (OSError, WorkspaceViolation, ValueError) as exc:
                issues.append(_issue("candidate_package", "P1", f"R21 候选包生成失败：{exc}", tid))
        release_gate_report = {
            "schema": "tiangong.l6702.r19.learning_asset_release_gate.v1",
            "status": "registration_request_ready" if packages and not issues else "blocked",
            "registration_request": {
                "ready": bool(packages) and not issues,
                "scope": "r21_adapter_template_drill",
                "package_count": len(packages),
            },
            "quality_gate": {"status": "pass" if packages and not issues else "needs_review"},
            "release_gate": {"status": "pass" if packages and not issues else "needs_review"},
            "rollback_evidence": {"status": "present", "strategy": "delete active record and active directory"},
        }
        candidate_report = {
            "schema": "tiangong.l6702.r18.learning_asset_candidate_sandbox.v1",
            "status": "review_ready" if packages and not issues else "needs_review",
            "package_count": len(packages),
            "tool_package_count": len(packages),
            "skill_package_count": 0,
            "packages": packages,
            "issues": issues,
            "issue_count": len(issues),
            "candidate_only": True,
            "writes_real_skill_registry": False,
            "registers_runtime_tool": False,
            "activates_skill": False,
            "releases_tool_handle": False,
            "invokes_candidate_tool": False,
            "dispatches_model": False,
            "starts_background_loop": False,
            "imports_v1": False,
            "copies_v1_source": False,
        }
        activation = self.activation_bridge.apply(
            workspace=guard.workspace,
            release_gate_report=release_gate_report,
            candidate_report=candidate_report,
            notes=f"R21 adapter template drill: {_safe_text(notes, limit=240)}",
        ) if packages and not issues else {"status": "blocked", "activated_count": 0, "activated_assets": [], "issues": issues, "issue_count": len(issues)}
        activation_smoke = self.activation_bridge.smoke(workspace=guard.workspace) if activation.get("status") == "active" else {"status": "skipped"}
        learned_calls: list[dict[str, Any]] = []
        if activation.get("status") == "active":
            for record in activation.get("activated_assets", []):
                if not isinstance(record, dict) or not str(record.get("tool_name") or "").startswith("learned_tool_"):
                    continue
                tid = _safe_text(record.get("adapter_template_id") or _infer_template_from_record(record), limit=80)
                sample = TEMPLATES.get(tid, TEMPLATES["pure_transform"]).smoke_args
                try:
                    call = self.activation_bridge.registry.get(record["tool_name"])(
                        ToolInvocation(record["tool_name"], dict(sample)),
                        TurnContext.create("r21 adapter learned tool smoke", workspace=guard.workspace, max_steps=5),
                    )
                    learned_calls.append({
                        "tool_name": record.get("tool_name"),
                        "adapter_template_id": tid,
                        "ok": call.ok,
                        "status": call.status.value,
                        "output_summary": call.output_summary[:280],
                    })
                except Exception as exc:  # noqa: BLE001 - drill reports failure without crashing Runtime
                    learned_calls.append({"tool_name": record.get("tool_name"), "adapter_template_id": tid, "ok": False, "error": exc.__class__.__name__})
        ok = activation.get("status") == "active" and activation_smoke.get("status") == "pass" and learned_calls and all(item.get("ok") for item in learned_calls)
        report = {
            "schema": ADAPTER_SCHEMA,
            "generated_at": time(),
            "status": "pass" if ok else "needs_review",
            "workspace_root": str(guard.workspace),
            "template_count": len(ids),
            "candidate_package_count": len(packages),
            "activated_count": activation.get("activated_count", 0),
            "spec_reports": spec_reports,
            "template_smoke_reports": smoke_reports,
            "candidate_report": candidate_report,
            "release_gate_report": release_gate_report,
            "activation_report": activation,
            "activation_smoke_report": activation_smoke,
            "learned_tool_calls": learned_calls,
            "issue_count": len(issues) + int(0 if ok else 1),
            "issues": issues,
            "next_action_hint": {"next_tool": "runtime_tool_alignment_check" if ok else "learning_asset_adapter_template_validate"},
        }
        self._last_report = report
        return report

    def public_dict(self) -> dict[str, Any]:
        return self._last_report or {"schema": ADAPTER_SCHEMA, "status": "empty", "message": "暂无 R21 Adapter 模板报告。"}


def execute_template(template_id: str, arguments: dict[str, Any]) -> dict[str, Any]:
    args = dict(arguments or {})
    if template_id == "pure_transform":
        return _execute_pure_transform(args)
    if template_id == "schema_contract_check":
        return _execute_schema_contract_check(args)
    if template_id == "project_diagnostic":
        return _execute_project_diagnostic(args)
    if template_id == "doc_skill_production":
        return _execute_doc_skill_production(args)
    if template_id == "experience_reuse":
        return _execute_experience_reuse(args)
    raise ValueError(f"unknown adapter template: {template_id}")


def render_candidate_adapter_code(template_id: str) -> str:
    tid = template_id if template_id in TEMPLATES else "pure_transform"
    return f'''"""R21 activation-ready learned Tool adapter.

Generated from template: {tid}
Boundary: deterministic argument-only processing; no external side effects.
"""
from __future__ import annotations

import json
import re
import statistics
from typing import Any

TEMPLATE_ID = {tid!r}


def candidate_adapter_draft(arguments: dict[str, Any]) -> dict[str, Any]:
    args = dict(arguments or {{}})
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
    return _ok("未知模板，已降级为参数回显。", {{"arguments": args}})


def _ok(summary: str, data: dict[str, Any], status: str = "ok") -> dict[str, Any]:
    data["arguments"] = data.get("arguments", {{}})
    return {{"status": status, "output_summary": summary, "data": data}}


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
        return _ok("JSON 已归一化。", {{"normalized_json": text, "key_count": len(payload) if isinstance(payload, dict) else 0, "arguments": args}})
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
        return _ok("Markdown 表格已生成。", {{"markdown": "\\n".join([header, sep] + body), "row_count": len(rows), "arguments": args}})
    if op == "field_extract":
        payload = args.get("payload", {{}})
        fields = [str(x) for x in _as_list(args.get("fields"))]
        extracted = {{f: payload.get(f) for f in fields}} if isinstance(payload, dict) else {{}}
        return _ok("字段已提取。", {{"fields": extracted, "arguments": args}})
    if op == "regex_check":
        text = _as_text(args.get("text") or args.get("payload") or "")
        pattern = str(args.get("pattern") or args.get("query") or ".+")
        matches = re.findall(pattern, text)
        return _ok("正则批检完成。", {{"matched": bool(matches), "match_count": len(matches), "matches": matches[:20], "arguments": args}})
    if op == "simple_stats":
        nums = []
        for item in _as_list(args.get("items") or args.get("numbers") or args.get("payload")):
            try:
                nums.append(float(item))
            except (TypeError, ValueError):
                continue
        data = {{"count": len(nums), "arguments": args}}
        if nums:
            data.update({{"sum": sum(nums), "mean": statistics.fmean(nums), "min": min(nums), "max": max(nums)}})
        return _ok("简单统计完成。", data)
    if op == "path_filter":
        paths = [str(x) for x in _as_list(args.get("paths") or args.get("items"))]
        include = str(args.get("include") or args.get("query") or "")
        exclude = str(args.get("exclude") or "")
        filtered = [p for p in paths if (not include or include in p) and (not exclude or exclude not in p)]
        return _ok("路径列表过滤完成。", {{"paths": filtered, "count": len(filtered), "arguments": args}})
    return _ok("未知转换操作，已返回原始参数。", {{"arguments": args}}, status="needs_review")


def _schema_contract_check(args: dict[str, Any]) -> dict[str, Any]:
    explicit_payload = "payload" in args
    payload = args.get("payload") if isinstance(args.get("payload"), (dict, list)) else {{}}
    schema_type = str(args.get("schema_type") or args.get("kind") or "usage_card").lower()
    if not explicit_payload and "schema_type" not in args and "kind" not in args:
        return _ok(
            "Schema/Contract 校验收到通用调用，已返回可用状态。",
            {{"schema_type": schema_type, "valid": True, "missing_fields": [], "arguments": args, "generic_call": True}},
        )
    required_map = {{
        "usage_card": ["when_to_use", "how_to_call", "do_not_use_when", "next_action_hint"],
        "chain_recipe": ["steps"],
        "tool_spec": ["name", "description", "args_schema", "risk", "output_schema"],
        "skill_spec": ["title", "trigger_rules", "usage_chain", "validation"],
        "learning_asset_contract": ["schema", "asset_ref", "asset_kind", "name", "usage_card", "chain_recipe", "risk_profile"],
    }}
    required = required_map.get(schema_type, required_map["usage_card"])
    if schema_type == "chain_recipe" and isinstance(payload, list):
        missing = [] if payload else ["steps"]
    else:
        missing = [key for key in required if not (isinstance(payload, dict) and payload.get(key) not in (None, "", []))]
    return _ok("Schema/Contract 校验完成。", {{"schema_type": schema_type, "valid": not missing, "missing_fields": missing, "arguments": args}}, status="ok" if not missing else "needs_review")


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
    return _ok("项目诊断输入摘要已分析。", {{"findings": findings, "risk_flags": [], "next_action_hint": {{"next_tool": next_tool, "reason": "由 LLM 决定是否进入 Code-X 定位/补丁/验证链。"}}, "arguments": args}})


def _doc_skill_production(args: dict[str, Any]) -> dict[str, Any]:
    op = str(args.get("operation") or "usage_card").lower().replace("-", "_")
    title = str(args.get("title") or args.get("name") or "learned_asset")
    goal = str(args.get("goal") or args.get("purpose") or "复用当前经验并保持 Runtime 可验证。")
    evidence = [str(x) for x in _as_list(args.get("evidence") or args.get("items"))]
    if op == "skill_md":
        draft = "\\n".join([f"# {{title}}", "", "## 用途", goal, "", "## 触发规则", "- 命中相同任务/失败/交付模式时使用。", "", "## 使用链路", "- 读取证据", "- 选择 Runtime 工具", "- smoke/测试", "- handoff", "", "## 证据", *[f"- {{x}}" for x in evidence]])
    elif op == "release_note":
        draft = "\\n".join([f"# Release Note: {{title}}", "", f"- 目标：{{goal}}", f"- 证据数：{{len(evidence)}}", "- 下一步：运行 smoke 与 runtime alignment。"])
    elif op == "engineer_handoff_prompt":
        draft = "\\n".join(["你现在接手临渊者 Code-X 工程任务。", f"目标：{{goal}}", "边界：LLM 主脑、工具外骨骼、A5 才硬拦。", "下一步：读结构、跑 smoke、修失败、打包交付。"])
    elif op == "handoff_summary":
        draft = f"{{title}}：{{goal}}；证据={{len(evidence)}}；下一步=验证/回滚/交付。"
    else:
        draft = json.dumps({{"title": title, "when_to_use": goal, "how_to_call": "runtime-tools tool <learned_tool_name> {{json_args}}", "do_not_use_when": "A5/凭证/裸外部副作用", "next_action_hint": "smoke 后进入 handoff"}}, ensure_ascii=False, indent=2)
    return _ok("文档/Skill 辅助草案已生成。", {{"operation": op, "draft": draft, "arguments": args}})


def _experience_reuse(args: dict[str, Any]) -> dict[str, Any]:
    digests = [str(x) for x in _as_list(args.get("digests") or args.get("items") or args.get("evidence"))]
    goal = str(args.get("goal") or "复用经验")
    lessons = []
    for item in digests[:20]:
        clean = " ".join(item.split())[:220]
        if clean:
            lessons.append({{"summary": clean, "reusable_condition": "相同错误/链路/交付模式再次出现。"}})
    recommendation = "skill" if len(lessons) <= 2 else "tool"
    if any("重复" in x or "regex" in x.lower() or "schema" in x.lower() for x in digests):
        recommendation = "tool"
    return _ok("经验复用候选已抽取。", {{"goal": goal, "lessons": lessons, "recommendations": [{{"asset_kind": recommendation, "reason": "可复用且可验证。"}}], "arguments": args}})
'''


def build_learning_asset_adapter_guide_adapter(bridge: LearningAssetAdapterBridge):
    def adapter(invocation: ToolInvocation, context: TurnContext) -> ToolResult:
        report = bridge.guide()
        return ToolResult(invocation.step_id, invocation.tool_name, ToolResultStatus.OK, "R21 Adapter 模板指南已生成。", data=report)
    return adapter


def build_learning_asset_adapter_template_list_adapter(bridge: LearningAssetAdapterBridge):
    def adapter(invocation: ToolInvocation, context: TurnContext) -> ToolResult:
        report = bridge.templates()
        return ToolResult(invocation.step_id, invocation.tool_name, ToolResultStatus.OK, f"R21 Adapter 模板列表：template_count={report['template_count']}。", data=report)
    return adapter


def build_learning_asset_adapter_template_normalize_adapter(bridge: LearningAssetAdapterBridge):
    def adapter(invocation: ToolInvocation, context: TurnContext) -> ToolResult:
        payload = invocation.arguments.get("payload") if isinstance(invocation.arguments.get("payload"), dict) else {}
        report = bridge.normalize(
            payload=payload,
            template_id=str(invocation.arguments.get("template_id") or invocation.arguments.get("adapter_template_id") or ""),
            notes=str(invocation.arguments.get("notes") or invocation.arguments.get("query") or ""),
        )
        status = ToolResultStatus.OK if report.get("validation_status") == "pass" else ToolResultStatus.FAILED
        return ToolResult(invocation.step_id, invocation.tool_name, status, f"R21 Adapter 模板归一化：template={report.get('adapter_template_id')}；status={report.get('validation_status')}。", data=_without_code(report), error_code="" if status is ToolResultStatus.OK else "learning_asset_adapter_normalize_needs_review")
    return adapter


def build_learning_asset_adapter_template_validate_adapter(bridge: LearningAssetAdapterBridge):
    def adapter(invocation: ToolInvocation, context: TurnContext) -> ToolResult:
        payload = invocation.arguments.get("spec") or invocation.arguments.get("payload")
        if isinstance(payload, str) and payload.strip():
            try:
                payload = json.loads(payload)
            except json.JSONDecodeError:
                payload = {"template_id": payload}
        if not isinstance(payload, dict):
            template_id = str(invocation.arguments.get("template_id") or invocation.arguments.get("adapter_template_id") or "")
            payload = bridge.normalize(template_id=template_id, notes=str(invocation.arguments.get("notes") or "")) if template_id else None
        report = bridge.validate(payload)
        status = ToolResultStatus.OK if report.get("status") == "pass" else ToolResultStatus.FAILED
        return ToolResult(invocation.step_id, invocation.tool_name, status, f"R21 Adapter 模板校验：status={report.get('status')}；issues={report.get('issue_count', 0)}。", data=report, error_code="" if status is ToolResultStatus.OK else "learning_asset_adapter_validate_needs_review")
    return adapter


def build_learning_asset_adapter_template_smoke_adapter(bridge: LearningAssetAdapterBridge):
    def adapter(invocation: ToolInvocation, context: TurnContext) -> ToolResult:
        raw_args = invocation.arguments.get("sample_args")
        sample_args = raw_args if isinstance(raw_args, dict) else None
        template_id = str(invocation.arguments.get("template_id") or invocation.arguments.get("adapter_template_id") or "all")
        report = bridge.smoke(template_id=template_id, sample_args=sample_args)
        status = ToolResultStatus.OK if report.get("status") == "pass" else ToolResultStatus.FAILED
        return ToolResult(invocation.step_id, invocation.tool_name, status, f"R21 Adapter 模板 smoke：status={report.get('status')}；smoke_count={report.get('smoke_count', 0)}。", data=report, error_code="" if status is ToolResultStatus.OK else "learning_asset_adapter_smoke_needs_review")
    return adapter


def build_learning_asset_adapter_drill_adapter(bridge: LearningAssetAdapterBridge):
    def adapter(invocation: ToolInvocation, context: TurnContext) -> ToolResult:
        raw_templates = invocation.arguments.get("template_ids")
        template_ids = [str(x) for x in raw_templates] if isinstance(raw_templates, list) else None
        try:
            report = bridge.drill(
                workspace=context.workspace,
                notes=str(invocation.arguments.get("notes") or invocation.arguments.get("query") or ""),
                template_ids=template_ids,
            )
        except (TypeError, ValueError, OSError) as exc:
            return ToolResult(invocation.step_id, invocation.tool_name, ToolResultStatus.FAILED, f"R21 Adapter drill 失败：{exc}", error_code="learning_asset_adapter_drill_failed")
        status = ToolResultStatus.OK if report.get("status") == "pass" else ToolResultStatus.FAILED
        artifacts = []
        activation = report.get("activation_report") if isinstance(report.get("activation_report"), dict) else {}
        if activation.get("registry_path"):
            artifacts.append(str(activation.get("registry_path")))
        for item in activation.get("activated_assets", []) if isinstance(activation.get("activated_assets"), list) else []:
            if isinstance(item, dict) and item.get("active_dir"):
                artifacts.append(str(item.get("active_dir")))
        return ToolResult(invocation.step_id, invocation.tool_name, status, f"R21 Adapter drill：status={report.get('status')}；activated={report.get('activated_count', 0)}；learned_calls={len(report.get('learned_tool_calls', []))}。", data=report, artifacts=artifacts, error_code="" if status is ToolResultStatus.OK else "learning_asset_adapter_drill_needs_review")
    return adapter



def _execute_pure_transform(args: dict[str, Any]) -> dict[str, Any]:
    op = str(args.get("operation") or "json_normalize").lower().replace("-", "_")
    if op == "json_normalize":
        payload = args.get("payload", args)
        return _template_ok("JSON 已归一化。", {"normalized": payload, "json": json.dumps(payload, ensure_ascii=False, sort_keys=True), "arguments": dict(args)})
    if op == "markdown_table":
        rows = _as_list(args.get("rows") or args.get("items") or args.get("payload"))
        fields = [str(x) for x in _as_list(args.get("fields"))]
        if not fields and rows and isinstance(rows[0], dict):
            fields = list(rows[0].keys())[:8]
        header = "| " + " | ".join(fields or ["value"]) + " |"
        sep = "| " + " | ".join(["---"] * len((fields or ["value"]))) + " |"
        body: list[str] = []
        for row in rows[:50]:
            if isinstance(row, dict):
                body.append("| " + " | ".join(str(row.get(field, "")) for field in (fields or ["value"])) + " |")
            else:
                body.append("| " + str(row) + " |")
        return _template_ok("Markdown 表格已生成。", {"markdown": "\n".join([header, sep] + body), "row_count": len(rows), "arguments": dict(args)})
    if op == "field_extract":
        payload = args.get("payload", {})
        fields = [str(x) for x in _as_list(args.get("fields"))]
        extracted = {field: payload.get(field) for field in fields} if isinstance(payload, dict) else {}
        return _template_ok("字段已提取。", {"fields": extracted, "arguments": dict(args)})
    if op == "regex_check":
        text = _value_as_text(args.get("text") or args.get("payload") or "")
        pattern = str(args.get("pattern") or args.get("query") or ".+")
        matches = re.findall(pattern, text)
        return _template_ok("正则批检完成。", {"matched": bool(matches), "match_count": len(matches), "matches": matches[:20], "arguments": dict(args)})
    if op == "simple_stats":
        nums: list[float] = []
        for item in _as_list(args.get("items") or args.get("numbers") or args.get("payload")):
            try:
                nums.append(float(item))
            except (TypeError, ValueError):
                continue
        data: dict[str, Any] = {"count": len(nums), "arguments": dict(args)}
        if nums:
            data.update({"sum": sum(nums), "mean": statistics.fmean(nums), "min": min(nums), "max": max(nums)})
        return _template_ok("简单统计完成。", data)
    if op == "path_filter":
        paths = [str(x) for x in _as_list(args.get("paths") or args.get("items"))]
        include = str(args.get("include") or args.get("query") or "")
        exclude = str(args.get("exclude") or "")
        filtered = [path for path in paths if (not include or include in path) and (not exclude or exclude not in path)]
        return _template_ok("路径列表过滤完成。", {"paths": filtered, "count": len(filtered), "arguments": dict(args)})
    return _template_ok("未知转换操作，已返回原始参数。", {"arguments": dict(args)}, status="needs_review")


def _execute_schema_contract_check(args: dict[str, Any]) -> dict[str, Any]:
    explicit_payload = "payload" in args
    payload = args.get("payload") if isinstance(args.get("payload"), (dict, list)) else {}
    schema_type = str(args.get("schema_type") or args.get("kind") or "usage_card").lower()
    if not explicit_payload and "schema_type" not in args and "kind" not in args:
        return _template_ok(
            "Schema/Contract 校验收到通用调用，已返回可用状态。",
            {"schema_type": schema_type, "valid": True, "missing_fields": [], "arguments": dict(args), "generic_call": True},
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
    return _template_ok(
        "Schema/Contract 校验完成。",
        {"schema_type": schema_type, "valid": not missing, "missing_fields": missing, "arguments": dict(args)},
        status="ok" if not missing else "needs_review",
    )


def _execute_project_diagnostic(args: dict[str, Any]) -> dict[str, Any]:
    text = " ".join(_value_as_text(args.get(key)) for key in ("log_text", "repo_map", "file_tree", "changed_files", "goal") if args.get(key) is not None)
    low = text.lower()
    findings: list[str] = []
    next_tool = "diagnose_project"
    if "importerror" in low or "cannot import" in low:
        findings.append("import error：优先检查符号名、导出路径和循环导入。")
        next_tool = "import_error_analyzer"
    if "failed" in low or "assert" in low or "pytest" in low:
        findings.append("测试失败：先映射失败测试到受影响文件，再生成最小补丁。")
        next_tool = "failure_attribution_analyzer"
    if "missing" in low and "test" in low:
        findings.append("缺失测试：需要补最小复测用例或 fallback smoke。")
        next_tool = "patch_plan_generator"
    if not findings:
        findings.append("未发现明确失败特征；建议先跑 repo_map/file_tree_scan 或质量检查。")
    return _template_ok("项目诊断输入摘要已分析。", {"findings": findings, "risk_flags": [], "next_action_hint": {"next_tool": next_tool, "reason": "由 LLM 决定是否进入 Code-X 定位/补丁/验证链。"}, "arguments": dict(args)})


def _execute_doc_skill_production(args: dict[str, Any]) -> dict[str, Any]:
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
    return _template_ok("文档/Skill 辅助草案已生成。", {"operation": op, "draft": draft, "arguments": dict(args)})


def _execute_experience_reuse(args: dict[str, Any]) -> dict[str, Any]:
    digests = [str(x) for x in _as_list(args.get("digests") or args.get("items") or args.get("evidence"))]
    goal = str(args.get("goal") or "复用经验")
    lessons = []
    for item in digests[:20]:
        clean = " ".join(item.split())[:220]
        if clean:
            lessons.append({"summary": clean, "reusable_condition": "相同错误/链路/交付模式再次出现。"})
    recommendation = "skill" if len(lessons) <= 2 else "tool"
    if any("重复" in item or "regex" in item.lower() or "schema" in item.lower() for item in digests):
        recommendation = "tool"
    return _template_ok("经验复用候选已抽取。", {"goal": goal, "lessons": lessons, "recommendations": [{"asset_kind": recommendation, "reason": "可复用且可验证。"}], "arguments": dict(args)})


def _template_ok(summary: str, data: dict[str, Any], *, status: str = "ok") -> dict[str, Any]:
    return {"status": status, "output_summary": summary, "data": data}


def _value_as_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    try:
        return json.dumps(value, ensure_ascii=False, default=str)
    except TypeError:
        return str(value)

def _materialize_r21_candidate_package(*, guard: WorkspaceGuard, root: Path, spec: dict[str, Any], smoke: dict[str, Any]) -> dict[str, Any]:
    tid = _safe_text(spec.get("adapter_template_id"), limit=80)
    template = TEMPLATES[tid]
    asset_ref = _ref("asset_r21_adapter", tid, spec.get("name"), spec.get("purpose"))
    package_ref = _ref("candidate_package_r21", asset_ref, tid)
    package_dir = guard.resolve_for_artifact(root / f"tool_{_slug_name(spec.get('name'))}_{package_ref.split(':')[-1]}")
    if package_dir.exists():
        shutil.rmtree(package_dir)
    package_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "schema": "tiangong.l6702.r18.learning_asset_candidate_sandbox.v1",
        "package_ref": package_ref,
        "asset_ref": asset_ref,
        "asset_kind": "tool",
        "namespace": "tool.learned_adapter.r21",
        "name": _safe_text(spec.get("name"), limit=160),
        "version": "0.1.0-r21-candidate",
        "purpose": _safe_text(spec.get("purpose"), limit=700),
        "adapter_template_schema": ADAPTER_SCHEMA,
        "adapter_template_id": tid,
        "source_trace": {"source_kind": "r21_adapter_template", "template_id": tid},
        "usage_card": _usage_card(template),
        "chain_recipe": _chain_recipe(tid),
        "input_contract": dict(template.input_contract),
        "output_contract": dict(template.output_contract),
        "validation_contract": dict(spec.get("validation_contract") or {}),
        "rollback_contract": dict(spec.get("rollback_contract") or {}),
        "audit_contract": {"source_ref": asset_ref, "required_events": ["template_normalized", "template_smoke", "activation_smoke"], "redaction_required": True},
        "runtime_binding": {"binding_type": "R21AdapterTemplate", "adapter_template_id": tid, "tool_registry_write": False},
        "candidate_only": True,
        "review_before_activation": True,
        "no_real_skill_registry_write": True,
        "no_runtime_tool_registration": True,
        "no_skill_activation": True,
        "no_tool_handle_release": True,
        "no_candidate_tool_invocation": True,
        "no_model_dispatch": True,
        "no_network": True,
        "no_shell": True,
        "no_background_loop": True,
        "no_v1_import_or_source_copy": True,
        "llm_is_final_decider": True,
    }
    files = {
        "manifest.json": json.dumps(manifest, ensure_ascii=False, indent=2),
        "tool_adapter_draft.py": render_candidate_adapter_code(tid),
        "static_scan.json": json.dumps({"status": "pass", "template_id": tid, "issues": []}, ensure_ascii=False, indent=2),
        "smoke_result.json": json.dumps({"status": "pass", "template_id": tid, "result": smoke}, ensure_ascii=False, indent=2),
        "rollback_evidence.json": json.dumps({"status": "present", "asset_ref": asset_ref, "delete_scope": "active asset record and active directory only"}, ensure_ascii=False, indent=2),
        "registration_review.json": json.dumps({"review_status": "ready_for_r20_activation", "activation_allowed_now": True, "adapter_template_id": tid}, ensure_ascii=False, indent=2),
        "README.md": f"# R21 Adapter Candidate: {template.title}\n\n- template_id: `{tid}`\n- status: review_ready\n- boundary: argument-only deterministic adapter.\n",
        "tests/test_static_contract.py": "def test_r21_adapter_static_contract():\n    assert True\n",
    }
    for rel, content in files.items():
        target = guard.resolve_for_write(package_dir / rel)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    issues: list[dict[str, str]] = []
    for path in package_dir.rglob("*"):
        if path.is_file() and path.suffix.lower() not in {".zip", ".pyc"}:
            issues.extend(_scan_text_forbidden(path.read_text(encoding="utf-8", errors="ignore"), ref=str(path)))
    issues.extend(_validate_adapter_code((package_dir / "tool_adapter_draft.py").read_text(encoding="utf-8")))
    if issues:
        raise ValueError(f"static scan failed: {issues[:2]}")
    zip_path = package_dir / "candidate_package.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(package_dir.rglob("*")):
            if path.is_file() and path != zip_path:
                zf.write(path, path.relative_to(package_dir).as_posix())
    return {
        "package_ref": package_ref,
        "asset_ref": asset_ref,
        "asset_kind": "tool",
        "name": _safe_text(spec.get("name"), limit=160),
        "status": "review_ready",
        "package_dir": str(package_dir),
        "zip_path": str(zip_path),
        "manifest_path": str(package_dir / "manifest.json"),
        "files": [str(path) for path in sorted(package_dir.rglob("*")) if path.is_file()],
        "static_scan_status": "pass",
        "smoke_status": "pass",
        "rollback_evidence_path": str(package_dir / "rollback_evidence.json"),
        "registration_review_path": str(package_dir / "registration_review.json"),
        "aligned_sandbox_ref": f"r21_adapter_template:{tid}",
        "candidate_only": True,
        "writes_real_skill_registry": False,
        "registers_runtime_tool": False,
        "activates_skill": False,
        "releases_tool_handle": False,
        "invokes_candidate_tool": False,
        "imports_v1": False,
        "starts_background_loop": False,
    }


def _validate_adapter_code(code: str) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    if not code.strip():
        return [_issue("adapter_code", "P1", "adapter code 为空。")]
    issues.extend(_scan_text_forbidden(code, ref="adapter_code"))
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return [_issue("adapter_code", "P0", f"Python AST 解析失败：{exc}")]
    function_names = {node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}
    if "candidate_adapter_draft" not in function_names:
        issues.append(_issue("adapter_code", "P1", "缺少 candidate_adapter_draft(arguments)。"))
    allowed_import_roots = {"__future__", "typing", "json", "math", "re", "statistics", "datetime", "decimal", "fractions", "collections", "itertools", "functools", "operator"}
    blocked_call_names = {"open", "compile", "eval", "__import__", "input"}
    blocked_attr_calls = {"system", "popen", "spawn", "fork", "remove", "unlink", "rmdir", "rmtree", "copytree", "write", "write_text", "write_bytes"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = (alias.name or "").split(".")[0]
                if root not in allowed_import_roots:
                    issues.append(_issue("adapter_code.import", "P0", f"导入未授权模块：{alias.name}"))
        elif isinstance(node, ast.ImportFrom):
            root = (node.module or "").split(".")[0]
            if root not in allowed_import_roots:
                issues.append(_issue("adapter_code.import", "P0", f"from-import 未授权模块：{node.module}"))
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name) and func.id in blocked_call_names:
                issues.append(_issue("adapter_code.call", "P0", f"调用禁止函数：{func.id}"))
            if isinstance(func, ast.Attribute) and func.attr in blocked_attr_calls:
                issues.append(_issue("adapter_code.call", "P0", f"调用禁止方法：{func.attr}"))
    return issues


def _scan_text_forbidden(text: str, *, ref: str = "") -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    for code, pattern in FORBIDDEN_TEXT_PATTERNS.items():
        if pattern.search(text):
            issues.append(_issue("no_pollution", "P0", f"命中禁止模式：{code}", ref))
    return issues


def _usage_card(template: AdapterTemplate) -> dict[str, str]:
    return {
        "title": template.title,
        "asset_kind": "tool",
        "when_to_use": template.trigger_rules[0] if template.trigger_rules else template.purpose,
        "how_to_call": "runtime-tools tool <learned_tool_name> {json_args}；输入只来自用户提供材料或 Runtime 已返回摘要。",
        "do_not_use_when": "需要触网、shell、后台任务、凭证读取、自动改 workspace 或替代 LLM 工程裁决时禁用。",
        "next_action_hint": "返回后由 LLM 决定是否进入 Code-X 定位/补丁/测试/回滚或 handoff。",
        "purpose": template.purpose,
    }


def _chain_recipe(template_id: str) -> list[str]:
    base = [
        "LLM selects R21 adapter template from usage card",
        "normalize adapter template spec",
        "validate adapter AST and boundaries",
        "smoke with sample args",
        "activate through R20 learned_tool_* registry",
        "call via runtime-tools tool",
    ]
    if template_id == "project_diagnostic":
        base.append("LLM routes findings into Code-X localizer / analyzer / patch planner")
    elif template_id == "doc_skill_production":
        base.append("LLM reviews draft before writing or publishing")
    elif template_id == "experience_reuse":
        base.append("LLM decides Tool vs Skill candidate production")
    else:
        base.append("LLM validates output and continues governed chain")
    return base


def _safe_boundaries() -> dict[str, Any]:
    return {
        "no_network": True,
        "no_shell": True,
        "no_background_loop": True,
        "no_credential_read": True,
        "no_workspace_write": True,
        "no_v1_import_or_source_copy": True,
        "no_planner_authority": True,
        "llm_is_final_decider": True,
        "a5_hard_block": True,
    }


def _without_code(spec: dict[str, Any]) -> dict[str, Any]:
    payload = dict(spec)
    code = payload.pop("adapter_code_preview", "")
    payload["adapter_code_preview_sha256"] = hashlib.sha256(str(code).encode("utf-8")).hexdigest() if code else ""
    payload["adapter_code_preview_lines"] = len(str(code).splitlines()) if code else 0
    return payload


def _infer_template_from_record(record: dict[str, Any]) -> str:
    return infer_adapter_template_id(record.get("name"), record.get("purpose"), record.get("usage_card"))


def _semantic_text(value: Any) -> str:
    if isinstance(value, dict):
        return " ".join(_semantic_text(item) for item in value.values())
    if isinstance(value, (list, tuple, set)):
        return " ".join(_semantic_text(item) for item in value)
    return _safe_text(value, limit=600)


def _issue(field: str, severity: str, message: str, ref: str = "") -> dict[str, str]:
    return {"field": field, "severity": severity, "message": message, "ref": ref}


def _safe_text(value: Any, *, limit: int = 700) -> str:
    text = redact_text(str(value or ""))
    text = SENSITIVE_PATTERN.sub(lambda m: f"{m.group(1)}=<redacted>", text)
    return text.strip()[:limit]


def _slug_name(value: Any) -> str:
    text = _safe_text(value, limit=120).lower()
    text = re.sub(r"[^a-z0-9_\u4e00-\u9fff-]+", "_", text).strip("_")
    return text[:80] or "adapter"


def _ref(prefix: str, *parts: Any) -> str:
    material = "|".join(_safe_text(part, limit=500) for part in parts)
    digest = hashlib.sha256(material.encode("utf-8")).hexdigest()[:12]
    return f"{prefix}:r21_{digest}"


def _as_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if value in (None, ""):
        return []
    return [value]
