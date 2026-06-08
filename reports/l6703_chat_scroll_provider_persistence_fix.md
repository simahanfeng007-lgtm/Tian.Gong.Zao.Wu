# L6.70.3 桌面端聊天滚动与 Provider 配置持久化修复报告

## 用户反馈

- 聊天窗口记录一直停在最初始聊天位置，不显示实时聊天进度。
- 配置 Key 不能保存。

## 根因

1. 聊天窗口每次流式快照刷新后重建 Text 控件，但未将视口定位到最新输出，Tk 默认停留在顶部。
2. 本地桌面桥接层 `BridgeState` 只把 Provider Key/Base URL 保存在进程内存，重启桥接后配置丢失。
3. 设置页进入时只读取已有 `RuntimeSnapshot`，没有主动刷新 `/settings/provider`，导致已保存配置的 digest 状态不稳定显示。

## 修复

- `ui/main_window.py`
  - 新增 `_render_chat_messages_into()`。
  - 新增 `_render_live_chat_transcript()`。
  - SSE 快照应用时优先直接刷新聊天 transcript，并强制滚动到末尾。
  - 设置页进入时调用 `refresh_snapshot()` 获取最新 provider projection。
  - 设置页表单从 Runtime 脱敏投影同步 provider/model，Key/Base URL 不回填明文。

- `desktop/linyuanzhe_local_runtime_bridge_l671.py`
  - 新增 Runtime 托管 provider 配置文件读取/写入。
  - 保存 provider/model/base_url/api_key 到本机 Runtime 配置路径。
  - `/settings/provider` 继续只返回 configured/digest，不返回明文。
  - 留空 Key/Base URL 保存时沿用已保存值。

- `desktop/start_linyuanzhe_desktop_l671.py`
  - 启动说明更新为 L6.70.3。

## 安全边界

- 前端不保存 API Key。
- 前端不回显 API Key。
- 前端不直接调用 Provider SDK。
- 本地桥接层是 Runtime 托管配置方。
- 配置文件路径可用 `LINYUANZHE_PROVIDER_CONFIG_FILE` 覆盖。
