#!/usr/bin/env python3
"""Build today's edition of The Morning Dispatch.

Runs every morning in GitHub Actions. Standard library only, no installs.

  1. Collect: RSS headlines per desk, scores from ESPN's public scoreboards,
     index quotes from Yahoo Finance. Any source that fails is skipped.
  2. Write: if ANTHROPIC_API_KEY is set, Claude turns the raw material into a
     short edition (lead story + summaries). Otherwise the page lists the
     headlines with links.
  3. Render: dispatch/index.html, plus a dated copy in dispatch/archive/.

Local test without network:  python scripts/build_dispatch.py --fixture tests/sample.json
"""
from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import os
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "dispatch"
STATE_FILE = OUT_DIR / "state.json"
TEMPLATE = ROOT / "scripts" / "template.html"
PT = ZoneInfo("America/Los_Angeles")
UA = "Mozilla/5.0 (compatible; MorningDispatch/1.0; +https://github.com)"

# ---------------------------------------------------------------- sources
# Edit these lists to change what the Dispatch reads.
FEEDS = {
    "ai": [
        ("TechCrunch AI", "https://techcrunch.com/category/artificial-intelligence/feed/"),
        ("The Verge AI", "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml"),
        ("Ars Technica", "https://feeds.arstechnica.com/arstechnica/technology-lab"),
        ("MIT Tech Review", "https://www.technologyreview.com/topic/artificial-intelligence/feed"),
    ],
    "finance": [
        ("CNBC Markets", "https://www.cnbc.com/id/15839069/device/rss/rss.html"),
        ("CNBC Top News", "https://www.cnbc.com/id/100003114/device/rss/rss.html"),
        ("MarketWatch", "https://feeds.content.dowjones.io/public/rss/mw_topstories"),
    ],
    "football": [
        ("BBC Football", "https://feeds.bbci.co.uk/sport/football/rss.xml"),
        ("Daily Sabah Football", "https://www.dailysabah.com/rss/sports/football"),
        ("ESPN Soccer", "https://www.espn.com/espn/rss/soccer/news"),
    ],
    "nfl": [
        ("ESPN NFL", "https://www.espn.com/espn/rss/nfl/news"),
    ],
    "tennis": [
        ("ESPN Tennis", "https://www.espn.com/espn/rss/tennis/news"),
    ],
}

ESPN = "https://site.api.espn.com/apis/site/v2/sports"
SCOREBOARDS = [
    # (label, path, desk)
    ("NFL", "football/nfl", "nfl"),
    ("Süper Lig", "soccer/tur.1", "football"),
    ("Premier League", "soccer/eng.1", "football"),
    ("LaLiga", "soccer/esp.1", "football"),
    ("Serie A", "soccer/ita.1", "football"),
    ("Bundesliga", "soccer/ger.1", "football"),
    ("Champions League", "soccer/uefa.champions", "football"),
    ("Europa League", "soccer/uefa.europa", "football"),
]
QUOTES = [("S&P 500", "^GSPC"), ("Dow", "^DJI"), ("Nasdaq", "^IXIC"), ("10-yr yield", "^TNX")]

MAX_PER_FEED = 8
LOOKBACK_HOURS = 30


# ---------------------------------------------------------------- helpers
def log(msg: str) -> None:
    print(msg, file=sys.stderr)


def fetch(url: str, timeout: int = 15, headers: dict | None = None, data: bytes | None = None) -> bytes:
    req = urllib.request.Request(url, data=data, headers={"User-Agent": UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def clean(text: str | None, limit: int = 0) -> str:
    text = re.sub(r"<[^>]+>", " ", text or "")
    text = html.unescape(re.sub(r"\s+", " ", text)).strip()
    if limit and len(text) > limit:
        text = text[: limit].rsplit(" ", 1)[0] + "…"
    return text


def parse_date(s: str | None) -> dt.datetime | None:
    if not s:
        return None
    from email.utils import parsedate_to_datetime
    try:
        d = parsedate_to_datetime(s)
    except (TypeError, ValueError):
        try:
            d = dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
        except ValueError:
            return None
    return d if d.tzinfo else d.replace(tzinfo=dt.timezone.utc)


# ---------------------------------------------------------------- collect
def read_feed(source: str, url: str) -> list[dict]:
    root = ET.fromstring(fetch(url))
    ns = {"a": "http://www.w3.org/2005/Atom"}
    items = []
    for it in root.iter("item"):  # RSS 2.0
        items.append({
            "title": clean(it.findtext("title")),
            "url": (it.findtext("link") or "").strip(),
            "summary": clean(it.findtext("description"), 300),
            "published": parse_date(it.findtext("pubDate")),
        })
    for it in root.findall("a:entry", ns):  # Atom
        link = it.find("a:link[@rel='alternate']", ns)
        if link is None:  # Elements without children are falsy, so no `or` here
            link = it.find("a:link", ns)
        items.append({
            "title": clean(it.findtext("a:title", namespaces=ns)),
            "url": link.get("href", "") if link is not None else "",
            "summary": clean(it.findtext("a:summary", namespaces=ns), 300),
            "published": parse_date(it.findtext("a:updated", namespaces=ns)),
        })
    cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=LOOKBACK_HOURS)
    out = []
    for i in items:
        if not i["title"] or not i["url"].startswith("http"):
            continue
        if i["published"] and i["published"] < cutoff:
            continue
        i["source"] = source
        i["published"] = i["published"].isoformat() if i["published"] else None
        out.append(i)
    return out[:MAX_PER_FEED]


def read_scoreboard(label: str, path: str) -> list[dict]:
    data = json.loads(fetch(f"{ESPN}/{path}/scoreboard"))
    games = []
    for ev in data.get("events", []):
        comp = (ev.get("competitions") or [{}])[0]
        teams = comp.get("competitors", [])
        if len(teams) != 2:
            continue
        home = next((t for t in teams if t.get("homeAway") == "home"), teams[0])
        away = next((t for t in teams if t.get("homeAway") == "away"), teams[1])
        status = ev.get("status", {}).get("type", {})
        state = status.get("state")  # pre / in / post
        start = parse_date(ev.get("date"))
        games.append({
            "league": label,
            "home": home["team"].get("shortDisplayName") or home["team"].get("displayName"),
            "away": away["team"].get("shortDisplayName") or away["team"].get("displayName"),
            "home_score": home.get("score") if state != "pre" else None,
            "away_score": away.get("score") if state != "pre" else None,
            "home_won": bool(home.get("winner")),
            "away_won": bool(away.get("winner")),
            "state": state,
            "detail": status.get("shortDetail", ""),
            "start_pt": start.astimezone(PT).strftime("%a %-I:%M %p") if start else "",
            "start_iso": start.isoformat() if start else "",
        })
    return games


def read_quote(name: str, symbol: str) -> dict:
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.request.quote(symbol)}?range=5d&interval=1d"
    meta = json.loads(fetch(url))["chart"]["result"][0]["meta"]
    price, prev = meta["regularMarketPrice"], meta.get("chartPreviousClose") or meta.get("previousClose")
    pct = (price - prev) / prev * 100 if prev else 0.0
    return {"name": name, "symbol": symbol, "price": price, "pct": pct}


def collect() -> dict:
    raw = {"feeds": {}, "scores": [], "quotes": [], "errors": []}
    for desk, feeds in FEEDS.items():
        raw["feeds"][desk] = []
        for source, url in feeds:
            try:
                raw["feeds"][desk] += read_feed(source, url)
            except Exception as e:  # noqa: BLE001 - one bad feed must not stop the edition
                raw["errors"].append(f"{source}: {e}")
    for label, path, _desk in SCOREBOARDS:
        try:
            raw["scores"] += read_scoreboard(label, path)
        except Exception as e:  # noqa: BLE001
            raw["errors"].append(f"{label} scores: {e}")
    for name, symbol in QUOTES:
        try:
            raw["quotes"].append(read_quote(name, symbol))
        except Exception as e:  # noqa: BLE001
            raw["errors"].append(f"{name} quote: {e}")
    for e in raw["errors"]:
        log(f"skipped: {e}")
    return raw


# ---------------------------------------------------------------- write (Claude)
PROMPT = """You are the editor of The Morning Dispatch, a one-page morning briefing for a reader in the San Francisco Bay Area.
Today is {today}. Below is raw material gathered in the last ~30 hours: headlines with links and teaser text, sports scores, and market quotes.

Write today's edition as JSON with exactly this shape:
{{
  "lead": {{"kicker": "Lead · <desk>", "headline": "...", "paragraphs": ["...", "..."],
            "facts": [["label", "value"], ...], "sources": [{{"name": "...", "url": "..."}}]}},
  "ai": [item, ...],          // 3-4 items: frontier labs, big tech, chips, major funding, AI policy
  "finance": [item, ...],     // 3 items: the market move and why, a notable mover, what to watch
  "football": [item, ...],    // 1-3 items: Türkiye clubs and national team first, then Europe's top leagues and the Champions League
  "nfl": [item, ...],         // 1-2 items
  "tennis": [item, ...]       // 0-1 items, only for a big event (Grand Slam, ATP/WTA Finals, Masters 1000, Davis Cup)
}}
where item = {{"headline": "...", "summary": "1-3 sentences", "sources": [{{"name": "...", "url": "..."}}]}}.

Rules:
- Use only facts present in the material. Never invent numbers, scores, quotes or dates.
- Every source url must be copied exactly from the material.
- Write summaries in your own words, in plain direct English. Do not copy sentences from the teasers.
- The lead is the single biggest story of the day across all desks; do not repeat it in a desk.
- "facts" holds 3-6 short label/value pairs about the lead; use [] if none fit.
- Prefer news over opinion, and skip minor product updates and listicles.
- Output the JSON object only, with no other text.

MATERIAL:
{material}
"""


def write_with_claude(raw: dict, today: str) -> dict | None:
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        return None
    model = os.environ.get("DISPATCH_MODEL") or "claude-sonnet-5-5"
    material = json.dumps({"headlines": raw["feeds"], "scores": raw["scores"], "quotes": raw["quotes"]},
                          ensure_ascii=False)[:120_000]
    body = json.dumps({
        "model": model,
        "max_tokens": 4000,
        "messages": [{"role": "user", "content": PROMPT.format(today=today, material=material)}],
    }).encode()
    try:
        resp = json.loads(fetch("https://api.anthropic.com/v1/messages", timeout=180, data=body, headers={
            "x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"}))
        text = "".join(b.get("text", "") for b in resp.get("content", []))
        edition = json.loads(text[text.find("{"): text.rfind("}") + 1])
    except Exception as e:  # noqa: BLE001 - fall back to the headlines-only edition
        log(f"Claude step failed, using headlines only: {e}")
        return None
    return keep_known_links(edition, raw)


def keep_known_links(edition: dict, raw: dict) -> dict:
    """Drop any source link that wasn't in the material, so nothing made-up gets published."""
    known = {i["url"] for items in raw["feeds"].values() for i in items}

    def fix(item: dict) -> dict:
        item["sources"] = [s for s in item.get("sources", []) if s.get("url") in known]
        return item

    if edition.get("lead"):
        fix(edition["lead"])
    for desk in ("ai", "finance", "football", "nfl", "tennis"):
        edition[desk] = [fix(i) for i in edition.get(desk, []) if i.get("headline")]
    return edition


def headlines_only(raw: dict) -> dict:
    """Edition built without Claude: newest headlines per desk, deduplicated."""
    def pick(desk: str, n: int) -> list[dict]:
        seen, out = set(), []
        items = sorted(raw["feeds"].get(desk, []), key=lambda i: i["published"] or "", reverse=True)
        for i in items:
            k = re.sub(r"\W+", "", i["title"].lower())[:60]
            if k in seen:
                continue
            seen.add(k)
            out.append({"headline": i["title"], "summary": "", "sources": [{"name": i["source"], "url": i["url"]}]})
            if len(out) == n:
                break
        return out

    return {"lead": None, "ai": pick("ai", 6), "finance": pick("finance", 5),
            "football": pick("football", 4), "nfl": pick("nfl", 3), "tennis": pick("tennis", 2)}


# ---------------------------------------------------------------- render
def esc(s) -> str:
    return html.escape(str(s or ""), quote=True)


def sources_line(sources: list[dict]) -> str:
    links = [f'<a href="{esc(s["url"])}">{esc(s["name"])}</a>' for s in sources if s.get("url")]
    return f'<p class="src">{" · ".join(links)}</p>' if links else ""


def render_items(items: list[dict]) -> str:
    out = []
    for i in items:
        summary = f'<p>{esc(i["summary"])}</p>' if i.get("summary") else ""
        out.append(f'<article class="item"><h3>{esc(i["headline"])}</h3>{summary}{sources_line(i.get("sources", []))}</article>')
    return "\n".join(out)


def render_ticker(quotes: list[dict]) -> str:
    if not quotes:
        return ""
    cells = []
    for q in quotes:
        cls = "up" if q["pct"] >= 0 else "down"
        sign = "+" if q["pct"] >= 0 else "−"
        val = f'{q["price"]:.2f}%' if q["symbol"] == "^TNX" else f'{q["price"]:,.2f}'
        cells.append(f'<div class="tick"><span class="name">{esc(q["name"])}</span>'
                     f'<span class="val">{val}</span><span class="chg {cls}">{sign}{abs(q["pct"]):.2f}%</span></div>')
    return (f'<section aria-label="Markets"><div class="ticker">{"".join(cells)}</div>'
            f'<div class="ticker-note">Latest prices when this edition was built. Change is from the previous close.</div></section>')


def render_lead(lead: dict | None) -> str:
    if not lead:
        return ""
    paras = "".join(f"<p>{esc(p)}</p>" for p in lead.get("paragraphs", []))
    facts = "".join(f'<div class="fact"><span>{esc(a)}</span><span>{esc(b)}</span></div>'
                    for a, b in lead.get("facts", []))
    aside = f'<aside class="facts" aria-label="At a glance"><h3>At a glance</h3>{facts}</aside>' if facts else ""
    return (f'<section class="lead{"" if aside else " solo"}"><div><div class="kicker">{esc(lead.get("kicker", "Lead"))}</div>'
            f'<h2>{esc(lead["headline"])}</h2>{paras}{sources_line(lead.get("sources", []))}</div>{aside}</section>')


def render_scores(scores: list[dict], leagues: set[str], finished: bool, limit: int) -> str:
    rows = []
    for g in scores:
        if g["league"] not in leagues:
            continue
        if finished and g["state"] == "post":
            a = f'<span class="w">{esc(g["away"])}</span>' if g["away_won"] else esc(g["away"])
            h = f'<span class="w">{esc(g["home"])}</span>' if g["home_won"] else esc(g["home"])
            sep = " at " if g["league"] == "NFL" else " v "
            left, right = (a, h) if g["league"] == "NFL" else (h, a)
            score = (f'{g["away_score"]}–{g["home_score"]}' if g["league"] == "NFL"
                     else f'{g["home_score"]}–{g["away_score"]}')
            rows.append(f'<tr><td>{left}{sep}{right} <span class="lg">{esc(g["league"])}</span></td><td class="n">{score}</td></tr>')
        elif not finished and g["state"] == "pre":
            sep, (left, right) = (" at ", (g["away"], g["home"])) if g["league"] == "NFL" else (" v ", (g["home"], g["away"]))
            rows.append(f'<tr><td>{esc(left)}{sep}{esc(right)} <span class="lg">{esc(g["league"])}</span></td>'
                        f'<td class="n">{esc(g["start_pt"])}</td></tr>')
        if len(rows) == limit:
            break
    if not rows:
        return ""
    title = "Results" if finished else "Coming up (PT)"
    return f'<div class="table-block"><div class="tlabel">{title}</div><table class="scores">{"".join(rows)}</table></div>'


def render_sports(ed: dict, scores: list[dict]) -> str:
    soccer = {lbl for lbl, _p, d in SCOREBOARDS if d == "football"}
    parts = []
    football = render_items(ed.get("football", [])) + render_scores(scores, soccer, True, 8) + render_scores(scores, soccer, False, 6)
    if football.strip():
        parts.append(f'<div class="sub">Football: Türkiye &amp; Europe</div>{football}')
    nfl = render_items(ed.get("nfl", [])) + render_scores(scores, {"NFL"}, True, 8) + render_scores(scores, {"NFL"}, False, 4)
    if nfl.strip():
        parts.append(f'<div class="sub">NFL</div>{nfl}')
    if ed.get("tennis"):
        parts.append(f'<div class="sub">Tennis</div>{render_items(ed["tennis"])}')
    return "\n".join(parts) or '<p class="src">No sports news came in today.</p>'


def render(ed: dict, raw: dict, now: dt.datetime, edition_no: int, mode: str) -> str:
    def desk(items: list[dict]) -> str:
        return render_items(items) or '<p class="src">No new stories came in today.</p>'

    swap = {
        "{{DATE}}": now.strftime("%A, %B %-d, %Y"),
        "{{EDITION}}": str(edition_no),
        "{{TICKER}}": render_ticker(raw["quotes"]),
        "{{LEAD}}": render_lead(ed.get("lead")),
        "{{AI}}": desk(ed.get("ai", [])),
        "{{SPORTS}}": render_sports(ed, raw["scores"]),
        "{{FINANCE}}": desk(ed.get("finance", [])),
        "{{BUILT}}": now.strftime("%-I:%M %p PT, %a %b %-d"),
        "{{MODE}}": "Summaries written by Claude from the linked sources." if mode == "claude"
                    else "Headlines from the linked sources.",
    }
    page = TEMPLATE.read_text(encoding="utf-8")
    for k, v in swap.items():
        page = page.replace(k, v)
    return page


def write_archive_index() -> None:
    days = sorted((p.stem for p in (OUT_DIR / "archive").glob("20*.html")), reverse=True)
    rows = "".join(
        f'<li><a href="{d}.html">{dt.date.fromisoformat(d).strftime("%A, %B %-d, %Y")}</a></li>' for d in days)
    page = TEMPLATE.read_text(encoding="utf-8")
    head = page[: page.index("<body>")]
    (OUT_DIR / "archive" / "index.html").write_text(
        head + '<body><div class="wrap"><nav class="topnav"><a href="/dispatch/">← Today\'s edition</a></nav>'
        '<header class="mast"><h1>Past editions</h1></header>'
        f'<ul class="archive">{rows}</ul></div></body></html>', encoding="utf-8")


# ---------------------------------------------------------------- main
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fixture", help="use saved raw material instead of fetching (for testing)")
    ap.add_argument("--save-raw", help="also save the fetched material to this path")
    args = ap.parse_args()

    now = dt.datetime.now(PT)
    raw = json.loads(Path(args.fixture).read_text()) if args.fixture else collect()
    if args.save_raw:
        Path(args.save_raw).write_text(json.dumps(raw, ensure_ascii=False, indent=1))

    ed = write_with_claude(raw, now.strftime("%A, %B %-d, %Y"))
    mode = "claude" if ed else "headlines"
    ed = ed or headlines_only(raw)

    state = json.loads(STATE_FILE.read_text()) if STATE_FILE.exists() else {"edition": 0, "last_date": ""}
    today = now.date().isoformat()
    if state["last_date"] != today:
        state = {"edition": state["edition"] + 1, "last_date": today}

    page = render(ed, raw, now, state["edition"], mode)
    OUT_DIR.mkdir(exist_ok=True)
    (OUT_DIR / "index.html").write_text(page, encoding="utf-8")
    (OUT_DIR / "archive").mkdir(exist_ok=True)
    (OUT_DIR / "archive" / f"{today}.html").write_text(page, encoding="utf-8")
    write_archive_index()
    if not args.fixture:
        STATE_FILE.write_text(json.dumps(state))
    n = sum(len(ed.get(d, [])) for d in ("ai", "finance", "football", "nfl", "tennis"))
    log(f"Edition {state['edition']} built ({mode}): {n} stories, {len(raw['scores'])} games, {len(raw['quotes'])} quotes.")


if __name__ == "__main__":
    main()
