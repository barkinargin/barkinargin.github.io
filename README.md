# barkinargin.github.io

Personal site, **The Morning Dispatch** (daily AI & tech and finance front page, at /dispatch) and **Dispatch Sport** (teletext-style scores and tables, at /sport).

## How the Dispatch works

Every morning at 5:44 AM Pacific, `.github/workflows/dispatch.yml` runs `scripts/build_dispatch.py`, which:

1. **Collects** headlines from RSS feeds, scores from ESPN's public scoreboards, and index quotes. A source that fails is skipped.
2. **Writes** the edition. If the repo has an `ANTHROPIC_API_KEY` secret, Claude writes a lead story and short summaries, and any link that wasn't in the source material is dropped. Without a key, the page lists the headlines with links.
3. **Publishes** `dispatch/index.html` plus a dated copy in `dispatch/archive/`, commits them, and deploys the site to GitHub Pages.

To change the sources, edit the `FEEDS` and `SCOREBOARDS` lists at the top of the script. To change the design, edit `scripts/template.html`.

## Setup (one time)

1. **Settings → Pages → Build and deployment → Source: GitHub Actions.**
2. *(Optional)* **Settings → Secrets and variables → Actions → New repository secret** named `ANTHROPIC_API_KEY`, holding a key from console.anthropic.com. This turns on the Claude-written summaries. It's billed per use, separately from a claude.ai subscription.
3. *(Optional)* Add a repository **variable** `DISPATCH_MODEL` to pick the model. The default is `claude-sonnet-5-5`; `claude-haiku-5-5` is cheaper.
4. To publish an edition now: **Actions → Morning Dispatch → Run workflow**.

## Custom domain

Buy a domain, then follow GitHub's guide for an apex domain: add the four `A` records for GitHub Pages at your registrar and enter the domain under **Settings → Pages → Custom domain**.

## Test locally

```
python scripts/build_dispatch.py --fixture tests/sample.json
```
