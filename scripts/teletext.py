"""Teletext-style sport pages (P300-P304) for The Morning Dispatch.

render_teletext(ed, raw, now) returns one HTML document. Each teletext "page" is a
<section>; a little script shows one at a time (hash #p301 etc.) and adds the
remote-control behaviour. Without JavaScript every page simply shows, stacked.
"""
from __future__ import annotations

import datetime as dt
import html
import re

TR_PATTERN = re.compile(
    r"galatasaray|fenerbah|be[sş]ikta[sş]|trabzon|t[uü]rkiye|turkey|turkish|s[uü]per lig|"
    r"ba[sş]ak[sş]ehir|samsunspor|g[oö]ztepe|kocaeli|konyaspor|montella|arda g[uü]ler|kenan y[iı]ld[iı]z",
    re.I,
)
EUROPE_LEAGUES = ["Champions League", "Europa League", "Premier League", "LaLiga", "Serie A", "Bundesliga"]
LEAGUE_SHORT = {"Champions League": "UCL", "Europa League": "UEL", "Premier League": "PREM",
                "LaLiga": "LIGA", "Serie A": "SERIE A", "Bundesliga": "BUNDES", "Süper Lig": "SÜPER LIG", "NFL": "NFL"}

# 5x5 mosaic letters for the block-graphic banners ("#" = lit cell)
FONT = {
    "A": [".###.", "#...#", "#####", "#...#", "#...#"],
    "E": ["#####", "#....", "####.", "#....", "#####"],
    "F": ["#####", "#....", "####.", "#....", "#...."],
    "I": ["#####", "..#..", "..#..", "..#..", "#####"],
    "K": ["#...#", "#..#.", "###..", "#..#.", "#...#"],
    "L": ["#....", "#....", "#....", "#....", "#####"],
    "N": ["#...#", "##..#", "#.#.#", "#..##", "#...#"],
    "O": [".###.", "#...#", "#...#", "#...#", ".###."],
    "P": ["####.", "#...#", "####.", "#....", "#...."],
    "R": ["####.", "#...#", "####.", "#..#.", "#...#"],
    "S": [".####", "#....", ".###.", "....#", "####."],
    "T": ["#####", "..#..", "..#..", "..#..", "..#.."],
    "U": ["#...#", "#...#", "#...#", "#...#", ".###."],
    "Y": ["#...#", ".#.#.", "..#..", "..#..", "..#.."],
    " ": [".....", ".....", ".....", ".....", "....."],
}

PAGES = [
    # number, banner word, title, fastext colour
    (300, "SPORT", "Index", None),
    (301, "TURKIYE", "Türkiye", "red"),
    (302, "EUROPE", "Europe", "green"),
    (303, "NFL", "NFL", "yellow"),
    (304, "TENNIS", "Tennis", "cyan"),
]


def esc(s) -> str:
    return html.escape(str(s if s is not None else ""), quote=True)


def mosaic(word: str, colour: str) -> str:
    """Block-graphic banner, drawn as a grid of cells like teletext mosaics."""
    cols = len(word) * 6 - 1
    cells = []
    for row in range(5):
        line = []
        for ch in word:
            line.append(FONT.get(ch, FONT[" "])[row] + ".")
        line = "".join(line)[:cols]
        cells += [f'<i class="{"on" if c == "#" else ""}"></i>' for c in line]
    return (f'<div class="mosaic mosaic-{colour}" style="--cols:{cols}" role="img" aria-label="{esc(word)}">'
            f'{"".join(cells)}</div>')


def is_turkish(text: str) -> bool:
    return bool(TR_PATTERN.search(text or ""))


def story_rows(items: list[dict], limit: int) -> str:
    rows = []
    for i in items[:limit]:
        src = i.get("sources") or []
        link = src[0]["url"] if src else ""
        head = f'<a href="{esc(link)}">{esc(i["headline"])}</a>' if link else esc(i["headline"])
        summary = f'<p class="sum">{esc(i["summary"])}</p>' if i.get("summary") else ""
        via = f'<span class="via">{esc(src[0]["name"])}</span>' if src else ""
        rows.append(f'<li class="story"><p class="hl">{head}</p>{summary}{via}</li>')
    return f'<ul class="stories">{"".join(rows)}</ul>' if rows else ""


def _row(left, mid, right, meta, lwon=False, rwon=False, live=False) -> str:
    return (f'<div class="r{" live" if live else ""}"><span class="{"win" if lwon else "team"} l">{esc(left)}</span>'
            f'<span class="sc">{mid}</span><span class="{"win" if rwon else "team"}">{esc(right)}</span>'
            f'<span class="meta">{meta}</span></div>')


def score_rows(games: list[dict], leagues: list[str], finished: bool, limit: int, show_league: bool) -> str:
    rows = []
    for lg in leagues:
        for g in games:
            if g["league"] != lg:
                continue
            nfl = lg == "NFL"
            left, right = (g["away"], g["home"]) if nfl else (g["home"], g["away"])
            lwon, rwon = (g["away_won"], g["home_won"]) if nfl else (g["home_won"], g["away_won"])
            ls, rs = (g["away_score"], g["home_score"]) if nfl else (g["home_score"], g["away_score"])
            tag = f'<span class="lg">{esc(LEAGUE_SHORT.get(lg, lg))}</span>' if show_league else ""
            if finished and g["state"] == "in":
                rows.insert(0, _row(left, f"{esc(ls)}-{esc(rs)}", right,
                                    f'{tag}<span class="livetag">LIVE {esc(g["detail"])}</span>', live=True))
            elif finished and g["state"] == "post":
                rows.append(_row(left, f"{esc(ls)}-{esc(rs)}", right, tag, lwon, rwon))
            elif not finished and g["state"] == "pre":
                rows.append(_row(left, "at" if nfl else "v", right, f'{tag}<span class="ko">{esc(g["start_pt"])}</span>'))
            if len(rows) >= limit:
                break
        if len(rows) >= limit:
            break
    return f'<div class="grid">{"".join(rows)}</div>' if rows else ""


def table_rows(rows: list[dict], limit: int) -> str:
    if not rows:
        return ""
    body = "".join(
        f'<tr class="{"hi" if r["pos"] <= 4 else ""}"><td class="pos">{r["pos"]}</td><td class="tm">{esc(r["team"])}</td>'
        f'<td>{r["p"]}</td><td>{r["w"]}</td><td>{r["d"]}</td><td>{r["l"]}</td>'
        f'<td class="gd">{"+" if r["gd"] > 0 else ""}{r["gd"]}</td><td class="pts">{r["pts"]}</td></tr>'
        for r in rows[:limit])
    return ('<table class="league"><thead><tr><th></th><th class="tm">Team</th><th>P</th><th>W</th><th>D</th>'
            f'<th>L</th><th class="gd">GD</th><th>Pts</th></tr></thead><tbody>{body}</tbody></table>')


def band(text: str, colour: str) -> str:
    return f'<h3 class="band band-{colour}">{esc(text)}</h3>'


def block(title: str, colour: str, inner: str) -> str:
    return f'{band(title, colour)}{inner}' if inner else ""


def render_teletext(ed: dict, raw: dict, now: dt.datetime) -> str:
    scores, tables = raw.get("scores", []), raw.get("tables", {})
    football = ed.get("football", [])
    tr_items = [i for i in football if is_turkish(i["headline"] + " " + i.get("summary", ""))]
    eu_items = [i for i in football if i not in tr_items]
    nfl_items, tennis_items = ed.get("nfl", []), ed.get("tennis", [])

    body = {
        301: "".join([
            block("TÜRKİYE: TOP STORIES", "blue", story_rows(tr_items, 4)),
            block("SÜPER LIG: RESULTS", "blue", score_rows(scores, ["Süper Lig"], True, 10, False)),
            block("SÜPER LIG: COMING UP (PT)", "magenta", score_rows(scores, ["Süper Lig"], False, 10, False)),
            block("SÜPER LIG: TABLE", "green", table_rows(tables.get("Süper Lig", []), 18)),
        ]),
        302: "".join([
            block("EUROPE: TOP STORIES", "blue", story_rows(eu_items, 4)),
            block("RESULTS", "blue", score_rows(scores, EUROPE_LEAGUES, True, 14, True)),
            block("COMING UP (PT)", "magenta", score_rows(scores, EUROPE_LEAGUES, False, 14, True)),
            block("PREMIER LEAGUE: TABLE", "green", table_rows(tables.get("Premier League", []), 20)),
        ]),
        303: "".join([
            block("NFL: TOP STORIES", "blue", story_rows(nfl_items, 4)),
            block("NFL: RESULTS", "blue", score_rows(scores, ["NFL"], True, 16, False)),
            block("NFL: COMING UP (PT)", "magenta", score_rows(scores, ["NFL"], False, 16, False)),
        ]),
        304: block("TENNIS: TOP STORIES", "blue", story_rows(tennis_items, 6)),
    }

    def index_line(no: int, label: str, colour: str) -> str:
        return (f'<li><a href="#p{no}" data-go="{no}"><span class="c-{colour}">{esc(label)}</span>'
                f'<span class="dots" aria-hidden="true"></span><span class="pno">{no}</span></a></li>')

    top = []
    for items, no in ((tr_items, 301), (eu_items, 302), (nfl_items, 303), (tennis_items, 304)):
        for i in items[:2]:
            top.append(f'<li><a href="#p{no}" data-go="{no}"><span class="c-white">{esc(i["headline"])}</span>'
                       f'<span class="dots" aria-hidden="true"></span><span class="pno">{no}</span></a></li>')
    body[300] = (
        band("TODAY'S HEADLINES", "blue")
        + (f'<ul class="index">{"".join(top)}</ul>' if top else '<p class="empty">No sport headlines came in today.</p>')
        + band("PAGES", "magenta")
        + '<ul class="index">'
        + index_line(301, "TÜRKİYE · SÜPER LIG", "red")
        + index_line(302, "EUROPE · UCL · PREMIER LEAGUE", "green")
        + index_line(303, "NFL", "yellow")
        + index_line(304, "TENNIS", "cyan")
        + "</ul>"
        + '<p class="hint">Type a page number, or use the coloured buttons below.</p>'
    )

    mosaic_colour = {300: "yellow", 301: "red", 302: "green", 303: "yellow", 304: "cyan"}
    sections = []
    for no, word, title, _c in PAGES:
        content = body[no] or '<p class="empty">Nothing on this page today. Check back tomorrow morning.</p>'
        sections.append(
            f'<section class="ttx-page" id="p{no}" data-page="{no}" aria-labelledby="t{no}">'
            f'<h2 class="sr" id="t{no}">P{no} {esc(title)}</h2>{mosaic(word, mosaic_colour[no])}{content}</section>')

    stamp = now.strftime("%a %d %b")
    clock = now.strftime("%H:%M:%S")
    return PAGE.replace("{{STAMP}}", stamp).replace("{{CLOCK}}", clock) \
               .replace("{{BUILT}}", now.strftime("%-I:%M %p PT, %a %b %-d")) \
               .replace("{{PAGES}}", "\n".join(sections))


PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Dispatch Sport</title>
<meta name="description" content="Teletext-style sport pages: Süper Lig, European football, NFL and tennis, updated every morning.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=VT323&display=swap" rel="stylesheet">
<style>
/* Layout: a 1980s teletext screen. Header row with page number and clock, mosaic banner,
   coloured bands over score grids, fastext buttons along the bottom. Single black theme by choice. */
:root {
  --black: #000; --red: #ff3b30; --green: #00f000; --yellow: #ffff00;
  --blue: #1010e0; --magenta: #ff00ff; --cyan: #00ffff; --white: #ffffff;
  --ttx: "VT323", "Courier New", ui-monospace, monospace;
  color-scheme: dark;
}
* { box-sizing: border-box; }
html, body { margin: 0; background: var(--black); color: var(--white); }
body { font-family: var(--ttx); font-size: 24px; line-height: 1.15; -webkit-font-smoothing: none; }
a { color: inherit; text-decoration: none; }
a:hover { text-decoration: underline; text-underline-offset: 3px; }
a:focus-visible, button:focus-visible { outline: 2px solid var(--yellow); outline-offset: 2px; }
.screen { max-width: 880px; margin: 0 auto; padding: 12px 16px 96px; position: relative; }
.screen::after { /* faint scanlines */
  content: ""; position: fixed; inset: 0; pointer-events: none;
  background: repeating-linear-gradient(to bottom, rgba(255,255,255,0.03) 0 1px, transparent 1px 3px);
}
.sr { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); }

/* header row */
.ttx-head { display: flex; flex-wrap: wrap; gap: 0 14px; align-items: baseline; padding: 4px 0 10px; }
.ttx-head .pno { color: var(--white); }
.ttx-head .entry { color: var(--yellow); min-width: 3ch; }
.ttx-head .svc { color: var(--cyan); flex: 1; }
.ttx-head .date { color: var(--white); }
.ttx-head .clock { color: var(--yellow); font-variant-numeric: tabular-nums; }
.ttx-head a { color: var(--white); }

/* mosaic banner */
.mosaic { display: grid; grid-template-columns: repeat(var(--cols), 1fr); gap: 0; width: min(100%, calc(var(--cols) * 18px));
  margin: 6px 0 14px; padding: 8px; background: var(--blue); aspect-ratio: calc(var(--cols) + 1) / 6.2; }
.mosaic i { display: block; }
.mosaic-yellow i.on { background: var(--yellow); }
.mosaic-red i.on { background: var(--red); }
.mosaic-green i.on { background: var(--green); }
.mosaic-cyan i.on { background: var(--cyan); }

/* coloured bands */
.band { font-weight: normal; font-size: 26px; margin: 18px 0 6px; padding: 2px 10px; letter-spacing: 0.04em; }
.band-blue { background: var(--blue); color: var(--yellow); }
.band-magenta { background: var(--magenta); color: var(--white); }
.band-green { background: var(--green); color: var(--black); }

/* index */
.index { list-style: none; margin: 0; padding: 0; display: grid; gap: 4px; }
.index a { display: flex; gap: 8px; align-items: baseline; }
.index .dots { flex: 1; border-bottom: 2px dotted rgba(255,255,255,0.35); transform: translateY(-5px); min-width: 20px; }
.index .pno { color: var(--yellow); }
.c-red { color: var(--red); } .c-green { color: var(--green); } .c-yellow { color: var(--yellow); }
.c-cyan { color: var(--cyan); } .c-white { color: var(--white); }
.hint, .empty { color: var(--cyan); margin: 14px 0 0; }

/* stories */
.stories { list-style: none; margin: 0; padding: 0; display: grid; gap: 12px; }
.story .hl { margin: 0; color: var(--white); }
.story .hl a { color: var(--white); }
.story .sum { margin: 2px 0 0; color: var(--cyan); }
.story .via { color: var(--green); font-size: 20px; }

/* score grids */
.grid { display: grid; gap: 2px; }
.grid .r { display: grid; grid-template-columns: minmax(0, 1fr) 4.5ch minmax(0, 1fr) auto; gap: 0 10px; align-items: baseline; }
.grid .team, .grid .win { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.grid .team { color: var(--cyan); }
.grid .win { color: var(--white); }
.grid .l { text-align: right; }
.grid .sc { color: var(--yellow); text-align: center; white-space: nowrap; font-variant-numeric: tabular-nums; }
.grid .meta { text-align: right; white-space: nowrap; }
.grid .lg { color: var(--green); margin-right: 10px; }
.grid .ko { color: var(--white); }
.livetag { color: var(--red); animation: blink 1.2s steps(2, start) infinite; }
@keyframes blink { to { visibility: hidden; } }

/* league tables */
.league { width: 100%; border-collapse: collapse; font-variant-numeric: tabular-nums; }
.league th { color: var(--yellow); font-weight: normal; text-align: right; padding: 0 4px; }
.league td { text-align: right; padding: 0 4px; color: var(--white); }
.league .tm { text-align: left; width: 50%; max-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.league td.tm { color: var(--cyan); }
.league .pos { color: var(--white); width: 2ch; }
.league .pts { color: var(--yellow); }
.league tr.hi td.tm { color: var(--white); }

/* fastext bar */
.fastext { position: fixed; left: 0; right: 0; bottom: 0; background: var(--black); border-top: 2px solid #222; }
.fastext .row { max-width: 880px; margin: 0 auto; padding: 8px 16px calc(8px + env(safe-area-inset-bottom)); display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; }
.fastext a { display: block; text-align: center; padding: 6px 4px; color: var(--black); font-size: 22px; }
.fastext a:hover { text-decoration: none; filter: brightness(1.15); }
.fx-red { background: var(--red); } .fx-green { background: var(--green); }
.fx-yellow { background: var(--yellow); } .fx-cyan { background: var(--cyan); }
.foot { color: var(--green); font-size: 20px; margin-top: 26px; }
.foot a { color: var(--white); text-decoration: underline; }

/* one page at a time when JS is on */
.js .ttx-page { display: none; }
.js .ttx-page.on { display: block; }
.ttx-page + .ttx-page { margin-top: 40px; }
.js .ttx-page + .ttx-page { margin-top: 0; }

@media (max-width: 560px) {
  body { font-size: 21px; }
  .ttx-head .date { display: none; }
  .ttx-head .svc { flex: 1; }
  .band { font-size: 22px; }
  .grid .r { grid-template-columns: minmax(0, 1fr) 4ch minmax(0, 1fr); }
  .grid .meta { grid-column: 1 / -1; text-align: center; font-size: 18px; margin-top: -2px; margin-bottom: 4px; }
  .league .gd { display: none; }
  .fastext a { font-size: 18px; }
}
@media (prefers-reduced-motion: reduce) { .livetag { animation: none; } }
</style>
</head>
<body>
<div class="screen">
  <header class="ttx-head">
    <span class="pno">P<span id="pno">300</span></span>
    <span class="entry" id="entry" aria-live="polite"></span>
    <span class="svc"><a href="/dispatch/">DISPATCH</a> SPORT</span>
    <span class="date">{{STAMP}}</span>
    <span class="clock" id="clock">{{CLOCK}}</span>
  </header>
  {{PAGES}}
  <p class="foot">Updated {{BUILT}} · Scores via ESPN · <a href="/dispatch/">Back to the Dispatch</a></p>
</div>
<nav class="fastext" aria-label="Sport pages">
  <div class="row">
    <a class="fx-red" href="#p301" data-go="301">Türkiye</a>
    <a class="fx-green" href="#p302" data-go="302">Europe</a>
    <a class="fx-yellow" href="#p303" data-go="303">NFL</a>
    <a class="fx-cyan" href="#p304" data-go="304">Tennis</a>
  </div>
</nav>
<script>
(function () {
  document.documentElement.classList.add("js");
  var pages = Array.prototype.slice.call(document.querySelectorAll(".ttx-page"));
  var nums = pages.map(function (p) { return p.dataset.page; });
  var pno = document.getElementById("pno"), entry = document.getElementById("entry");
  function show(n) {
    if (nums.indexOf(String(n)) < 0) n = "300";
    pages.forEach(function (p) { p.classList.toggle("on", p.dataset.page === String(n)); });
    pno.textContent = n;
    window.scrollTo(0, 0);
  }
  function fromHash() { show((location.hash.match(/^#p(\\d{3})$/) || [])[1] || "300"); }
  window.addEventListener("hashchange", fromHash);
  fromHash();

  // remote control: type three digits to jump to a page; arrows step through pages
  var typed = "", timer;
  document.addEventListener("keydown", function (e) {
    if (e.metaKey || e.ctrlKey || e.altKey) return;
    if (/^[0-9]$/.test(e.key)) {
      typed += e.key; entry.textContent = typed; clearTimeout(timer);
      if (typed.length === 3) {
        var target = typed; typed = "";
        setTimeout(function () { entry.textContent = ""; location.hash = "p" + target; }, 250);
      } else {
        timer = setTimeout(function () { typed = ""; entry.textContent = ""; }, 2500);
      }
    } else if (e.key === "ArrowRight" || e.key === "ArrowLeft") {
      var i = nums.indexOf(pno.textContent) + (e.key === "ArrowRight" ? 1 : -1);
      location.hash = "p" + nums[(i + nums.length) % nums.length];
    }
  });

  // live clock, Pacific time
  var clock = document.getElementById("clock");
  function tick() {
    try {
      clock.textContent = new Date().toLocaleTimeString("en-GB", { timeZone: "America/Los_Angeles", hour12: false });
    } catch (err) { /* keep the build time */ }
  }
  tick(); setInterval(tick, 1000);
})();
</script>
</body>
</html>
"""
