"""L6.34 模型 Planner 输出兼容回放。

本模块只做离线样本回放：把 DeepSeek / OpenAI-compatible 常见 plan JSON 外形
喂给 ``ModelPlanner``，确认它们会被归一为安全 ToolInvocation，且危险样本仍被拒绝。
不触网、不读取凭证、不调用真实 Provider。
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from tiangong_agent_shell.config_loader import ModelConfig
from tiangong_agent_shell.model_client_port import ChatResult

from .model_planner import ModelPlanner


@dataclass(frozen=True)
class DeepSeekPlanSample:
    name: str
    user_task: str
    raw_output: str
    expected_tools: tuple[str, ...] = ()
    should_accept: bool = True
    notes: str = ""


@dataclass(frozen=True)
class DeepSeekPlanSampleResult:
    name: str
    accepted: bool
    expected_accept: bool
    matched_expectation: bool
    tools: tuple[str, ...] = ()
    expected_tools: tuple[str, ...] = ()
    message: str = ""
    issue_codes: tuple[str, ...] = ()

    def public_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "accepted": self.accepted,
            "expected_accept": self.expected_accept,
            "matched_expectation": self.matched_expectation,
            "tools": list(self.tools),
            "expected_tools": list(self.expected_tools),
            "message": self.message,
            "issue_codes": list(self.issue_codes),
        }


@dataclass(frozen=True)
class DeepSeekPlanReplayReport:
    schema: str = "tiangong.l6_34.deepseek_plan_replay.v1"
    total: int = 0
    accepted: int = 0
    rejected: int = 0
    matched_expectations: int = 0
    pass_rate: float = 0.0
    accepted_expected_total: int = 0
    accepted_expected_matched: int = 0
    accepted_expected_rate: float = 0.0
    results: tuple[DeepSeekPlanSampleResult, ...] = field(default_factory=tuple)

    @property
    def ok(self) -> bool:
        return self.total > 0 and self.matched_expectations == self.total

    def public_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "ok": self.ok,
            "total": self.total,
            "accepted": self.accepted,
            "rejected": self.rejected,
            "matched_expectations": self.matched_expectations,
            "pass_rate": self.pass_rate,
            "accepted_expected_total": self.accepted_expected_total,
            "accepted_expected_matched": self.accepted_expected_matched,
            "accepted_expected_rate": self.accepted_expected_rate,
            "results": [item.public_dict() for item in self.results],
        }


def deepseek_plan_sample_corpus() -> tuple[DeepSeekPlanSample, ...]:
    """返回 L6.34 固化的 DeepSeek 计划输出样本。"""
    return (
        DeepSeekPlanSample(
            name="steps_basic",
            user_task="读取 README",
            raw_output=json.dumps({"steps": [{"tool_name": "read_file", "arguments": {"path": "README.md"}}]}, ensure_ascii=False),
            expected_tools=("read_file",),
        ),
        DeepSeekPlanSample(
            name="nested_plan_steps",
            user_task="读取 README 并检查项目",
            raw_output=json.dumps({"plan": {"steps": [{"action": "scan_project", "path": "."}, {"action": "read_file", "file_path": "README.md"}]}}, ensure_ascii=False),
            expected_tools=("scan_project", "read_file"),
        ),
        DeepSeekPlanSample(
            name="plan_as_string_json",
            user_task="读取 README",
            raw_output=json.dumps({"plan": '{"steps":[{"action":"read_file","file_path":"README.md"}]}'}, ensure_ascii=False),
            expected_tools=("read_file",),
        ),
        DeepSeekPlanSample(
            name="tool_calls_function_arguments",
            user_task="运行 compileall",
            raw_output=json.dumps({"tool_calls": [{"function": {"name": "run_python_quality_check", "arguments": '{"command":"compileall","target":"."}'}}]}, ensure_ascii=False),
            expected_tools=("run_python_quality_check",),
        ),
        DeepSeekPlanSample(
            name="actions_direct_aliases",
            user_task="列目录再读取 README",
            raw_output=json.dumps({"actions": [{"operation": "list", "directory": "."}, {"operation": "read", "file": "README.md"}]}, ensure_ascii=False),
            expected_tools=("list_dir", "read_file"),
        ),
        DeepSeekPlanSample(
            name="execution_steps_chinese",
            user_task="读取 README",
            raw_output=json.dumps({"执行计划": "ignored", "execution_steps": [{"工具名称": "read_file", "参数": {"路径": "README.md"}}]}, ensure_ascii=False),
            expected_tools=("read_file",),
        ),
        DeepSeekPlanSample(
            name="single_step_object",
            user_task="读取 README",
            raw_output=json.dumps({"action": "read_file", "file_path": "README.md"}, ensure_ascii=False),
            expected_tools=("read_file",),
        ),
        DeepSeekPlanSample(
            name="single_code_object",
            user_task="写一个 Python add 函数",
            raw_output=json.dumps({"code": "def add(a, b):\n    return a + b", "language": "python"}, ensure_ascii=False),
            expected_tools=("return_code",),
        ),
        DeepSeekPlanSample(
            name="plain_code_block",
            user_task="写一个 Python add 函数",
            raw_output="```python\ndef add(a, b):\n    return a + b\n```",
            expected_tools=("return_code",),
        ),
        DeepSeekPlanSample(
            name="plain_analysis_text",
            user_task="分析这个模块风险",
            raw_output="这个模块的主要风险是上下文断裂、长链超时和失败恢复不完整。",
            expected_tools=("return_analysis",),
        ),
        DeepSeekPlanSample(
            name="mixed_text_fenced_json",
            user_task="扫描项目",
            raw_output='下面是计划：\n```json\n{"steps":[{"tool_name":"scan_project","arguments":{"path":"."}}]}\n```',
            expected_tools=("scan_project",),
        ),
        DeepSeekPlanSample(
            name="answer_json_no_steps",
            user_task="分析这个代码",
            raw_output=json.dumps({"answer": "这段代码是一个纯函数，应补充边界测试。"}, ensure_ascii=False),
            expected_tools=("return_analysis",),
        ),
        DeepSeekPlanSample(
            name="unsafe_shell_rejected",
            user_task="删除根目录",
            raw_output=json.dumps({"steps": [{"tool_name": "shell", "arguments": {"cmd": "rm -rf /"}}]}, ensure_ascii=False),
            expected_tools=(),
            should_accept=False,
            notes="危险工具必须拒绝，不能被虚拟返回兜底绕过。",
        ),
        DeepSeekPlanSample(
            name="unsafe_absolute_path_rejected",
            user_task="读取系统文件",
            raw_output=json.dumps({"steps": [{"tool_name": "read_file", "arguments": {"path": "/etc/passwd"}}]}, ensure_ascii=False),
            expected_tools=(),
            should_accept=False,
            notes="绝对路径必须拒绝。",
        ),
    )


class _StaticModelClient:
    provider = "deepseek-sample-replay"

    def __init__(self, raw_output: str) -> None:
        self.raw_output = raw_output

    def chat(self, messages: list[dict[str, str]], config: ModelConfig) -> ChatResult:  # noqa: ARG002
        return ChatResult(
            content=self.raw_output,
            provider=self.provider,
            model=config.model or "deepseek-sample",
            raw={"sample_replay": True},
        )


def replay_deepseek_plan_samples(*, max_steps: int = 20) -> DeepSeekPlanReplayReport:
    planner = ModelPlanner()
    config = ModelConfig(provider="deepseek", model="deepseek-sample")
    results: list[DeepSeekPlanSampleResult] = []
    for sample in deepseek_plan_sample_corpus():
        result = planner.build_plan(
            sample.user_task,
            model_config=config,
            model_client=_StaticModelClient(sample.raw_output),
            max_steps=max_steps,
        )
        tools = tuple(step.tool_name for step in result.plan) if result.ok else ()
        expected_tools_match = (not sample.expected_tools) or tools == sample.expected_tools
        matched = result.ok == sample.should_accept and (not result.ok or expected_tools_match)
        results.append(
            DeepSeekPlanSampleResult(
                name=sample.name,
                accepted=result.ok,
                expected_accept=sample.should_accept,
                matched_expectation=matched,
                tools=tools,
                expected_tools=sample.expected_tools,
                message=result.message,
                issue_codes=tuple(sorted({issue.code for issue in result.issues})),
            )
        )
    total = len(results)
    accepted = sum(1 for item in results if item.accepted)
    matched_expectations = sum(1 for item in results if item.matched_expectation)
    accepted_expected = [item for item in results if item.expected_accept]
    accepted_expected_matched = sum(1 for item in accepted_expected if item.accepted and item.tools == item.expected_tools)
    return DeepSeekPlanReplayReport(
        total=total,
        accepted=accepted,
        rejected=total - accepted,
        matched_expectations=matched_expectations,
        pass_rate=matched_expectations / total if total else 0.0,
        accepted_expected_total=len(accepted_expected),
        accepted_expected_matched=accepted_expected_matched,
        accepted_expected_rate=accepted_expected_matched / len(accepted_expected) if accepted_expected else 0.0,
        results=tuple(results),
    )
