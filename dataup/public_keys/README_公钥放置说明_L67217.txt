DataUp Ed25519 公钥放置说明（L6.73.8）

默认路径：dataup/public_keys/dataup_ed25519_public_key.pem
环境变量覆盖：LINYUANZHE_DATAUP_PUBLIC_KEY

L6.73.8 起，DataUp 更新包必须包含 dataup_manifest.json 的 detached signature：
- dataup_manifest.sig
- 或 dataup_signature.sig
- 或 manifest.sig

无签名、签名错误、公钥缺失、sha256 错误均禁止 apply。
