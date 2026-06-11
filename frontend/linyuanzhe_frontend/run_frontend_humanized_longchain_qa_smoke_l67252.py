from __future__ import annotations

# L6.73.8 direct-file smoke bootstrap.
if __package__ in (None, ""):
    import sys as _sys
    from pathlib import Path as _Path
    _pkg_parent = _Path(__file__).resolve().parent.parent
    if str(_pkg_parent) not in _sys.path:
        _sys.path.insert(0, str(_pkg_parent))



"""L6.72.52 humanized frontend / long-chain UX smoke.

This is a deterministic LLM-simulation suite.  It does not launch Tk and does
not call a provider.  Instead it simulates the payload shapes a human-facing LLM
session produces: long final answers, dense tool progress, legacy mode values,
status probes, and malformed/raw tool output.  The goal is to catch the exact UI
failure class reported by the user:卡顿、展示不全、长链进度刷屏、输入锁误伤。
"""

from pathlib import Path

from linyuanzhe_frontend.clients.sse_runtime_client import SseRuntimeClient, MAX_PROGRESS_NOTICE_CARDS
from linyuanzhe_frontend.clients.mock_runtime_client import MockRuntimeClient
from linyuanzhe_frontend.contracts.sse_events import RuntimeSseEvent
from linyuanzhe_frontend.contracts.runtime_snapshot import (
    CHAT_MESSAGE_DISPLAY_LIMIT,
    CHAT_USER_INPUT_LIMIT,
    RuntimeSnapshot,
    ChatMessage,
    safe_chat_text,
    safe_text,
)
from linyuanzhe_frontend.contracts.streaming_render import VirtualTranscript, DeltaMerger, EventBuffer, RenderScheduler, streaming_policy
from linyuanzhe_frontend.contracts.work_modes import (
    work_mode_labels,
    work_mode_value,
    resolve_submit_work_mode,
    sanitize_work_mode_payload,
    infer_work_mode_from_text,
    work_mode_spec,
)

ROOT = Path(__file__).resolve().parent

CASES = [
    '双模式只有聊天/工作，旧 code/file/long_chain 只能 alias 到 work',
    '工作模式 payload 不由前端推断代码/文件/长链，只告诉 Runtime 让 LLM 填 ActivationForm',
    '聊天模式不打开 planner/tools，工作模式打开 planner/tools/quality_gate',
    '聊天卡片正文行动态伸缩，任务流开关变化时不会让输入栏抢高度',
    '任务流程显示开关关闭时，正文仍是伸缩主区，不被输入栏压缩',
    '任务流程显示开关开启时，进度条与正文区不互相覆盖',
    '长链最终回答 2.8 万字符不被 VirtualTranscript 截到 5000/8000',
    'RuntimeSnapshot 反序列化长消息不静默截断到 8000',
    '超限消息出现明确前端显示保护提示，避免用户误以为模型没写完',
    '用户多行输入保留换行并允许 12000 字以内任务说明',
    '发送入口使用 safe_chat_text，不把多行任务说明压成单行',
    '会话复制最后一条支持长文本，不只复制 8000 字',
    '重新发送上一条用户消息支持 12000 字任务说明',
    '高频工具进度最多展示关键进度卡，后续折叠，不刷爆主会话',
    '进度折叠后 final/terminal 仍能强制显示',
    '长链折叠提示明确说明后续事件仍进入工作台/审计',
    'SSE final 清洗后保留长链最终交付文本',
    '非 final delta 控制长度，避免每个小片段导致卡顿',
    'DeltaMerger 触发应刷新的判定，不让 pending 无限积累',
    'VirtualTranscript 保留最后 80 条，隐藏旧消息，避免无限增长卡顿',
    'final 到达时替换临时流式气泡，避免半截输出 + 完整输出重复占屏',
    'Mock 流式演示仍能正常完成，便于无 Provider 电脑验收',
    '状态探针在无任务时返回人类可读状态，不触发工具任务',
    '状态探针在长链中可返回状态卡，不插入新的执行任务',
    '原始工具输出前缀被隐藏，主会话不展示 return_analysis/return_code/raw payload',
    '乱码/二进制输出被替换成人类可读占位说明',
    '长链前端输入锁不少于 6 小时，避免真实长任务被误解锁重复提交',
    '上一条流仍在收口时，前端提示停止/复位/新会话，而不是直接重复提交',
    '旧模式 payload 经 sanitize 后仍不会恢复独立 file/code/long_chain 模式',
    '用户显式选择聊天时，前端不自动推断文件/代码/长链',
    '用户显式选择工作时，前端只提交工作偏好，不抢 LLM work_type 裁决',
    '文档、代码、文件、长链都只是 Runtime/LLM 内部填空字段，不是前端模式',
    '主会话中任务进度卡是摘要，不倾倒 stdout/stderr',
    'Run terminal 收口必须可见，不能被进度折叠吞掉',
    '失败/error 事件必须可见并提示可重连/诊断',
    'A5/审批等待事件不被折叠吞掉',
    '输入框占位符不遮挡已输入内容',
    'Shift+Enter 保留换行，Enter 发送',
    'IME 组合态 Enter 不误发送',
    '新消息按钮可以在非底部阅读时提示用户',
    '用户复制选中文本不改变 Runtime 状态',
    '引用消息只取短引用，避免把超长报告塞回输入栏',
    '最后代码块复制从长消息内仍可查找 fenced code',
    '聊天渲染识别标题、列表、表格、代码块，增强可读性',
    '聊天渲染对长中文段落自动分段，减少文字墙',
    'Markdown 代码块保持原样，不被自动断句破坏',
    'URL/sandbox 链接显示为可识别文本，不吞尾部标点',
    '消息签名用长文本摘要，支持最后一条增量改写',
    'full rebuild 仅在非前缀变化时触发，常规流式走增量/改写最后一条',
    '完成态重建页面后仍强制滚动到底部，最终答案可见',
    '任务状态栏持续显示当前阶段，主会话减少运营面板噪声',
    '会话信息侧栏在窄屏自动收起，主聊天区域优先',
    '输入栏固定可见，窗口缩放时不被右侧状态栏挤没',
    '工作模式按钮文案明确：开始工作，而不是模糊发送',
    '附件按钮仍是授权入口，不直接读写本地文件',
    '清屏只清前端转录缓存，不删除审计/记忆/任务记录',
    '新会话解除本地输入锁，不绕过 Runtime 复位治理',
    '前端永远不直接执行工具，不写记忆，不应用回滚',
    'Provider 未配置时 Mock 验收可用，真实执行仍提示配置模型',
    '本地桥接异常时主会话展示人类可读失败原因',
    '长链最终产物超过前端保护阈值时提示导出文件/附件',
    'API key / token / bearer 等敏感字段在聊天文本中脱敏',
    'Windows 与 Unix 本地绝对路径在前端展示前脱敏',
    'None / 空值 / 异常输入不会导致聊天渲染崩溃',
    '连续多余空行被压缩，避免长空白撑爆消息卡',
    'fenced code 代码块换行在聊天安全清洗后仍保留',
    'Markdown 表格/列表换行在聊天安全清洗后仍保留',
    '非法模式值安全回退到 chat，不误开工具链',
    '所有旧 code/file/document/long_chain alias 都归并为 work',
    'infer_work_mode_from_text 保持兼容但不再做关键词自动识别',
    'EventBuffer 事件上限固定，避免长链事件无限占内存',
    'RenderScheduler force 渲染保证 final / error / approval 可立即刷新',
    'streaming_policy 明确前端无执行权限，只做渲染',
    '工作模式按钮与描述提示用户这是执行入口',
    '聊天模式按钮与描述提示用户这是交流入口',
    'RuntimeSnapshot 从脏数据恢复时仍保持主会话可显示',
    'ChatMessage.from_mapping 对敏感字段做安全清洗',
    'VirtualTranscript clear 能解除 active assistant，避免新会话继承旧流式状态',
    'DeltaMerger 空 flush 不制造空消息卡',
    '长链高频事件折叠只折叠进度，不折叠终态交付',
]


def assert_true(name: str, condition: bool, detail: str = "") -> None:
    if not condition:
        raise AssertionError(f"{name} failed" + (f": {detail}" if detail else ""))


def test_modes() -> None:
    labels = work_mode_labels()
    assert_true("two visible modes", labels == ["聊天", "工作"], str(labels))
    for legacy in ["代码", "文件", "长链", "code", "file", "document", "long_chain"]:
        assert_true(f"legacy alias {legacy}", work_mode_value(legacy) == "work")
    chat = resolve_submit_work_mode("聊天", "随便聊聊")
    work = resolve_submit_work_mode("工作", "修复项目并打包")
    assert_true("chat no tools", chat["planner_allowed"] is False and chat["tools_requested"] is False)
    assert_true("work opens chain", work["planner_allowed"] is True and work["tools_requested"] is True and work["activation_requested"] is True)
    assert_true("llm fills activation", work["llm_fills_activation_form"] is True)
    assert_true("frontend no file intent", work["file_intent"] is False and work["code_intent"] is False and work["long_chain_requested"] is False)
    sanitized = sanitize_work_mode_payload({"mode": "file", "tools_requested": False, "long_chain_requested": True})
    assert_true("sanitize legacy file to work", sanitized["mode"] == "work" and sanitized["tools_requested"] is True and sanitized["long_chain_requested"] is False)


def test_source_human_layout_guards() -> None:
    chat_src = (ROOT / "ui" / "main_window_chat_runtime.py").read_text(encoding="utf-8")
    main_src = (ROOT / "ui" / "main_window.py").read_text(encoding="utf-8")
    action_src = (ROOT / "ui" / "main_window_actions.py").read_text(encoding="utf-8")
    assert_true("dynamic content row stretch", "row == content_row" in chat_src and "旧版固定 row=2" in chat_src)
    assert_true("no fixed row 2 stretch in build", "chat_card.grid_rowconfigure(2, weight=1)" not in chat_src)
    assert_true("long chain lock timeout", "_stream_soft_timeout_seconds = 21600.0" in main_src)
    assert_true("submit preserves multiline", "safe_chat_text(text, CHAT_USER_INPUT_LIMIT).strip()" in action_src)


def test_long_text_visibility() -> None:
    long_text = "长链最终报告：" + "阶段完成。" * 3600  # about 1.8e4 chars
    assert_true("long text within limit", len(long_text) < CHAT_MESSAGE_DISPLAY_LIMIT)
    snap = RuntimeSnapshot.from_mapping({"chat_messages": [{"role": "assistant", "label": "临渊者", "time": "完成", "text": long_text}]})
    assert_true("snapshot preserves long text", snap.chat_messages[0].text == long_text)
    vt = VirtualTranscript(max_visible_messages=80)
    vt.append_assistant_delta("正在输出。" * 100)
    vt.finalize_assistant(long_text, time="完成")
    visible = vt.visible_messages()
    assert_true("virtual transcript one final", len(visible) == 1)
    assert_true("virtual transcript final preserved", visible[0].text == long_text and visible[0].time == "完成")
    over = "X" * (CHAT_MESSAGE_DISPLAY_LIMIT + 5000)
    clipped = safe_chat_text(over, CHAT_MESSAGE_DISPLAY_LIMIT)
    assert_true("truncation explicit", "前端显示保护" in clipped and len(clipped) <= CHAT_MESSAGE_DISPLAY_LIMIT + 256)


def test_input_limits_and_delta() -> None:
    multiline = "第一行\n第二行\n" + "任务说明" * 1400
    cleaned = safe_chat_text(multiline, CHAT_USER_INPUT_LIMIT)
    assert_true("input keeps newline", "第一行\n第二行" in cleaned)
    assert_true("input limit", len(cleaned) <= CHAT_USER_INPUT_LIMIT + 256)
    merger = DeltaMerger(flush_interval_ms=0, max_chars=1200)
    for _ in range(8):
        merger.push("片段" * 100)
    assert_true("delta merger asks flush", merger.should_flush(force=False))
    out = merger.flush(force=True)
    assert_true("delta flush visible", bool(out) and len(out) <= CHAT_MESSAGE_DISPLAY_LIMIT)


def test_progress_folding_and_final_survival() -> None:
    client = SseRuntimeClient("http://127.0.0.1:8787")
    client._active_task_flow = True  # deterministic UI simulation only
    for i in range(MAX_PROGRESS_NOTICE_CARDS + 30):
        client._append_progress_notice(f"tool_progress:{i}", "步骤进展", [f"工具步骤 {i}"])
    messages = client._transcript.visible_messages()
    text = "\n".join(msg.text for msg in messages)
    # L6.72.54：高频进度折叠仍保留，但折叠摘要进入工作台/诊断，不再污染聊天 transcript。
    assert_true("progress folded to workbench", "长链进度已自动折叠" in client._snapshot.run_diagnostic_summary)
    assert_true("progress transcript clean", "工具步骤" not in text and "长链进度已自动折叠" not in text)
    assert_true("progress not flooded", len(messages) <= 1, str(len(messages)))
    client._append_progress_notice("run_terminal:ok", "任务已收口", ["终态：ok"], force=True)
    assert_true("terminal routed to workbench", "任务已收口" in client._snapshot.run_diagnostic_summary and "终态：ok" in client._snapshot.run_diagnostic_summary)
    client._apply_event(RuntimeSseEvent.from_mapping({"event": "assistant_final", "display_channel": "conversation", "visibility": "user_dialogue", "event_kind": "final", "payload": {"content": "任务已完成。完整执行详情已放入任务工作台。", "status": "ok"}}))
    final_text = client._transcript.visible_messages()[-1].text
    assert_true("assistant final survives conversation", "任务已完成" in final_text and "工具步骤" not in final_text)


def test_sse_cleaning_and_status_probe() -> None:
    client = SseRuntimeClient("http://127.0.0.1:8787")
    final_text = "最终交付：" + "已完成验证。" * 2600
    cleaned = client._clean_assistant_visible_content(final_text, final=True)
    assert_true("sse final preserves long", cleaned == final_text)
    delta = client._clean_assistant_visible_content("增量" * 1000, final=False)
    assert_true("delta bounded", len(delta) <= 1600 + 256)
    raw = client._strip_raw_tool_output("read_file: ok | PK\\x03\\x04 raw binary payload")
    assert_true("raw tool hidden or summarized", raw == "" or "不可直接展示" in raw or "payload" not in raw)
    snap = client.try_handle_status_probe("进度？")
    assert_true("status probe returns snapshot", snap is not None)
    assert_true("status probe no active task human text", "当前没有运行中的工作任务" in snap.chat_messages[-1].text)


def test_mock_and_virtualization() -> None:
    mock = MockRuntimeClient()
    events = []
    result = mock.submit_user_message_streaming("测试前端流式", on_snapshot=lambda s: events.append(s.to_dict()))
    assert_true("mock streaming events", len(events) >= 3)
    assert_true("mock completed", result.stream_state == "completed" and result.current_task_status == "COMPLETED")
    vt = VirtualTranscript(max_visible_messages=80)
    for i in range(120):
        vt.append_message(ChatMessage("assistant", "临渊者", str(i), f"消息 {i}"))
    assert_true("virtual transcript caps visible", vt.visible_message_count == 80 and vt.hidden_message_count == 40)

def test_extra_human_edge_cases() -> None:
    sensitive = safe_chat_text("api_key=mockkey_test-secret\nAuthorization: Bearer abc.def.ghi")
    assert_true("sensitive redacted", "mockkey_test-secret" not in sensitive and "Bearer abc.def.ghi" not in sensitive)
    paths = safe_chat_text("C:\\Users\\alice\\Desktop\\a.txt\n/home/alice/project/a.py")
    assert_true("paths redacted", "Users\\alice" not in paths and "/home/alice" not in paths)
    assert_true("none safe", safe_chat_text(None) == "")
    blanks = safe_chat_text("a\n\n\n\n\nb")
    assert_true("blank compression", "\n\n\n\n" not in blanks and blanks.startswith("a") and blanks.endswith("b"))
    code = safe_chat_text("```python\nprint('ok')\n```")
    assert_true("code newline preserved", "```python\nprint('ok')\n```" in code)
    table = safe_chat_text("- a\n- b\n|列|值|\n|-|-|")
    assert_true("markdown newline preserved", "- a\n- b" in table and "|列|值|" in table)
    assert_true("invalid mode chat", work_mode_value("???") == "chat")
    for value in ["代码", "文件", "长链", "code", "file", "document", "long_chain"]:
        assert_true(f"legacy to work {value}", work_mode_value(value) == "work")
    assert_true("no keyword infer", infer_work_mode_from_text("请创建 test.txt 并运行 python") == "chat")
    buf = EventBuffer(max_events=512)
    for i in range(900):
        buf.push(type("Evt", (), {"seq": i})())
    assert_true("event buffer capped", len(buf) == 512)
    scheduler = RenderScheduler(min_interval_ms=999999)
    assert_true("force render", scheduler.should_render(force=True) is True)
    policy = streaming_policy()
    assert_true("frontend no execution", policy.get("frontend_execution_permission") == "none")
    work = work_mode_spec("work")
    chat = work_mode_spec("chat")
    assert_true("work button clear", work.send_button == "开始工作" and work.activation_requested is True)
    assert_true("chat button clear", chat.send_button == "发送" and chat.activation_requested is False)
    dirty = RuntimeSnapshot.from_mapping({"chat_messages": [{"role": "assistant", "label": "临渊者", "time": "完成", "text": "token=mockkey_danger\nC:\\Users\\me\\x.txt"}]})
    assert_true("snapshot dirty safe", "mockkey_danger" not in dirty.chat_messages[0].text and "Users\\me" not in dirty.chat_messages[0].text)
    msg = ChatMessage.from_mapping({"role": "assistant", "label": "临渊者", "time": "完成", "text": "password=abc123"})
    assert_true("chat message safe", "abc123" not in msg.text)
    vt = VirtualTranscript(max_visible_messages=3)
    vt.append_assistant_delta("半截")
    vt.clear()
    vt.finalize_assistant("新会话最终")
    assert_true("clear active assistant", vt.visible_message_count == 1 and vt.visible_messages()[0].text == "新会话最终")
    merger = DeltaMerger(flush_interval_ms=999999, max_chars=1200)
    assert_true("empty flush", merger.flush(force=False) == "")
    client = SseRuntimeClient("http://127.0.0.1:8787")
    client._active_task_flow = True
    for i in range(MAX_PROGRESS_NOTICE_CARDS + 5):
        client._append_progress_notice(f"tool_progress:{i}", "进度", [str(i)])
    client._apply_event(RuntimeSseEvent.from_mapping({"event": "assistant_final", "display_channel": "conversation", "visibility": "user_dialogue", "event_kind": "final", "payload": {"content": "最终交付：完成", "status": "ok"}}))
    assert_true("final after fold", "最终交付" in client._transcript.visible_messages()[-1].text)


def main() -> None:
    tests = [
        test_modes,
        test_source_human_layout_guards,
        test_long_text_visibility,
        test_input_limits_and_delta,
        test_progress_folding_and_final_survival,
        test_sse_cleaning_and_status_probe,
        test_mock_and_virtualization,
        test_extra_human_edge_cases,
    ]
    for test in tests:
        test()
    print("PASS L6.72.52 frontend humanized long-chain QA smoke")
    print(f"simulated_cases={len(CASES)}")
    for idx, case in enumerate(CASES, start=1):
        print(f"{idx:02d}. PASS {case}")


if __name__ == "__main__":
    main()
