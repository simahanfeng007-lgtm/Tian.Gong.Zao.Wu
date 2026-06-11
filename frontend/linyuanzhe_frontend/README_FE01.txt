# 临渊者桌面端 FE.01

版本：FE01 STEP68 / L6.73.8
类型：Python 标准库桌面端 / tkinter / Runtime SSE 契约端 / Provider 设置页 / Run Workbench / 文件上传交接 / 设置持久化。

## 定位

本目录是临渊者桌面端前端，不是第二 Runtime。前端只负责显示、输入、设置保存、状态投影、错误可读化与工作台呈现；不执行工具、不写记忆、不应用回滚、不抢 LLM 的 ActivationForm 裁决。

## 当前验收重点

- chat/work 双模式显示边界。
- conversation 与 workbench 事件分流。
- Provider 设置保存与 Base URL 回填。
- API Key write-only / digest-only。
- 文件上传 public/private handoff 合同。
- A5 approval projection。
- Tk self-check 区分 tkinter_import 与 tkinter_display。

## 验证入口

- `python -m compileall -q backend frontend desktop scripts`
- `python frontend/linyuanzhe_frontend/scripts/validate_demo_package.py`
- `bash frontend/linyuanzhe_frontend/run_rc_preflight.sh --contract-server`

历史 L6.54/L6.58/STEP15/STEP19 文档只作为追溯材料，不作为当前交付验收口径。
