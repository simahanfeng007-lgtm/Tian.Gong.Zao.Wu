from __future__ import annotations

import stat
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENTRY = ROOT / "01_启动入口"


def fail(msg: str) -> None:
    raise SystemExit(f"FAIL: {msg}")


def assert_exists(path: Path) -> None:
    if not path.exists():
        fail(f"missing {path.relative_to(ROOT)}")


def has_crlf_only(path: Path) -> bool:
    data = path.read_bytes()
    return b"\n" not in data.replace(b"\r\n", b"")


def main() -> int:
    expected = [
        ENTRY / "Windows" / "01_启动临渊者桌面端_自动模式_L6710.bat",
        ENTRY / "Windows" / "02_启动临渊者桌面端_真实模型_L6710.bat",
        ENTRY / "Windows" / "03_启动临渊者桌面端_演示Mock_L6710.bat",
        ENTRY / "Windows" / "04_一键自检_L6710.bat",
        ENTRY / "macOS" / "01_启动临渊者桌面端_自动模式_L6710.command",
        ENTRY / "macOS" / "02_启动临渊者桌面端_真实模型_L6710.command",
        ENTRY / "macOS" / "03_启动临渊者桌面端_演示Mock_L6710.command",
        ENTRY / "macOS" / "04_一键自检_L6710.command",
        ENTRY / "Linux" / "01_start_desktop_auto_l6710.sh",
        ENTRY / "Linux" / "02_start_desktop_provider_l6710.sh",
        ENTRY / "Linux" / "03_start_desktop_mock_l6710.sh",
        ENTRY / "Linux" / "04_self_check_l6710.sh",
        ENTRY / "通用Python" / "START_DESKTOP_L6710.py",
        ENTRY / "通用Python" / "SELF_CHECK_L6710.py",
    ]
    for path in expected:
        assert_exists(path)

    root_scripts = [p.name for p in ROOT.iterdir() if p.is_file() and p.suffix.lower() in {".bat", ".cmd", ".ps1", ".sh", ".command", ".py"}]
    if root_scripts:
        fail(f"root still has script files: {root_scripts}")

    for bat in (ENTRY / "Windows").glob("*.bat"):
        if not has_crlf_only(bat):
            fail(f"Windows bat is not CRLF-only: {bat.relative_to(ROOT)}")

    for sh in list((ENTRY / "Linux").glob("*.sh")) + list((ENTRY / "macOS").glob("*.command")):
        mode = sh.stat().st_mode
        if not (mode & stat.S_IXUSR):
            fail(f"missing executable bit: {sh.relative_to(ROOT)}")

    result = subprocess.run(
        [sys.executable, str(ENTRY / "通用Python" / "SELF_CHECK_L6710.py")],
        cwd=str(ROOT),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=30,
    )
    if result.returncode != 0:
        fail("self-check failed:\n" + result.stdout)
    print("PASS: L6710 categorized entry layout verified")
    print("root_scripts=0")
    print("windows_entry_bat=4")
    print("macos_entry_command=4")
    print("linux_entry_sh=4")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
