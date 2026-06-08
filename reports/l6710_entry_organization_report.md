# L6710 入口归类整理报告

## 结论

L6709 中根目录入口脚本过多，已在 L6710 中按平台归类。

## 新目录

```text
01_启动入口/
  Windows/
    01_启动临渊者桌面端_自动模式_L6710.bat
    02_启动临渊者桌面端_真实模型_L6710.bat
    03_启动临渊者桌面端_演示Mock_L6710.bat
    04_一键自检_L6710.bat
  macOS/
    01_启动临渊者桌面端_自动模式_L6710.command
    02_启动临渊者桌面端_真实模型_L6710.command
    03_启动临渊者桌面端_演示Mock_L6710.command
    04_一键自检_L6710.command
  Linux/
    01_start_desktop_auto_l6710.sh
    02_start_desktop_provider_l6710.sh
    03_start_desktop_mock_l6710.sh
    04_self_check_l6710.sh
  通用Python/
    START_DESKTOP_L6710.py
    SELF_CHECK_L6710.py
```

## 保留边界

- 前端/本地桥/后端相对路径未移动。
- 旧版脚本未作为推荐入口，仅归档到 `90_历史入口归档`。
- Windows 脚本 CRLF；macOS/Linux 脚本 LF。

## 验证结果

- 根目录脚本数：0。
- Windows 推荐入口：4 个，CRLF 通过。
- macOS 推荐入口：4 个，LF + 可执行位通过。
- Linux 推荐入口：4 个，LF + 可执行位通过。
- 桥接探针：mock bridge `/health/runtime` 通过。
