# L6.71.3 / FE01 STEP31M

## 主题
基础 Markdown 渲染、聊天换行保真与纯文本体验修复。

## 修复
- Tk Text 聊天区增加标题、加粗、列表、引用、分割线、代码块、行内代码、链接识别的基础 Markdown tag 渲染。
- `safe_chat_text` 保留聊天正文换行，同时沿用敏感信息脱敏策略。
- Streaming DeltaMerger / VirtualTranscript 保留换行，防止代码块和列表在流式输出中被压平。
- Mock 聊天样例加入 Markdown 内容，便于截图验收。

## 不变边界
- 不改 Runtime 主链。
- 不裸调 Provider SDK。
- 不直接调用工具。
- 不写记忆。
- 不绕过 QualityGate。
- 链接只识别高亮，不自动外跳。
