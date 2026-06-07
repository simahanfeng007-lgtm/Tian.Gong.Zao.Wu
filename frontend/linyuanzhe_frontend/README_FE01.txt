# 临渊者桌面驾驶舱 FE.01

版本：L6-FE.01【前端契约驾驶舱原型】
类型：Python 标准库桌面端 / tkinter / Mock + JSON Report + L6.58 Runtime SSE 流式续接与 RC 预检驱动

## 1. 定位

本目录是临渊者桌面端前端原型，不是 Web 端，不是第二 Runtime。

FE.01 只做：

- 桌面窗口
- 首页 UI
- RuntimeClient 契约
- MockRuntimeClient
- JsonReportRuntimeClient
- FutureRuntimeClient 兼容占位
- SseRuntimeClient（L6.54 真实 Runtime SSE 契约端点、断连续接、任务控制请求、Agent UI 显示事件）
- GUI smoke test

FE.01 不做：

- 不调真实工具
- 不裸调模型 SDK
- 不调用 Adapter
- 不写 tiangong_kernel
- 不绕过 PlannerExecutionController / LongChainRunner / ExecutionSpine
- 不实现第二 Runtime；真实连接只能走 /chat/stream-events 等后端契约端点

## 2. 启动方式

在包含 `linyuanzhe_frontend/` 的父目录执行：

```bash
python -m linyuanzhe_frontend.app
```

或直接执行：

```bash
python linyuanzhe_frontend/app.py
```

读取 Mock 文件：

```bash
python -m linyuanzhe_frontend.app --mock-file linyuanzhe_frontend/mock_data/runtime_snapshot_mock.json
```

读取后端 JSON 报告目录：

```bash
python -m linyuanzhe_frontend.app --json-report path/to/export_dir
```

读取单个 JSON 报告：

```bash
python -m linyuanzhe_frontend.app --json-report path/to/p0_system2.json
```

连接 L6.58 Runtime SSE 网关：

```bash
python -m linyuanzhe_frontend.app --runtime-url http://127.0.0.1:8787
```

或设置环境变量后启动：

```bash
export LINYUANZHE_RUNTIME_URL=http://127.0.0.1:8787
python -m linyuanzhe_frontend.app
```


## 2.1 L6.54 顺滑层与控制边界

STEP15 在 STEP14 基础上新增四项桌面端优化能力：

1. EventBuffer：缓存 Runtime SSE 事件，避免 UI 线程逐事件重刷。
2. DeltaMerger：合并 assistant_delta，默认 45ms 批量刷新。
3. VirtualTranscript：长对话只保留可见消息窗口，历史数量用 hidden_message_count 标记。
4. Agent UI Event Contract：Runtime 事件归一为 text_delta / tool_call_started / quality_gate_required / audit_recorded 等显示事件。

停止 / 复位按钮仍只向 Runtime 网关提交控制请求，不直接停止工具、不复位内核、不写审计、不应用回滚。这些能力仍然是前端契约层能力，不改变 Planner / ExecutionSpine / Runtime / QualityGate / Audit / Rollback 主链。


## 2.2 L6.58 真实后端联调、Provider 回执与 RC 前置预检

STEP17/STEP18/STEP19 新增联调、Provider 写入回执与 RC 前置预检，但不改变前端执行边界：

1. `scripts/runtime_contract_server.py`：本地受控 Runtime 契约服务器，仅用于前端回归；不调用 Provider，不执行工具。
2. `clients/runtime_integration_probe.py`：探测 `/health/runtime`、`/metadata/product`、`/settings/provider`，并通过 `SseRuntimeClient` 执行 `/chat/stream-events` 端到端 smoke。
3. `run_backend_integration_smoke.py`：一键输出联调报告，报告只写 `runtime_url_digest`，不写 Runtime URL 明文、Provider Key 或 Provider Base URL。
4. `run_rc_preflight.py`：STEP19 RC 前置闸口；真实 Runtime 运行实例存在时可用 `--require-real` 强制预检，契约服务器回归不会被误判成正式合成通过。

本地契约服务器 smoke：

```bash
python -m linyuanzhe_frontend.run_backend_integration_smoke --contract-server
python -m linyuanzhe_frontend.run_rc_preflight --contract-server
```

真实 Runtime smoke：

```bash
export LINYUANZHE_RUNTIME_URL=http://127.0.0.1:8787
python -m linyuanzhe_frontend.run_backend_integration_smoke --out reports/real_runtime_l6_58_smoke.json
python -m linyuanzhe_frontend.run_rc_preflight --require-real --out reports/real_runtime_l6_58_rc_preflight.json
```

## 3. 验证方式

```bash
python -m compileall -q linyuanzhe_frontend
python linyuanzhe_frontend/tests/smoke_test_frontend.py
python -m pytest -q linyuanzhe_frontend/tests/test_frontend_contracts.py linyuanzhe_frontend/tests/test_l6_52_sse_runtime_client.py linyuanzhe_frontend/tests/test_l6_53_streaming_controls.py linyuanzhe_frontend/tests/test_l6_54_smooth_agent_ui.py linyuanzhe_frontend/tests/test_l6_55_action_guard_cards.py linyuanzhe_frontend/tests/test_l6_56_e2e_integration_smoke.py linyuanzhe_frontend/tests/test_l6_57_provider_settings_writeback.py linyuanzhe_frontend/tests/test_l6_58_rc_preflight.py
python -m linyuanzhe_frontend.run_backend_integration_smoke --contract-server
python -m linyuanzhe_frontend.run_rc_preflight --contract-server
```

注意：GUI 启动需要本地桌面环境；无 DISPLAY 的 CI/沙箱中只执行 smoke test。

## 4. 目录说明

```text
linyuanzhe_frontend/
  app.py
  contracts/
    runtime_client.py
    runtime_snapshot.py
  clients/
    mock_runtime_client.py
    json_report_runtime_client.py
    future_runtime_client.py
    sse_runtime_client.py
  ui/
    theme.py
    widgets.py
    main_window.py
  mock_data/
    runtime_snapshot_mock.json
  reports/
    README.txt
  tests/
    smoke_test_frontend.py
```

## 5. 接线口径

后端 L6.51.1 契约已冻结；STEP15 / L6.54 已接入真实 Runtime SSE 流式状态、续接和控制请求。
默认仍使用 MockRuntimeClient / JsonReportRuntimeClient；提供 --runtime-url 后切换为 SseRuntimeClient。
SseRuntimeClient 只能访问 /health/runtime、/metadata/product、/settings/provider、/chat/stream-events，不裸调 Provider SDK、Adapter、工具、记忆、审计或回滚。

真实接线必须继续通过后端治理链：

```text
RuntimeEntry → PlannerExecutionController → LongChainRunner → ExecutionSpine → PermitGateway / AuditBridge / RuntimeToolRegistry
```

## STEP06：GUI 首页布局与页面切换骨架

本阶段将 STEP05 的单首页骨架升级为 Shell + 四页面结构：

- 聊天：首页，显示主聊天区、当前任务状态、执行摘要、右侧三张摘要卡。
- 执行：二级详情页，显示执行链 Timeline、质量门详情、恢复续接、确认票据。
- 记忆：二级详情页，仅显示 sanitized_summary / digest / evidence_ref。
- 设置：二级详情页，显示 RuntimeClient 状态与 FE.01 安全边界。

历史阶段说明：当时不接真实 Runtime；当前 STEP15 只允许通过 L6.58 Runtime SSE 契约端点接线，仍不裸调模型/Provider SDK、不直接执行工具、不调用 Adapter、不写 tiangong_kernel。

## STEP07：页面细节与交互占位完善

本阶段在 STEP06 四页面结构上增强前端可演示性：

- 聊天页支持发送输入；提交后只写入 Mock/JSON 前端状态，不触发真实 Runtime。
- 设置页增加“刷新快照 F5”，只重新读取 Mock/JSON 快照。
- 设置页增加“导出前端快照”，只写入 `linyuanzhe_frontend/reports/frontend_snapshot_export.json`，不写后端内核。
- 质量门、审计摘要、恢复续接增加脱敏详情弹窗。
- 确认票据支持确认/拒绝后的前端状态回显。
- 客户端读取异常会降级为 DISCONNECTED 快照，不崩溃桌面壳。
- smoke test 增加 refresh_snapshot 契约和脱敏守卫测试。

历史阶段说明：当时不接真实 Runtime；当前 STEP15 只允许通过 L6.58 Runtime SSE 契约端点接线，仍不裸调模型/Provider SDK、不直接执行工具、不调用 Adapter、不写 tiangong_kernel。

## STEP08：视觉打磨与可演示桌面效果增强

本阶段在 STEP07 可演示交互基础上增强极夜桌面驾驶舱视觉效果：

- 补充 `ui/visual_spec.py`，冻结 STEP08 视觉验收项。
- 扩展 `ui/theme.py`，增加桌面演示级颜色、字体、布局、按钮 token。
- 扩展 `ui/widgets.py`，增加 Chip、MetricRow、StepItem、readonly banner、统一按钮工厂。
- 首页增加 FE.01 只读演示提示条。
- 顶部栏、左侧导航、状态栏、执行摘要和执行步骤样式增强。
- smoke test 增加视觉规格检查，防止后续偏离极夜桌面驾驶舱方向。

历史阶段说明：当时不接真实 Runtime；当前 STEP15 只允许通过 L6.58 Runtime SSE 契约端点接线，仍不裸调模型/Provider SDK、不直接执行工具、不调用 Adapter、不写 tiangong_kernel。

## STEP09：GUI 演示包与启动说明收口

本阶段把 STEP08 可演示桌面端收口成可交付演示包：

- 新增 `DEMO_START_HERE.txt`，作为交付包第一阅读文件。
- 新增 `run_desktop_demo.py`，用于一键进入 Mock 演示模式。
- 新增 `run_desktop_demo.bat` / `run_desktop_demo.sh`，方便 Windows / macOS / Linux 启动。
- 新增 `scripts/validate_demo_package.py`，统一执行 compileall、smoke test、演示资产完整性检查。
- 新增 `run_validation.bat` / `run_validation.sh`，方便非开发用户验证包体。
- 新增 `requirements.txt`，明确 FE.01 零第三方依赖，只使用 Python 标准库。
- 新增 `docs/demo_manifest_step09.json`，记录演示包资产、边界和验证入口。

历史阶段说明：当时不接真实 Runtime；当前 STEP15 只允许通过 L6.58 Runtime SSE 契约端点接线，仍不裸调模型/Provider SDK、不直接执行工具、不调用 Adapter、不写 tiangong_kernel。


## STEP10B：视觉精修与真实桌面截图验收

本阶段在 STEP10A 首页纠偏基础上继续收口：

- 首页任务卡进一步简化。
- 固定聊天输入栏继续作为硬约束。
- 右侧仅保留当前任务、质量门、审计摘要。
- 计划 ID、执行计数和完整步骤不在首页展示。
- 新增 `docs/homepage_screenshot_acceptance_step10b.txt`，用于本地真实桌面截图验收。

历史阶段说明：当时不接真实 Runtime；当前 STEP15 只允许通过 L6.58 Runtime SSE 契约端点接线，仍不裸调模型/Provider SDK、不直接执行工具、不调用 Adapter、不写 tiangong_kernel。


STEP12 补充：
- 首页右侧接入任务快照与对话引导。
- 新增自我迭代区与四路径状态页。
- API 输入口、主模型选择、模型搜索/筛选均集中在设置页。
- 主模型搜索为前端本地 catalog/filter，占位等待真实 Runtime Provider 契约。
- API Key 保存只写脱敏摘要与 digest，不保存明文，不调用真实 Provider。

STEP12 补充：
- 已修复 STEP11 GUI 启动崩溃。
- 已补齐任务快照、对话引导、设置保存、模型选择、自我迭代确认 5 个缺失方法。
- 底部状态栏已按 L6.51.1 固定为 9 字段。
- 产品身份元数据已对齐：唯一开发者 于泳翔；天使投资人 胖胖龙；公开入口 /metadata/product。
- API Key / Base URL 在设置页为 write-only 输入，保存后只保留 digest，不展示、不回显、不落明文。
- L6.52 已接真实 SSE / Runtime 状态；L6.54 增加流式续接与控制请求，仍禁止前端裸调 Provider / 工具 / 记忆 / 审计。


STEP13 / L6.52 补充：
- 新增 SseRuntimeClient，支持正式 Runtime 网关 URL。
- 新增 SSE 事件解析与脱敏投影：run_started / planner_started / planner_plan / runtime_state / quality_gate / tool_started / tool_result / audit_event / assistant_delta / assistant_final / run_terminal / error。
- 固化 assistant_final -> run_terminal 顺序校验，异常时降级为 PARTIAL_OR_FAILED，不崩溃。
- 设置页读取 /metadata/product 与 /settings/provider 的只读脱敏投影。
- Provider api_key/base_url 即使误入后端事件，也在前端投影层改写为 configured/digest。
- 新增 run_runtime_sse_demo.py / .sh / .bat 作为真实 Runtime 接线入口。


STEP15 / L6.54 补充：
- 发送消息改为后台线程，不阻塞 Tk 主线程。
- SSE 每个事件进入 RuntimeSnapshot 后可刷新 UI。
- 未收到 run_terminal 时按 run_id + last_seq 发起受控续接。
- 停止 / 复位按钮只提交 Runtime 控制请求，不直接停止工具或复位内核。


## 2.2 L6.57 行动守卫卡与确认请求 UX

STEP17 在 STEP15 顺滑层基础上新增 QualityGate 行动守卫卡、审计只读卡、回滚只读卡。允许 / 拒绝 / 请求修改按钮只会向 Runtime 网关提交 `/confirmations/submit` 请求，不会由前端直接放行工具、写审计、应用回滚或合入自我迭代。

新增验证：

```bash
python -m pytest -q linyuanzhe_frontend/tests/test_l6_56_action_guard_cards.py
```

## 2.5 L6.64 文件传输、对话引导与中断任务

STEP25 在 HookBus 与观测台基础上补齐三项桌面端产品能力：

1. 文件传输：首页附件按钮与“文件”二级页只提交脱敏 transfer request；真实读取、落盘、转存、下载中转仍由 Runtime / TiangongWangguan / QualityGate 管控。
2. 对话引导：推荐动作与建议问题以可点击芯片展示，点击后只填入输入栏，用户仍需确认发送。
3. 中断任务：新增中断按钮，只向 Runtime 提交控制请求，不由前端直接停止工具或杀进程。

验证：

```bash
python -m linyuanzhe_frontend.run_file_transfer_guide_interrupt_smoke
```

## FE01 STEP28 / L6.67

新增多任务 Session 管理器：任务塔台、搜索、恢复请求、等待确认/失败/完成状态投影与快捷键入口。前端只提交 Runtime 请求，不直接恢复工具或写入记忆/审计/回滚。

## 2.8 L6.68 安装器 RC 前置结构

STEP29 新增安装器 RC 前置结构，但仍不是最终 exe/msi 安装包：

- `installer/installer_manifest_l668.json`
- active / rollback / candidate 版本槽骨架
- 启动自检脚本
- 崩溃报告本地模板
- 更新器骨架
- 离线修复 dry-run
- 回滚槽恢复计划
- 桌面端「安装」二级页

验证：

```bash
python -m linyuanzhe_frontend.run_installer_rc_smoke
python ../scripts/installer_rc_preflight_l668.py
```

边界：前端不可生成安装包、不可应用更新、不可恢复回滚槽、不可上传崩溃报告、不可修改 Runtime 核心文件。
