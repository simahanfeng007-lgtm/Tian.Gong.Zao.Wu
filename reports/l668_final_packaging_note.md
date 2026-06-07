# L6.68 打包说明

本包为前后端合成 RC 前置总包，包含 backend、frontend、launchers、scripts、docs、reports 与 installer 前置目录。

本包不是最终安装包。installer 目录只提供安装器 RC 前置结构、版本槽、启动自检、离线修复 dry-run 与回滚计划 dry-run。

真实 Runtime 联调仍未执行，因此合成状态保持 blocked，ready_for_combine 保持 false。
