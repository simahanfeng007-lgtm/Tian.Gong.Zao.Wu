# FE01 STEP27 / L6.66 MCP / 连接器注册表前置治理合成报告

生成时间：2026-06-07T06:27:59

## 本轮结论

- L6.66 已完成。
- 本轮只做 MCP / 连接器注册表前置治理，不接开放市场，不安装、不执行连接器。
- 前端新增连接器只读投影页与注册请求入口，但真实注册、启用、隔离、执行均必须经 Runtime / TiangongWangguan / QualityGate / Agent Workspace。
- 未触碰后端核心主链。
- 当前环境未提供真实 Runtime 地址，ready_for_combine 仍为 false。

## 新增能力

1. 连接器注册表契约：`contracts/connectors.py`。
2. 连接器只读投影：Registry、Manifest、RegistrationRecord。
3. RuntimeClient 新增 `request_connector_registration(...)`。
4. SSE 客户端新增 `/connectors/registry` 只读读取与 `/connectors/register/request` 请求入口。
5. Mock / Future / JSON report RuntimeClient 均补齐连接器注册请求回执。
6. HookBus 新增 `pre_connector_registration_request` 确定性守卫。
7. 桌面端新增「连接器」二级页。
8. 契约服务器新增连接器注册表投影与受控注册请求回执。
9. 新增 L6.66 smoke、preflight、release verifier、启动脚本与文档。

## 硬边界

- 前端不得安装 MCP server。
- 前端不得执行连接器。
- 前端不得保存连接器密钥。
- 前端不得绕过工作区授权。
- 前端不得绕过 QualityGate。
- 前端不得直接调用工具、写记忆、写审计、应用回滚。
- 连接器 manifest 只展示 digest 与安全摘要。

## 验证摘要

- 后端 compileall：PASS。
- 前端 / scripts / launchers compileall：PASS。
- L6.62 observability preflight：PASS。
- L6.63 HookBus preflight：PASS。
- L6.64 文件传输 / 对话引导 / 中断任务 preflight：PASS。
- L6.65 Agent Workspace preflight：PASS。
- L6.66 connector registry preflight：PASS。
- RC preflight contract-server：PASS。
- real Runtime unlock：未执行，缺少真实 Runtime 地址时按预期阻断。
- secret scan / Provider SDK import scan / bare except pass scan：PASS。

## 状态

- P0：未发现。
- P1：真实 Runtime 实例 smoke 未执行。
- ready_for_combine：false。
