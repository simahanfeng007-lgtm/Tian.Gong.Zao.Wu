# 临渊者 FE01 STEP20 / L6.59 前后端合成 RC 前置总包

## 目录

- `backend/project/`：后端 L6.51.1 Runtime / TiangongWangguan 契约相关源码。未改动核心主链。
- `frontend/linyuanzhe_frontend/`：前端 STEP19 桌面端运行源码。历史测试夹具、旧报告不进入本 RC 包。
- `launchers/`：统一启动器。
- `scripts/`：L6.59 合成 preflight 与扫描脚本。
- `reports/`：本轮验证、阻断项、哈希与合成报告。

## 启动

真实 Runtime 已经在外部启动时：

```bash
export LINYUANZHE_RUNTIME_URL="<runtime-url>"
python launchers/start_linyuanzhe_rc.py --mode real
```

无真实 Runtime 时，只允许契约回归演示：

```bash
python launchers/start_linyuanzhe_rc.py --mode contract --preflight-only
```

契约模式不等于真实 Runtime 联调通过。

## 边界

前端只负责渲染、提交请求、展示回执；不得裸调 Provider、工具、长期记忆、审计、回滚。Runtime 仍是唯一执行调度中枢，TiangongWangguan 仍是统一入口。

产品身份元数据保留：唯一开发者「于泳翔」，天使投资人「胖胖龙」。
