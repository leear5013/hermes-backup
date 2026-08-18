---
name: ai-job-hunt
description: Use when setting up AI job-hunt tooling.
---

# AI-Assisted Job Hunt

Helping the user (Hesham, Data Engineer, Cairo, graduating June 2026) land a first intern/job with AI tooling. Covers the recommended toolchain, where it lives on this box, and how to wire it up.

## The Reddit consensus (researched 2026-08-18)

- **#1 recommended repo: `santifer/career-ops`** (~64K★). Top answer in r/hermesagent's "Anyone using hermes agent for job search?" thread. A-F scoring of JDs vs your profile, per-JD tailored ATS CV PDFs, application tracker, 82 job-board providers (Greenhouse, Ashby, Lever, Workday, Amazon, HN Who's Hiring, etc). Human-in-the-loop: evaluates/drafts, never auto-submits.
- **Native Hermes port: `starMagic/career-ops-hermes`** — 17 skills (scan, compare, tracker, followup, interview-prep, apply, pdf...), `./install.sh` copies them into `~/.hermes/skills/`.
- Anti-bot walls on LinkedIn/Indeed/Glassdoor are the #1 pain point; workarounds = computer-use (CUA), local parsers, or ATS APIs (public/zero-token).
- Reddit pans spray-and-pray auto-apply bots (LazyApply & co) — blacklist risk, generic answers. Apply manually to 4.0+/5 scores only.

## Repos already cloned on this box (under /opt/work/repos/ — never /data)

- `career-ops` (original, v1.26.0, 82 providers, 40+ modes, node >=18)
- `career-ops-hermes` (Hermes port; skills/ has SKILL.md files with `hermes:` frontmatter)
- `career-ops-docs` (docs site source; `content/docs/free-ai-engine.mdx` = free-engine guide)
- `career-ops-plugin-do-not-fork-currently-updating-v2-` (Claude Cowork plugin, 9 skills)
- `JobSpy` (1abdelhalim fork of speedyapply/JobSpy ★4.1K upstream — LinkedIn/Indeed/Glassdoor/Google scrapers; needs proxies to avoid blocks)
- `job-scraper` (1abdelhalim fork of anandanair/job-scraper ★42 — GitHub Actions + Supabase + litellm resume-parse pipeline)
- `job_finder` (1abdelhalim fork of ATAboukhadra/job_finder ★91 — **the Egypt/MENA one**: scrapers for Wuzzuf, Bayt, GulfTalent + free API boards Remotive/Arbeitnow/Himalayas/TheMuse; local LLM via Ollama; LaTeX CV + cover letter pipeline; Flask dashboard)

## Setup workflow for this user

1. `cd /opt/work/repos/career-ops-hermes && ./install.sh` → installs 17 career-ops skills into ~/.hermes/skills (idempotent; --force to overwrite)
2. Fill `config/profile.yml` (target_roles: Data Engineer, PySpark/Kafka/Flink/Airflow; narrative; proof_points) + `cv.md` in the career-ops root; also `cp modes/_profile.template.md modes/_profile.md` and `cp templates/portals.example.yml portals.yml` — `node doctor.mjs` lists exactly what's missing (✓/⚠ checklist)
3. `npm install` in career-ops root — **MUST set `PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1`** or the postinstall tries to download chromium into /data/.cache (500MB cap → ENOSPC). Then `PLAYWRIGHT_BROWSERS_PATH=/opt/work/.pw-browsers npx playwright install chromium` (~656MB, lands on the 1.8TB overlay). Export that env var before every node run that needs the browser (scan --verify, pdf).
4. Run via any agent CLI — OpenCode (user's stack) or Hermes CLI work; no Claude subscription needed (`npm run or` = OpenRouter runner, or free-ai-engine docs)
5. Loop: `scan` (portals) → `oferta` (evaluate URL/JD) → `pdf` (ATS CV) → `tracker` / `followup`
6. Add job_finder's Wuzzuf/Bayt/GulfTalent scrapers for Egyptian/MENA boards (`python main.py scrape --boards wuzzuf bayt` style)
7. JobSpy only if LinkedIn/Indeed coverage needed — pair with proxies/residential IPs

## Current deployment state (verified 2026-08-18)

- 17 career-ops skills installed in /data/.hermes/skills (scan, evaluate, compare, tracker, apply, followup, interview-prep, batch, contact, deep, latex, pdf, pipeline, patterns, project, shared, training)
- career-ops workspace at /opt/work/repos/career-ops: `node doctor.mjs` clean except Node v20 warning — tracker's SQLite index wants Node >=22.5 (markdown tracker works fine without it, non-blocking)
- config/profile.yml + cv.md + modes/_profile.md + portals.yml all filled with Hesham's profile (Data Engineer, Cairo, RASD/decrypt-bot/Hermes-ops proof points)
- npm deps installed, 0 vulnerabilities; chromium at /opt/work/.pw-browsers

## Daily digest cron (deployed 2026-08-18)

- Script: `/data/.hermes/scripts/career_ops_daily.sh` — `cd /opt/work/repos/career-ops && node scan.mjs --since 2`, then greps titles for targets minus seniority terms. Prints ONLY new relevant matches to stdout.
- Cron: Hermes cronjob, `no_agent=true` + `script=career_ops_daily.sh` + `deliver=origin`, schedule `0 8 * * *` (job 56927fe99007). **Watchdog pattern: non-empty stdout → Telegram digest; empty stdout → silent day, no spam.**
- Filter recipe: include `data (engineer|analyst)|big data|etl|spark|kafka|flink|airflow|junior|entry|intern|graduate|pipeline engineer|devops`, exclude `Senior|Lead|Staff|Principal|Director|Manager`.
- Scan output is ~90% senior/irrelevant on big boards (Allianz etc.) — the title filter is what makes the digest usable.
- User's scope (his words): Data Engineer **and** DevOps, **internships included**, open to remote positions worldwide (not city-bound; e.g. Duplin), wants LinkedIn-posted roles included if reachable.

## Job sources & anti-bot reality (verified 2026-08-18)

- **ATS APIs are free and zero-token**: Greenhouse, Ashby, Lever, Workday, BambooHR, SmartRecruiters, Recruitee, Workable, Pinpoint, Rippling, iCIMS... — career-ops providers cover them. This is the no-anti-bot path (the #1 Reddit pain point is LinkedIn/Indeed/Glassdoor blocking headless agents).
- **LinkedIn guest jobs endpoints return HTTP 200 from datacenter IPs**: `linkedin.com/jobs/search?keywords=<kw>&f_WT=2&start=0&count=10` (~270KB HTML) and `linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords=<kw>&start=0` (~27KB) both answered 200 with a browser UA. Parse-into-listings status UNVERIFIED as of 2026-08-18 (session ended at the 200 check). Try this route before reaching for MCP/linkedin-mcp-server.
- **HN "Who is hiring?"** monthly thread via Algolia API (`hn.algolia.com/api/v1/search?tags=front_page` reachable) — career-ops has a `hackernews` provider.
- **Remotive API** (`remotive.com/api/remote-jobs?search=X`) free and working from this box; results skew senior/contract.
- JobSpy (user's fork) is the library fallback for LinkedIn/Indeed/Glassdoor — needs proxies/residential IPs at scale.

## Finding more job-hunt tooling on Reddit (discovery pattern)

When asked "what does Reddit recommend for X":
1. `web_search` with `site:reddit.com/r/<sub> <keywords>` (works from datacenter IPs; returns post URLs + IDs)
2. Fetch posts/comments by ID via Arctic-Shift (`api/posts/ids?ids=<id>`, `api/comments/search?link_id=<id>`) — never text-search Arctic-Shift (broken)
3. r/hermesagent weekly threads ("What have you done with Hermes Agent this week") are a goldmine for use-case + skill recommendations
4. GitHub search for the named repos (auth via /data/.git-credentials, Bearer scheme) to get stars/upstream/fork status

## Pitfalls

- career-ops is a filter, not a spammer: recommend against applying below 4.0/5; first evaluations are weak until the profile is fed (CV, career story, proof points).
- LinkedIn/Indeed scraping without proxies = quick IP blocks; prefer ATS APIs or local parsers.
- The user's forks (JobSpy, job-scraper, job_finder) have 0 stars — treat as forks of the starred upstreams, verify upstream before recommending.
- career-ops has NO auto-apply by design; a few forks add it — flag the ethics/blacklist tradeoff when the user asks for auto-apply.
- Node <22.5: `node:sqlite` missing → tracker SQLite index unavailable; markdown tracker still works. Check with `node doctor.mjs` before debugging phantom failures.
- **Playwright browser path**: any `npx playwright install` run without PLAYWRIGHT_BROWSERS_PATH set writes to /data/.cache → ENOSPC under the 500MB cap. Always target /opt/work/.pw-browsers and export it in the same shell as the node commands that use the browser.

## Reddit discovery — Arctic-Shift limits (verified 2026-08-18)

The `reddit-content-retrieval` / `reddit-fetch` / `reddit-research` skills (user-owned, not patchable here) say `limit=200` and pagination work — **they don't**:
- `limit=100` is the hard ceiling; `limit=200`/`150` → HTTP 400 on most subs. Some big/old subs (cscareerquestions, EngineeringResumes, resumes) → HTTP 422 at any size.
- `after=<id>` / `after=t3_<id>` pagination → HTTP 400 (verified r/hermesagent). Only the most recent ~100 posts per sub are reachable — a rolling window, not an archive. Older threads: find IDs via `web_search site:reddit.com/r/<sub> <topic>` then fetch by ID (`/api/posts/ids`).
- 400/422 arrive as `{"data": null}` — scripts that check `len(data)` report "0 posts" for subs that actually have content. Always inspect the `error` key. Pace requests (4-8s sleeps, retry with backoff; transient "Timeout. Maybe slow down" recovers).

## Support files
- `references/repo-inventory.md` — per-repo details: providers, modes, skills list, key files.
- `references/ecosystem-and-setup.md` — toolchain tier map, Reddit consensus patterns, career-ops internals (mode router, providers, plugins, free engines), job_finder MENA internals, setup pitfalls (ENOSPC/Playwright).
