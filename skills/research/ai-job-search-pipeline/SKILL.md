---
name: ai-job-search-pipeline
description: Use when setting up an AI-assisted job search or job digest.
---

# AI-Assisted Job Search Pipeline

Reddit-validated tooling + working anonymous scrapers for a candidate job hunt.
Use when the user wants job-search automation, recommends career-ops, asks for
LinkedIn/remote/intern coverage, or wants a recurring job digest.

## The Reddit consensus (r/hermesagent "Anyone using hermes agent for job search?", 2026-08)
1. **santifer/career-ops** is THE recommended repo (~64K★): A-F evaluation rubric,
   per-JD tailored PDF CVs, application tracker, 82 job-board providers (Greenhouse,
   Ashby, Lever, Workday, Amazon, HN Who's Hiring, …), human-in-the-loop (never
   auto-submits). Runs in any AI coding CLI; free AI engine paths exist.
2. **starMagic/career-ops-hermes** is a native Hermes port with 17 SKILL.md files
   (scan, evaluate, tracker, followup, interview-prep, apply, …). Install:
   `cd <repo> && ./install.sh` → lands in ~/.hermes/skills/.
3. Anti-bot is the #1 blocker on LinkedIn/Indeed — prefer ATS APIs + guest endpoints.
4. Majority workflow pattern: cron scan → Telegram digest → tailor CV per JD → apply
   to only top scores (≥4.0/5). Auto-apply bots (LazyApply etc.) are widely panned.

## Setup (verified on this box)
- Repos live in /opt/work/repos/ (NEVER /data — 500MB cap; see memory).
- career-ops needs: `npm install` with `PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1`, then
  `PLAYWRIGHT_BROWSERS_PATH=/opt/work/.pw-browsers npx playwright install chromium`
  (browsers are ~650MB — must NOT go in ~/.cache on a capped box).
- `node doctor.mjs` gate: needs config/profile.yml, cv.md, modes/_profile.md, portals.yml.
- Scan works zero-token: `node scan.mjs --dry-run` (do NOT pass --dry-run for real runs).
- `node scan.mjs` output lines look like `+ Company | Title | Location` — grep them.
- Node ≥22.5 recommended for the SQLite tracker index; markdown tracker works on v20.

## Free anonymous LinkedIn routes (tested from datacenter IP)
See `references/linkedin-anonymous-routes.md` (also saved under open-source-api-recon):
- Guest jobs API (`/jobs-guest/api/seeMoreJobPostings/search`) — jobs tab, no login.
  Add `f_TPR=r86400` for last-24h freshness and `f_WT=2` for remote. Parse the HTML:
  split cards on `base-search-card--link` (NOT `base-search-card` — the shorter token
  also appears in class definitions and fragments the cards), title in
  `<span class="sr-only">`, company as the TEXT of `class="hidden-nested-link"`
  (matches `>  DLA Piper  </a>` with re.S; the href is a tracker link, not the name),
  location in `job-search-card__location`.
- Company page (`/company/<name>/`) — HR job-posts as company updates, `"text"` blobs.
- Post permalink (`/feed/update/urn:li:activity:<ID>/`) — full post body in og:description, no login.
- Personal profiles `/in/<handle>/` → HTTP 999 (blocked) — camoufox+noVNC for that.
- python-jobspy `scrape_jobs(site_name=['linkedin'], ...)` uses the guest API; pass a
  VALID `country_indeed` string (empty string raises ValueError).

## Free non-LinkedIn sources (no keys)
- Remotive API: `https://remotive.com/api/remote-jobs?search=<kw>&limit=N` (remote-only).
- HN Who is hiring: Algolia HN API + parse top-level comments.
- career-ops scan (82 providers incl. HN, Remotive, Himalayas, EchoJobs, 4 Day Week).

## Daily digest pattern (watchdog cron)
- `no_agent=true` cron + a script whose STDOUT is the digest: non-empty stdout is
  delivered to Telegram, empty stdout = silent day (no spam). Script exits 0 always.
- Script pattern: run scan → grep titles for target keywords, exclude seniority words
  (`Senior|Lead|Staff|Principal|Director|Manager`), filter for
  `junior|entry|intern|graduate|data engineer|data analyst|devops|etl|spark|kafka|...`.
- Scope user's target: Data Engineer + DevOps, internships, remote worldwide (Egypt-based).
- **Dedupe hygiene**: persist a seen-set (`/opt/work/.jobhunt_cache/seen.json`) and only
  print items not seen in previous runs — otherwise every cron tick re-sends the same
  listings. Full unified scanner at /opt/work/jobhunt_scanner.py (JobSpy guest API +
  company posts + Remotive + HN + career-ops scan; ~4 min per run).

## Arctic-Shift (Reddit archive) API limits — verified 2026-08
- `limit=200` → HTTP 400; use `limit=100` (r/hermesagent serves 100 fine).
- `after=<id>` / `after=t3_<id>` pagination → HTTP 400 (broken). You get ONE page of
  the most recent ~100 posts per sub; no deep pagination.
- Some big subs (r/cscareerquestions, r/dataengineering) → HTTP 422 Unprocessable
  even at limit=100; a 0-posts result may actually be an error — probe the raw status.
- Treat `{"data": null, "error": "Timeout. Maybe slow down a bit"}` as rate-limit;
  back off 4-8s between calls.

## Pitfalls
- `npm install` runs a playwright postinstall that fails with ENOSPC on a capped
  filesystem — set PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1 and install browsers separately
  with PLAYWRIGHT_BROWSERS_PATH pointing outside /data.
- career-ops scan output mixes all seniority levels; always exclude senior keywords.
- Old skill notes saying "LinkedIn blocks ALL anonymous access" are OUTDATED — the
  guest API, company pages and activity permalinks work; re-verify before relying.
- A `li_at` cookie DOES remove the login wall on personal-profile post permalinks, but
  the authed page's og: tags are blank and the post text is NOT in the initial HTML
  (it loads via client-side XHR / Voyager). Simple regex-over-`commentary` does NOT
  extract it (those hits are schema definitions, not the post).
- **Voyager API — the definitive wall (2026-08):** `li_at` + a FRESH `JSESSIONID`
  (from a cookie-jar fetch of `https://www.linkedin.com/feed/`) sent as BOTH the
  `JSESSIONID` cookie AND the `Csrf-Token` header returns HTTP 200 from
  `/voyager/api/feed/updates/urn%3Ali%3Aactivity%3A<id>` — but the payload is
  `"This post cannot be displayed"` for personal-profile posts from a datacenter IP.
  The content is gated behind browser-context verification; cookies alone are NOT
  enough. Real options: real-browser automation (camoufox) or user copy-paste.
- **LinkedIn guest API IGNORES the `intern` keyword** — `keywords=data engineer intern`
  returns ordinary Data Engineer roles (loose matching). Internships only surface by
  filtering client-side (`intern|trainee|new grad|skillbridge` in the title) over
  broader windows (`f_TPR=r604800`/`r2592000`); they arrive in waves (e.g. TikTok /
  ByteDance "2027 Start" graduate postings cluster in late summer).
- **camoufox setup** (for the real-browser route to personal posts): install into the
  venv, `HOME=/opt/work/.home` MUST be the same for `camoufox fetch` AND launch
  (browser lives in `$HOME/.cache/camoufox`); correct API is
  `Camoufox(persistent_context=True, ...)` — `user_data_dir` as a top-level arg
  raises TypeError. Details in `references/linkedin-personal-posts-voyager.md`.

## Working style with this user (Hesham)
- Do NOT stop between steps to ask "ok?" / "continue?" — batch multiple tool calls per
  turn, use background processes + `process wait`, and return ONLY the final result.
  He has explicitly called out one-step-per-turn prompting as exhausting. Run the
  whole scan/verify/fix loop to completion before replying.
