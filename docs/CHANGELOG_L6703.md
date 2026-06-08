# CHANGELOG L6.70.3

## FE01 STEP31C / L6.70.3

### 修复

1. 聊天区实时输出滚动：
   - SSE 快照到达后直接刷新当前聊天 Text widget。
   - 渲染完成后强制 `see("end")` 与 `yview_moveto(1.0)`。
   - 避免聊天窗口长期停留在首轮消息位置，实时 delta/final 输出可见。

2. Provider/API Key 配置保存：
   - 前端仍不持久化、不回显 API Key/Base URL 明文。
   - 本地 Runtime 桥接层新增托管配置文件，保存 provider/model/base_url/api_key。
   - 设置页进入时会刷新 `/settings/provider`，显示 configured/digest 状态。
   - 留空 Key/Base URL 再保存时，沿用 Runtime 已保存值。

3. 状态边界：
   - 修复仅限桌面投影、设置页回执与本地桥接配置托管。
   - 不改变 Runtime 主链、Planner、工具执行、记忆、审计或回滚边界。
