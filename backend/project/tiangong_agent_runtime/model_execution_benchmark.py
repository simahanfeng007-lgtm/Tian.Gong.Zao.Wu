"""L6.72.59 模型执行力操作系统 Benchmark 与 RC Gate。

本模块提供离线、确定性、可复跑的 benchmark。它不触网、不读取真实凭证，
只通过 RuntimeEntry / Planner / ExecutionSpine / Tool adapters / Frontend SSE projection
验证 L6.72.54-58 已完成能力是否真正收口为“模型执行力操作系统”。
"""

from __future__ import annotations

import json
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from statistics import mean
from typing import Any, Callable

from tiangong_agent_shell.config_loader import ModelConfig
from tiangong_agent_shell.model_client_port import ChatResult, CompiledPromptEnvelope

from .activation_protocol import ActivationForm
from .frontend_contract import runtime_result_to_sse_events
from .planner_mode import PlannerMode
from .runtime_entry import RuntimeEntry, RuntimeRunResult

BENCHMARK_SCHEMA = "tiangong.l6_72_59.model_execution_os_benchmark.v1"
RC_CANDIDATE_NAME = "L6.73.0_ModelExecutionOS_RC"
SUCCESS_STATUSES = {"ok", "completed_pass", "completed_with_warnings", "deterministic_fallback"}
RECOVERABLE_STATUSES = {"partial_with_resume", "failed_recoverable", "provider_not_ready", "model_required"}
CHAT_POLLUTION_MARKERS = (
    "planner_plan",
    "tool_name",
    "tool_started",
    "tool_result",
    "active_model_policy",
    "context_window_bundle",
    "skill_playbook_route",
    "ExecutionSpine",
    "compiled_prompt_id",
    "stderr",
    "stdout",
    "repo_map",
    "patch_plan",
    "Step 1",
    "步骤1",
)


@dataclass(frozen=True)
class BenchmarkCaseResult:
    case_id: str
    title: str
    ok: bool
    status: str
    failure_kind: str = ""
    activation_success: bool = False
    plan_parse_success: bool = False
    tool_execution_success_rate: float = 0.0
    recovery_expected: bool = False
    recovery_attempted: bool = False
    recovery_succeeded: bool = False
    quality_gate_pass: bool = False
    artifact_delivery: bool = False
    human_intervention_count: int = 0
    false_completed: bool = False
    chat_transcript_pollution_count: int = 0
    observed_details: dict[str, Any] = field(default_factory=dict)

    def public_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "title": self.title,
            "ok": self.ok,
            "status": self.status,
            "failure_kind": self.failure_kind,
            "activation_success": self.activation_success,
            "plan_parse_success": self.plan_parse_success,
            "tool_execution_success_rate": round(self.tool_execution_success_rate, 4),
            "recovery_expected": self.recovery_expected,
            "recovery_attempted": self.recovery_attempted,
            "recovery_succeeded": self.recovery_succeeded,
            "quality_gate_pass": self.quality_gate_pass,
            "artifact_delivery": self.artifact_delivery,
            "human_intervention_count": self.human_intervention_count,
            "false_completed": self.false_completed,
            "chat_transcript_pollution_count": self.chat_transcript_pollution_count,
            "observed_details": _json_safe(self.observed_details),
        }


@dataclass(frozen=True)
class BenchmarkMetrics:
    activation_success_rate: float
    plan_parse_success_rate: float
    tool_execution_success_rate: float
    recovery_success_rate: float
    quality_gate_pass_rate: float
    artifact_delivery_rate: float
    average_retries: float
    human_intervention_count: int
    false_completed_count: int
    chat_transcript_pollution_count: int

    def public_dict(self) -> dict[str, Any]:
        return {
            "activation_success_rate": round(self.activation_success_rate, 4),
            "plan_parse_success_rate": round(self.plan_parse_success_rate, 4),
            "tool_execution_success_rate": round(self.tool_execution_success_rate, 4),
            "recovery_success_rate": round(self.recovery_success_rate, 4),
            "quality_gate_pass_rate": round(self.quality_gate_pass_rate, 4),
            "artifact_delivery_rate": round(self.artifact_delivery_rate, 4),
            "average_retries": round(self.average_retries, 4),
            "human_intervention_count": self.human_intervention_count,
            "false_completed_count": self.false_completed_count,
            "chat_transcript_pollution_count": self.chat_transcript_pollution_count,
        }


@dataclass(frozen=True)
class BenchmarkSuiteReport:
    schema: str
    rc_candidate: str
    ok: bool
    rc_ready: bool
    status: str
    metrics: BenchmarkMetrics
    cases: tuple[BenchmarkCaseResult, ...]
    functional_gap_assessment: tuple[dict[str, Any], ...]
    frontend_quality_assessment: tuple[dict[str, Any], ...]
    release_blockers: tuple[str, ...] = tuple()
    next_action: str = ""

    def public_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "rc_candidate": self.rc_candidate,
            "ok": self.ok,
            "rc_ready": self.rc_ready,
            "status": self.status,
            "metrics": self.metrics.public_dict(),
            "cases": [case.public_dict() for case in self.cases],
            "functional_gap_assessment": list(self.functional_gap_assessment),
            "frontend_quality_assessment": list(self.frontend_quality_assessment),
            "release_blockers": list(self.release_blockers),
            "next_action": self.next_action,
            "rc_gate": {
                "false_completed_count_must_be_zero": True,
                "chat_transcript_pollution_count_must_be_zero": True,
                "provider_secret_free": True,
                "conversation_workbench_separation": True,
            },
        }

    def to_markdown(self) -> str:
        data = self.public_dict()
        lines = [
            f"# {self.rc_candidate} Benchmark RC 报告",
            "",
            f"- status: {self.status}",
            f"- ok: {self.ok}",
            f"- rc_ready: {self.rc_ready}",
            "",
            "## Metrics",
        ]
        for key, value in data["metrics"].items():
            lines.append(f"- {key}: {value}")
        lines.extend(["", "## Cases"])
        for case in self.cases:
            mark = "PASS" if case.ok else "FAIL"
            lines.append(f"- {mark} {case.case_id}｜{case.title}｜status={case.status}｜pollution={case.chat_transcript_pollution_count}｜false_completed={case.false_completed}")
        lines.extend(["", "## Functional Gap Assessment"])
        for item in self.functional_gap_assessment:
            lines.append(f"- {item.get('status')}: {item.get('gap')} → {item.get('action')}")
        lines.extend(["", "## Frontend Quality Assessment"])
        for item in self.frontend_quality_assessment:
            lines.append(f"- {item.get('status')}: {item.get('finding')} → {item.get('action')}")
        if self.release_blockers:
            lines.extend(["", "## Release Blockers"])
            for blocker in self.release_blockers:
                lines.append(f"- {blocker}")
        lines.extend(["", f"next_action: {self.next_action}"])
        return "\n".join(lines).rstrip() + "\n"


class StaticPlanClient:
    """Deterministic model-client stand-in used only for offline benchmark."""

    provider = "mock"

    def __init__(self, *plans: dict[str, Any]) -> None:
        self._plans = list(plans)
        self.calls: list[CompiledPromptEnvelope] = []

    def chat(self, prompt: CompiledPromptEnvelope, config: ModelConfig) -> ChatResult:
        self.calls.append(prompt)
        payload = self._plans.pop(0) if self._plans else {"steps": []}
        return ChatResult(content=json.dumps(payload, ensure_ascii=False), provider="mock", model=config.model)


class FailIfCalledClient:
    provider = "mock"

    def chat(self, prompt: CompiledPromptEnvelope, config: ModelConfig) -> ChatResult:  # pragma: no cover - should not be called
        raise AssertionError("弱模型被错误送入主脑 Planner。")


def run_model_execution_os_benchmark(workspace_root: str | Path | None = None) -> BenchmarkSuiteReport:
    """Run the deterministic L6.72.59 suite and return an RC gate report."""

    root_ctx = _workspace_context(workspace_root)
    with root_ctx as root:
        root_path = Path(root)
        cases = (
            _case_simple_file(root_path / "case01_simple_file"),
            _case_code_micro_fix(root_path / "case02_code_micro_fix"),
            _case_code_multifile_fix(root_path / "case03_multifile_fix"),
            _case_document_export(root_path / "case04_document"),
            _case_recovery_loop(root_path / "case05_recovery"),
            _case_long_chain_delivery(root_path / "case06_long_chain_delivery"),
            _case_weak_model_block(root_path / "case07_weak_model_block"),
        )
    metrics = _compute_metrics(cases)
    release_blockers: list[str] = []
    if any(not case.ok for case in cases):
        release_blockers.append("one_or_more_benchmark_cases_failed")
    if metrics.false_completed_count != 0:
        release_blockers.append("false_completed_count_must_be_zero")
    if metrics.chat_transcript_pollution_count != 0:
        release_blockers.append("chat_transcript_pollution_count_must_be_zero")
    if metrics.activation_success_rate < 0.99:
        release_blockers.append("activation_success_rate_below_rc_threshold")
    if metrics.plan_parse_success_rate < 0.80:
        release_blockers.append("plan_parse_success_rate_below_rc_threshold")
    if metrics.artifact_delivery_rate < 0.75:
        release_blockers.append("artifact_delivery_rate_below_rc_threshold")

    functional_gaps = (
        {
            "gap": "缺少固定 benchmark/RC gate 会影响版本是否可宣称执行力操作系统收口。",
            "impact": "release_confidence",
            "action": "已补充 L6.72.59 离线 benchmark、指标聚合、false_completed/chat_pollution 硬门。",
            "status": "supplemented",
        },
        {
            "gap": "document_apply_rewrite 旧清洗逻辑会剥离代码行尾冒号，可能造成工具报告成功但代码未真正修好。",
            "impact": "false_completed_risk",
            "action": "已改为保留代码/配置 literal replacement 的行尾冒号和语法字符，并纳入 smoke。",
            "status": "supplemented",
        },
    )
    frontend_findings = (
        {
            "finding": "前端终态只认 ok/completed/success，未覆盖 completed_pass/completed_with_warnings/deterministic_fallback。",
            "impact": "success_task_displayed_as_failed",
            "action": "已补充统一 success status 判定与 RunWorkbench 状态 alias。",
            "status": "optimized",
        },
        {
            "finding": "run_started 提示仍写‘后续步骤会持续写入会话区’，与 L6.72.54 会话/工作台分离口径冲突。",
            "impact": "human_factors_confusion",
            "action": "已改为‘后续步骤写入任务工作台，不写入会话区’。",
            "status": "optimized",
        },
    )
    ok = not release_blockers
    return BenchmarkSuiteReport(
        schema=BENCHMARK_SCHEMA,
        rc_candidate=RC_CANDIDATE_NAME,
        ok=ok,
        rc_ready=ok,
        status="rc_ready" if ok else "rc_blocked",
        metrics=metrics,
        cases=cases,
        functional_gap_assessment=functional_gaps,
        frontend_quality_assessment=frontend_findings,
        release_blockers=tuple(release_blockers),
        next_action="promote_to_L6.73.0_RC" if ok else "fix_release_blockers_and_rerun_benchmark",
    )


def _case_simple_file(workspace: Path) -> BenchmarkCaseResult:
    workspace.mkdir(parents=True, exist_ok=True)
    form = _work_form("file", "single_step")
    result = RuntimeEntry().run_text(
        "创建 hello.txt 内容 abc",
        workspace=workspace,
        planner_mode=PlannerMode.MODEL_SUGGEST,
        model_config=ModelConfig(provider="openai", model="gpt-5-test", api_key=""),
        activation_form=form,
    )
    artifact_ok = (workspace / "hello.txt").read_text(encoding="utf-8") == "abc"
    return _evaluate_case("simple_file_task", "创建 txt、读取、验证内容", result, artifact_ok=artifact_ok)


def _case_code_micro_fix(workspace: Path) -> BenchmarkCaseResult:
    workspace.mkdir(parents=True, exist_ok=True)
    (workspace / "micro.py").write_text("def answer():\n    return 42\n", encoding="utf-8")
    plan = {
        "steps": [
            {"tool_name": "write_workspace_file", "arguments": {"path": "micro.py", "content": "def answer():\n    return 43\n"}, "reason": "minimal patch"},
            {"tool_name": "run_python_quality_check", "arguments": {"command": "compileall", "target": "micro.py"}, "reason": "verify compileall"},
        ]
    }
    result = RuntimeEntry().run_text(
        "修复一个 Python 微错误并运行 compileall",
        workspace=workspace,
        planner_mode=PlannerMode.MODEL_SUGGEST,
        model_config=_strong_cfg(),
        model_client=StaticPlanClient(plan),
        activation_form=_work_form("code", "multi_step"),
    )
    artifact_ok = "return 43" in (workspace / "micro.py").read_text(encoding="utf-8")
    return _evaluate_case("code_micro_fix", "修复 Python syntax/import 类微错误并跑 compileall", result, artifact_ok=artifact_ok)


def _case_code_multifile_fix(workspace: Path) -> BenchmarkCaseResult:
    pkg = workspace / "pkg"
    pkg.mkdir(parents=True, exist_ok=True)
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "a.py").write_text("from .b import value\n\ndef answer():\n    return value()\n", encoding="utf-8")
    (pkg / "b.py").write_text("def value():\n    return 1\n", encoding="utf-8")
    plan = {
        "steps": [
            {"tool_name": "write_workspace_file", "arguments": {"path": "pkg/a.py", "content": "from .b import value\n\ndef answer():\n    return value() + 1\n"}, "reason": "patch caller"},
            {"tool_name": "write_workspace_file", "arguments": {"path": "pkg/b.py", "content": "def value():\n    return 41\n"}, "reason": "patch callee"},
            {"tool_name": "run_python_quality_check", "arguments": {"command": "compileall", "target": "pkg"}, "reason": "verify multi-file compile"},
        ]
    }
    result = RuntimeEntry().run_text(
        "定位跨文件错误，修改两个文件并运行质量检查",
        workspace=workspace,
        planner_mode=PlannerMode.MODEL_SUGGEST,
        model_config=_strong_cfg(),
        model_client=StaticPlanClient(plan),
        activation_form=_work_form("code", "long_chain"),
    )
    artifact_ok = "return value() + 1" in (pkg / "a.py").read_text(encoding="utf-8") and "return 41" in (pkg / "b.py").read_text(encoding="utf-8")
    return _evaluate_case("code_multifile_fix", "定位跨文件错误、改两个文件、跑 compileall", result, artifact_ok=artifact_ok)


def _case_document_export(workspace: Path) -> BenchmarkCaseResult:
    doc_dir = workspace / "docs"
    doc_dir.mkdir(parents=True, exist_ok=True)
    (doc_dir / "report.md").write_text("# AI 转型需求\n\n企业需要培训、流程梳理、落地陪跑和交付验收。\n", encoding="utf-8")
    plan = {
        "steps": [
            {"tool_name": "document_parse", "arguments": {"path": "docs/report.md", "max_chars": 4000}, "reason": "parse document"},
            {"tool_name": "document_query", "arguments": {"path": "docs/report.md", "query": "企业需要什么", "top_k": 3}, "reason": "answer with context"},
            {"tool_name": "document_export", "arguments": {"path": "docs/report.md", "target": "exports/report_summary.md", "format": "md", "query": "AI 转型需求"}, "reason": "export summary"},
        ]
    }
    result = RuntimeEntry().run_text(
        "解析 report.md，回答问题并导出摘要",
        workspace=workspace,
        planner_mode=PlannerMode.MODEL_SUGGEST,
        model_config=_strong_cfg(),
        model_client=StaticPlanClient(plan),
        activation_form=_work_form("document", "multi_step"),
    )
    artifact_ok = (workspace / "exports" / "report_summary.md").exists()
    return _evaluate_case("document_task", "解析文档、追问、导出摘要", result, artifact_ok=artifact_ok)


def _case_recovery_loop(workspace: Path) -> BenchmarkCaseResult:
    workspace.mkdir(parents=True, exist_ok=True)
    (workspace / "bad.py").write_text("def broken()\n    return 1\n", encoding="utf-8")
    initial = {"steps": [{"tool_name": "run_python_quality_check", "arguments": {"command": "compileall", "target": "bad.py"}, "reason": "first validation must fail"}]}
    repair = {
        "steps": [
            {"tool_name": "write_workspace_file", "arguments": {"path": "bad.py", "content": "def broken():\n    return 1\n"}, "reason": "rewrite syntax fix"},
            {"tool_name": "run_python_quality_check", "arguments": {"command": "compileall", "target": "bad.py"}, "reason": "verify repair"},
        ]
    }
    result = RuntimeEntry().run_text(
        "第一次计划会失败，请进入 repair loop 后修复 Python 语法错误",
        workspace=workspace,
        planner_mode=PlannerMode.MODEL_SUGGEST,
        model_config=_strong_cfg(),
        model_client=StaticPlanClient(initial, repair),
        activation_form=_work_form("code", "multi_step"),
    )
    artifact_ok = "def broken():" in (workspace / "bad.py").read_text(encoding="utf-8")
    return _evaluate_case("recovery_task", "第一次计划失败后进入一次性 repair loop", result, artifact_ok=artifact_ok, recovery_expected=True)


def _case_long_chain_delivery(workspace: Path) -> BenchmarkCaseResult:
    src = workspace / "src"
    src.mkdir(parents=True, exist_ok=True)
    (src / "app.py").write_text("def main():\n    return 'ok'\n", encoding="utf-8")
    (workspace / "README.md").write_text("# delivery fixture\n", encoding="utf-8")
    plan = {
        "steps": [
            {"tool_name": "scan_project", "arguments": {"path": ".", "max_depth": 4, "max_files": 200}, "reason": "repo discovery"},
            {"tool_name": "run_python_quality_check", "arguments": {"command": "compileall", "target": "src"}, "reason": "quality check"},
            {"tool_name": "diagnose_project", "arguments": {"path": ".", "max_depth": 4, "max_files": 200}, "reason": "diagnose"},
            {"tool_name": "create_zip_package", "arguments": {"source": ".", "target": "dist/delivery.zip"}, "reason": "delivery artifact"},
        ]
    }
    result = RuntimeEntry().run_text(
        "扫描项目，质量检查，打包交付 zip，并生成报告",
        workspace=workspace,
        planner_mode=PlannerMode.MODEL_SUGGEST,
        model_config=_strong_cfg(),
        model_client=StaticPlanClient(plan),
        activation_form=_work_form("mixed", "long_chain"),
    )
    artifact_ok = (workspace / "dist" / "delivery.zip").exists() and (workspace / "dist" / "delivery.zip.sha256").exists()
    return _evaluate_case("long_chain_delivery", "扫描项目→验证→诊断→打包→报告", result, artifact_ok=artifact_ok)


def _case_weak_model_block(workspace: Path) -> BenchmarkCaseResult:
    workspace.mkdir(parents=True, exist_ok=True)
    result = RuntimeEntry().run_text(
        "修复这个项目并打包",
        workspace=workspace,
        planner_mode=PlannerMode.MODEL_SUGGEST,
        model_config=ModelConfig(provider="weak", model="weak-tiny", api_key="mockkey_test", base_url="https://api.example"),
        model_client=FailIfCalledClient(),
        activation_form=_work_form("code", "long_chain"),
    )
    expected_block = result.status == "model_required" and result.failure_kind == "weak_model_not_allowed" and not result.has_executed_tools
    return _evaluate_case("weak_model_block", "弱模型不能被误当主脑", result, artifact_ok=expected_block, expected_success_status=False)


def _evaluate_case(
    case_id: str,
    title: str,
    result: RuntimeRunResult,
    *,
    artifact_ok: bool,
    recovery_expected: bool = False,
    expected_success_status: bool = True,
) -> BenchmarkCaseResult:
    public_events = runtime_result_to_sse_events(result)
    conversation_payload = json.dumps([e.get("payload", {}) for e in public_events if e.get("display_channel") == "conversation"], ensure_ascii=False)
    pollution_count = sum(1 for marker in CHAT_POLLUTION_MARKERS if marker.lower() in conversation_payload.lower())
    result_status = str(getattr(result, "status", "") or (getattr(getattr(result, "projection", None), "status", "") or ""))
    success_status = result_status in SUCCESS_STATUSES
    failed_results = [item for item in getattr(result, "results", []) or [] if not getattr(item, "ok", False)]
    result_count = len(getattr(result, "results", []) or [])
    ok_results = result_count - len(failed_results)
    tool_rate = 1.0 if result_count == 0 else ok_results / max(1, result_count)
    adaptive = getattr(result, "adaptive_work_loop", None)
    recovery_attempted = bool(getattr(adaptive, "attempted", False) or getattr(result, "plan_repair_attempted", False))
    recovery_succeeded = bool(getattr(adaptive, "repair_succeeded", False))
    activation_success = getattr(result, "activation_form", None) is not None
    planner_result = getattr(result, "planner_result", None)
    plan_parse_success = bool(getattr(planner_result, "ok", False) or getattr(result, "deterministic_fallback_used", False) or (not expected_success_status and result_status in RECOVERABLE_STATUSES | {"model_required"}))
    quality_gate_pass = bool(success_status or (recovery_expected and recovery_succeeded))
    human_count = len(getattr(result, "pending_confirmations", []) or [])
    false_completed = bool(success_status and expected_success_status and (not artifact_ok or (failed_results and not recovery_succeeded)))
    if not expected_success_status:
        false_completed = success_status
    ok = bool(
        artifact_ok
        and activation_success
        and plan_parse_success
        and pollution_count == 0
        and not false_completed
        and ((success_status or recovery_succeeded) if expected_success_status else result_status in RECOVERABLE_STATUSES | {"model_required"})
    )
    return BenchmarkCaseResult(
        case_id=case_id,
        title=title,
        ok=ok,
        status=result_status,
        failure_kind=str(getattr(result, "failure_kind", "") or ""),
        activation_success=activation_success,
        plan_parse_success=plan_parse_success,
        tool_execution_success_rate=tool_rate,
        recovery_expected=recovery_expected,
        recovery_attempted=recovery_attempted,
        recovery_succeeded=recovery_succeeded,
        quality_gate_pass=quality_gate_pass,
        artifact_delivery=artifact_ok,
        human_intervention_count=human_count,
        false_completed=false_completed,
        chat_transcript_pollution_count=pollution_count,
        observed_details={
            "plan_step_count": len(getattr(result, "plan", []) or []),
            "result_count": result_count,
            "failed_result_count": len(failed_results),
            "provider_status": getattr(result, "provider_status", ""),
            "next_action": getattr(result, "next_action", ""),
            "conversation_event_count": len([e for e in public_events if e.get("display_channel") == "conversation"]),
            "workbench_event_count": len([e for e in public_events if e.get("display_channel") == "workbench"]),
        },
    )


def _compute_metrics(cases: tuple[BenchmarkCaseResult, ...]) -> BenchmarkMetrics:
    recovery_cases = [case for case in cases if case.recovery_expected]
    retry_values = [1.0 if case.recovery_attempted else 0.0 for case in cases]
    return BenchmarkMetrics(
        activation_success_rate=_rate(case.activation_success for case in cases),
        plan_parse_success_rate=_rate(case.plan_parse_success for case in cases),
        tool_execution_success_rate=mean(case.tool_execution_success_rate for case in cases) if cases else 0.0,
        recovery_success_rate=_rate(case.recovery_succeeded for case in recovery_cases) if recovery_cases else 1.0,
        quality_gate_pass_rate=_rate(case.quality_gate_pass for case in cases if case.status not in {"model_required"}),
        artifact_delivery_rate=_rate(case.artifact_delivery for case in cases),
        average_retries=mean(retry_values) if retry_values else 0.0,
        human_intervention_count=sum(case.human_intervention_count for case in cases),
        false_completed_count=sum(1 for case in cases if case.false_completed),
        chat_transcript_pollution_count=sum(case.chat_transcript_pollution_count for case in cases),
    )


def _work_form(work_type: str, depth: str) -> ActivationForm:
    return ActivationForm(
        mode="work",
        work_type=work_type,
        execution_depth=depth,
        tools_requested=True,
        risk_level="A1",
        need_quality_gate=True,
        final_output_contract="execution_report",
    )


def _strong_cfg() -> ModelConfig:
    return ModelConfig(provider="openai", model="gpt-5-test", api_key="mockkey_test-not-real")


def _rate(values: Any) -> float:
    seq = list(values)
    if not seq:
        return 0.0
    return sum(1 for item in seq if item) / len(seq)


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


class _workspace_context:
    def __init__(self, root: str | Path | None) -> None:
        self.root = Path(root).expanduser().resolve() if root is not None else None
        self._tmp: tempfile.TemporaryDirectory[str] | None = None

    def __enter__(self) -> Path:
        if self.root is not None:
            self.root.mkdir(parents=True, exist_ok=True)
            return self.root
        self._tmp = tempfile.TemporaryDirectory(prefix="l67259_benchmark_")
        return Path(self._tmp.name)

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        if self._tmp is not None:
            self._tmp.cleanup()
