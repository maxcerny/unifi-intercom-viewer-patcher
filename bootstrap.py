#!/usr/bin/env python3
"""
Download the binaries the patcher needs into a local ``tools/`` folder, so you
don't have to install a JDK / Android SDK / apktool system-wide. Especially
handy on Windows.

    python3 bootstrap.py           # fetch whatever is missing for this OS
    python3 bootstrap.py --force   # re-download everything
    python3 bootstrap.py --yes     # don't prompt about the Android SDK licence

Fetches:
  * a Temurin JDK 17  (Adoptium)            — only if no JDK is already present
  * Android build-tools  (dl.google.com)    — apksigner + zipalign
  * apktool.jar  (github.com/iBotPeaches)

Nothing is committed to the repo; ``tools/`` is git-ignored.
"""
from __future__ import annotations

import argparse
import os
import platform
import shutil
import stat
import sys
import tarfile
import urllib.request
import zipfile

ROOT = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.join(ROOT, "tools")

APKTOOL_VERSION = "2.10.0"
BUILD_TOOLS_REV = "r34"  # = build-tools 34.0.0

APKTOOL_URL = (
    f"https://github.com/iBotPeaches/Apktool/releases/download/"
    f"v{APKTOOL_VERSION}/apktool_{APKTOOL_VERSION}.jar"
)


def _os_tokens() -> tuple[str, str, str, str]:
    """Return (adoptium_os, google_os, arch, archive_ext)."""
    sysname = platform.system()
    machine = platform.machine().lower()
    arch = "aarch64" if machine in ("arm64", "aarch64") else "x64"
    if sysname == "Windows":
        return "windows", "windows", arch, "zip"
    if sysname == "Darwin":
        return "mac", "macosx", arch, "tar.gz"
    return "linux", "linux", arch, "tar.gz"


def _download(url: str, dest: str) -> None:
    print(f"    downloading {url}")
    req = urllib.request.Request(url, headers={"User-Agent": "uvp-bootstrap"})
    with urllib.request.urlopen(req) as r, open(dest, "wb") as out:
        total = int(r.headers.get("Content-Length", 0))
        done = 0
        while True:
            chunk = r.read(1 << 20)
            if not chunk:
                break
            out.write(chunk)
            done += len(chunk)
            if total:
                pct = done * 100 // total
                print(f"\r    {done >> 20} / {total >> 20} MiB ({pct}%)", end="", flush=True)
        print()


def _extract(archive: str, dest: str) -> None:
    os.makedirs(dest, exist_ok=True)
    if archive.endswith(".zip"):
        with zipfile.ZipFile(archive) as z:
            z.extractall(dest)
    else:
        with tarfile.open(archive) as t:
            t.extractall(dest)
    if os.name != "nt":
        _make_executables(dest)


def _make_executables(path: str) -> None:
    """zip extraction drops the exec bit; restore it for bin/ + extension-less files."""
    for base, _dirs, files in os.walk(path):
        in_bin = os.path.basename(base) == "bin"
        for f in files:
            if in_bin or "." not in f:
                fp = os.path.join(base, f)
                try:
                    os.chmod(fp, os.stat(fp).st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
                except OSError:
                    pass


def _have(cmd: str) -> bool:
    suffixes = (".exe", ".bat", "") if os.name == "nt" else ("",)
    return any(shutil.which(cmd + s) for s in suffixes)


def ensure_jdk(force: bool) -> None:
    jdk_dir = os.path.join(TOOLS, "jdk")
    if not force and os.path.isdir(jdk_dir) and os.listdir(jdk_dir):
        print("[*] JDK: already in tools/jdk")
        return
    if not force and _have("java") and _have("keytool"):
        print("[*] JDK: using the one already on PATH")
        return
    adop_os, _g, arch, ext = _os_tokens()
    url = (f"https://api.adoptium.net/v3/binary/latest/17/ga/"
           f"{adop_os}/{arch}/jdk/hotspot/normal/eclipse")
    print("[*] JDK 17 (Temurin / Adoptium)")
    shutil.rmtree(jdk_dir, ignore_errors=True)
    tmp = os.path.join(TOOLS, f"_jdk.{ext}")
    _download(url, tmp)
    _extract(tmp, jdk_dir)
    os.remove(tmp)


def ensure_build_tools(force: bool) -> None:
    bt_dir = os.path.join(TOOLS, "build-tools")
    if not force and os.path.isdir(bt_dir) and os.listdir(bt_dir):
        print("[*] build-tools: already in tools/build-tools")
        return
    _a, google_os, _arch, _ext = _os_tokens()
    url = f"https://dl.google.com/android/repository/build-tools_{BUILD_TOOLS_REV}-{google_os}.zip"
    print(f"[*] Android build-tools ({BUILD_TOOLS_REV})")
    shutil.rmtree(bt_dir, ignore_errors=True)
    tmp = os.path.join(TOOLS, "_bt.zip")
    _download(url, tmp)
    _extract(tmp, bt_dir)
    os.remove(tmp)


def ensure_apktool(force: bool) -> None:
    dest = os.path.join(TOOLS, f"apktool_{APKTOOL_VERSION}.jar")
    if not force and os.path.exists(dest):
        print("[*] apktool: already in tools/")
        return
    print(f"[*] apktool {APKTOOL_VERSION}")
    _download(APKTOOL_URL, dest)


def main() -> int:
    ap = argparse.ArgumentParser(description="Download the patcher's binaries into tools/.")
    ap.add_argument("--force", action="store_true", help="re-download everything")
    ap.add_argument("--yes", action="store_true", help="accept the Android SDK licence non-interactively")
    args = ap.parse_args()

    os.makedirs(TOOLS, exist_ok=True)
    print("This downloads Android build-tools from Google. By continuing you accept the")
    print("Android SDK licence (https://developer.android.com/studio/terms). apktool is")
    print("Apache-2.0; the Temurin JDK is GPLv2+CE. None of it is redistributed by this repo.")
    if not args.yes and sys.stdin.isatty():
        if input("Continue? [y/N] ").strip().lower() not in ("y", "yes"):
            print("aborted.")
            return 1
    print()

    ensure_jdk(args.force)
    ensure_build_tools(args.force)
    ensure_apktool(args.force)

    print()
    print("[*] done. You can now run:")
    print("      python3 patch.py <firmware.zip> -o IntercomViewer-portable.apk")
    return 0


if __name__ == "__main__":
    sys.exit(main())
