# FE01 STEP31A / L6.70.1 桌面端前后端一体化启动包

## 定位

本包解决“只给前端、不方便启动后端”的问题：根目录提供双击启动脚本，自动拉起本地桌面桥接后端，再打开 Tk 桌面前端。

这不是正式 exe/msi 安装器，也不把本地桥接当作真实 TiangongWangguan/Runtime RC 解阻证据。

## Windows 使用

1. 解压 zip。
2. 双击：`启动临渊者桌面端.bat`。
3. 需要自检时双击：`一键自检_L6701.bat`。

离线默认模式使用 bundled mock 后端，能验证桌面端、SSE、assistant_final -> run_terminal 顺序、只读投影与请求信封边界。

需要连接真实模型时，双击：`启动临渊者桌面端_真实模型.bat`，按提示输入 Base URL、Provider Key、模型名。密钥只保存在当前窗口进程内存，不写入包体、报告或日志。

## 边界

- 前端仍不裸调 Provider SDK。
- 前端仍不直接调用工具。
- 前端仍不直接写长期记忆。
- 前端仍不直接写审计。
- 前端仍不直接应用回滚。
- 文件、工作区、连接器、确认、控制请求仍走 Runtime envelope。
- 本地桥接仅负责把桌面端请求转交给 bundled 后端 CLI。

## 正式 RC 阻断

L6.70.1 桌面一体包可启动，但 `ready_for_combine=false` 仍保持：正式 RC 还需要真实 TiangongWangguan/Runtime URL 跑 L6.70 解阻。
