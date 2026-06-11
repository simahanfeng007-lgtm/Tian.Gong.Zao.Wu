# FE01 STEP26 / L6.65 Agent Workspace / 沙箱与文件授权

## 本轮目标

在 L6.64 文件传输入口之上，补齐产品级文件边界：Agent Workspace、沙箱边界、目录白名单、文件授权请求、下载中转回执。

## 硬边界

- 前端不创建工作区。
- 前端不修改 ACL。
- 前端不复制文件字节。
- 前端不显示原始本地路径。
- 前端不显示原始下载 token。
- 前端不写长期记忆、审计、回滚。
- 写入授权必须继续经 Runtime / QualityGate / TiangongWangguan 裁决。

## 新增能力

- `contracts/workspace.py`：WorkspacePolicyProjection、WorkspaceMount、FileAuthorizationRequest、FileAuthorizationPublicRecord、DownloadHandoffRecord。
- `/workspace/policy`：工作区策略只读投影。
- `/workspace/file/authorize`：文件授权请求。
- `/files/download/claim`：下载中转回执投影。
- 桌面端新增「工作区」页。
- HookBus 新增 `pre_workspace_authorization_request`。

## 当前状态

L6.65 仍是 RC 前置层。真实 Runtime 未提供时，授权请求只做前端 fallback 记录，不把 `ready_for_combine` 改为 true。
