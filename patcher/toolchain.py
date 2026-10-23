"""Locate external tools (apktool, Android build-tools, java/keytool).

Resolution order for every tool:
  1. a local ``tools/`` folder populated by ``bootstrap.py`` (self-contained,
     the easy path on Windows — no system install needed);
  2. the system ``PATH`` (apt/brew/choco installs);
  3. the Android SDK build-tools directory.

On Windows the ``.exe``/``.bat``/``.cmd`` suffixes are tried automatically.
apktool and apksigner are invoked as ``java -jar`` so a bundled JDK is enough.
"""
from __future__ import annotations

import glob
import os
import shutil
import subprocess

EXE_SUFFIXES = (".exe", ".bat", ".cmd", "") if os.name == "nt" else ("",)

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUNDLED = os.environ.get("UVP_TOOLS") or os.path.join(REPO_ROOT, "tools")


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


def _bundled(name: str) -> str | None:
    """Find an executable called `name` anywhere under the bundled tools dir."""
    if not os.path.isdir(BUNDLED):
        return None
    for suffix in EXE_SUFFIXES:
        hits = glob.glob(os.path.join(BUNDLED, "**", name + suffix), recursive=True)
        hits = [h for h in hits if os.path.isfile(h)]
        if hits:
            # pick the shortest path (top-most) for determinism
            return sorted(hits, key=len)[0]
    return None


def _bundled_file(pattern: str) -> str | None:
    if not os.path.isdir(BUNDLED):
        return None
    hits = [h for h in glob.glob(os.path.join(BUNDLED, "**", pattern), recursive=True)
            if os.path.isfile(h)]
    return sorted(hits, key=len)[0] if hits else None


# --- Java -----------------------------------------------------------------

def find_java() -> str:
    b = _bundled("java")
    if b:
        return b
    exe = _which("java")
    if exe:
        return exe
    raise ToolError(
        "java not found. Run 'python3 bootstrap.py' to download a bundled JDK, "
        "or install a JDK 17+."
    )


def find_keytool() -> str:
    b = _bundled("keytool")
    if b:
        return b
    exe = _which("keytool")
    if exe:
        return exe
    java = find_java()
    cand = _in_dir(os.path.dirname(java), "keytool")
    if cand:
        return cand
    raise ToolError("keytool not found. Run 'python3 bootstrap.py' or install a JDK.")


# --- apktool --------------------------------------------------------------

def find_apktool() -> list[str]:
    jar = _bundled_file("apktool*.jar") or (
        os.environ.get("APKTOOL_JAR") if os.environ.get("APKTOOL_JAR") and
        os.path.exists(os.environ.get("APKTOOL_JAR", "")) else None
    )
    if jar:
        return [find_java(), "-jar", jar]
    exe = _which("apktool")
    if exe:
        return [exe]
    raise ToolError(
        "apktool not found. Run 'python3 bootstrap.py' to download it, or install "
        "it (Debian: 'sudo apt install apktool'; macOS: 'brew install apktool')."
    )


# --- build-tools: zipalign (native) + apksigner (jar) ---------------------

def _sdk_build_tools_dirs() -> list[str]:
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
        if _in_dir(root, "apksigner"):
            dirs.append(root)
        for d in sorted(glob.glob(os.path.join(root, "build-tools", "*")), reverse=True):
            dirs.append(d)
    return dirs


def find_zipalign() -> str:
    b = _bundled("zipalign")
    if b:
        return b
    exe = _which("zipalign")
    if exe:
        return exe
    for d in _sdk_build_tools_dirs():
        hit = _in_dir(d, "zipalign")
        if hit:
            return hit
    raise ToolError(
        "zipalign not found. Run 'python3 bootstrap.py' to download Android "
        "build-tools, or install them (Debian: 'sudo apt install zipalign')."
    )


def find_apksigner() -> list[str]:
    """Return a command prefix for apksigner (invoked via java -jar for portability)."""
    jar = _bundled_file("apksigner.jar")
    if jar:
        return [find_java(), "-jar", jar]
    exe = _which("apksigner")
    if exe:
        return [exe]
    for d in _sdk_build_tools_dirs():
        j = os.path.join(d, "lib", "apksigner.jar")
        if os.path.exists(j):
            return [find_java(), "-jar", j]
        hit = _in_dir(d, "apksigner")
        if hit:
            return [hit]
    raise ToolError(
        "apksigner not found. Run 'python3 bootstrap.py' to download Android "
        "build-tools, or install them (Debian: 'sudo apt install apksigner')."
    )


def run(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=True, **kw)
