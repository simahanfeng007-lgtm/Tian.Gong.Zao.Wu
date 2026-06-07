# L6.64 合成报告：文件传输、对话引导、中断任务

## 结论

- L6.64 已完成。
- 前端新增文件传输请求、对话引导芯片、中断任务请求。
- 前端没有获得工具执行、长期记忆写入、审计写入、回滚应用或 Provider 直连权限。
- 真实 Runtime 地址未提供，`ready_for_combine` 仍为 false。

## 本轮内容

1. 文件传输
   - 新增 `contracts/file_transfer.py`。
   - 新增 `/files/transfer/request` 契约路径。
   - 新增桌面端“文件”页和首页附件按钮。
   - 文件记录只展示文件名、大小、摘要、用途、状态、审计引用和 Runtime 回执。

2. 对话引导
   - 首页对话引导从静态文案变为可点击提示词芯片。
   - 点击后只填入输入栏，用户仍需手动发送。
   - 不替代 Planner，不自动发起长链任务。

3. 中断任务
   - 新增 `/control/task/interrupt` 控制请求。
   - 首页新增“中断”按钮。
   - 中断、停止、复位都只向 Runtime 提交请求，前端不杀进程、不直接控制工具。

4. HookBus
   - 新增 `pre_file_transfer_request` 阶段。
   - 缺少只走 Runtime、禁止前端工具执行、禁止路径暴露等安全标记时阻断。

## 验证摘要

- 后端 compileall：PASS。
- 前端 / scripts / launchers compileall：PASS。
- L6.62 observability preflight：PASS。
- L6.63 HookBus preflight：PASS。
- L6.64 file transfer / guide / interrupt preflight：PASS。
- RC preflight contract-server：PASS。
- real Runtime unlock：未执行；缺少真实 Runtime 地址时按预期阻断。
- secret scan：PASS。
- Provider SDK import scan：PASS。
- bare except pass scan：PASS。

## 阻断项

- 真实 Runtime 实例 smoke 未执行。
