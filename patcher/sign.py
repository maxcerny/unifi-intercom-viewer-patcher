"""zipalign + apksigner, with a throwaway keystore generated on demand."""
from __future__ import annotations

import os

from . import toolchain


def ensure_keystore(path: str, storepass: str = "android") -> str:
    if os.path.exists(path):
        return path
    keytool = os.path.join(os.path.dirname(toolchain.find_java()), "keytool")
    if not os.path.exists(keytool):
        keytool = "keytool"
    toolchain.run([
        keytool, "-genkeypair", "-v",
        "-keystore", path, "-alias", "key",
        "-keyalg", "RSA", "-keysize", "2048", "-validity", "10000",
        "-storepass", storepass, "-keypass", storepass,
        "-dname", "CN=IntercomViewer Portable",
    ])
    return path


def align_and_sign(unsigned: str, out: str, keystore: str, storepass: str = "android") -> None:
    bt = toolchain.find_build_tools()
    zipalign = os.path.join(bt, "zipalign")
    apksigner = os.path.join(bt, "apksigner")
    aligned = unsigned + ".aligned"
    toolchain.run([zipalign, "-f", "-p", "4", unsigned, aligned])
    toolchain.run([
        apksigner, "sign",
        "--ks", keystore, "--ks-pass", f"pass:{storepass}", "--key-pass", f"pass:{storepass}",
        "--out", out, aligned,
    ])
    toolchain.run([apksigner, "verify", out])
    try:
        os.remove(aligned)
    except OSError:
        pass
