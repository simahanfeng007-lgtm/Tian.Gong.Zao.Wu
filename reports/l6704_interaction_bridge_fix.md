# L6.70.4 桌面端交互质量与本地桥接修复报告

## 问题分桶

- 任务塔台继续显示 `SESS-MOCK-*`：旧版演示 Session 投影污染。
- 质量门/聊天区域反复出现恢复请求：Session 恢复回执被写入主聊天 transcript。
- 自我迭代确认 404：本地桥缺少自我迭代确认端点。
- 文件上传后不自动执行：上传只生成 transfer request，没有继续生成 Runtime 文件处理任务。
- 写入授权入口误导：写入请求仍走普通打开文件选择器。
- MCP 注册没反馈：本地桥没有形成注册记录与状态投影。
- 启动自检运行不起来：前端无按钮，桥接无自检端点。
- 聊天刷新回顶：Tk Text 重建后视口回到首行。
- 记忆界面过空、视觉过黑：布局与主题选项不足。

## 修改文件

- `frontend/linyuanzhe_frontend/contracts/runtime_snapshot.py`
- `frontend/linyuanzhe_frontend/contracts/file_transfer.py`
- `frontend/linyuanzhe_frontend/clients/sse_runtime_client.py`
- `frontend/linyuanzhe_frontend/ui/main_window.py`
- `frontend/linyuanzhe_frontend/ui/theme.py`
- `frontend/linyuanzhe_frontend/VERSION_FE01.txt`
- `desktop/linyuanzhe_local_runtime_bridge_l671.py`
- `desktop/start_linyuanzhe_desktop_l671.py`
- `docs/CHANGELOG_L6704.md`
- `scripts/desktop_step31d_regression_l6704.py`

## 结果

- mock session 不再进入任务列表。
- mock session 恢复点击只做清理，不再污染聊天/质量门观感。
- 自我迭代确认可到达本地 Runtime 桥接。
- 文件上传后可自动提交 Runtime 文件处理任务。
- 写入授权进入输出路径选择。
- MCP 注册提交后有状态提示和注册回执。
- 自检按钮可执行桥接自检。
- 聊天区刷新/流式更新保持滚动到底部。
- 记忆页更紧凑，配色支持三档切换。

## 验证产物

- `reports/l6704_compileall.log`
- `reports/desktop_step31d_regression_l6704.json`
- `reports/l6704_desktop_bundle_preflight_l671.log`
- `reports/l6704_verify_l671_release.log`
