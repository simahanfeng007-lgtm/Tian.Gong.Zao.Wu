# FE01 STEP25 / L6.64 文件传输、对话引导与中断任务

## 目标

本轮只补桌面端产品层能力，不改变 Runtime 主链：

1. 文件传输：前端提供附件入口与文件回执页，但只提交脱敏 transfer request。
2. 对话引导：前端把 Runtime 快照转成可点击提示词芯片，用户点击后仅填入输入栏。
3. 中断任务：前端提供“中断”按钮，但只向 Runtime 提交控制请求。

## 边界

- 前端不裸调 Provider。
- 前端不直接执行工具。
- 前端不写长期记忆。
- 前端不写审计。
- 前端不应用回滚。
- 文件传输不在报告中暴露本地原始路径或文件正文。
- 真实读取、落盘、转存、下载中转必须由 TiangongWangguan / Runtime / QualityGate 管控。

## 新增端点契约

- `/files/transfer/request`：文件传输请求，只提交文件名、大小、摘要、用途和安全标记。
- `/control/task/interrupt`：中断任务请求，只提交 run/task 上下文和理由。

## 前端展示

- 首页：保留固定输入栏；新增附件按钮、中断按钮、可点击引导芯片。
- 文件页：展示最近文件传输回执、摘要、审计引用和边界说明。
- 规则页：HookBus 增加 `pre_file_transfer_request` 规则。

## 验证

运行：

```bash
python scripts/file_transfer_interrupt_preflight_l664.py
python scripts/verify_l664_release.py
```

真实 Runtime 解阻仍由 L6.61 脚本控制；没有真实 Runtime 地址时，`ready_for_combine` 继续保持 false。
