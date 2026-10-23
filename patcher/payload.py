"""
Minimal Android A/B OTA (CrAU) payload.bin reader.

Clean-room implementation: parses the `payload.bin` container and the
`DeltaArchiveManifest` protobuf just enough to extract a full-OTA partition
image, using only the Python standard library. Supports the operation types
used by full (non-incremental) payloads: REPLACE, REPLACE_BZ, REPLACE_XZ, ZERO.

No third-party protobuf runtime is used (some vendor payloads trip the stock
protobuf parser), so this walks the wire format directly.
"""
from __future__ import annotations

import bz2
import lzma
import struct
from dataclasses import dataclass, field
from typing import Iterator


def _read_varint(buf: bytes, i: int) -> tuple[int, int]:
    shift = 0
    val = 0
    while True:
        b = buf[i]
        i += 1
        val |= (b & 0x7F) << shift
        if not (b & 0x80):
            return val, i
        shift += 7


def _fields(buf: bytes) -> Iterator[tuple[int, int, object]]:
    """Yield (field_number, wire_type, value) for a protobuf message."""
    i, n = 0, len(buf)
    while i < n:
        tag, i = _read_varint(buf, i)
        fn, wt = tag >> 3, tag & 7
        if wt == 0:
            v, i = _read_varint(buf, i)
            yield fn, wt, v
        elif wt == 2:
            ln, i = _read_varint(buf, i)
            yield fn, wt, buf[i:i + ln]
            i += ln
        elif wt == 1:
            yield fn, wt, buf[i:i + 8]
            i += 8
        elif wt == 5:
            yield fn, wt, buf[i:i + 4]
            i += 4
        else:
            raise ValueError(f"unsupported wire type {wt} at offset {i}")


# InstallOperation.Type values (chromeos_update_engine)
REPLACE, REPLACE_BZ, REPLACE_XZ, ZERO = 0, 1, 8, 6


@dataclass
class Partition:
    name: str
    operations: list[bytes] = field(default_factory=list)
    new_size: int | None = None


class Payload:
    MAGIC = b"CrAU"

    def __init__(self, path: str):
        self.path = path
        self._fh = open(path, "rb")
        magic = self._fh.read(4)
        if magic != self.MAGIC:
            raise ValueError("not a CrAU payload (bad magic)")
        self.version = struct.unpack(">Q", self._fh.read(8))[0]
        manifest_len = struct.unpack(">Q", self._fh.read(8))[0]
        sig_len = struct.unpack(">I", self._fh.read(4))[0]
        self.block_size = 4096
        self.data_offset = self._fh.tell() + manifest_len + sig_len
        manifest = self._fh.read(manifest_len)
        self.partitions = self._parse_manifest(manifest)

    def _parse_manifest(self, man: bytes) -> list[Partition]:
        parts: list[Partition] = []
        for fn, wt, v in _fields(man):
            if fn == 3 and wt == 0:       # block_size
                self.block_size = v
            elif fn == 13 and wt == 2:    # repeated PartitionUpdate
                parts.append(self._parse_partition(v))
        return parts

    def _parse_partition(self, pb: bytes) -> Partition:
        p = Partition(name="")
        for fn, wt, v in _fields(pb):
            if fn == 1 and wt == 2:       # partition_name
                p.name = v.decode("utf-8", "replace")
            elif fn == 8 and wt == 2:     # repeated InstallOperation
                p.operations.append(v)
            elif fn == 7 and wt == 2:     # new_partition_info
                for a, _, c in _fields(v):
                    if a == 1:            # size
                        p.new_size = c
        return p

    def partition(self, name: str) -> Partition | None:
        for p in self.partitions:
            if p.name == name:
                return p
        return None

    def extract_partition(self, name: str, out_path: str) -> int:
        """Write the full image for `name` to `out_path`; return its size."""
        part = self.partition(name)
        if part is None:
            raise KeyError(f"partition {name!r} not in payload")
        bs = self.block_size
        with open(out_path, "wb") as out:
            for ob in part.operations:
                typ = data_off = data_len = None
                dst: list[tuple[int, int]] = []
                for fn, wt, v in _fields(ob):
                    if fn == 1 and wt == 0:
                        typ = v
                    elif fn == 2 and wt == 0:
                        data_off = v
                    elif fn == 3 and wt == 0:
                        data_len = v
                    elif fn == 6 and wt == 2:   # repeated Extent dst_extents
                        start = num = 0
                        for a, _, c in _fields(v):
                            if a == 1:
                                start = c
                            elif a == 2:
                                num = c
                        dst.append((start, num))
                if typ in (REPLACE, REPLACE_BZ, REPLACE_XZ):
                    self._fh.seek(self.data_offset + data_off)
                    raw = self._fh.read(data_len)
                    if typ == REPLACE_BZ:
                        data = bz2.decompress(raw)
                    elif typ == REPLACE_XZ:
                        data = lzma.decompress(raw)
                    else:
                        data = raw
                elif typ == ZERO:
                    data = b"\x00" * (sum(n for _, n in dst) * bs)
                else:
                    raise NotImplementedError(
                        f"operation type {typ} not supported (not a full OTA?)"
                    )
                pos = 0
                for start, num in dst:
                    out.seek(start * bs)
                    out.write(data[pos:pos + num * bs])
                    pos += num * bs
            out.flush()
            return out.tell()

    def close(self) -> None:
        self._fh.close()
