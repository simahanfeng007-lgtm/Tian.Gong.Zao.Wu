"""L6.35 长链压力回放探针。

只使用 RuntimeEntry / PlannerExecutionController / LongChainRunner 真实主链，
不直接调用 adapter，不触网，不读凭证，不修改 tiangong_kernel。
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from time import time
from typing import Any

from tiangong_agent_shell.tool_bridge import ToolExecutionMode

from .runtime_entry import RuntimeEntry
from .tool_invocation import ToolInvocation

L6_35_PRESSURE_SCHEMA = "tiangong.l6_35.long_chain_pressure_probe.v1"


@dataclass(frozen=True)
class LongChainPressureCase:
    name: str
    step_count: int
    status: str
    executed_steps: int
    succeeded_steps: int
    failed_steps: int
    timeout_steps: int
    skipped_steps: int
    progress_snapshot_count: int
    replay_event_count: int
    stopped_reason: str
    report_digest: str
    resume_mode: str
    can_resume: bool
    no_kernel_mutation: bool = True
    no_provider_call: bool = True

    def public_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "step_count": self.step_count,
            "status": self.status,
            "executed_steps": self.executed_steps,
            "succeeded_steps": self.succeeded_steps,
            "failed_steps": self.failed_steps,
            "timeout_steps": self.timeout_steps,
            "skipped_steps": self.skipped_steps,
            "progress_snapshot_count": self.progress_snapshot_count,
            "replay_event_count": self.replay_event_count,
            "stopped_reason": self.stopped_reason,
            "report_digest": self.report_digest,
            "resume_mode": self.resume_mode,
            "can_resume": self.can_resume,
            "no_kernel_mutation": self.no_kernel_mutation,
            "no_provider_call": self.no_provider_call,
        }


@dataclass(frozen=True)
class LongChainPressureReport:
    cases: list[LongChainPressureCase]
    generated_at: float = field(default_factory=time)
    schema: str = L6_35_PRESSURE_SCHEMA
    no_direct_adapter_call: bool = True
    no_parallel_runtime: bool = True
    no_kernel_mutation: bool = True
    no_provider_call: bool = True

    @property
    def ok(self) -> bool:
        return all(case.status == "completed" for case in self.cases)

    def public_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "ok": self.ok,
            "generated_at": self.generated_at,
            "case_count": len(self.cases),
            "cases": [case.public_dict() for case in self.cases],
            "no_direct_adapter_call": self.no_direct_adapter_call,
            "no_parallel_runtime": self.no_parallel_runtime,
            "no_kernel_mutation": self.no_kernel_mutation,
            "no_provider_call": self.no_provider_call,
        }

    def export_json(self, path: str | Path) -> Path:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.public_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        return target

    def markdown_report(self) -> str:
        rows = [
            "# L6.35 长链压力回放报告",
            "",
            f"schema: `{self.schema}`",
            f"ok: `{self.ok}`",
            "",
            "| case | steps | status | executed | progress | replay | stopped | resume |",
            "|---|---:|---|---:|---:|---:|---|---|",
        ]
        for case in self.cases:
            rows.append(
                f"| {case.name} | {case.step_count} | {case.status} | {case.executed_steps} | "
                f"{case.progress_snapshot_count} | {case.replay_event_count} | {case.stopped_reason} | {case.resume_mode} |"
            )
        return "\n".join(rows) + "\n"


def build_pressure_plan(step_count: int) -> list[ToolInvocation]:
    plan: list[ToolInvocation] = []
    for index in range(1, step_count + 1):
        if index % 10 == 1:
            plan.append(ToolInvocation("list_dir", {"path": ".", "source_plan_id": f"pressure_{step_count}"}, step_id=f"p{step_count}_{index:03d}"))
        elif index % 10 == 2:
            plan.append(ToolInvocation("read_file", {"path": "README.md", "max_bytes": 2048, "source_plan_id": f"pressure_{step_count}"}, step_id=f"p{step_count}_{index:03d}"))
        elif index % 3 == 0:
            plan.append(ToolInvocation("return_code", {"language": "python", "content": f"# generated step {index}\nvalue = {index}", "source_plan_id": f"pressure_{step_count}"}, step_id=f"p{step_count}_{index:03d}"))
        else:
            plan.append(ToolInvocation("return_analysis", {"content": f"pressure analysis step {index}", "source_plan_id": f"pressure_{step_count}"}, step_id=f"p{step_count}_{index:03d}"))
    return plan


def run_long_chain_pressure_probe(workspace: str | Path, *, step_counts: tuple[int, ...] = (20, 50, 100)) -> LongChainPressureReport:
    root = Path(workspace)
    root.mkdir(parents=True, exist_ok=True)
    readme = root / "README.md"
    if not readme.exists():
        readme.write_text("# L6.35 pressure workspace\n", encoding="utf-8")
    cases: list[LongChainPressureCase] = []
    for count in step_counts:
        runtime = RuntimeEntry()
        result = runtime.execute_plan(
            build_pressure_plan(count),
            workspace=root,
            user_message=f"l6_35_pressure_{count}",
            tool_mode=ToolExecutionMode.RUNTIME_GOVERNED,
            max_steps=count + 5,
        )
        report = runtime.planner_execution_snapshot()
        resume = report["resume_envelope"]
        cases.append(
            LongChainPressureCase(
                name=f"pressure_{count}",
                step_count=count,
                status=str(report["status"]),
                executed_steps=int(report["executed_steps"]),
                succeeded_steps=int(report["succeeded_steps"]),
                failed_steps=int(report["failed_steps"]),
                timeout_steps=int(report.get("timeout_steps", 0)),
                skipped_steps=int(report["skipped_steps"]),
                progress_snapshot_count=int(report["progress_snapshot_count"]),
                replay_event_count=int(report["replay_event_count"]),
                stopped_reason=str(report["stopped_reason"]),
                report_digest=str(report["report_digest"]),
                resume_mode=str(resume["resume_mode"]),
                can_resume=bool(resume["can_resume"]),
            )
        )
        _ = result
    return LongChainPressureReport(cases=cases)
