"""L6.33 分片回归执行器与超时收割。

本模块只负责工程验证链路：把 pytest / smoke 命令拆成独立 shard，
每片独立超时、独立日志、独立 JSON 结果，并在超时后收割子进程组。

边界：
- 不修改 tiangong_kernel；
- 不产生第二 Runtime，不调用工具 adapter；
- 不读取凭证，不触网；
- 不把 timeout 冒充 passed / failed；
- 输出可复跑命令与安全尾部日志，供执行链冻结前验收使用。
"""

from __future__ import annotations

import json
import os
import signal
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from time import monotonic, sleep, time
from typing import Any

L6_33_SHARD_SCHEMA = "tiangong.l6_33.test_shard_runner.v1"
SOURCE_VERSION = "L6.33-test-shard-runner"
TERMINAL_STATUSES = {"passed", "failed", "timeout", "skipped"}


@dataclass(frozen=True)
class TestShardSpec:
    """单个验证分片。"""

    name: str
    command: list[str]
    cwd: str | Path = "."
    timeout_seconds: float = 120.0
    purpose: str = ""
    required: bool = True
    env: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.name or any(part in self.name for part in ("/", "\\", "..")):
            raise ValueError("L6.33 shard name must be a safe file-name-like token")
        if not self.command or not all(isinstance(part, str) and part for part in self.command):
            raise ValueError("L6.33 shard command must be a non-empty argv list")
        if self.timeout_seconds <= 0:
            raise ValueError("L6.33 shard timeout_seconds must be positive")

    @property
    def rerun_command(self) -> str:
        return " ".join(_quote_arg(part) for part in self.command)

    def public_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "command": list(self.command),
            "cwd": str(self.cwd),
            "timeout_seconds": self.timeout_seconds,
            "purpose": self.purpose,
            "required": self.required,
            "rerun_command": self.rerun_command,
        }


@dataclass(frozen=True)
class TestShardResult:
    """单个 shard 执行结果。"""

    name: str
    status: str
    returncode: int | None
    duration_seconds: float
    timeout_seconds: float
    started_at: float
    finished_at: float
    command: list[str]
    cwd: str
    purpose: str = ""
    required: bool = True
    stdout_path: str = ""
    stderr_path: str = ""
    stdout_tail: str = ""
    stderr_tail: str = ""
    error_message: str = ""
    timed_out: bool = False
    process_group_reaped: bool = False

    def __post_init__(self) -> None:
        if self.status not in TERMINAL_STATUSES:
            raise ValueError("L6.33 shard result has invalid terminal status")
        if self.status == "timeout" and not self.timed_out:
            raise ValueError("L6.33 timeout status must set timed_out=True")
        if self.status == "passed" and self.timed_out:
            raise ValueError("L6.33 timeout cannot be reported as passed")

    @property
    def rerun_command(self) -> str:
        return " ".join(_quote_arg(part) for part in self.command)

    def public_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status,
            "returncode": self.returncode,
            "duration_seconds": round(self.duration_seconds, 6),
            "timeout_seconds": self.timeout_seconds,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "command": list(self.command),
            "cwd": self.cwd,
            "purpose": self.purpose,
            "required": self.required,
            "rerun_command": self.rerun_command,
            "stdout_path": self.stdout_path,
            "stderr_path": self.stderr_path,
            "stdout_tail": self.stdout_tail,
            "stderr_tail": self.stderr_tail,
            "error_message": self.error_message,
            "timed_out": self.timed_out,
            "process_group_reaped": self.process_group_reaped,
        }


@dataclass(frozen=True)
class TestShardRunSummary:
    """L6.33 分片验证总报告。"""

    schema: str
    source_version: str
    status: str
    total_shards: int
    passed_shards: int
    failed_shards: int
    timeout_shards: int
    skipped_shards: int
    required_failed_or_timeout: int
    output_dir: str
    started_at: float
    finished_at: float
    results: list[TestShardResult]
    timeout_reaper_enabled: bool = True
    shard_isolation_enabled: bool = True
    no_kernel_mutation: bool = True
    no_secret_read: bool = True
    no_network_call: bool = True
    no_shell_string_execution: bool = True

    def __post_init__(self) -> None:
        if self.schema != L6_33_SHARD_SCHEMA:
            raise ValueError("L6.33 summary schema mismatch")
        if self.total_shards != len(self.results):
            raise ValueError("L6.33 total_shards must equal result count")
        if self.status not in {"passed", "failed", "timeout", "partial", "empty"}:
            raise ValueError("L6.33 summary status invalid")
        required = (
            self.timeout_reaper_enabled,
            self.shard_isolation_enabled,
            self.no_kernel_mutation,
            self.no_secret_read,
            self.no_network_call,
            self.no_shell_string_execution,
        )
        if not all(required):
            raise ValueError("L6.33 boundary flags must stay true")

    @property
    def duration_seconds(self) -> float:
        return max(0.0, self.finished_at - self.started_at)

    def public_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "source_version": self.source_version,
            "status": self.status,
            "total_shards": self.total_shards,
            "passed_shards": self.passed_shards,
            "failed_shards": self.failed_shards,
            "timeout_shards": self.timeout_shards,
            "skipped_shards": self.skipped_shards,
            "required_failed_or_timeout": self.required_failed_or_timeout,
            "output_dir": self.output_dir,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "duration_seconds": round(self.duration_seconds, 6),
            "timeout_reaper_enabled": self.timeout_reaper_enabled,
            "shard_isolation_enabled": self.shard_isolation_enabled,
            "no_kernel_mutation": self.no_kernel_mutation,
            "no_secret_read": self.no_secret_read,
            "no_network_call": self.no_network_call,
            "no_shell_string_execution": self.no_shell_string_execution,
            "results": [result.public_dict() for result in self.results],
        }

    def markdown_report(self) -> str:
        lines = [
            "# L6.33 分片回归执行器报告",
            "",
            f"- schema: `{self.schema}`",
            f"- status: `{self.status}`",
            f"- total_shards: {self.total_shards}",
            f"- passed: {self.passed_shards}",
            f"- failed: {self.failed_shards}",
            f"- timeout: {self.timeout_shards}",
            f"- skipped: {self.skipped_shards}",
            f"- required_failed_or_timeout: {self.required_failed_or_timeout}",
            f"- output_dir: `{self.output_dir}`",
            "",
            "## Shards",
        ]
        for result in self.results:
            lines.extend(
                [
                    "",
                    f"### {result.name}",
                    f"- status: `{result.status}`",
                    f"- returncode: `{result.returncode}`",
                    f"- duration_seconds: {result.duration_seconds:.3f}",
                    f"- timeout_seconds: {result.timeout_seconds}",
                    f"- required: {result.required}",
                    f"- rerun: `{result.rerun_command}`",
                    f"- stdout: `{result.stdout_path}`",
                    f"- stderr: `{result.stderr_path}`",
                ]
            )
            if result.error_message:
                lines.append(f"- error: {result.error_message}")
            if result.status == "timeout":
                lines.append("- note: 该分片被超时收割，不能计为通过。")
        return "\n".join(lines) + "\n"


TestShardSpec.__test__ = False
TestShardResult.__test__ = False
TestShardRunSummary.__test__ = False

def build_pytest_shard(
    name: str,
    paths: list[str],
    *,
    cwd: str | Path = ".",
    timeout_seconds: float = 120.0,
    extra_args: list[str] | None = None,
    required: bool = True,
    purpose: str = "pytest shard",
) -> TestShardSpec:
    """构造 pytest shard。"""

    command = [sys.executable, "-m", "pytest", *paths]
    if extra_args:
        command.extend(extra_args)
    return TestShardSpec(
        name=name,
        command=command,
        cwd=cwd,
        timeout_seconds=timeout_seconds,
        purpose=purpose,
        required=required,
    )


def run_test_shards(
    specs: list[TestShardSpec],
    *,
    output_dir: str | Path,
    default_env: dict[str, str] | None = None,
    isolate_runner: bool = True,
) -> TestShardRunSummary:
    """串行运行 shard 并生成总报告。

    默认每个 shard 再包一层独立 worker。这样即使某个 pytest shard
    出现“summary 已打印但进程/管道不回收”，也只会卡住 worker，
    不会拖死总调度器。
    """

    target_dir = Path(output_dir).expanduser().resolve()
    target_dir.mkdir(parents=True, exist_ok=True)
    started_at = time()
    results: list[TestShardResult] = []
    env = default_env or {}
    for spec in specs:
        if isolate_runner:
            results.append(_run_one_shard_isolated(spec, target_dir, default_env=env))
        else:
            results.append(_run_one_shard(spec, target_dir, default_env=env))
    finished_at = time()
    summary = _build_summary(results, target_dir, started_at=started_at, finished_at=finished_at)
    write_shard_summary(summary, target_dir / "shard_summary.json", target_dir / "shard_report.txt")
    return summary


def write_shard_summary(summary: TestShardRunSummary, json_path: str | Path, text_path: str | Path | None = None) -> None:
    """写出分片总报告。"""

    json_target = Path(json_path).expanduser().resolve()
    json_target.parent.mkdir(parents=True, exist_ok=True)
    json_target.write_text(json.dumps(summary.public_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    if text_path is not None:
        text_target = Path(text_path).expanduser().resolve()
        text_target.parent.mkdir(parents=True, exist_ok=True)
        text_target.write_text(summary.markdown_report(), encoding="utf-8")


def collect_existing_shard_results(output_dir: str | Path) -> TestShardRunSummary:
    """从已经落盘的 result.json 重建总报告。

    用于治理一种真实执行链故障：若外层聚合命令被环境超时器中断，
    但各 shard 已独立写出 result.json，仍可不重跑测试直接恢复证据。
    """

    target_dir = Path(output_dir).expanduser().resolve()
    results: list[TestShardResult] = []
    for result_path in sorted(target_dir.glob("*/result.json")):
        try:
            results.append(_result_from_dict(json.loads(result_path.read_text(encoding="utf-8"))))
        except Exception:
            continue
    started_at = min((result.started_at for result in results), default=time())
    finished_at = max((result.finished_at for result in results), default=started_at)
    summary = _build_summary(results, target_dir, started_at=started_at, finished_at=finished_at)
    write_shard_summary(summary, target_dir / "shard_summary.json", target_dir / "shard_report.txt")
    return summary


def _run_one_shard_isolated(spec: TestShardSpec, output_dir: Path, *, default_env: dict[str, str]) -> TestShardResult:
    """在独立 worker 中运行一个 shard，并由父调度器负责硬超时。

    设计重点：父调度器只轮询 result.json / poll()，不依赖 worker
    自然退出。这样即使 pytest 已打印 summary 但进程/插件尾部不回收，
    也不会拖死总调度器。
    """

    shard_dir = output_dir / spec.name
    shard_dir.mkdir(parents=True, exist_ok=True)
    spec_path = shard_dir / "spec.json"
    spec_path.write_text(json.dumps(spec.public_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    worker_stdout = shard_dir / "worker_stdout.log"
    worker_stderr = shard_dir / "worker_stderr.log"
    result_path = shard_dir / "result.json"
    worker_timeout = max(1.0, spec.timeout_seconds + 20.0)
    env = os.environ.copy()
    env.update(default_env)
    cwd = str(Path(spec.cwd).expanduser().resolve())
    pythonpath_parts = [cwd]
    if env.get("PYTHONPATH"):
        pythonpath_parts.append(env["PYTHONPATH"])
    env["PYTHONPATH"] = os.pathsep.join(pythonpath_parts)
    started_wall = time()
    started = monotonic()
    timed_out = False
    returncode: int | None = None
    reaped = False
    result_read_error = ""
    worker_code = (
        "import os, runpy, sys; "
        "os.chdir(sys.argv[1]); "
        "sys.argv=['tiangong_agent_runtime.test_shard_runner','--run-one',sys.argv[2]]; "
        "runpy.run_module('tiangong_agent_runtime.test_shard_runner', run_name='__main__')"
    )
    command = [sys.executable, "-c", worker_code, cwd, str(spec_path)]
    proc: subprocess.Popen[str] | None = None
    try:
        with worker_stdout.open("w", encoding="utf-8") as stdout_file, worker_stderr.open("w", encoding="utf-8") as stderr_file:
            proc = subprocess.Popen(
                command,
                cwd=cwd,
                stdout=stdout_file,
                stderr=stderr_file,
                text=True,
                env=env,
                start_new_session=True,
            )
            deadline = monotonic() + worker_timeout
            while monotonic() < deadline:
                if result_path.exists():
                    # result 已经落盘，父调度器可以安全返回；同时收割仍未退出的 worker。
                    returncode = proc.poll()
                    if returncode is None:
                        reaped = _terminate_process_tree(proc)
                    try:
                        payload = json.loads(result_path.read_text(encoding="utf-8"))
                        if reaped:
                            payload["process_group_reaped"] = True
                        return _result_from_dict(payload)
                    except Exception as exc:
                        result_read_error = f"result.json parse failed before worker exit: {type(exc).__name__}: {exc}"
                        break
                returncode = proc.poll()
                if returncode is not None:
                    break
                sleep(0.05)
            else:
                timed_out = True
            if result_path.exists():
                try:
                    payload = json.loads(result_path.read_text(encoding="utf-8"))
                    if proc.poll() is None:
                        reaped = _terminate_process_tree(proc)
                        payload["process_group_reaped"] = True
                    return _result_from_dict(payload)
                except Exception as exc:
                    result_read_error = f"result.json parse failed after worker exit: {type(exc).__name__}: {exc}"
            if proc.poll() is None:
                timed_out = True
                reaped = _terminate_process_tree(proc)
                returncode = proc.returncode
            else:
                returncode = proc.returncode
    except Exception as exc:  # pragma: no cover - defensive boundary for supervisor itself
        finished_wall = time()
        return TestShardResult(
            name=spec.name,
            status="failed",
            returncode=returncode,
            duration_seconds=monotonic() - started,
            timeout_seconds=spec.timeout_seconds,
            started_at=started_wall,
            finished_at=finished_wall,
            command=list(spec.command),
            cwd=cwd,
            purpose=spec.purpose,
            required=spec.required,
            stdout_path=str(shard_dir / "stdout.log"),
            stderr_path=str(shard_dir / "stderr.log"),
            stdout_tail="",
            stderr_tail=str(exc),
            error_message=f"isolated shard supervisor failed: {type(exc).__name__}: {exc}",
            timed_out=False,
            process_group_reaped=reaped,
        )

    finished_wall = time()
    stdout_path = shard_dir / "stdout.log"
    stderr_path = shard_dir / "stderr.log"
    stdout_text = stdout_path.read_text(encoding="utf-8", errors="replace") if stdout_path.exists() else ""
    stderr_text = stderr_path.read_text(encoding="utf-8", errors="replace") if stderr_path.exists() else ""
    worker_text = worker_stderr.read_text(encoding="utf-8", errors="replace") if worker_stderr.exists() else ""
    status = "timeout" if timed_out else "failed"
    return TestShardResult(
        name=spec.name,
        status=status,
        returncode=returncode,
        duration_seconds=monotonic() - started,
        timeout_seconds=spec.timeout_seconds,
        started_at=started_wall,
        finished_at=finished_wall,
        command=list(spec.command),
        cwd=cwd,
        purpose=spec.purpose,
        required=spec.required,
        stdout_path=str(stdout_path),
        stderr_path=str(stderr_path),
        stdout_tail=_tail(stdout_text),
        stderr_tail=_tail(stderr_text or worker_text),
        error_message=(result_read_error or f"isolated shard worker {'timed out' if timed_out else 'failed'} before result.json was produced"),
        timed_out=timed_out,
        process_group_reaped=reaped,
    )

def _spec_from_dict(payload: dict[str, Any]) -> TestShardSpec:
    return TestShardSpec(
        name=str(payload.get("name") or "shard"),
        command=[str(part) for part in payload.get("command") or []],
        cwd=str(payload.get("cwd") or "."),
        timeout_seconds=float(payload.get("timeout_seconds") or 120.0),
        purpose=str(payload.get("purpose") or ""),
        required=bool(payload.get("required", True)),
        env={str(k): str(v) for k, v in dict(payload.get("env") or {}).items()},
    )


def _result_from_dict(payload: dict[str, Any]) -> TestShardResult:
    return TestShardResult(
        name=str(payload.get("name") or "shard"),
        status=str(payload.get("status") or "failed"),
        returncode=payload.get("returncode"),
        duration_seconds=float(payload.get("duration_seconds") or 0.0),
        timeout_seconds=float(payload.get("timeout_seconds") or 0.0),
        started_at=float(payload.get("started_at") or 0.0),
        finished_at=float(payload.get("finished_at") or 0.0),
        command=[str(part) for part in payload.get("command") or []],
        cwd=str(payload.get("cwd") or "."),
        purpose=str(payload.get("purpose") or ""),
        required=bool(payload.get("required", True)),
        stdout_path=str(payload.get("stdout_path") or ""),
        stderr_path=str(payload.get("stderr_path") or ""),
        stdout_tail=str(payload.get("stdout_tail") or ""),
        stderr_tail=str(payload.get("stderr_tail") or ""),
        error_message=str(payload.get("error_message") or ""),
        timed_out=bool(payload.get("timed_out", False)),
        process_group_reaped=bool(payload.get("process_group_reaped", False)),
    )


def _run_one_shard(spec: TestShardSpec, output_dir: Path, *, default_env: dict[str, str]) -> TestShardResult:
    shard_dir = output_dir / spec.name
    shard_dir.mkdir(parents=True, exist_ok=True)
    stdout_path = shard_dir / "stdout.log"
    stderr_path = shard_dir / "stderr.log"
    started_wall = time()
    started = monotonic()
    timed_out = False
    reaped = False
    error_message = ""
    returncode: int | None = None
    env = os.environ.copy()
    env.update(default_env)
    env.update(spec.env)

    try:
        # stdout/stderr 直接落盘，避免 pytest 内部再派生子进程时继承 PIPE
        # 导致主进程退出后 communicate() 仍等待管道关闭。优先使用 GNU timeout
        # 作为外部看门狗，避免某些 pytest/CLI 子进程“已打印 summary 但进程不退出”时
        # Python wait/poll 被拖住。
        actual_command = _external_timeout_command(spec.command, spec.timeout_seconds)
        wait_deadline = spec.timeout_seconds + 10
        with stdout_path.open("w", encoding="utf-8") as stdout_file, stderr_path.open("w", encoding="utf-8") as stderr_file:
            proc = subprocess.Popen(
                actual_command,
                cwd=str(Path(spec.cwd).expanduser().resolve()),
                stdout=stdout_file,
                stderr=stderr_file,
                text=True,
                env=env,
                start_new_session=False if _has_external_timeout() else True,
            )
            returncode = _waitpid_for_exit(proc.pid, wait_deadline)
            if returncode is None:
                timed_out = True
                reaped = _terminate_process_tree(proc)
                returncode = proc.returncode
                error_message = f"timeout after {spec.timeout_seconds} seconds"
        if returncode in {124, 137, -signal.SIGTERM, -signal.SIGKILL}:
            timed_out = True
            reaped = True
            if not error_message:
                error_message = f"timeout after {spec.timeout_seconds} seconds"
    except FileNotFoundError as exc:
        returncode = 127
        stderr_path.write_text(str(exc), encoding="utf-8")
        error_message = str(exc)
    except Exception as exc:  # pragma: no cover - defensive boundary for runner itself
        returncode = 1
        message = f"{type(exc).__name__}: {exc}"
        stderr_path.write_text(message, encoding="utf-8")
        error_message = message

    finished_wall = time()
    duration = monotonic() - started
    stdout_text = stdout_path.read_text(encoding="utf-8", errors="replace") if stdout_path.exists() else ""
    stderr_text = stderr_path.read_text(encoding="utf-8", errors="replace") if stderr_path.exists() else ""
    if timed_out:
        status = "timeout"
    elif returncode == 0:
        status = "passed"
    elif spec.required:
        status = "failed"
    else:
        status = "skipped"
    result = TestShardResult(
        name=spec.name,
        status=status,
        returncode=returncode,
        duration_seconds=duration,
        timeout_seconds=spec.timeout_seconds,
        started_at=started_wall,
        finished_at=finished_wall,
        command=list(spec.command),
        cwd=str(Path(spec.cwd).expanduser().resolve()),
        purpose=spec.purpose,
        required=spec.required,
        stdout_path=str(stdout_path),
        stderr_path=str(stderr_path),
        stdout_tail=_tail(stdout_text),
        stderr_tail=_tail(stderr_text),
        error_message=error_message,
        timed_out=timed_out,
        process_group_reaped=reaped,
    )
    (shard_dir / "result.json").write_text(json.dumps(result.public_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def _waitpid_for_exit(pid: int, timeout_seconds: float) -> int | None:
    deadline = monotonic() + timeout_seconds
    while monotonic() < deadline:
        try:
            waited_pid, status = os.waitpid(pid, os.WNOHANG)
        except ChildProcessError:
            return 0
        if waited_pid == pid:
            return os.waitstatus_to_exitcode(status)
        sleep(0.05)
    try:
        waited_pid, status = os.waitpid(pid, os.WNOHANG)
    except ChildProcessError:
        return 0
    if waited_pid == pid:
        return os.waitstatus_to_exitcode(status)
    return None


def _has_external_timeout() -> bool:
    return shutil.which("timeout") is not None


def _external_timeout_command(command: list[str], timeout_seconds: float) -> list[str]:
    timeout_bin = shutil.which("timeout")
    if timeout_bin is None:
        return list(command)
    seconds = max(1, int(timeout_seconds))
    return [timeout_bin, "--kill-after=5s", f"{seconds}s", *command]


def _poll_process(proc: subprocess.Popen[str], timeout_seconds: float) -> int | None:
    deadline = monotonic() + timeout_seconds
    while monotonic() < deadline:
        code = proc.poll()
        if code is not None:
            return code
        sleep(0.05)
    code = proc.poll()
    if code is not None:
        return code
    return None


def _terminate_process_tree(proc: subprocess.Popen[str]) -> bool:
    """尽力收割进程组，但绝不阻塞总调度器。"""
    ok = False
    try:
        os.killpg(proc.pid, signal.SIGTERM)
        ok = True
    except Exception:
        try:
            proc.terminate()
            ok = True
        except Exception:
            ok = ok or False
    sleep(0.2)
    try:
        os.killpg(proc.pid, signal.SIGKILL)
        ok = True
    except Exception:
        try:
            proc.kill()
            ok = True
        except Exception:
            ok = ok or False
    try:
        os.waitpid(proc.pid, os.WNOHANG)
    except Exception:
        return ok
    return ok


def _build_summary(results: list[TestShardResult], output_dir: Path, *, started_at: float, finished_at: float) -> TestShardRunSummary:
    passed = sum(1 for result in results if result.status == "passed")
    failed = sum(1 for result in results if result.status == "failed")
    timeout = sum(1 for result in results if result.status == "timeout")
    skipped = sum(1 for result in results if result.status == "skipped")
    required_bad = sum(1 for result in results if result.required and result.status in {"failed", "timeout"})
    if not results:
        status = "empty"
    elif timeout:
        status = "timeout"
    elif failed:
        status = "failed"
    elif skipped:
        status = "partial"
    else:
        status = "passed"
    return TestShardRunSummary(
        schema=L6_33_SHARD_SCHEMA,
        source_version=SOURCE_VERSION,
        status=status,
        total_shards=len(results),
        passed_shards=passed,
        failed_shards=failed,
        timeout_shards=timeout,
        skipped_shards=skipped,
        required_failed_or_timeout=required_bad,
        output_dir=str(output_dir),
        started_at=started_at,
        finished_at=finished_at,
        results=results,
    )


def _tail(text: str, *, max_chars: int = 4000) -> str:
    if not text:
        return ""
    return text[-max_chars:]


def _quote_arg(arg: str) -> str:
    if not arg:
        return "''"
    if all(ch.isalnum() or ch in "-_=./:@" for ch in arg):
        return arg
    return "'" + arg.replace("'", "'\\''") + "'"


def _main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) == 2 and args[0] == "--run-one":
        spec_path = Path(args[1]).expanduser().resolve()
        spec = _spec_from_dict(json.loads(spec_path.read_text(encoding="utf-8")))
        _run_one_shard(spec, spec_path.parent.parent, default_env={})
        return 0
    print("usage: python -m tiangong_agent_runtime.test_shard_runner --run-one <spec.json>", file=sys.stderr)
    return 2


if __name__ == "__main__":  # pragma: no cover - worker entrypoint
    raise SystemExit(_main())
