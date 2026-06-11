# 天工造物v2·0-临渊者 差异对比与融合报告

## 融合输入

1. `天工造物v2.0-临渊者.zip`：用户上传成品外壳，原始根目录为 `L6_51`，zip 内中文路径存在 CP437/UTF-8 标志缺失导致的显示乱码，已在融合时修复为正常中文路径。
2. `临渊者_FE01_STEP31Q_L6721.1_ActiveAssets可迁移工作模式地基修复_20260608.zip`：最新可用后端/前端/工作模式地基基线。

## 目录级差异

- 用户包文件数：2028
- L6721.1 文件数：2303
- 共同文件：2025
- 内容不同文件：56
- 用户包独有文件：3
- L6721.1 独有文件：278

## 用户包独有内容

保留并合入：

- `00_ASCII_START_HERE/windows/DEPENDENCY_CHECK.bat`
- `00_ASCII_START_HERE/python/DEPENDENCY_CHECK.py`
- `00_ASCII_START_HERE/linux_macos/dependency_check.sh`

## L6721.1 优先保留内容

- R20/R21 active learned assets 工作模式
- active_assets 可迁移 / 可重定位修复
- 前端 STEP31Q/L6721 修复后的模块化 UI
- L6721 生物动态模型增强底座
- L6719 入口编码与 Tk 启动健壮性修复
- Code-X / runtime alignment / frontend bridge smoke 脚本

## 冲突处理规则

1. 后端、Runtime、learning_asset_activation、active_assets registry：采用 L6721.1。
2. 前端主代码：采用 L6721.1。
3. 用户包独有依赖检测入口：合入。
4. 包根目录：统一为 `天工造物v2·0-临渊者`。
5. 产品标题：前端标题改为 `天工造物v2·0-临渊者 - FE01 STEP31Q / L6.72.1`。

## 风险判断

本次不是大架构改造，不接入 L6722 状态总线；只做融合、命名、路径修复保留与用户独有入口合入。不会改变 LLM 主脑边界。
