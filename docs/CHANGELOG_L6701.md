# CHANGELOG L6.70.1

## FE01 STEP31A / L6.70.1

新增桌面端前后端一体化启动包能力：

1. 新增 `desktop/linyuanzhe_local_runtime_bridge_l671.py`。
2. 新增 `desktop/start_linyuanzhe_desktop_l671.py`。
3. 根目录新增 `启动临渊者桌面端.bat`、`启动临渊者桌面端_真实模型.bat`、`一键自检_L6701.bat`。
4. 新增桌面一体包预检 `scripts/desktop_bundle_preflight_l671.py`。
5. 新增聚合验证 `scripts/verify_l671_release.py`。
6. 明确：本地桥接可用于桌面端启动与本地验收，但不冒充真实 Runtime RC 解阻。

## 状态

- desktop_all_in_one_ready：以本轮自检结果为准。
- ready_for_combine：false。
- final_installer_allowed：false。
- windows_installer_artifact_emitted：false。
