#!/usr/bin/env python3
"""Compose the homepage panorama from photos: Istanbul | London | Los Angeles.

Each photo is cropped, toned to one silver-grey palette, anchored to a shared horizon,
and blended into its neighbours with soft masks. The middle (behind the phone) is the
aerial London shot; Big Ben stands just left of the phone so it stays visible.

Inputs live in assets/src/ (not committed). Output: assets/panorama.jpg and assets/panorama-1600.jpg
"""
from pathlib import Path

from PIL import Image, ImageChops, ImageEnhance, ImageFilter, ImageOps

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "assets" / "src"
W, H = 3000, 1180

# silver duotone: shadows -> graphite, highlights -> near white
DARK, LIGHT = (52, 56, 63), (246, 247, 248)


def tone(im: Image.Image, contrast=1.12, brightness=1.04) -> Image.Image:
    g = ImageOps.grayscale(im)
    g = ImageOps.autocontrast(g, cutoff=1)
    g = ImageEnhance.Contrast(g).enhance(contrast)
    g = ImageEnhance.Brightness(g).enhance(brightness)
    return ImageOps.colorize(g, black=DARK, white=LIGHT, mid=(150, 154, 160))


def fit(im: Image.Image, box_w: int, box_h: int) -> Image.Image:
    """Scale to cover box_w x box_h, keeping the bottom (the horizon side)."""
    s = max(box_w / im.width, box_h / im.height)
    im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    left = (im.width - box_w) // 2
    return im.crop((left, im.height - box_h, left + box_w, im.height))


def hmask(w: int, h: int, fade_l: int, fade_r: int, fade_top: int) -> Image.Image:
    """Alpha mask: soft left/right edges and a soft top edge that dissolves into the sky."""
    m = Image.new("L", (w, h), 255)
    px = m.load()
    for x in range(w):
        a = 1.0
        if fade_l and x < fade_l:
            a = min(a, x / fade_l)
        if fade_r and x > w - fade_r:
            a = min(a, (w - x) / fade_r)
        for y in range(h):
            b = a
            if fade_top and y < fade_top:
                b = min(b, (y / fade_top) ** 1.4)
            px[x, y] = int(255 * b)
    return m


def place(canvas: Image.Image, im: Image.Image, x: int, y_bottom: int, fades=(0, 0, 0)) -> None:
    mask = hmask(im.width, im.height, *fades)
    canvas.paste(im, (x, y_bottom - im.height), mask)


# ---------------------------------------------------------------- sky
sky = Image.new("RGB", (W, H))
top, bottom = (226, 229, 233), (245, 246, 247)
for y in range(H):
    t = y / H
    c = tuple(round(top[i] + (bottom[i] - top[i]) * t) for i in range(3))
    sky.paste(c, (0, y, W, y + 1))
canvas = sky.copy()

# ---------------------------------------------------------------- photos
# London aerial: the wide middle, mostly behind the phone
aerial = Image.open(SRC / "london-aerial.png").crop((0, 90, 1000, 667))
aerial = fit(tone(aerial, 1.08, 1.06), 1350, 900)
place(canvas, aerial, 830, H, (260, 260, 260))

# Los Angeles: palms and downtown, right side
la = Image.open(SRC / "la-palms.png")
la = fit(tone(la, 1.25, 1.0), 1250, 1060)
place(canvas, la, W - 1250, H, (320, 0, 260))

# Istanbul: Bosphorus Bridge, cropped well above the coffee cup
bridge = Image.open(SRC / "istanbul-bridge.png").crop((0, 20, 495, 380))
bridge = fit(tone(bridge, 1.15, 1.02), 1150, 960)
place(canvas, bridge, 0, H, (0, 300, 240))

# Big Ben: tower and Whitehall rooftops, standing just left of the phone
ben = Image.open(SRC / "london-bigben.png").crop((430, 380, 1090, 1250))
ben = fit(tone(ben, 1.18, 1.02), 470, 1000)
place(canvas, ben, 620, H, (150, 150, 380))

# ---------------------------------------------------------------- finish
canvas = canvas.filter(ImageFilter.UnsharpMask(radius=2, percent=60, threshold=2))
# a soft light bloom behind where the phone rises
bloom = Image.new("L", (W, H), 0)
bp = bloom.load()
cx, cy, r = W // 2, int(H * 0.66), 820
for y in range(0, H, 2):
    for x in range(0, W, 2):
        d = ((x - cx) ** 2 + ((y - cy) * 1.6) ** 2) ** 0.5
        v = max(0, 1 - d / r) ** 2 * 70
        bp[x, y] = int(v)
bloom = bloom.filter(ImageFilter.GaussianBlur(6))
canvas = ImageChops.add(canvas, Image.merge("RGB", (bloom, bloom, bloom)))

out = ROOT / "assets"
canvas.save(out / "panorama.jpg", quality=84, optimize=True, progressive=True)
canvas.resize((1600, round(H * 1600 / W)), Image.LANCZOS).save(out / "panorama-1600.jpg", quality=82, optimize=True, progressive=True)
print("wrote assets/panorama.jpg and assets/panorama-1600.jpg")
