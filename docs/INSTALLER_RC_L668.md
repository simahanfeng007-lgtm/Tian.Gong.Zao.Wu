# FE01 STEP29 / L6.68 安装器 RC 前置结构

## 目标

L6.68 把工程总包推进到安装包前结构，但仍不是最终 exe/msi 安装包。本轮补齐：

1. 安装 manifest。
2. active / rollback / candidate 三类版本槽。
3. 启动自检脚本。
4. 崩溃报告本地模板。
5. 更新器骨架。
6. 离线修复 dry-run。
7. 回滚槽恢复计划。
8. 桌面端「安装」二级页。

## 硬边界

- 前端不可生成安装包。
- 前端不可应用更新。
- 前端不可恢复回滚槽。
- 前端不可上传崩溃报告。
- 前端不可修改 Runtime 核心文件。
- 真实安装、更新、回滚和修复必须由安装器控制器或用户显式运行的维护脚本执行。

## 关键文件

- `installer/installer_manifest_l668.json`
- `installer/startup/startup_self_check_l668.py`
- `installer/recovery/offline_repair_l668.py`
- `installer/recovery/rollback_slot_restore_l668.py`
- `installer/updater/update_manifest_l668.json`
- `installer/crash/crash_report_template_l668.json`
- `scripts/installer_rc_preflight_l668.py`
- `scripts/verify_l668_release.py`

## 验证入口

```bash
python scripts/installer_rc_preflight_l668.py
python scripts/verify_l668_release.py
python launchers/start_linyuanzhe_rc.py --installer-rc-preflight
```

## 状态

当前仍然 `ready_for_combine=false`。原因不是安装器结构缺失，而是真实 Runtime 实例 smoke 尚未执行。
