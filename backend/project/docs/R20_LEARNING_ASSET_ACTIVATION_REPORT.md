# L6.70.2 R20 学习资产受控注册激活报告

## 结论

R19 只生成注册申请，不满足“学习成功后能用”。R20 已补成：

```text
学习成功 → R16 契约 → R17 沙箱对齐 → R18 候选包 → R19 发布门 → R20 受控注册激活 → learned_* 可调用 → smoke → 对齐复检
```

## 当前能力

- Runtime 基础工具数：143。
- R20 drill 激活后工具数：147。
- usage card：147 / 147 全覆盖。
- learned Tool：注册为 `learned_tool_*`，会加载并执行通过门禁的 `candidate_adapter_draft(arguments)`。
- learned Skill：注册为 `learned_skill_*`，会返回激活 Skill 卡、触发规则、使用链和下一步提示。
- active asset 可跨 RuntimeEntry 自动加载，保存在 workspace 的 `.linyuanzhe/active_assets/r20/`。

## 新增工具

- `learning_asset_activation_guide`
- `learning_asset_activation_apply`
- `learning_asset_activation_status`
- `learning_asset_activation_smoke`

## 新增命令

```text
asset-activate guide
asset-activate apply
asset-activate status
asset-activate smoke
asset-activate drill pytest missing tests
runtime-tools tool <learned_tool_name> {json_args}
```

## 激活产物

```text
.linyuanzhe/active_assets/r20/
├─ active_assets_registry.json
└─ <tool_or_skill>_<name>_<hash>/
   ├─ activation_manifest.json
   ├─ manifest.json
   ├─ rollback_evidence.json
   ├─ registration_review.json
   └─ SKILL.md / tool_adapter_draft.py
```

## 实测结果

- backend compileall：PASS
- frontend/backend compileall：PASS
- pytest：20 passed
- Code-X Runtime smoke：PASS
- R20 activation smoke：PASS
- frontend bridge smoke：PASS
- no-pollution AST scan：PASS

## 执行边界

- 允许：workspace 内 active registry 写入、`learned_tool_*` / `learned_skill_*` 动态注册、候选 adapter 受控调用、smoke 调用。
- 禁止：覆盖内置工具、写 workspace 外路径、复制/import v1、复用 v1 registry/executor/provider/self-iteration、monkey patch、后台 loop、凭证读取。
