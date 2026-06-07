# L6.67 阻断项报告

## 阻断项

- `real Runtime instance smoke not executed`

## 级别

P1 / RC 阻断项。

## 说明

本轮所有本地 contract-server、compileall、scan、Session Manager preflight 均通过，但没有真实 Runtime 地址，无法执行真实联调。

## 禁止

不得以 contract-server 结果替代真实 Runtime 联调结果。
不得将 `ready_for_combine` 改为 true。
