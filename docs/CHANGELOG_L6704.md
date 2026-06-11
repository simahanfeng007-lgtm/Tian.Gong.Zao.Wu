# CHANGELOG L6.70.4

## FE01 STEP31D / L6.70.4

本轮修复目标：继续收口桌面端交互质量门、任务 Session 投影、本地 Runtime 桥接和低对比视觉问题。所有改动保持前端边界：前端只提交 Runtime envelope，不直接执行工具、不写记忆、不写审计、不应用回滚。

### 修复项

1. **旧版 mock Session 清理**
   - 过滤 `SESS-MOCK-*` 历史演示任务。
   - 点击恢复旧 mock Session 时只清理投影，不再向 Runtime 发恢复请求。
   - 恢复请求不再写入主聊天 transcript，避免被误认为 QualityGate 输出。

2. **自我迭代确认 404**
   - 本地桥新增 `/self-iteration/confirm`、`/self_iteration/confirm`、`/self-iteration/confirm/request`。
   - 前端按兼容端点顺序提交，成功后显示 Runtime 已接收，不再出现 `HTTP Error 404: Not Found`。

3. **文件上传自动进入 Runtime 文件处理链**
   - 文件传输请求新增本地 Runtime handoff path，仅交给本地桥接/Runtime 子进程。
   - 上传后可自动提交“读取/分析附件”的 Runtime 任务。
   - UI/报告继续只展示文件名、大小、摘要、回执，不展示原始路径或文件正文。

4. **文件授权 UI 语义修正**
   - 只读授权使用打开文件选择器。
   - 写入授权使用保存/输出位置选择器，并设置 `workspace_outbox`、`workspace_output_write`。

5. **MCP 注册请求无反馈**
   - 本地桥接收 `/connectors/register/request` 并返回注册回执。
   - 连接器页面增加提交状态提示，并在注册表投影中显示注册记录。

6. **启动自检不可运行**
   - 前端新增“运行自检”按钮。
   - 本地桥提供 `/installer/startup/self-check`，返回三项基础自检：后端入口、桥接服务、前端边界。

7. **聊天区刷新滚动条回顶**
   - 聊天页重渲染后继续钉到最新输出。
   - SSE delta/final 和手动刷新均调用多次延迟 pin，避免 Tk Text 视口回到首行。

8. **记忆界面留白与配色**
   - 记忆页改成紧凑摘要 + L1-L5 层级 + 边界说明 + 最近上下文摘要。
   - 设置页新增三套桌面配色：极夜蓝、暖灰白、墨绿；选择会持久化到本地 UI preference。

### 验证

- `python -m compileall desktop frontend/linyuanzhe_frontend scripts installer/startup` 通过。
- `scripts/desktop_step31d_regression_l6704.py` 通过。
- `scripts/desktop_bundle_preflight_l671.py` 通过。
- `scripts/verify_l671_release.py` 通过。

### 保持边界

- `ready_for_combine=false` 继续保留：桌面本地桥接不是正式 TiangongWangguan/Runtime 解阻证据。
- 前端仍不直接执行工具、写长期记忆、写审计、应用回滚或合入自我迭代。
