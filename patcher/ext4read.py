"""
Read individual files out of an ext4 image (read-only), using the pure-Python
`ext4` package. Used to pull the viewer APK and build.prop out of the extracted
`system` partition without mounting anything (works on macOS/Windows/Linux).
"""
from __future__ import annotations

import ext4


def _ftype(ft) -> int:
    if hasattr(ft, "value"):
        return ft.value
    if isinstance(ft, (bytes, bytearray)):
        return ft[0]
    return int(ft)


def open_volume(image_path: str) -> "ext4.Volume":
    return ext4.Volume(open(image_path, "rb"))


def walk(volume: "ext4.Volume"):
    """Yield (full_path, is_dir) for every entry in the volume."""
    def rec(inode, path, depth=0):
        if depth > 10:
            return
        try:
            entries = list(inode.opendir())
        except Exception:
            return
        for de, ft in entries:
            name = de.name_str if hasattr(de, "name_str") else de.name.decode("utf-8", "replace")
            if name in (".", ".."):
                continue
            full = path + "/" + name
            is_dir = _ftype(ft) == 2
            yield full, is_dir
            if is_dir:
                try:
                    yield from _walk_child(volume, full)
                except Exception:
                    pass

    def _walk_child(volume, full):
        try:
            child = volume.inode_at(full)
        except Exception:
            return
        yield from rec(child, full, depth=0)

    yield from rec(volume.root, "", 0)


def find_apks(volume: "ext4.Volume") -> list[tuple[str, int]]:
    """Return [(path, size)] for every *.apk in the image."""
    out: list[tuple[str, int]] = []
    for path, is_dir in walk(volume):
        if not is_dir and path.lower().endswith(".apk"):
            try:
                size = volume.inode_at(path).i_size
            except Exception:
                size = -1
            out.append((path, size))
    return out


def read_file(volume: "ext4.Volume", path: str, out_path: str) -> int:
    inode = volume.inode_at(path)
    total = 0
    with inode.open() as fh, open(out_path, "wb") as out:
        while True:
            chunk = fh.read(1 << 20)
            if not chunk:
                break
            out.write(chunk)
            total += len(chunk)
    return total


def read_text(volume: "ext4.Volume", path: str) -> str:
    inode = volume.inode_at(path)
    with inode.open() as fh:
        return fh.read().decode("utf-8", "replace")


def read_build_prop(volume: "ext4.Volume") -> dict[str, str]:
    """Parse /system/build.prop into a dict (empty if absent)."""
    for candidate in ("/system/build.prop", "/build.prop"):
        try:
            text = read_text(volume, candidate)
        except Exception:
            continue
        props: dict[str, str] = {}
        for line in text.splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            props[k.strip()] = v.strip()
        return props
    return {}
