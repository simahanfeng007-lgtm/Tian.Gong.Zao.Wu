# L6.66 MCP / 连接器注册表前置治理

本轮只做连接器治理外壳，不接开放市场，不安装 MCP server，不执行连接器工具。

## 新增边界

- 前端只显示连接器注册表投影。
- 前端只提交 `ConnectorRegistrationRequest` envelope。
- 注册、启用、隔离、执行、密钥存储均必须由 Runtime / TiangongWangguan / QualityGate / Agent Workspace 接管。
- 开放 MCP 市场一键安装默认禁用。
- 原始 endpoint、原始 secret、manifest 正文不得写入日志、报告、fixture、zip。

## 新增端点契约

- `/connectors/registry`
- `/connectors/register/request`
- `/connectors/quarantine/request`

## 默认策略

- `default_mode=disabled`
- `read_only_default=true`
- `quality_gate_required=true`
- `workspace_authorization_required=true`
- `runtime_authority_required=true`
- `frontend_may_install_connector=false`
- `frontend_may_execute_connector=false`
- `frontend_may_store_connector_secret=false`

## 验证

```bash
python scripts/connector_registry_preflight_l666.py
python scripts/verify_l666_release.py
```
