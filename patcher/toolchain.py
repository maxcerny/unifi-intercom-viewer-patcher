"""Locate external tools (apktool, Android build-tools, java/keytool)."""
from __future__ import annotations

import glob
import os
import shutil
import subprocess


class ToolError(RuntimeError):
    pass


def _which(name: str) -> str | None:
    return shutil.which(name)


def find_apktool() -> list[str]:
    exe = _which("apktool")
    if exe:
        return [exe]
    jar = os.environ.get("APKTOOL_JAR")
    if jar and os.path.exists(jar):
        return [find_java(), "-jar", jar]
    raise ToolError("apktool not found (install it or set APKTOOL_JAR=/path/apktool.jar)")


def find_java() -> str:
    exe = _which("java")
    if not exe:
        raise ToolError("java not found on PATH")
    return exe


def find_build_tools() -> str:
    """Return a build-tools dir containing apksigner + zipalign."""
    env = os.environ.get("ANDROID_BUILD_TOOLS")
    if env and os.path.exists(os.path.join(env, "apksigner")):
        return env
    roots = [
        os.environ.get("ANDROID_SDK_ROOT", ""),
        os.environ.get("ANDROID_HOME", ""),
        os.path.expanduser("~/Library/Android/sdk"),
        os.path.expanduser("~/Android/Sdk"),
        os.path.expanduser("~/AppData/Local/Android/Sdk"),
    ]
    best = None
    for root in roots:
        if not root:
            continue
        for d in glob.glob(os.path.join(root, "build-tools", "*")):
            if os.path.exists(os.path.join(d, "apksigner")) or os.path.exists(
                os.path.join(d, "apksigner.bat")
            ):
                if best is None or os.path.basename(d) > os.path.basename(best):
                    best = d
    if not best:
        raise ToolError(
            "Android build-tools not found. Install the SDK build-tools, or set "
            "ANDROID_BUILD_TOOLS=/path/to/build-tools/<ver>"
        )
    return best


def run(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=True, **kw)
