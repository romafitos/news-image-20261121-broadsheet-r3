#!/usr/bin/env python3
"""Deliver the rendered front page to the harness output folder.

This is the entry point for the news-image-20261121 round 3 submission.
The page itself lives in ``entry.png`` next to this script; the script's
only job is to hand that file over, untouched, after proving it is a
genuine 1024x1024 PNG that fits the 1 MiB size cap.

The destination folder comes from the ``MAKEFUN_OUTPUT_DIR`` environment
variable, which the harness sets before it runs this script. Nothing is
downloaded, nothing is rendered here, and no third-party package is used:
the PNG dimensions are read straight out of the file header with the
standard library, so the script runs on a bare Python 3 install.
"""

import os
import struct
import sys
from pathlib import Path

# The bounty caps every entry file at one mebibyte.
MAX_BYTES = 1024 * 1024

# The front page is rendered at exactly this size, no exceptions.
EXPECTED_WIDTH = 1024
EXPECTED_HEIGHT = 1024

# The first eight bytes of every PNG file, fixed by the format.
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"

# The IHDR chunk carries the width and height as two big-endian uint32s.
# Layout of the bytes we read: 8 magic + 4 length + 4 type ("IHDR") +
# 4 width + 4 height = 24 bytes; we read a little extra so a truncated
# file fails the length check instead of the unpack.
HEADER_BYTES = 33


def read_png_size(path):
    """Return ``(width, height)`` of a PNG file from its IHDR chunk.

    Raises ``ValueError`` when the file is not a PNG at all, when it is
    too short to hold a header, or when its first chunk is not IHDR.
    Raises ``OSError`` when the file cannot be opened or read.
    """
    with open(path, "rb") as handle:
        header = handle.read(HEADER_BYTES)
    if len(header) < HEADER_BYTES:
        raise ValueError(f"{path}: file is too short to be a PNG")
    if header[:8] != PNG_MAGIC:
        raise ValueError(f"{path}: missing PNG signature")
    if header[12:16] != b"IHDR":
        raise ValueError(f"{path}: first chunk is not IHDR")
    width, height = struct.unpack(">II", header[16:24])
    return width, height


def check_entry(path):
    """Check ``path`` against the bounty limits; return its size in bytes.

    The file must exist, must fit inside ``MAX_BYTES``, and must measure
    exactly ``EXPECTED_WIDTH`` by ``EXPECTED_HEIGHT`` pixels. Anything
    else is a hard error, raised as ``ValueError`` (bad content) or
    ``OSError`` (unreadable file) so the caller can report it and stop.
    """
    size = path.stat().st_size
    if size > MAX_BYTES:
        raise ValueError(
            f"{path}: {size} bytes, over the {MAX_BYTES} byte limit"
        )
    width, height = read_png_size(path)
    if width != EXPECTED_WIDTH or height != EXPECTED_HEIGHT:
        raise ValueError(
            f"{path}: {width}x{height}, "
            f"expected {EXPECTED_WIDTH}x{EXPECTED_HEIGHT}"
        )
    return size


def fail(message):
    """Print ``message`` to stderr and return the failure exit code."""
    print(f"error: {message}", file=sys.stderr)
    return 1


def main():
    """Copy the verified front page into ``$MAKEFUN_OUTPUT_DIR``."""
    output_dir = os.environ.get("MAKEFUN_OUTPUT_DIR")
    if not output_dir:
        return fail("MAKEFUN_OUTPUT_DIR is not set")

    # The image sits beside this script, wherever the repo was checked out.
    source = Path(__file__).resolve().parent / "entry.png"

    # Verify first: never hand over a file that breaks the bounty rules.
    try:
        size = check_entry(source)
    except (OSError, ValueError) as exc:
        return fail(str(exc))

    target = Path(output_dir) / "entry.png"
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())
    except OSError as exc:
        return fail(f"cannot write {target}: {exc}")

    print(f"wrote {target} ({size} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
