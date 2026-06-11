# CHANGELOG L6.61

## 新增

1. `scripts/real_runtime_unlock_l661.py`：真实 Runtime 联调解阻执行脚本。
2. `scripts/verify_l661_release.py`：L6.61 发布包自检脚本。
3. `launchers/run_real_runtime_unlock_l661.sh/.bat`：一键真实联调入口。
4. `docs/REAL_RUNTIME_UNLOCK_L661.md`：本机执行说明。

## 修复

1. 真实 Runtime 联调默认改为 Provider 只读投影检查。
2. 只有显式 smoke 模式且提供专用烟测凭证时，才提交 Provider 写入请求。
3. 报告继续只写 digest，不写 Runtime 地址或 Provider 明文。

## 未改变

- Runtime 仍是唯一执行调度中枢。
- TiangongWangguan 仍是统一网关入口。
- 前端仍只做渲染、提交请求、展示回执。
- 后端核心主链未改。
