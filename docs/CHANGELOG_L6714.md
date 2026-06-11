# L6.71.4 / FE01 STEP31N

主题：流式输出与思考态修复。

## 本轮修复

1. 聊天发送后立即显示轻量思考态：`正在思考`。
2. Runtime / Mock 进入 assistant_delta 后切换为 `正在输出`。
3. 断流续接显示 `断线续接中`，完成或错误后自动收口提示。
4. Tk 聊天区保持 STEP31L/STEP31M 的增量渲染，不回退到全量 rebuild。
5. SSE assistant_delta / assistant_final 改用 `safe_chat_text`，保留 Markdown 换行与代码块结构。
6. Mock 客户端新增前端只读流式演示，用于无 Provider 时验证思考态、增量输出、Markdown 渲染和边界声明。
7. 新增验收脚本：`scripts/desktop_streaming_thinking_acceptance_l6714.py`。

## 边界

- 前端不调用工具。
- 前端不裸调 Provider SDK。
- 前端不写记忆。
- 前端不写审计。
- 前端不绕过 Runtime / QualityGate。
- Mock 流式演示只用于 UI 回归，不代表真实 AI 回复。
