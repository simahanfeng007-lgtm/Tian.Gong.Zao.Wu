# L6.68 安装器 RC 前置结构

本目录是安装包前的工程结构，不是最终 exe/msi。它只预留：安装 manifest、版本槽、启动自检、崩溃报告模板、更新器骨架、离线修复和回滚计划脚本。

边界：

- 前端不可生成安装包。
- 前端不可应用更新。
- 前端不可恢复回滚槽。
- 前端不可上传崩溃报告。
- 前端不可修改 Runtime 核心文件。
- 真实安装、更新、回滚和修复必须进入安装器控制器或用户显式执行的维护脚本。

推荐入口：

```bash
python installer/startup/startup_self_check_l668.py
python installer/recovery/offline_repair_l668.py
python installer/recovery/rollback_slot_restore_l668.py
python scripts/installer_rc_preflight_l668.py
```
