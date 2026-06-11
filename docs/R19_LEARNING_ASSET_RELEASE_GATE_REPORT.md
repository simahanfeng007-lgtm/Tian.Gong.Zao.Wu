# L6.70.2 R19 Tool/Skill 候选发布门轻量执行版

## 结论

R19 通过。R18 已有候选包生产沙箱，本轮不扩复杂治理，只新增轻量发布门：

```text
learning_asset_candidate_sandbox_review
→ learning_asset_release_gate_check
```

## 新增 Runtime 工具

- `learning_asset_release_gate_guide`
- `learning_asset_release_gate_check`

## 新增命令

- `asset-release guide`
- `asset-release gate`
- `asset-release drill pytest missing tests`

## 四项门

- 质量门：`review_ready + static_scan_pass + smoke_pass + candidate_boundary_clean`
- 发布门：只允许形成注册申请，不允许自动注册或激活
- 回滚证据：每个候选包必须存在 `rollback_evidence_path`
- 注册申请：写入 `.linyuanzhe/candidate_sandbox/r19/r19_release_gate_request.json`

## 边界

- 不写正式 Skill 注册表
- 不注册 Runtime Tool
- 不激活 Skill
- 不释放工具句柄
- 不调用候选工具
- 不导入或复制 v1 源码
- 不调用模型、网络、shell
- 不启动后台 loop

## 实测

- backend compileall：PASS
- frontend compileall：PASS
- pytest：18 passed
- Code-X smoke：PASS
- Runtime tool alignment smoke：PASS，139 tools / 139 usage cards
- frontend Code-X bridge smoke：PASS
- R19 release gate smoke：PASS
- no-pollution：PASS
