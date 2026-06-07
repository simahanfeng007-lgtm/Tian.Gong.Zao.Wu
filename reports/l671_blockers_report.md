# L6.70.1 阻断项报告

## 已解除

1. 用户侧“不方便自己启动后端”的操作阻断已解除：根目录双击脚本会自动启动本地桥接后端并打开桌面前端。
2. 前端与 bundled 后端 CLI 已可通过本地 SSE 桥接跑通单轮对话。

## 仍保留

1. `ready_for_combine=false`：未执行正式 TiangongWangguan/Runtime 真实联调。
2. `final_installer_allowed=false`：未进入正式 exe/msi 安装器构建阶段。
3. `windows_installer_artifact_emitted=false`：本包是 zip 解压即用包，不是安装器。

## 原因

本地桥接服务是桌面一体包的可用性桥，不是正式 Runtime RC 证据。不能把它伪装成真实 Runtime 联调通过。
