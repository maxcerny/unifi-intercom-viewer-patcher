"""
Ubiquiti MAC address generator.

Produces valid, globally-administered **unicast** MACs inside OUI prefixes that
are publicly registered to Ubiquiti Inc. (IEEE MA-L assignments). The patched
viewer advertises this MAC for UniFi discovery/adoption, so using a
Ubiquiti-OUI MAC makes a UniFi controller recognize the device as Ubiquiti
hardware. Each generated MAC is random in the lower 24 bits, so collisions are
effectively impossible — but use a distinct MAC per device.

This file contains no vendor code — only the public OUI prefixes (facts) and
standard-library randomness.
"""
from __future__ import annotations

import argparse
import random
import re
import sys

# Publicly registered Ubiquiti Inc. / Ubiquiti Networks OUIs (first 3 octets).
# Source: IEEE OUI registry. These are public allocations, not vendor code.
UBIQUITI_OUIS: tuple[str, ...] = (
    "00:15:6D", "00:27:22", "04:18:D6", "18:E8:29", "24:5A:4C", "24:A4:3C",
    "44:D9:E7", "60:22:32", "68:72:51", "68:D7:9A", "70:A7:41", "74:83:C2",
    "74:AC:B9", "78:45:58", "78:8A:20", "80:2A:A8", "94:2A:6F", "9C:05:D6",
    "AC:8B:A9", "B4:FB:E4", "D0:21:F9", "DC:9F:DB", "DC:FB:48", "E0:63:DA",
    "E4:38:83", "F0:9F:C2", "F4:92:BF", "FC:EC:DA",
)

_OUI_RE = re.compile(r"^[0-9A-Fa-f]{2}([:-]?)[0-9A-Fa-f]{2}\1[0-9A-Fa-f]{2}$")


def _normalize_oui(oui: str) -> tuple[int, int, int]:
    if not _OUI_RE.match(oui):
        raise ValueError(f"invalid OUI: {oui!r} (expected AA:BB:CC)")
    octets = re.split(r"[:-]", oui) if (":" in oui or "-" in oui) else \
        [oui[0:2], oui[2:4], oui[4:6]]
    b0, b1, b2 = (int(x, 16) for x in octets)
    if b0 & 0x01:
        raise ValueError("OUI first octet has the multicast bit set (not a unicast address)")
    return b0, b1, b2


def generate(oui: str | None = None, *, rng: random.Random | None = None) -> str:
    """Return a MAC like 'f4:92:bf:1a:2b:3c'. Random Ubiquiti OUI if none given."""
    rng = rng or random
    prefix = oui if oui else rng.choice(UBIQUITI_OUIS)
    b0, b1, b2 = _normalize_oui(prefix)
    tail = (rng.randint(0, 255), rng.randint(0, 255), rng.randint(0, 255))
    return ":".join(f"{x:02x}" for x in (b0, b1, b2, *tail))


def device_id(mac: str) -> str:
    """The id the viewer derives from its MAC: lowercase hex, no separators."""
    return re.sub(r"[^0-9a-fA-F]", "", mac).lower()


def format_mac(mac: str, sep: str = ":", upper: bool = False) -> str:
    hexchars = device_id(mac)
    pairs = [hexchars[i:i + 2] for i in range(0, 12, 2)]
    out = sep.join(pairs) if sep else "".join(pairs)
    return out.upper() if upper else out


def _cli() -> int:
    ap = argparse.ArgumentParser(
        description="Generate valid Ubiquiti-OUI MAC addresses for the patched viewer."
    )
    ap.add_argument("-n", "--count", type=int, default=1, help="how many to generate")
    ap.add_argument("--oui", default=None,
                    help="force a specific OUI (AA:BB:CC); default: random Ubiquiti OUI")
    ap.add_argument("--sep", default=":", choices=[":", "-", "none"],
                    help="separator ('none' for bare hex)")
    ap.add_argument("--upper", action="store_true", help="uppercase output")
    ap.add_argument("--with-id", action="store_true",
                    help="also print the viewer device id (MAC without separators)")
    ap.add_argument("--list-ouis", action="store_true", help="list the Ubiquiti OUIs and exit")
    ap.add_argument("--seed", type=int, default=None, help="RNG seed (reproducible)")
    args = ap.parse_args()

    if args.list_ouis:
        for o in UBIQUITI_OUIS:
            print(o)
        return 0

    rng = random.Random(args.seed) if args.seed is not None else random
    sep = "" if args.sep == "none" else args.sep
    try:
        macs = [generate(args.oui, rng=rng) for _ in range(max(1, args.count))]
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    for mac in macs:
        line = format_mac(mac, sep=sep, upper=args.upper)
        if args.with_id:
            line += f"\tid={device_id(mac)}"
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
