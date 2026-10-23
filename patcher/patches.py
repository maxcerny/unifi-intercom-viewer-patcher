"""
Patch definitions for the UniFi Access Intercom Viewer APK.

These operate on an apktool-decoded tree of *the user's own* extracted APK. This
module contains NO Ubiquiti code: the injected smali below is ordinary Android
framework code (window flags, WifiManager.MulticastLock, immersive mode) written
for this project; identity values are read from the user's firmware at run time.
Each patch locates an anchor and fails loudly if the target structure is not
found, so a mismatched firmware never yields a silently-broken APK.
"""
from __future__ import annotations

import glob
import os
import re


class PatchError(RuntimeError):
    pass


def _find_smali(decoded: str, rel: str) -> str:
    hits = glob.glob(os.path.join(decoded, "smali*", rel))
    if not hits:
        raise PatchError(f"smali not found: {rel}")
    return hits[0]


def _read(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _write(path: str, text: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def _replace_once(text: str, old: str, new: str, what: str) -> str:
    if old not in text:
        raise PatchError(f"anchor not found: {what}")
    return text.replace(old, new, 1)


# --- 1. Manifest: make it installable as a normal app ----------------------

def patch_manifest(decoded: str) -> None:
    path = os.path.join(decoded, "AndroidManifest.xml")
    text = _read(path)
    before = text
    for attr in (
        r'\s+android:sharedUserId="[^"]*"',
        r'\s+android:sharedUserMaxSdkVersion="[^"]*"',
        r'\s+android:persistent="true"',
    ):
        text = re.sub(attr, "", text)
    if text == before:
        raise PatchError("manifest: nothing removed (already patched?)")
    _write(path, text)


# --- 2. Device identity for UniFi discovery/adoption -----------------------

def _early_return_string(path: str, method_sig: str, value: str, what: str) -> None:
    text = _read(path)
    pat = re.compile(
        r"(\.method[^\n]*\b" + re.escape(method_sig) + r"\n\s*\.locals \d+\n)"
    )
    m = pat.search(text)
    if not m:
        raise PatchError(f"method not found: {what}")
    inject = f'    const-string v0, "{value}"\n\n    return-object v0\n\n'
    text = text[: m.end()] + inject + text[m.end():]
    _write(path, text)


def patch_mac(decoded: str, mac: str) -> None:
    """Advertise a fixed MAC instead of the off-device placeholder."""
    path = _find_smali(decoded, os.path.join("ce", "g.smali"))
    _early_return_string(path, "d()Ljava/lang/String;", mac.lower(), "ce/g.d (MAC)")


def patch_identity(decoded: str, fw_id: str, fw_version: str) -> None:
    """Report the real firmware id/version (read from the user's firmware)."""
    path = _find_smali(decoded, os.path.join("ce", "e$a.smali"))
    _early_return_string(path, "f()Ljava/lang/String;", fw_id, "ce/e$a.f (firmware id)")
    _early_return_string(path, "i()Ljava/lang/String;", fw_version, "ce/e$a.i (fw version)")
    _early_return_string(path, "j()Ljava/lang/String;", fw_version, "ce/e$a.j (version)")


def patch_wlan0(decoded: str) -> None:
    """Join the discovery multicast on wlan0 (phones have no eth0)."""
    path = _find_smali(
        decoded,
        os.path.join("com", "ui", "da", "viewer", "app", "cmpts", "discovery",
                     "ResponderImpl.smali"),
    )
    text = _read(path)
    if '"eth0"' not in text:
        raise PatchError("ResponderImpl: eth0 anchor not found")
    _write(path, text.replace('"eth0"', '"wlan0"'))


def patch_multicast_lock(decoded: str) -> None:
    """Hold a Wi-Fi MulticastLock so inbound discovery multicast is delivered."""
    path = _find_smali(decoded, os.path.join("com", "ui", "da", "viewer", "app", "App.smali"))
    text = _read(path)
    # add a static field to retain the lock
    text = _replace_once(
        text,
        "# static fields\n",
        "# static fields\n"
        ".field public static mcastLock:Landroid/net/wifi/WifiManager$MulticastLock;\n\n",
        "App: static fields header",
    )
    # acquire in onCreate, right after the singleton is stored
    anchor = "    sput-object p0, Lcom/ui/da/viewer/app/App;->X:Lcom/ui/da/viewer/app/App;\n"
    inject = (
        '    const-string v6, "wifi"\n\n'
        "    invoke-virtual {p0, v6}, Landroid/content/Context;->getSystemService(Ljava/lang/String;)Ljava/lang/Object;\n\n"
        "    move-result-object v6\n\n"
        "    check-cast v6, Landroid/net/wifi/WifiManager;\n\n"
        '    const-string v7, "uv-mcast"\n\n'
        "    invoke-virtual {v6, v7}, Landroid/net/wifi/WifiManager;->createMulticastLock(Ljava/lang/String;)Landroid/net/wifi/WifiManager$MulticastLock;\n\n"
        "    move-result-object v6\n\n"
        "    sput-object v6, Lcom/ui/da/viewer/app/App;->mcastLock:Landroid/net/wifi/WifiManager$MulticastLock;\n\n"
        "    invoke-virtual {v6}, Landroid/net/wifi/WifiManager$MulticastLock;->acquire()V\n\n"
    )
    text = _replace_once(text, anchor, anchor + inject, "App.onCreate singleton store")
    _write(path, text)


# --- 3. Device optimizations: keep screen on + immersive fullscreen --------

def patch_screen(decoded: str) -> None:
    path = _find_smali(decoded, os.path.join("com", "ui", "da", "viewer", "app", "MainActivity.smali"))
    text = _read(path)
    anchor = (
        "    invoke-super {p0, p1}, Lcom/ui/da/viewer/app/Hilt_MainActivity;->"
        "onCreate(Landroid/os/Bundle;)V\n"
    )
    inject = (
        "\n    invoke-virtual {p0}, Landroid/app/Activity;->getWindow()Landroid/view/Window;\n\n"
        "    move-result-object v0\n\n"
        "    const/16 v1, 0x80\n\n"
        "    invoke-virtual {v0, v1}, Landroid/view/Window;->addFlags(I)V\n\n"
        "    invoke-virtual {v0}, Landroid/view/Window;->getDecorView()Landroid/view/View;\n\n"
        "    sget v1, Landroid/os/Build$VERSION;->SDK_INT:I\n\n"
        "    const/16 v2, 0x1e\n\n"
        "    if-lt v1, v2, :uvp_legacy\n\n"
        "    const/4 v1, 0x0\n\n"
        "    invoke-virtual {v0, v1}, Landroid/view/Window;->setDecorFitsSystemWindows(Z)V\n\n"
        "    invoke-virtual {v0}, Landroid/view/Window;->getInsetsController()Landroid/view/WindowInsetsController;\n\n"
        "    move-result-object v1\n\n"
        "    if-eqz v1, :uvp_done\n\n"
        "    invoke-static {}, Landroid/view/WindowInsets$Type;->systemBars()I\n\n"
        "    move-result v2\n\n"
        "    invoke-interface {v1, v2}, Landroid/view/WindowInsetsController;->hide(I)V\n\n"
        "    const/4 v2, 0x2\n\n"
        "    invoke-interface {v1, v2}, Landroid/view/WindowInsetsController;->setSystemBarsBehavior(I)V\n\n"
        "    goto :uvp_done\n\n"
        "    :uvp_legacy\n\n"
        "    invoke-virtual {v0}, Landroid/view/Window;->getDecorView()Landroid/view/View;\n\n"
        "    move-result-object v1\n\n"
        "    const/16 v2, 0x1706\n\n"
        "    invoke-virtual {v1, v2}, Landroid/view/View;->setSystemUiVisibility(I)V\n\n"
        "    :uvp_done\n"
    )
    text = _replace_once(text, anchor, anchor + inject, "MainActivity.onCreate super call")
    _write(path, text)


# --- 4. Fill the letterbox with a gradient (keep live-view aspect) ---------

GRADIENT_DRAWABLE = """<?xml version="1.0" encoding="utf-8"?>
<shape xmlns:android="http://schemas.android.com/apk/res/android" android:shape="rectangle">
    <gradient
        android:type="linear"
        android:angle="270"
        android:startColor="#2A3A4D"
        android:centerColor="#141C26"
        android:endColor="#05080C" />
</shape>
"""


def patch_gradient(decoded: str) -> None:
    # drop in the gradient drawable
    draw_dir = os.path.join(decoded, "res", "drawable")
    os.makedirs(draw_dir, exist_ok=True)
    _write(os.path.join(draw_dir, "viewport_gradient.xml"), GRADIENT_DRAWABLE)

    # set it as the root layout background
    layout = os.path.join(decoded, "res", "layout", "layout_main.xml")
    text = _read(layout)
    if "viewport_gradient" not in text:
        text = _replace_once(
            text,
            '<FrameLayout android:layout_width="match_parent" android:layout_height="match_parent"',
            '<FrameLayout android:layout_width="match_parent" android:layout_height="match_parent" '
            'android:background="@drawable/viewport_gradient"',
            "layout_main FrameLayout",
        )
        _write(layout, text)

    # make the root Surface transparent so the gradient shows through
    main = _find_smali(decoded, os.path.join("com", "ui", "da", "viewer", "app", "MainActivity.smali"))
    text = _read(main)
    text = _replace_once(
        text,
        "    move-wide v5, v6\n\n    .line 94\n    const-wide/16 v7, 0x0",
        "    const-wide/16 v5, 0x0\n\n    .line 94\n    const-wide/16 v7, 0x0",
        "MainActivity.Z0 Surface color",
    )
    _write(main, text)
