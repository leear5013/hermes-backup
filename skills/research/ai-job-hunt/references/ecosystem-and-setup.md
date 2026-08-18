# Job-hunt ecosystem map — repos, tools, patterns (researched 2026-08-18)

## The toolchain tiers

| Tier | Tool | What it does | Reddit consensus |
|---|---|---|---|
| Strategy | santifer/career-ops (~64K★) | A-F JD scoring vs profile, per-JD ATS PDF CVs, tracker, 82 board providers, 40+ modes, human-in-the-loop | 🔥 top recommendation (r/hermesagent "Anyone using hermes agent for job search?" — top comment: "github find career-ops and configure it") |
| Hermes-native | starMagic/career-ops-hermes | career-ops ported to 17 Hermes skills; `./install.sh` → ~/.hermes/skills | the "get the skills" answer for Hermes users |
| Discovery | career-ops-docs | docs site source; `content/docs/free-ai-engine.mdx` = run career-ops for $0 (OpenCode+free provider, Ollama, OpenRouter `npm run or`) | |
| Scraping lib | speedyapply/JobSpy ★4.1K | LinkedIn/Indeed/Glassdoor/Google/ZipRecruiter scraper library (python-jobspy) | widely used; **needs proxies** — boards block datacenter IPs fast |
| CI pipeline | anandanair/job-scraper ★42 | GitHub Actions + Supabase + litellm (400+ providers) — scrape, resume parse (Gemini), JD-score, ATS PDF | |
| Egypt/MENA | ATAboukhadra/job_finder ★91 | **Only tool with Wuzzuf + Bayt + GulfTalent scrapers**; free API boards (Remotive/Arbeitnow/Himalayas/TheMuse/Adzuna/JSearch); sentence-transformers matching; Ollama LLM; LaTeX CV+cover letter; Flask dashboard; `python main.py pipeline` | |
| Browser layer | Playwright / computer-use (CUA) | the anti-bot answer everyone ends up using | consensus workaround |

## Reddit patterns (majority opinion)

1. **Skill + config pattern**: a job-hunt skill holding resume + config.yaml (target roles/locations) + cron scan → Telegram digest of matches.
2. **Anti-bot is THE blocker** — LinkedIn/Indeed/Glassdoor all block headless. Workarounds in order of preference: ATS APIs (Greenhouse/Ashby/Lever public, zero-token) → local parsers (SSR/stable HTML) → computer-use/CUA → paid proxies (BrightData etc).
3. **Quality over volume**: apply to 4.0+/5 scores only. Auto-apply bots (LazyApply, Loopcv, Sonara) are panned — blacklist risk, generic AI answers, refund complaints.
4. **Human-in-the-loop is the norm**: tools evaluate/draft/track; the user submits. career-ops hard-codes this ("never submits, sends, or clicks").

## Key career-ops internals (v1.26.0)

- **Mode router** (`.agents/skills/career-ops/SKILL.md`): JD text/URL → auto-pipeline; named modes: oferta, ofertas, contacto, deep, interview-prep, pdf, latex, cover, email, add, expand, training, project, tracker, apply, scan, discover, batch, patterns, offer-prep, titles, upskill, followup, outcome, update.
- **82 providers** (`providers/*.mjs`, table in `docs/SUPPORTED_JOB_BOARDS.md`): Greenhouse/Ashby/Lever auto-detect, Workday, SmartRecruiters, Eightfold, iCIMS, SAP SuccessFactors, Amazon, IBM, HN "Who is hiring?" (Algolia), 4dayweek, EchoJobs, Himalayas, Remotive, RemoteOK, Jobicy, TheHub, WTTJ (Algolia), plus regional (NoFluffJobs, JustJoin, GetOnBoard, VDAB, Interamt).
- **Plugins** (`plugins-registry/*.json`): docx export, google-calendar ingest, linkedin-alerts (parse LinkedIn alert emails from Gmail), obsidian, markdown, serper, tavily, theirstack, startup-boards, outlook-interviews.
- **Free engine paths**: OpenCode + free provider (recommended), Ollama local (16GB+ VRAM), `npm run or` (OpenRouter), any OpenAI-compatible endpoint. `docs/FREE_TIER.md`, `docs/RUNNING_ON_A_BUDGET.md`.
- **Scanner**: `node scan.mjs` — zero-token by default (local parsers + ATS APIs); `--verify` adds Playwright URL checks; `--since N` for recent postings.
- **Tracker**: `data/applications.md` markdown; `node set-status.mjs <#|company> <state>`; states Evaluated → Applied → Responded → Interview → Offer/Rejected/Discarded/SKIP.

## job_finder internals (the MENA one)

- `python main.py scrape|match|top|customize|answers|pipeline|daemon` — pipeline = scrape → match → customize → cover letter → form answers → email digest.
- `profile.yaml` (skills/titles/keywords/search) + `life-story.md` drive semantic matching (sentence-transformers).
- `scrapers/wuzzuf.py`, `scrapers/bayt.py`, `scrapers/gulftalent.py` — Egypt/MENA boards, no API keys.
- Output: `~/CV/applications/<company-role-slug>/` per application; `python main.py answers --url` prints form-fill guide.

## Setup pitfalls hit on this box

- career-ops postinstall runs `npx playwright install chromium --with-deps` → downloads into `~/.cache` = **/data/.cache** → ENOSPC (500MB cap). Fix: `PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1 npm install`, then `PLAYWRIGHT_BROWSERS_PATH=/opt/work/.pw-browsers npx playwright install chromium` (~656MB, overlay disk).
- `node doctor.mjs` is the source of truth for missing setup (cv.md, _profile.md, portals.yml, fonts, browser). Run it before debugging anything.
- Node v20 on this box: tracker SQLite index (node:sqlite) unavailable → warning only; markdown tracker works.
