# CHANGELOG L6.70

- 进入 FE01 STEP31 / L6.70：真实 Runtime 联调执行与 RC 解阻。
- 修复真实联调前置缺陷：`real_runtime_gate_l660.py` 传入的 `--provider-write-mode` 已由 `rc_preflight_l659.py` 接收并透传给前端 RC preflight，避免真实 Runtime URL 存在时因 argparse 参数不匹配直接失败。
- 新增 `scripts/real_runtime_endpoint_smoke_l670.py`：真实 Runtime 只读端点矩阵与请求信封边界检查；缺少 `LINYUANZHE_RUNTIME_URL` 时只生成阻断证据，不使用 contract-server 冒充真实联调。
- 新增 `scripts/verify_l670_release.py`：聚合 L6.70 编译、L6.62-L6.69 preflight、contract-server 回归、真实 Runtime 解阻/endpoint smoke、扫描结果。
- 启动器新增 `--real-runtime-smoke-l670` 与 `--verify-l670`。
- 本阶段仍不输出 exe/msi；只有真实 Runtime unlock 与 endpoint smoke 均通过后，才允许进入 L6.71 正式 RC 收口包。
