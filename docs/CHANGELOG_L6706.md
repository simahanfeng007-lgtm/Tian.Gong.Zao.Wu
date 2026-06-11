# CHANGELOG L6.70.6 / FE01 STEP31F

## 目标

本轮从“代码级修复”升级为“类人视觉 / 点击体感审计”：以真实 Tk 窗口启动桌面端，逐页点击、切换、滚动、提交，确认用户可见交互是否稳定。

## 修复项

1. 桌面启动默认模式由 `mock` 改为 `auto`。
   - 未配置模型 Key/Base URL 时使用本地离线桥接。
   - 保存 Runtime Provider 配置后自动切换到 `provider`。
   - 保留强制真实模型与强制演示模式启动脚本。

2. 修复流式线程直接调用 Tk 的潜在崩溃/卡死风险。
   - 新增主线程 UI 事件队列。
   - SSE worker 只投递 UI 更新，不直接触碰 Tk 控件。

3. 非聊天页面统一加入外层滚动容器。
   - 执行、任务、观测、文件、工作区、连接器、记忆、自我迭代、四路径、安装、设置、Hooks 等页面在 1280x800 下不再出现下半部分不可达。

4. 聊天区刷新和流式输出后强制钉到底部。
   - 解决刷新后滚动条回到顶部、看不到实时进度的问题。

5. 主题切换改为整壳重绘。
   - 根窗口、顶栏、侧栏、状态栏、当前页一起刷新。
   - 保留极夜、暖灰、墨绿三套配色。

6. 新建任务和导入计划取消占位聊天污染。
   - “新建任务”只聚焦输入框，不向 Runtime 发送假消息。
   - “导入计划”走文件选择/传输链，不再生成伪聊天。

7. F5 刷新不再弹成功模态框。
   - 改为状态栏提示，避免频繁打断点击流。

8. 文件写入授权、MCP 注册、自检、Key 保存回执重新走点击审计。
   - 写入授权使用目录选择，scope 固定为 `workspace_outbox`。
   - MCP 注册提交后必须产生可见回执。
   - 设置保存后 Provider digest 与 effective backend mode 可见。

## 验证

- `compileall frontend desktop scripts`：通过。
- `desktop_human_visual_click_audit_l6706.py`：40 项通过。
- `desktop_bundle_preflight_l671.py`：通过。
- `verify_l671_release.py`：通过。
- 扫描门：通过。

## 边界

`ready_for_combine=false` 保持不变。本包证明桌面端与本地桥接链路可启动、可点击、可回执；不把本地桥接冒充正式 TiangongWangguan/Runtime RC 解阻证据。
