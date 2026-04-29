#!/usr/bin/env python3
"""Build assets/AppIcon.icns from assets/app_icon_1024.png (square or near-square source).

macOS applies the rounded "squircle" mask to .icns automatically (like other apps). Use a
full-bleed square image: avoid a small rounded panel floating on a dark grey margin — export
or crop so the art fills the square, or rely on this script to trim dark margins and flatten
transparency onto the widget card color (#B1A39E).
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from PIL import Image

from tm_resources import COL

ASSETS = ROOT / "assets"
SRC = ASSETS / "app_icon_1024.png"
MASTER = ASSETS / "app_icon_master.png"
ICONSET = ASSETS / "AppIcon.iconset"
OUT_ICNS = ASSETS / "AppIcon.icns"

SIZES: list[tuple[int, str]] = [
    (16, "icon_16x16.png"),
    (32, "icon_16x16@2x.png"),
    (32, "icon_32x32.png"),
    (64, "icon_32x32@2x.png"),
    (128, "icon_128x128.png"),
    (256, "icon_128x128@2x.png"),
    (256, "icon_256x256.png"),
    (512, "icon_256x256@2x.png"),
    (512, "icon_512x512.png"),
    (1024, "icon_512x512@2x.png"),
]


def _fill_corner_black(im: Image.Image) -> Image.Image:
    """Replace pure #000 used outside rounded art (common in AI exports) with card background."""
    im = im.convert("RGBA")
    px = im.load()
    w, h = im.size
    hx = COL["card"].lstrip("#")
    fr, fg, fb = int(hx[0:2], 16), int(hx[2:4], 16), int(hx[4:6], 16)
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if (r, g, b) == (0, 0, 0):
                px[x, y] = (fr, fg, fb, a)
    return im


def _composite_on_card(im: Image.Image) -> Image.Image:
    """Flatten transparency onto card color so rounded-rect exports do not show dark fringe."""
    im = im.convert("RGBA")
    w, h = im.size
    hx = COL["card"].lstrip("#")
    fr, fg, fb = int(hx[0:2], 16), int(hx[2:4], 16), int(hx[4:6], 16)
    base = Image.new("RGBA", (w, h), (fr, fg, fb, 255))
    return Image.alpha_composite(base, im)


def _trim_outer_frame(im: Image.Image, *, avg_row_max: float = 380.0) -> Image.Image:
    """Remove rows/columns that are mostly a dark screenshot margin (grey frame around the art)."""
    im = im.convert("RGBA")
    w, h = im.size
    px = im.load()
    min_keep = int(min(w, h) * 0.45)

    def row_mean_sum(y: int) -> float:
        t = 0
        for x in range(w):
            r, g, b, _ = px[x, y]
            t += r + g + b
        return t / float(w)

    def col_mean_sum(x: int) -> float:
        t = 0
        for y in range(h):
            r, g, b, _ = px[x, y]
            t += r + g + b
        return t / float(h)

    top = 0
    while top < h - min_keep and row_mean_sum(top) < avg_row_max:
        top += 1
    bottom = h - 1
    while bottom > top + min_keep and row_mean_sum(bottom) < avg_row_max:
        bottom -= 1
    left = 0
    while left < w - min_keep and col_mean_sum(left) < avg_row_max:
        left += 1
    right = w - 1
    while right > left + min_keep and col_mean_sum(right) < avg_row_max:
        right -= 1

    if right <= left or bottom <= top:
        return im
    return im.crop((left, top, right + 1, bottom + 1))


def main() -> int:
    if not SRC.is_file():
        print(f"Missing source icon: {SRC}", file=sys.stderr)
        return 1
    im = Image.open(SRC).convert("RGBA")
    im = _fill_corner_black(im)
    im = _trim_outer_frame(im)
    im = _composite_on_card(im)
    w, h = im.size
    side = min(w, h)
    left = (w - side) // 2
    top = (h - side) // 2
    im = im.crop((left, top, left + side, top + side)).resize((1024, 1024), Image.Resampling.LANCZOS)
    im = _fill_corner_black(im)
    im = _composite_on_card(im)
    im.save(MASTER, "PNG")

    if ICONSET.exists():
        shutil.rmtree(ICONSET)
    ICONSET.mkdir(parents=True)
    for px, name in SIZES:
        im.resize((px, px), Image.Resampling.LANCZOS).save(ICONSET / name, "PNG")

    subprocess.run(
        ["iconutil", "-c", "icns", str(ICONSET), "-o", str(OUT_ICNS)],
        check=True,
    )
    print(f"Wrote {OUT_ICNS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
