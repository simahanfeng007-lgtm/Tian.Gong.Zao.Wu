# L6718 工作模式激活固化

本轮不重构 Runtime，不改前端主壳，只把 L6717 融合包内的 R20/R21 学习资产从 smoke workspace 激活状态固化到主工作区：

- 主工作区：`backend/project`
- active registry：`backend/project/.linyuanzhe/active_assets/r20/active_assets_registry.json`
- active assets：9 个
- learned tools：7 个
- learned skills：2 个
- Runtime tools after active load：158
- usage cards：158 / 158
- direct learned_* calls：9 / 9 PASS
- pytest：22 passed
- no-pollution：PASS

复验入口：

```bash
bash launchers/run_workmode_activation_check_l6718.sh
```

Windows：

```bat
launchers\run_workmode_activation_check_l6718.bat
```
