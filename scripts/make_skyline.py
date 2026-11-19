#!/usr/bin/env python3
"""Draw the homepage panorama: Istanbul | London | Los Angeles, as one blue duotone skyline.

Writes assets/skyline.svg. Re-run after editing:  python scripts/make_skyline.py
"""
import math
import random
from pathlib import Path

W, H = 2400, 1100
HORIZON = 760          # where buildings stand
rnd = random.Random(7)

C = {
    "far": "#d3d6db",      # distant hills / buildings
    "mid": "#b4b9c0",      # main silhouettes
    "near": "#8a9099",     # foreground
    "deep": "#5b616b",     # ground / water edge
    "line": "#ffffff",     # cables, highlights
    "win": "#f7f8fa",      # lit windows
}
out: list[str] = []


def add(s: str) -> None:
    out.append(s)


def rect(x, y, w, h, fill, extra=""):
    add(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" fill="{fill}" {extra}/>')


def windows(x, y, w, h, density=0.18, size=4, gap=10):
    for wx in range(int(x + 6), int(x + w - 6), gap):
        for wy in range(int(y + 8), int(y + h - 6), gap + 4):
            if rnd.random() < density:
                rect(wx, wy, size, size + 1, C["win"], 'opacity="0.55"')


def block_row(x0, x1, base, hmin, hmax, fill, wmin=30, wmax=70, lit=0.12):
    x = x0
    while x < x1:
        w = rnd.uniform(wmin, wmax)
        h = rnd.uniform(hmin, hmax)
        rect(x, base - h, w, h, fill)
        if lit:
            windows(x, base - h, w, h, lit)
        x += w + rnd.uniform(-6, 4)


# ------------------------------------------------------------------ sky
add(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" preserveAspectRatio="xMidYMax slice">')
add("""<defs>
<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="#e4e6ea"/><stop offset="0.45" stop-color="#eef0f2"/>
  <stop offset="0.78" stop-color="#f7f8f9"/><stop offset="1" stop-color="#fbfbfc"/>
</linearGradient>
<linearGradient id="water" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="#d9dce1"/><stop offset="1" stop-color="#c4c8ce"/>
</linearGradient>
<radialGradient id="glow" cx="0.5" cy="0.62" r="0.5">
  <stop offset="0" stop-color="#ffffff" stop-opacity="0.7"/><stop offset="1" stop-color="#ffffff" stop-opacity="0"/>
</radialGradient>
</defs>""")
rect(0, 0, W, H, "url(#sky)")
rect(0, 0, W, H, "url(#glow)")
# soft cloud bands
for i in range(7):
    y = rnd.uniform(140, 420)
    add(f'<ellipse cx="{rnd.uniform(0, W):.0f}" cy="{y:.0f}" rx="{rnd.uniform(260, 520):.0f}" ry="{rnd.uniform(14, 30):.0f}" '
        f'fill="#ffffff" opacity="{rnd.uniform(0.35, 0.6):.2f}"/>')

# ------------------------------------------------------------------ far layer (all cities)
pts = [(0, HORIZON - 90)]
for x in range(0, W + 60, 60):
    pts.append((x, HORIZON - 90 - 40 * math.sin(x / 210) - 25 * math.sin(x / 77) - rnd.uniform(0, 20)))
pts += [(W, HORIZON), (0, HORIZON)]
add(f'<polygon points="{" ".join(f"{x:.0f},{y:.0f}" for x, y in pts)}" fill="{C["far"]}" opacity="0.55"/>')
block_row(0, W, HORIZON, 40, 130, C["far"], 24, 60, 0.04)

# ================================================================== ISTANBUL (0 - 800)
# hills with a mosque skyline (left), Galata-style tower, then the Bosphorus bridge
add(f'<path d="M0 {HORIZON-60} Q 160 {HORIZON-170} 340 {HORIZON-110} T 760 {HORIZON-70} L 800 {HORIZON} L 0 {HORIZON} Z" fill="{C["mid"]}"/>')


def mosque(cx, base, s, fill):
    # central dome on a drum, two half-domes, four minarets
    rect(cx - 70 * s, base - 70 * s, 140 * s, 70 * s, fill)
    add(f'<path d="M{cx-60*s} {base-70*s} A {60*s} {58*s} 0 0 1 {cx+60*s} {base-70*s} Z" fill="{fill}"/>')
    add(f'<path d="M{cx-110*s} {base-30*s} A {42*s} {38*s} 0 0 1 {cx-26*s} {base-30*s} Z" fill="{fill}"/>')
    add(f'<path d="M{cx+26*s} {base-30*s} A {42*s} {38*s} 0 0 1 {cx+110*s} {base-30*s} Z" fill="{fill}"/>')
    rect(cx - 2 * s, base - 150 * s, 4 * s, 24 * s, fill)
    for dx, hh in ((-150, 230), (-95, 200), (95, 200), (150, 230)):
        x = cx + dx * s
        rect(x - 6 * s, base - hh * s, 12 * s, hh * s, fill)
        rect(x - 9 * s, base - (hh - 70) * s, 18 * s, 6 * s, fill)
        add(f'<path d="M{x-6*s} {base-hh*s} L {x} {base-(hh+42)*s} L {x+6*s} {base-hh*s} Z" fill="{fill}"/>')
    rect(cx - 160 * s, base - 30 * s, 320 * s, 30 * s, fill)


mosque(250, HORIZON - 120, 0.9, C["near"])
# Galata-style tower
gx, gb = 560, HORIZON - 70
rect(gx - 22, gb - 170, 44, 170, C["near"])
rect(gx - 27, gb - 182, 54, 14, C["near"])
add(f'<path d="M{gx-26} {gb-182} L {gx} {gb-262} L {gx+26} {gb-182} Z" fill="{C["near"]}"/>')
for wy in range(int(gb - 160), int(gb - 30), 34):
    rect(gx - 4, wy, 8, 14, C["win"], 'opacity="0.5"')
block_row(380, 520, HORIZON - 60, 30, 90, C["near"], 26, 44, 0.15)
block_row(600, 800, HORIZON - 50, 30, 80, C["near"], 26, 44, 0.15)

# water (Bosphorus) in front
rect(0, HORIZON + 20, 800, H - HORIZON - 20, "url(#water)")
for i in range(40):
    y = rnd.uniform(HORIZON + 30, H - 40)
    x = rnd.uniform(0, 780)
    add(f'<rect x="{x:.0f}" y="{y:.0f}" width="{rnd.uniform(30, 90):.0f}" height="2" fill="#ffffff" opacity="{rnd.uniform(0.5, 0.9):.2f}"/>')

# Bosphorus Bridge: two towers, deck, main cable, hangers
deck = HORIZON + 40
t1, t2, top = 120, 640, HORIZON - 260
for tx in (t1, t2):
    rect(tx - 9, top, 7, deck - top + 120, C["deep"])
    rect(tx + 2, top, 7, deck - top + 120, C["deep"])
    for yy in (top + 30, top + 140, top + 250):
        rect(tx - 9, yy, 18, 8, C["deep"])
rect(-20, deck, 840, 14, C["deep"])
sag = deck - 30


def cable_y(x):
    # parabola between towers, straight back-stays outside
    if t1 <= x <= t2:
        m = (t1 + t2) / 2
        a = (top - sag) / ((t1 - m) ** 2)
        return sag + a * (x - m) ** 2
    return top + (abs(x - (t1 if x < t1 else t2)) / 180) * (deck - top) * 0.95


path = " ".join(f"{'M' if i == 0 else 'L'}{x} {cable_y(x):.1f}" for i, x in enumerate(range(-40, 841, 8)))
add(f'<path d="{path}" fill="none" stroke="{C["deep"]}" stroke-width="5"/>')
add(f'<path d="{path}" fill="none" stroke="{C["line"]}" stroke-width="1.4" opacity="0.6"/>')
for x in range(t1 + 16, t2, 16):
    add(f'<line x1="{x}" y1="{cable_y(x):.1f}" x2="{x}" y2="{deck}" stroke="{C["deep"]}" stroke-width="1.6"/>')
for x in list(range(-30, t1, 16)) + list(range(t2 + 16, 820, 16)):
    add(f'<line x1="{x}" y1="{cable_y(x):.1f}" x2="{x}" y2="{deck}" stroke="{C["deep"]}" stroke-width="1.6"/>')
# deck lights
for x in range(0, 800, 22):
    add(f'<circle cx="{x}" cy="{deck+4}" r="2" fill="{C["win"]}" opacity="0.9"/>')

# ================================================================== LONDON (800 - 1600)
block_row(800, 1600, HORIZON, 60, 170, C["mid"], 30, 70, 0.10)
# The Shard
sx = 1045
add(f'<path d="M{sx-60} {HORIZON} L {sx-8} {HORIZON-420} L {sx+2} {HORIZON-455} L {sx+14} {HORIZON-410} L {sx+64} {HORIZON} Z" fill="{C["mid"]}"/>')
for i in range(12):
    yy = HORIZON - 30 - i * 30
    half = 58 - i * 4.4
    add(f'<line x1="{sx-half+6:.0f}" y1="{yy}" x2="{sx+half-6:.0f}" y2="{yy}" stroke="{C["win"]}" stroke-width="1" opacity="0.3"/>')
# London Eye
ex, ey, er = 905, HORIZON - 170, 150
add(f'<circle cx="{ex}" cy="{ey}" r="{er}" fill="none" stroke="{C["near"]}" stroke-width="7"/>')
add(f'<circle cx="{ex}" cy="{ey}" r="{er-14}" fill="none" stroke="{C["near"]}" stroke-width="2"/>')
for a in range(0, 360, 12):
    r = math.radians(a)
    add(f'<line x1="{ex}" y1="{ey}" x2="{ex + er*math.cos(r):.1f}" y2="{ey + er*math.sin(r):.1f}" stroke="{C["near"]}" stroke-width="1.4"/>')
    add(f'<rect x="{ex + (er+6)*math.cos(r) - 6:.1f}" y="{ey + (er+6)*math.sin(r) - 4:.1f}" width="12" height="8" rx="3" fill="{C["near"]}"/>')
add(f'<path d="M{ex-70} {HORIZON} L {ex} {ey} L {ex+70} {HORIZON}" fill="none" stroke="{C["near"]}" stroke-width="8"/>')
add(f'<circle cx="{ex}" cy="{ey}" r="12" fill="{C["near"]}"/>')
# Palace of Westminster + Elizabeth Tower (Big Ben)
px0, px1, pb = 1400, 1660, HORIZON + 20
rect(px0, pb - 120, px1 - px0, 120, C["near"])
for x in range(px0 + 10, px1, 26):
    rect(x, pb - 150, 6, 30, C["near"])
    add(f'<path d="M{x-2} {pb-150} L {x+3} {pb-172} L {x+8} {pb-150} Z" fill="{C["near"]}"/>')
windows(px0, pb - 110, px1 - px0, 100, 0.22, 4, 13)
# Elizabeth Tower
bx, bw = 1460, 62
rect(bx, pb - 420, bw, 420, C["near"])
rect(bx - 6, pb - 470, bw + 12, 56, C["near"])                      # clock stage
add(f'<circle cx="{bx+bw/2}" cy="{pb-442}" r="21" fill="#f7f8fa" opacity="1"/>')
add(f'<line x1="{bx+bw/2}" y1="{pb-442}" x2="{bx+bw/2}" y2="{pb-456}" stroke="{C["near"]}" stroke-width="3"/>')
add(f'<line x1="{bx+bw/2}" y1="{pb-442}" x2="{bx+bw/2+10}" y2="{pb-440}" stroke="{C["near"]}" stroke-width="3"/>')
rect(bx - 2, pb - 520, bw + 4, 50, C["near"])                        # belfry
for x in range(int(bx + 6), int(bx + bw - 4), 12):
    rect(x, pb - 512, 5, 30, C["far"], 'opacity="0.7"')
add(f'<path d="M{bx-4} {pb-520} L {bx+bw/2} {pb-640} L {bx+bw+4} {pb-520} Z" fill="{C["near"]}"/>')
rect(bx + bw / 2 - 2, pb - 680, 4, 44, C["near"])
for yy in range(int(pb - 400), int(pb - 40), 40):
    rect(bx + 14, yy, 6, 22, C["win"], 'opacity="0.45"')
    rect(bx + bw - 20, yy, 6, 22, C["win"], 'opacity="0.45"')
# Thames
rect(800, HORIZON + 20, 860, H - HORIZON - 20, "url(#water)")
for i in range(30):
    add(f'<rect x="{rnd.uniform(800, 1580):.0f}" y="{rnd.uniform(HORIZON+50, H-40):.0f}" width="{rnd.uniform(30, 90):.0f}" height="2" fill="#ffffff" opacity="{rnd.uniform(0.5, 0.9):.2f}"/>')

# ================================================================== LOS ANGELES (1600 - 2400)
# hills with an observatory, downtown towers, palms
add(f'<path d="M1600 {HORIZON-40} Q 1760 {HORIZON-250} 1960 {HORIZON-200} T 2400 {HORIZON-150} L 2400 {HORIZON} L 1600 {HORIZON} Z" fill="{C["mid"]}" opacity="0.9"/>')
ox, oy = 1880, HORIZON - 222
rect(ox - 70, oy - 30, 140, 30, C["near"])
add(f'<path d="M{ox-30} {oy-30} A 30 30 0 0 1 {ox+30} {oy-30} Z" fill="{C["near"]}"/>')
for dx in (-62, 62):
    add(f'<path d="M{ox+dx-14} {oy-30} A 14 14 0 0 1 {ox+dx+14} {oy-30} Z" fill="{C["near"]}"/>')
# downtown
block_row(1980, 2380, HORIZON, 120, 260, C["mid"], 34, 60, 0.16)
# cylindrical tower with stepped crown
tx = 2120
rect(tx - 40, HORIZON - 520, 80, 520, C["near"])
for i, w in enumerate((70, 58, 44)):
    rect(tx - w / 2, HORIZON - 540 - i * 22, w, 22, C["near"])
windows(tx - 40, HORIZON - 510, 80, 500, 0.22)
# sail-shaped tower with spire
wx = 2250
add(f'<path d="M{wx-46} {HORIZON} L {wx-46} {HORIZON-470} Q {wx+10} {HORIZON-520} {wx+46} {HORIZON-560} L {wx+46} {HORIZON} Z" fill="{C["near"]}"/>')
rect(wx + 44, HORIZON - 640, 4, 84, C["near"])
windows(wx - 46, HORIZON - 460, 92, 450, 0.2)
rect(2010, HORIZON - 380, 70, 380, C["near"])
windows(2010, HORIZON - 370, 70, 360, 0.2)
rect(2320, HORIZON - 330, 66, 330, C["near"])
windows(2320, HORIZON - 320, 66, 310, 0.2)
# ground and street
add('<linearGradient id="sprawl" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#c9cdd3"/><stop offset="1" stop-color="#b3b8bf"/></linearGradient>')
rect(1660, HORIZON, 740, H - HORIZON, "url(#sprawl)")
for i in range(260):
    yy = rnd.uniform(HORIZON + 40, H - 70)
    add(f'<circle cx="{rnd.uniform(1660, 2400):.0f}" cy="{yy:.0f}" r="{rnd.uniform(1, 2.4):.1f}" '
        f'fill="{rnd.choice(["#ffffff", "#f3f4f6", "#8a9099"])}" opacity="{rnd.uniform(0.5, 0.95):.2f}"/>')
for x in range(1600, 2400, 40):
    add(f'<circle cx="{x+rnd.uniform(0, 20):.0f}" cy="{HORIZON + 26 + rnd.uniform(0, 8):.0f}" r="2.2" fill="#ffffff" opacity="0.9"/>')


def palm(x, base, h, lean):
    topx, topy = x + lean, base - h
    add(f'<path d="M{x-5} {base} Q {x+lean*0.3} {base-h*0.5} {topx-2} {topy} L {topx+2} {topy} Q {x+lean*0.3+6} {base-h*0.5} {x+5} {base} Z" fill="{C["deep"]}"/>')
    for a in (-170, -140, -110, -70, -40, -10, 20, 200):
        r = math.radians(a)
        ex2, ey2 = topx + 70 * math.cos(r), topy + 70 * math.sin(r) * 0.6 + 26
        mx, my = topx + 40 * math.cos(r), topy + 40 * math.sin(r) * 0.6 - 10
        add(f'<path d="M{topx} {topy} Q {mx:.0f} {my:.0f} {ex2:.0f} {ey2:.0f}" fill="none" stroke="{C["deep"]}" stroke-width="7" stroke-linecap="round"/>')


for x, h, lean in ((1640, 360, 12), (1700, 420, -10), (1790, 300, 8), (1930, 390, 14), (2400 - 40, 340, -12)):
    palm(x, HORIZON + 60, h, lean)

# ------------------------------------------------------------------ seams + labels
add("</svg>")

Path(__file__).resolve().parent.parent.joinpath("assets").mkdir(exist_ok=True)
Path(__file__).resolve().parent.parent.joinpath("assets", "skyline.svg").write_text("\n".join(out), encoding="utf-8")
print(f"wrote assets/skyline.svg ({len(out)} elements)")
