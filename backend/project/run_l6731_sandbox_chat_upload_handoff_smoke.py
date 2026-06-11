"""L6.73.1 沙盘聊天与上传文件交接回归测试。

覆盖用户实测问题：
1. 沙盘/工作模式下普通聊天不应误进入工具/ActivationForm 错误态。
2. 上传 TXT 应先由本地桥复制到 Runtime 交接区，再用真实 runtime_local_path 读取，不能按显示文件名触发 path_not_found。
3. UnicodeEncodeError / adaptiveworkloop / repaircontext 等内部诊断不得原样污染会话气泡。
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend" / "project"
FRONTEND = ROOT / "frontend"
for item in (str(ROOT), str(BACKEND), str(FRONTEND)):
    if item not in sys.path:
        sys.path.insert(0, item)

# 防止本机已有 provider_config 干扰离线 smoke。
os.environ["LINYUANZHE_PROVIDER_CONFIG_FILE"] = str(Path(tempfile.gettempdir()) / "linyuanzhe_l6731_empty_provider_config.json")
for key in ("TIANGONG_API_KEY", "LINYUANZHE_PROVIDER_KEY", "TIANGONG_BASE_URL", "LINYUANZHE_PROVIDER_BASE"):
    os.environ.pop(key, None)

from desktop import linyuanzhe_local_runtime_bridge_l671 as bridge  # noqa: E402
from frontend.linyuanzhe_frontend.clients.sse_runtime_client import SseRuntimeClient  # noqa: E402
from frontend.linyuanzhe_frontend.contracts.file_transfer import FileTransferRequest  # noqa: E402
from frontend.linyuanzhe_frontend.contracts.work_modes import resolve_submit_work_mode  # noqa: E402
from tiangong_agent_runtime.plan_bridge import PlanBridge  # noqa: E402
from tiangong_agent_shell.providers.provider_error import ProviderErrorKind, classify_provider_error  # noqa: E402


def assert_true(name: str, cond: bool, detail: str = "") -> None:
    if not cond:
        raise AssertionError(f"{name} failed" + (f": {detail}" if detail else ""))
    print(f"PASS {name}")


def tool_name(step: object) -> str:
    return str(getattr(step, "tool_name", getattr(step, "name", "")))


def tool_args(step: object) -> dict:
    return dict(getattr(step, "arguments", getattr(step, "args", {})) or {})


def make_state(timeout: float = 20) -> bridge.BridgeState:
    state = bridge.BridgeState(backend_mode="local", timeout=timeout)
    state.provider_key = ""
    state.provider_base = ""
    state.provider = "deepseek"
    state.model = "deepseek-chat"
    state.host_access_scope = "project_workspace"
    state.host_access_root = bridge.BACKEND
    state.file_handoffs.clear()
    return state


def test_work_payload_does_not_force_tools_or_long_chain() -> None:
    payload = {
        "message": "你是谁",
        "work_mode": {"mode": "work", "activation_requested": True, "tools_requested": True, "llm_fills_activation_form": True},
    }
    directives = bridge._runtime_directives_from_payload(payload)
    assert_true("work payload keeps activation", directives["activation_requested"] is True)
    assert_true("work payload does not force tools", directives["tools_requested"] is False, str(directives))
    assert_true("work payload does not force long chain", directives["long_chain_requested"] is False, str(directives))

    client = SseRuntimeClient("http://127.0.0.1:9")
    front_payload = resolve_submit_work_mode("work", "你是谁")
    assert_true("frontend work chat does not open task flow", client._payload_requests_task_flow(front_payload) is False, str(front_payload))
    long_payload = dict(front_payload)
    long_payload["long_chain_requested"] = True
    assert_true("frontend explicit long chain opens task flow", client._payload_requests_task_flow(long_payload) is True)


def test_sandbox_dialogue_offline_no_activation_error() -> None:
    state = make_state(timeout=12)
    payload = {"message": "你是谁", "work_mode": {"mode": "work", "activation_requested": True, "tools_requested": True, "llm_fills_activation_form": True}}
    directives = bridge._runtime_directives_from_payload(payload)
    answer, rc, elapsed = bridge._run_backend_once("你是谁", state, runtime_directives=directives)
    lowered = answer.lower()
    assert_true("dialogue rc zero", rc == 0, answer)
    assert_true("dialogue returns identity", "我是" in answer and "临渊者" in answer, answer)
    assert_true("dialogue no activationform leak", "activationform" not in lowered and "unicodeencodeerror" not in lowered, answer)
    assert_true("dialogue no task flow markers", "[计划器]" not in answer and "adaptiveworkloop" not in lowered, answer)
    assert_true("dialogue elapsed local", elapsed == "local_dialogue", elapsed)


def test_unicode_encode_error_is_chinese() -> None:
    exc = UnicodeEncodeError("gbk", "临渊者", 0, 1, "illegal multibyte sequence")
    err = classify_provider_error(exc, provider="deepseek")
    assert_true("unicode classified unsupported_feature", err.kind is ProviderErrorKind.UNSUPPORTED_FEATURE, str(err.public_dict()))
    assert_true("unicode user message chinese", "请求编码" in err.user_message and "UnicodeEncodeError" not in err.user_message, err.user_message)


def test_file_transfer_request_and_handoff_materialize() -> None:
    state = make_state(timeout=12)
    src = bridge.BACKEND / "l6731_upload_smoke.txt"
    src.write_text("L6731 上传TXT内容", encoding="utf-8")
    req = FileTransferRequest.from_path(src)
    public_payload = req.to_payload()
    payload = req.to_bridge_payload()
    public = req.to_public_record(status="prepared")
    assert_true("public payload hides raw local path", str(src.resolve()) not in str(public_payload), str(public_payload))
    assert_true("private bridge payload carries local path to bridge", payload.get("runtime_handoff_path") == str(src.resolve()))
    assert_true("frontend public hides raw path", str(src.resolve()) not in str(public), str(public))

    mat = bridge._materialize_file_handoff(payload, state)
    assert_true("handoff materialized", mat.get("handoff_status") == "materialized", str(mat))
    runtime_path = str(mat.get("runtime_handoff_path"))
    assert_true("runtime path not placeholder", runtime_path and not runtime_path.startswith("<"), runtime_path)
    copied = (state.host_access_root / runtime_path).resolve()
    assert_true("copied file exists", copied.exists(), str(copied))
    assert_true("copied content ok", copied.read_text(encoding="utf-8") == "L6731 上传TXT内容")

    missing = bridge._materialize_file_handoff({"file_name": "x.txt", "runtime_handoff_path": "<runtime-managed-handoff>"}, state)
    assert_true("missing source is not accepted as materialized", missing.get("handoff_status") == "metadata_only")


def test_plan_bridge_uses_runtime_handoff_path() -> None:
    text = "上传一个TXT文件\n\n[Runtime本地文件交接]\n附件1: smoke.txt | runtime_local_path=.linyuanzhe/file_handoffs/20260610/ft_x/smoke.txt"
    plan = PlanBridge().build_plan(text)
    assert_true("handoff plan exists", len(plan) == 1, str(plan))
    assert_true("handoff txt uses read_file", tool_name(plan[0]) == "read_file", str(plan[0]))
    assert_true("handoff path exact", tool_args(plan[0]).get("path") == ".linyuanzhe/file_handoffs/20260610/ft_x/smoke.txt", str(plan[0]))

    doc = "请解析上传的pdf\n\n[Runtime本地文件交接]\n附件1: a.pdf | runtime_local_path=.linyuanzhe/file_handoffs/20260610/ft_x/a.pdf"
    doc_plan = PlanBridge().build_plan(doc)
    assert_true("handoff pdf uses document_parse", tool_name(doc_plan[0]) == "document_parse", str(doc_plan[0]))


def test_backend_upload_txt_roundtrip() -> None:
    state = make_state(timeout=30)
    src = bridge.BACKEND / "l6731_runtime_roundtrip.txt"
    src.write_text("L6731 后端真实读取内容", encoding="utf-8")
    mat = bridge._materialize_file_handoff({"file_name": src.name, "runtime_handoff_path": str(src)}, state)
    runtime_path = str(mat["runtime_handoff_path"])
    msg = f"上传一个TXT文件\n\n[Runtime本地文件交接]\n附件1: {src.name} | runtime_local_path={runtime_path}"
    env = os.environ.copy()
    env.update({
        "PYTHONPATH": str(BACKEND),
        "PYTHONUTF8": "1",
        "PYTHONIOENCODING": "utf-8",
        "TIANGONG_USER_SELECTED_MODE": "work",
        "LINYUANZHE_FRONTEND_WORK_MODE": "work",
        "TIANGONG_PROVIDER_READY": "0",
    })
    cmd = [
        sys.executable,
        str(BACKEND / "run_agent.py"),
        "--once",
        msg,
        "--workspace",
        str(BACKEND),
        "--tool-mode",
        "runtime_governed",
        "--planner-mode",
        "model_suggest",
        "--max-steps",
        "5",
    ]
    proc = subprocess.run(cmd, cwd=str(BACKEND), env=env, text=True, encoding="utf-8", errors="replace", capture_output=True, timeout=60)
    output = (proc.stdout or "") + "\n" + (proc.stderr or "")
    assert_true("backend upload txt rc zero", proc.returncode == 0, output[:1200])
    assert_true("backend upload txt content visible", "L6731 后端真实读取内容" in output, output[:1200])
    assert_true("backend upload txt no path_not_found", "path_not_found" not in output.lower() and "文件不存在" not in output, output[:1200])

    cleaned = bridge._clean_user_facing_answer(output, "上传一个TXT文件")
    low = cleaned.lower()
    assert_true("cleaned output keeps content", "L6731 后端真实读取内容" in cleaned, cleaned)
    assert_true("cleaned output hides plan markers", "[计划器]" not in cleaned and "[工作链]" not in cleaned and "deterministic_fallback" not in low, cleaned)


def test_internal_error_sanitizer() -> None:
    raw = """adaptiveworkloopv1] status=failedrecoverable; repairattempted=False\nrepaircontext=原计划状态：failedwith_resume\n首个失败步骤 readfile/failed/pathnot_found\n[错误分类] 文件路径错误。\n"""
    cleaned = bridge._clean_user_facing_answer(raw, "上传一个TXT文件")
    low = cleaned.lower()
    assert_true("sanitize hides adaptiveworkloop", "adaptiveworkloop" not in low, cleaned)
    assert_true("sanitize hides repaircontext", "repaircontext" not in low and "failedwith_resume" not in low, cleaned)
    assert_true("sanitize keeps chinese classification", "文件路径错误" in cleaned or "文件不存在" in cleaned or "已收到" in cleaned, cleaned)


def main() -> None:
    if os.environ.get("TIANGONG_RUN_L6731_SANDBOX_UPLOAD_FULL") != "1":
        print("L6.73.1 sandbox_chat_upload_handoff_smoke SKIP: legacy/full smoke is disabled by default; set TIANGONG_RUN_L6731_SANDBOX_UPLOAD_FULL=1 to run the full path.")
        return 0
    tests = [
        test_work_payload_does_not_force_tools_or_long_chain,
        test_sandbox_dialogue_offline_no_activation_error,
        test_unicode_encode_error_is_chinese,
        test_file_transfer_request_and_handoff_materialize,
        test_plan_bridge_uses_runtime_handoff_path,
        test_backend_upload_txt_roundtrip,
        test_internal_error_sanitizer,
    ]
    for test in tests:
        test()
    print(f"L6.73.1 sandbox/chat/upload handoff smoke PASS: {len(tests)} groups")


if __name__ == "__main__":
    main()
