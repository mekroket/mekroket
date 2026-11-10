"""
Turns the profile photo into ASCII art for the card.

    python scripts/ascii.py path/to/photo.jpg [--preview out.png]

Writes ascii_dark.txt (bright pixels = dense characters, for light text on a
dark card) and ascii_light.txt (dark pixels = dense, for the light card).
The silhouette polygon is traced for the current 460x460 GitHub avatar; if you
change the photo, re-trace MASK and CROP.
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageOps

ROOT = Path(__file__).resolve().parent.parent

COLS, ROWS = 66, 40          # must match ART_* settings in generate.py
CELL_ASPECT = 5.5 / 12.5     # char width / line height at 10px Consolas, 12.5px lines
CROP_X, CROP_Y, CROP_W = 160, 112, 154   # region of the photo (height follows from aspect)

# Person silhouette on the 460x460 avatar (x, y)
MASK = [
    (193, 165), (196, 146), (205, 131), (222, 121), (245, 117), (265, 123), (278, 134),
    (284, 150), (282, 172), (279, 192), (276, 213), (268, 233), (262, 248), (267, 258),
    (300, 277), (318, 299), (326, 330), (332, 400), (336, 460), (88, 460), (99, 330),
    (112, 295), (130, 276), (170, 265), (200, 256), (204, 241), (198, 222), (194, 196),
]

# Head only (hair + face down to the chin), used to stretch facial contrast
HEAD = MASK[:13] + [(235, 252), (204, 241), (198, 222), (194, 196)]

RAMP = " .,:;~=+*xo%#&@"  # sparse -> dense


def _poly_mask(size, poly, blur):
    m = Image.new("L", size, 0)
    ImageDraw.Draw(m).polygon(poly, fill=255)
    return m.filter(ImageFilter.GaussianBlur(blur))


def _to_ascii(im: Image.Image, msmall: Image.Image, invert: bool, gamma: float) -> list[str]:
    small = im.filter(ImageFilter.UnsharpMask(radius=2, percent=120, threshold=2)).resize((COLS, ROWS), Image.LANCZOS)
    lines = []
    for y in range(ROWS):
        row = []
        for x in range(COLS):
            if msmall.getpixel((x, y)) <= 100:
                row.append(" ")
                continue
            v = small.getpixel((x, y)) / 255
            if invert:
                v = 1 - v
            v = v ** gamma
            row.append(RAMP[1 + min(len(RAMP) - 2, int(v * (len(RAMP) - 1)))])
        lines.append("".join(row).rstrip())
    return lines


def convert(photo: Path) -> tuple[list[str], list[str]]:
    im = Image.open(photo).convert("L")
    mask = _poly_mask(im.size, MASK, 1.5)
    head = _poly_mask(im.size, HEAD, 0).point(lambda v: 255 if v > 128 else 0)

    crop_h = ROWS * (CROP_W / COLS) / CELL_ASPECT
    box = (CROP_X, CROP_Y, CROP_X + CROP_W, round(CROP_Y + crop_h))
    im, mask, head = im.crop(box), mask.crop(box), head.crop(box)
    msmall = mask.resize((COLS, ROWS), Image.LANCZOS)

    # dark card: stretch contrast over the head only, so the black shirt fades to dots
    dark = _to_ascii(ImageOps.equalize(im, mask=head), msmall, invert=False, gamma=1.0)
    # light card: equalize over the whole silhouette so the shirt stays mid-tone
    full = mask.point(lambda v: 255 if v > 128 else 0)
    light = _to_ascii(ImageOps.equalize(im, mask=full), msmall, invert=True, gamma=1.1)
    return dark, light


def preview(dark: list[str], light: list[str], out: Path) -> None:
    from PIL import ImageFont
    font = ImageFont.truetype("consola.ttf", 10)
    w, h = int(COLS * 5.5) + 20, int(ROWS * 12.5) + 20
    img = Image.new("RGB", (w * 2, h), "#161b22")
    img.paste("#f6f8fa", (w, 0, w * 2, h))
    d = ImageDraw.Draw(img)
    for i, (a, b) in enumerate(zip(dark, light)):
        d.text((10, 10 + i * 12.5), a, font=font, fill="#c9d1d9")
        d.text((w + 10, 10 + i * 12.5), b, font=font, fill="#24292f")
    img.save(out)


if __name__ == "__main__":
    photo = Path(sys.argv[1])
    dark, light = convert(photo)
    (ROOT / "ascii_dark.txt").write_text("\n".join(dark) + "\n", encoding="utf-8")
    (ROOT / "ascii_light.txt").write_text("\n".join(light) + "\n", encoding="utf-8")
    print("\n".join(dark))
    if "--preview" in sys.argv:
        preview(dark, light, Path(sys.argv[sys.argv.index("--preview") + 1]))
