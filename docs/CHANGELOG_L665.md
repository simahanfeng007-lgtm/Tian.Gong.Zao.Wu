# CHANGELOG L6.65

- 新增 Agent Workspace / 沙箱与文件授权合约。
- 新增工作区二级页，展示策略、挂载、授权、下载中转回执。
- 新增文件授权请求方法，前端只提交 envelope。
- 新增 HookBus `pre_workspace_authorization_request` 确定性规则。
- 新增 `workspace_preflight_l665.py` 与 `verify_l665_release.py`。
- 未改后端核心主链；真实文件操作仍必须由 Runtime / TiangongWangguan 接管。
