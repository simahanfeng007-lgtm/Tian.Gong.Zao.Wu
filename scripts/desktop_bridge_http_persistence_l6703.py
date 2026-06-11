from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BRIDGE = ROOT / "desktop" / "linyuanzhe_local_runtime_bridge_l671.py"
URL_RE = re.compile(r"LINYUANZHE_LOCAL_RUNTIME_URL=(http://[^\s]+)")


def start_bridge(env: dict[str, str]) -> tuple[subprocess.Popen[str], str]:
    proc = subprocess.Popen([sys.executable, str(BRIDGE), "--host", "127.0.0.1", "--port", "0", "--backend-mode", "provider"], cwd=str(ROOT), env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=1)
    assert proc.stdout is not None
    deadline = time.time() + 10
    lines: list[str] = []
    while time.time() < deadline:
        line = proc.stdout.readline()
        if line:
            lines.append(line.rstrip())
            m = URL_RE.search(line)
            if m:
                return proc, m.group(1)
        if proc.poll() is not None:
            break
    raise RuntimeError("bridge not started: " + "\n".join(lines))


def json_request(url: str, path: str, payload: dict | None = None) -> dict:
    data = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url + path, data=data, method="POST" if payload is not None else "GET", headers={"Content-Type": "application/json; charset=utf-8"})
    with urllib.request.urlopen(req, timeout=5) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        cfg = Path(td) / "provider_config.json"
        env = os.environ.copy()
        env["LINYUANZHE_PROVIDER_CONFIG_FILE"] = str(cfg)
        env.pop("LINYUANZHE_PROVIDER", None)
        env.pop("LINYUANZHE_MODEL", None)
        env.pop("LINYUANZHE_PROVIDER_BASE", None)
        env.pop("LINYUANZHE_PROVIDER_KEY", None)
        proc1, url1 = start_bridge(env)
        try:
            posted = json_request(url1, "/settings/provider", {"provider": "deepseek", "model": "deepseek-reasoner", "base_url": "https://api.deepseek.com", "api_key": "local_secret_http_value_123456"})
            got1 = json_request(url1, "/settings/provider")
        finally:
            proc1.terminate(); proc1.wait(timeout=5)
        proc2, url2 = start_bridge(env)
        try:
            got2 = json_request(url2, "/settings/provider")
        finally:
            proc2.terminate(); proc2.wait(timeout=5)
        assert got1.get("api_key_configured") is True
        assert got2.get("api_key_configured") is True
        assert "local_secret_http" not in json.dumps(got2, ensure_ascii=False)
        out = {"ok": True, "posted_status": posted.get("status"), "first_digest": got1.get("api_key_digest"), "second_digest": got2.get("api_key_digest"), "persisted": got2.get("runtime_credential_persisted")}
        report = ROOT / "reports" / "desktop_bridge_http_persistence_l6703.json"
        report.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0

if __name__ == "__main__":
    raise SystemExit(main())
