# 临渊者 FE01 STEP31Q / L6.71.7 + R21 后端融合包

融合策略：

1. 以前端成品包 `FE01 STEP31Q / L6.71.7 DataUp` 为外壳，保留 UI、桌面启动器、DataUp 一键安全更新入口、跨平台启动脚本。
2. 将旧 `backend/project` 整体替换为 `L6.70.2 R21` 后端，获得学习资产实用型 Adapter、R20 激活闭环、Runtime 工具对齐与 Code-X Runtime 能力。
3. 外壳冲突文件以前端包为准；R21 的 Code-X / learning asset launcher、文档、报告只做非冲突补入。
4. 前端 contract server 已补回 R21 Code-X bridge smoke 分支，避免前端成品包丢失 Code-X 投影烟测能力。
5. 未复制 v1 源码，未引入后台 loop，未让 Planner / 子智能体夺权。

启动入口仍按前端成品包使用：

- Windows：`01_启动入口/Windows/01_启动临渊者桌面端_自动模式_L6710.bat`（压缩包中中文目录可能因系统解码显示不同）
- Linux：`01_启动入口/Linux/01_start_desktop_auto_l6710.sh`
- Python 直启：`python desktop/start_linyuanzhe_desktop_l671.py`

R21 后端验证入口：

- `bash launchers/run_codex_runtime_smoke_l6702.sh`
- `bash launchers/run_learning_asset_activation_smoke_l6702_r20.sh`
- `bash launchers/run_learning_asset_adapter_smoke_l6702_r21.sh`
- `bash launchers/run_runtime_tool_alignment_smoke_l6702.sh`
- `bash launchers/run_codex_frontend_bridge_smoke_l6702.sh`
