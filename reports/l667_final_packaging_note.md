# L6.67 final packaging note

- Final package root: FE01 STEP28 / L6.67 多任务 Session 管理器 RC 前置总包。
- Added multi-task Session Manager projections and Runtime request envelopes.
- Fixed SSE file authorization HookBus stage argument mismatch from L6.66/L6.65 chain.
- Fixed Runtime contract server connector registry projection helper mismatch (`from_manifests` / `to_public_dict`) to use available sanitized dataclass projections.
- No backend core main-chain mutation.
- Real Runtime smoke remains blocked until `LINYUANZHE_RUNTIME_URL` is provided.
