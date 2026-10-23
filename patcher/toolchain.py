"""Locate external tools (apktool, Android build-tools, java/keytool).

Cross-platform: resolves executables on PATH first (so apt/brew/choco installs
on Debian/Linux/Windows just work), then falls back to the Android SDK
build-tools directory, trying the platform's executable suffixes.
"""
from __future__ import annotations

import glob
import os
import shutil
import subprocess

# Executable name suffixes to try, in order, per platform.
EXE_SUFFIXES = (".exe", ".bat", ".cmd", "") if os.name == "nt" else ("",)


class ToolError(RuntimeError):
    pass


def _which(name: str) -> str | None:
    for suffix in EXE_SUFFIXES:
        hit = shutil.which(name + suffix)
        if hit:
            return hit
    return None


def _in_dir(directory: str, name: str) -> str | None:
    for suffix in EXE_SUFFIXES:
        cand = os.path.join(directory, name + suffix)
        if os.path.exists(cand):
            return cand
    return None


def find_apktool() -> list[str]:
    exe = _which("apktool")
    if exe:
        return [exe]
    jar = os.environ.get("APKTOOL_JAR")
    if jar and os.path.exists(jar):
        return [find_java(), "-jar", jar]
    raise ToolError(
        "apktool not found. Install it (Debian: 'sudo apt install apktool'; "
        "macOS: 'brew install apktool'; Windows: 'choco install apktool') "
        "or set APKTOOL_JAR=/path/to/apktool.jar"
    )


def find_java() -> str:
    exe = _which("java")
    if not exe:
        raise ToolError("java not found on PATH (install a JDK 17+)")
    return exe


def _build_tools_dirs() -> list[str]:
    roots = [
        os.environ.get("ANDROID_BUILD_TOOLS", ""),
        os.environ.get("ANDROID_SDK_ROOT", ""),
        os.environ.get("ANDROID_HOME", ""),
        os.path.expanduser("~/Library/Android/sdk"),
        os.path.expanduser("~/Android/Sdk"),
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "Android", "Sdk"),
    ]
    dirs: list[str] = []
    for root in roots:
        if not root:
            continue
        if _in_dir(root, "apksigner"):          # ANDROID_BUILD_TOOLS points straight at it
            dirs.append(root)
        for d in sorted(glob.glob(os.path.join(root, "build-tools", "*")), reverse=True):
            dirs.append(d)
    return dirs


def find_tool(name: str) -> str:
    """Resolve a build-tool (apksigner/zipalign/aapt2) on PATH or in the SDK."""
    exe = _which(name)
    if exe:
        return exe
    for d in _build_tools_dirs():
        hit = _in_dir(d, name)
        if hit:
            return hit
    raise ToolError(
        f"'{name}' not found. Install Android build-tools "
        "(Debian: 'sudo apt install {0}'; or via the SDK: "
        "'sdkmanager \"build-tools;34.0.0\"'), put it on PATH, "
        "or set ANDROID_BUILD_TOOLS=/path/to/build-tools/<ver>".format(name)
    )


def find_keytool() -> str:
    exe = _which("keytool")
    if exe:
        return exe
    # keytool ships next to java in the JDK
    java = find_java()
    cand = _in_dir(os.path.dirname(java), "keytool")
    if cand:
        return cand
    raise ToolError("keytool not found (install a JDK)")


def run(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=True, **kw)
