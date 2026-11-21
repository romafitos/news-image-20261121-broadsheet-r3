#!/usr/bin/env python3
"""Entry point for the news-image-20261121 r3 front page.

Copies the pre-rendered ``entry.png`` (1024x1024, built from
``frontpage.html`` with headless Chromium) into the directory given by
``MAKEFUN_OUTPUT_DIR``.

Stdlib only. No network access. Deterministic: the same input file always
produces the same output bytes.
"""

import hashlib
import os
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "entry.png"
OUTPUT_NAME = "entry.png"

# The rendered front page must be a square 1024x1024 PNG no larger than
# 1 MiB, per the bounty rules.
EXPECTED_MAX_BYTES = 1_048_576


# PNG signature (8 bytes) followed by the IHDR chunk; width and height are
# the first two 4-byte big-endian fields inside IHDR, at offsets 16 and 20.
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
EXPECTED_WIDTH = 1024
EXPECTED_HEIGHT = 1024


def check_png_dimensions(data: bytes) -> str | None:
    """Return an error message if *data* is not a 1024x1024 PNG, else None."""
    if len(data) < 24 or data[:8] != PNG_SIGNATURE:
        return "entry.png is not a PNG file"
    if data[12:16] != b"IHDR":
        return "entry.png has no IHDR chunk"
    width = int.from_bytes(data[16:20], "big")
    height = int.from_bytes(data[20:24], "big")
    if (width, height) != (EXPECTED_WIDTH, EXPECTED_HEIGHT):
        return (
            f"entry.png is {width}x{height}, expected "
            f"{EXPECTED_WIDTH}x{EXPECTED_HEIGHT}"
        )
    return None


def fail(message: str) -> "SystemExit":
    """Print an error to stderr and return a non-zero exit."""
    print(f"error: {message}", file=sys.stderr)
    return SystemExit(1)


def main() -> int:
    output_dir = os.environ.get("MAKEFUN_OUTPUT_DIR")
    if not output_dir:
        print("error: MAKEFUN_OUTPUT_DIR is not set", file=sys.stderr)
        return 1

    if not SOURCE.is_file():
        print(f"error: {SOURCE} not found", file=sys.stderr)
        return 1

    size = SOURCE.stat().st_size
    if size > EXPECTED_MAX_BYTES:
        print(
            f"error: entry.png is {size} bytes, over the "
            f"{EXPECTED_MAX_BYTES} byte limit",
            file=sys.stderr,
        )
        return 1

    raw = SOURCE.read_bytes()
    dimension_error = check_png_dimensions(raw)
    if dimension_error is not None:
        print(f"error: {dimension_error}", file=sys.stderr)
        return 1

    digest = hashlib.sha256(raw).hexdigest()
    print(f"entry.png: {size} bytes, sha256 {digest}")

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    destination = out_dir / OUTPUT_NAME
    shutil.copyfile(SOURCE, destination)

    copied = destination.stat().st_size
    if copied != size:
        print(
            f"error: copied {copied} bytes, expected {size}",
            file=sys.stderr,
        )
        return 1

    print(f"wrote {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
