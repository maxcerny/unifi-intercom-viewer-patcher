#!/usr/bin/env python3
"""
Ubiquiti MAC generator — standalone entry point.

    python3 genmac.py                 # one random Ubiquiti-OUI MAC
    python3 genmac.py -n 5 --with-id  # five, with the viewer device id
    python3 genmac.py --oui FC:EC:DA --sep -   # a specific OUI, dash-separated
    python3 genmac.py --list-ouis     # show the Ubiquiti OUIs used

Feed the result to the patcher:  python3 patch.py fw.zip --mac <generated>
"""
from patcher.macgen import _cli

if __name__ == "__main__":
    raise SystemExit(_cli())
