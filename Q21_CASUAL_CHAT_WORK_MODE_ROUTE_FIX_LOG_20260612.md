# Q21 Casual Chat / Work Mode Route Fix

## 用户复现

Windows 桌面端底部模式仍在「工作」时，用户输入「忙呢？」。
旧包把这类寒暄当作工作任务送入 ActivationForm/工具链路径，失败后在普通会话气泡里显示：

- 工作模式未执行：主脑本轮未激活工具链。
- Runtime 工具任务失败。
- 当前为：全电脑/系统盘。

## 根因

1. 前端两模式契约把「工作」选择统一提交为 activation_requested/tools_requested。
2. 桥接层已有部分寒暄保护，但未覆盖「忙呢？/在干嘛？」类口语。
3. Provider 模式下，如果工作激活失败，旧桥接层没有把 dialogue-only activation failure 收口为普通聊天回复。
4. 这导致普通问话被错误展示成 Runtime 工具任务失败。

## 修复

- 扩展前端与桥接层 casual chat 识别：忙呢、忙吗、忙不忙、在干嘛、干嘛呢等。
- `resolve_submit_work_mode("工作", "忙呢？")` 改为 effective `chat`，并标记 `casual_chat_override=True`。
- SSE payload 对这类消息不再请求 Planner/Tools/ActivationForm。
- 桥接层对旧 payload 的 dialogue-only work activation failure 增加兜底，不再把 Runtime 工具失败暴露给用户。
- 普通真实工作指令仍保留 work activation boundary，不影响长链工作。

## 新增验证

```bash
python -S -B scripts/verify_l6738_q21_casual_chat_work_mode_route.py
```

验证点：

- 「工作」模式 + 「忙呢？」前端提交为 chat。
- Runtime payload 不请求 activation/tools。
- 本地桥接返回友好寒暄回复，不显示 Runtime 工具任务失败。
- 旧 forced work payload 也不会把寒暄显示成工具失败。
- 真实工作指令仍保留 work activation/tools boundary。
