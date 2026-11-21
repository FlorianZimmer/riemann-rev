#!/usr/bin/env python3
"""Animated GIF of the guide: guide/proof-guide.gif, one frame per page of guide/proof-guide.pdf.

    python3 -B scripts/build_guide_gif.py                 # 5 s per page (6 s for the first), 130 dpi
    python3 -B scripts/build_guide_gif.py --seconds 10    # a slower pace
    python3 -B scripts/build_guide_gif.py --dpi 100       # a smaller file

Each page is rendered with pdftoppm and cropped to the printed area (the PDF has wide margins,
meant for paper), so that the type is as large as possible for a given width in pixels. All frames
share one palette: the colours of the document's design (ink, the four strata, the link colour)
are put in by hand, the rest is chosen from the pages at full resolution. Frames are converted
without dithering, which keeps the type sharp. The GIF loops for ever.

The GIF carries, in its comment block, the SHA-256 of the PDF it was made from; `make check`
compares it with the current PDF, so that the two cannot drift apart unnoticed. The script fails if
the number of frames differs from the number of pages.
"""
from __future__ import annotations

import argparse
import hashlib
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / "guide" / "proof-guide.pdf"
GIF = ROOT / "guide" / "proof-guide.gif"

# The part of the A4 page (210 mm x 297 mm) that is kept, in millimetres. It contains the diagram of
# page 1 (wider than the text), the marks hanging in the left margin and the page numbers.
CROP_MM = dict(left=13.0, top=13.0, width=184.0, height=273.0)
COLOURS = 128           # size of the common palette
# Colours of the guide (guide/proof-guide.tex) that must survive exactly: ink and its soft and faint
# variants, the rule, the four strata, the green of the checks, the colour of the Lean names.
FIXED = ["FFFFFF", "0F172A", "475569", "94A3B8", "CBD5E1", "C2410C", "7C3AED", "0891B2", "E11D48",
         "047857", "3730A3"]
COMMENT = "riemann-rev guide; made from proof-guide.pdf sha256="


def pdf_pages(pdf: Path) -> int:
    info = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True, check=True).stdout
    return int(re.search(r"Pages:\s+(\d+)", info).group(1))


def render(pdf: Path, dpi: int, tmp: Path) -> list[Image.Image]:
    """The pages of the PDF as RGB images, cropped to CROP_MM."""
    px = lambda mm: round(mm / 25.4 * dpi)
    subprocess.run(["pdftoppm", "-r", str(dpi), "-png",
                    "-x", str(px(CROP_MM["left"])), "-y", str(px(CROP_MM["top"])),
                    "-W", str(px(CROP_MM["width"])), "-H", str(px(CROP_MM["height"])),
                    str(pdf), str(tmp / "page")], check=True)
    files = sorted(tmp.glob("page-*.png"), key=lambda p: int(p.stem.split("-")[-1]))
    return [Image.open(f).convert("RGB") for f in files]


def common_palette(pages: list[Image.Image]) -> Image.Image:
    """One palette for all frames: the fixed colours, then colours chosen from all pages at full
    resolution (reduced copies lose the dark of thin strokes and the small coloured marks)."""
    sheet = Image.new("RGB", (pages[0].width, sum(p.height for p in pages)), "white")
    y = 0
    for p in pages:
        sheet.paste(p, (0, y))
        y += p.height
    fixed = [tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) for h in FIXED]
    adaptive = sheet.quantize(colors=COLOURS - len(fixed), method=Image.Quantize.MEDIANCUT,
                              dither=Image.Dither.NONE).getpalette()[: 3 * (COLOURS - len(fixed))]
    chosen = [tuple(adaptive[i:i + 3]) for i in range(0, len(adaptive), 3)]
    colours = fixed + [c for c in chosen if c not in fixed]
    palette = Image.new("P", (1, 1))
    palette.putpalette([v for c in colours for v in c])
    return palette


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--dpi", type=int, default=130, help="resolution of the frames (default 130)")
    ap.add_argument("--seconds", type=float, default=5.0, help="time each page is shown (default 5)")
    ap.add_argument("--first", type=float, default=None, help="time for the first page (default: one second more)")
    args = ap.parse_args()
    if not PDF.exists():
        print(f"guide gif: {PDF.relative_to(ROOT)} is missing; run `make guide` first")
        return 1
    first = args.first if args.first is not None else args.seconds + 1
    digest = hashlib.sha256(PDF.read_bytes()).hexdigest()
    with tempfile.TemporaryDirectory(prefix="guide-gif-") as tmp:
        pages = render(PDF, args.dpi, Path(tmp))
        palette = common_palette(pages)
        frames = [p.quantize(palette=palette, dither=Image.Dither.NONE) for p in pages]
    durations = [round(1000 * first)] + [round(1000 * args.seconds)] * (len(frames) - 1)
    frames[0].save(GIF, save_all=True, append_images=frames[1:], duration=durations, loop=0,
                   optimize=False, disposal=1, comment=(COMMENT + digest).encode("ascii"))

    # read the file back and compare it with what was asked for
    problems = []
    with Image.open(GIF) as g:
        n = getattr(g, "n_frames", 1)
        size = g.size
    want = pdf_pages(PDF)
    if n != want:
        problems.append(f"{n} frames for {want} pages")
    kib = GIF.stat().st_size // 1024
    print(f"guide gif: {GIF.relative_to(ROOT)}, {n} frames of {size[0]}x{size[1]} px, "
          f"{sum(durations) / 1000:.0f} s per loop, {kib} KiB" + ("" if not problems else " -- PROBLEMS: " + "; ".join(problems)))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
