#!/usr/bin/env python3
"""
UniFi Access Intercom Viewer — firmware patcher.

Takes the *official firmware OTA zip that you already possess*, extracts the
viewer APK from it, patches it so it installs/runs/adopts on an ordinary
non-rooted Android phone, and re-signs it.

This tool ships NO Ubiquiti code or binaries. It only transforms files it
extracts from your own firmware at run time. You are responsible for your right
to use that firmware.

Usage:
    python3 patch.py <firmware.zip> [-o OUTPUT.apk] [options]
"""
from __future__ import annotations

import argparse
import os
import random
import shutil
import sys
import tempfile
import zipfile

from patcher import ext4read, patches, sign, toolchain
from patcher.payload import Payload

UBIQUITI_OUI = "f4:92:bf"  # Ubiquiti Networks Inc. OUI (public IEEE registration)


def log(msg: str) -> None:
    print(f"[*] {msg}", flush=True)


def random_mac() -> str:
    tail = ":".join(f"{random.randint(0, 255):02x}" for _ in range(3))
    return f"{UBIQUITI_OUI}:{tail}"


def extract_payload(zip_path: str, work: str) -> str:
    log(f"reading OTA zip: {os.path.basename(zip_path)}")
    with zipfile.ZipFile(zip_path) as z:
        names = z.namelist()
        if "payload.bin" not in names:
            raise SystemExit("error: payload.bin not found in zip (is this an A/B OTA?)")
        out = os.path.join(work, "payload.bin")
        with z.open("payload.bin") as src, open(out, "wb") as dst:
            shutil.copyfileobj(src, dst, length=1 << 20)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Patch the UniFi Intercom Viewer firmware APK.")
    ap.add_argument("firmware", help="official firmware OTA .zip (you must own it)")
    ap.add_argument("-o", "--output", default="IntercomViewer-portable.apk",
                    help="output APK path (default: ./IntercomViewer-portable.apk)")
    ap.add_argument("--mac", default=None,
                    help="MAC to advertise (default: random Ubiquiti-OUI MAC). "
                         "Use a unique one per device.")
    ap.add_argument("--keystore", default=None,
                    help="signing keystore (default: ./portable.keystore, created if absent). "
                         "Reuse the same keystore to upgrade without a data wipe.")
    ap.add_argument("--partition", default="system", help="partition holding the APK")
    ap.add_argument("--apk-path", default=None,
                    help="path of the APK inside the image (default: auto-detect by package)")
    ap.add_argument("--package", default="com.ui.da.viewer.app",
                    help="package name to locate when auto-detecting the APK")
    ap.add_argument("--no-adopt", action="store_true",
                    help="skip the discovery/adoption identity patches")
    ap.add_argument("--no-optimize", action="store_true",
                    help="skip fullscreen / keep-screen-on / gradient patches")
    ap.add_argument("--keep-work", action="store_true", help="keep the temp work dir")
    ap.add_argument("--work", default=None, help="work directory (default: a temp dir)")
    args = ap.parse_args()

    if not os.path.exists(args.firmware):
        raise SystemExit(f"error: firmware not found: {args.firmware}")

    # fail fast if the toolchain is missing
    apktool = toolchain.find_apktool()
    toolchain.find_build_tools()

    work = args.work or tempfile.mkdtemp(prefix="uvp-")
    os.makedirs(work, exist_ok=True)
    mac = args.mac or random_mac()

    try:
        payload_bin = extract_payload(args.firmware, work)

        log("parsing payload + extracting system image")
        pl = Payload(payload_bin)
        system_img = os.path.join(work, f"{args.partition}.img")
        size = pl.extract_partition(args.partition, system_img)
        pl.close()
        log(f"  {args.partition}.img: {size:,} bytes")

        log("opening ext4 image")
        vol = ext4read.open_volume(system_img)

        apk_in_image = args.apk_path
        if not apk_in_image:
            log("locating viewer APK")
            apks = ext4read.find_apks(vol)
            cands = [p for p, _ in apks if "DoorAccess" in p or "Intercom" in p or "viewer" in p.lower()]
            if not cands:
                # fall back to the largest priv-app apk
                cands = [p for p, _ in sorted(apks, key=lambda t: -t[1]) if "priv-app" in p]
            if not cands:
                raise SystemExit("error: could not locate the viewer APK; pass --apk-path")
            apk_in_image = cands[0]
        log(f"  {apk_in_image}")

        apk_orig = os.path.join(work, "viewer-original.apk")
        ext4read.read_file(vol, apk_in_image, apk_orig)

        props = ext4read.read_build_prop(vol)
        fw_id = props.get("ro.ubnt.firmware.id", "")
        fw_version = props.get("ro.ubnt.firmware.version", "")
        fw_product = props.get("ro.ubnt.firmware.product", "")
        log(f"  firmware: product={fw_product or '?'} version={fw_version or '?'}")

        log("decoding APK (apktool)")
        decoded = os.path.join(work, "decoded")
        shutil.rmtree(decoded, ignore_errors=True)
        toolchain.run(apktool + ["d", "-f", apk_orig, "-o", decoded],
                      stdout=open(os.path.join(work, "apktool-d.log"), "w"))

        log("applying patches")
        patches.patch_manifest(decoded)
        log("  + installable manifest (dropped system shared-uid / persistent)")

        if not args.no_adopt:
            patches.patch_mac(decoded, mac)
            patches.patch_wlan0(decoded)
            patches.patch_multicast_lock(decoded)
            if fw_id and fw_version:
                patches.patch_identity(decoded, fw_id, fw_version)
                log(f"  + adoption identity (MAC {mac}, fw {fw_version})")
            else:
                log(f"  + adoption identity (MAC {mac}; firmware id/version not in build.prop)")

        if not args.no_optimize:
            patches.patch_screen(decoded)
            patches.patch_gradient(decoded)
            log("  + fullscreen + keep-screen-on + gradient background")

        log("rebuilding APK (apktool)")
        unsigned = os.path.join(work, "viewer-unsigned.apk")
        toolchain.run(apktool + ["b", decoded, "-o", unsigned],
                      stdout=open(os.path.join(work, "apktool-b.log"), "w"))

        log("signing")
        keystore = args.keystore or os.path.abspath("portable.keystore")
        sign.ensure_keystore(keystore)
        sign.align_and_sign(unsigned, os.path.abspath(args.output), keystore)

        log(f"done -> {args.output}")
        log(f"install with:  adb install -r -g {args.output}")
        print()
        print("    This device advertises MAC", mac)
        print("    Adopt it from UniFi Access on the SAME subnet/VLAN as the phone.")
        return 0
    finally:
        if not args.keep_work and not args.work:
            shutil.rmtree(work, ignore_errors=True)
        else:
            log(f"work dir kept: {work}")


if __name__ == "__main__":
    sys.exit(main())
