from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

SCHEMA = "tiangong.l67217.dataup_signature_guard_smoke.v1"


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _write_unsigned_package(path: Path, manifest_bytes: bytes, payload: bytes) -> None:
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("dataup_manifest.json", manifest_bytes)
        zf.writestr("payload/docs/dataup_signature_guard_smoke.txt", payload)


def _make_manifest(payload: bytes) -> bytes:
    data = {
        "schema": "tiangong.dataup.manifest.v1",
        "package_id": "l67217-signature-smoke",
        "version": "FE01 STEP31Q / L6.72.17",
        "target_min_version": "FE01 STEP31Q / L6.72.16",
        "channel": "community",
        "risk_level": "A4",
        "payload_prefix": "payload/",
        "files": [{"path": "docs/dataup_signature_guard_smoke.txt", "sha256": _sha(payload), "mode": "upsert"}],
    }
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(root / "scripts"))
    import dataup_update_core_l6717 as core

    payload = b"l67217 signature guard smoke\n"
    manifest_bytes = _make_manifest(payload)

    with tempfile.TemporaryDirectory(prefix="l67217_dataup_sig_") as td:
        tmp = Path(td)
        unsigned = tmp / "unsigned.zip"
        _write_unsigned_package(unsigned, manifest_bytes, payload)
        unsigned_plan = core.plan_package(unsigned, root)
        assert not unsigned_plan.ok, "unsigned package must be blocked"
        assert any("signature verification failed" in x for x in unsigned_plan.blocked), unsigned_plan.blocked

        try:
            core._download_json("http://example.invalid/latest.json")
        except core.DataUpError:
            https_guard = True
        else:
            https_guard = False
        assert https_guard, "non-HTTPS latest URL must be blocked"

        signed_ok = False
        openssl = shutil.which("openssl")
        if openssl:
            priv = tmp / "ed25519_private.pem"
            pub = tmp / "ed25519_public.pem"
            manifest_path = tmp / "manifest.json"
            sig = tmp / "dataup_manifest.sig"
            manifest_path.write_bytes(manifest_bytes)
            subprocess.run([openssl, "genpkey", "-algorithm", "ED25519", "-out", str(priv)], check=True, capture_output=True)
            subprocess.run([openssl, "pkey", "-in", str(priv), "-pubout", "-out", str(pub)], check=True, capture_output=True)
            subprocess.run([openssl, "pkeyutl", "-sign", "-inkey", str(priv), "-rawin", "-in", str(manifest_path), "-out", str(sig)], check=True, capture_output=True)
            signed = tmp / "signed.zip"
            with zipfile.ZipFile(signed, "w", zipfile.ZIP_DEFLATED) as zf:
                zf.writestr("dataup_manifest.json", manifest_bytes)
                zf.writestr("dataup_manifest.sig", sig.read_bytes())
                zf.writestr("payload/docs/dataup_signature_guard_smoke.txt", payload)
            old = os.environ.get(core.DATAUP_PUBLIC_KEY_ENV)
            os.environ[core.DATAUP_PUBLIC_KEY_ENV] = str(pub)
            try:
                signed_plan = core.plan_package(signed, root)
            finally:
                if old is None:
                    os.environ.pop(core.DATAUP_PUBLIC_KEY_ENV, None)
                else:
                    os.environ[core.DATAUP_PUBLIC_KEY_ENV] = old
            assert signed_plan.ok, signed_plan.blocked
            assert signed_plan.signature_verified, signed_plan.signature_note
            signed_ok = True

    print({"schema": SCHEMA, "status": "PASS", "unsigned_blocked": True, "https_guard": True, "signed_verify_smoke": signed_ok})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
