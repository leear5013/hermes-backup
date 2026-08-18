# Repo inventory — AI job-hunt toolchain (verified 2026-08-18, cloned at /opt/work/repos/)

## santifer/career-ops (original) — v1.26.0
- ~64K★. Node >=18. `package.json` scripts: `scan`, `scan:full`, `scan:yc`, `scan:seeds` (yc,a16z), `or` (OpenRouter runner), `pdf`, `tracker`, `find`, `patterns`, `upskill`, `add`, `digest`, `update`.
- `providers/*.mjs` — **82 job-board providers**: Greenhouse, Ashby, Lever, Workday, Amazon, IBM, Oracle (ORC), SuccessFactors, Eightfold, iCIMS, Workable, SmartRecruiters, Personio, BambooHR, Rippling, Pinpoint, Recruitee, Jobvite, Breezy, Teamtailor, JibeApply, Radancy, Phenom, Cornerstone, SAP, a16z speedrun, Getro, HN "Who is hiring?", RemoteOK, Remotive, Himalayas, NoDesk, WeWorkRemotely, Working Nomads, Jobicy, EchoJobs, TheMuse, 4DayWeek, Arbeitnow, Arbeitsagentur, NoFluffJobs, JustJoin.it, Glints, Jobstreet/SEEK, GetOnBoard, getManfred, The Hub, WelcomeToTheJungle, Landing.jobs, CryptocurrencyJobs, HigherEdJobs, LaraJobs, Jobspresso, Senjob (Africa), SolidJobs, Flowxtra, Gem, softgarden, Avature, BeeSite, Comeet, Deutsche Bahn, Rheinmetall, TKMS, Dassault, Heckler&Koch, join.com, Meituan, Tencent, Alibaba + regional ones. Full table: `docs/SUPPORTED_JOB_BOARDS.md`.
- `modes/` — 40+ .md mode files + regional dirs (ar/da/de/es/fr/hi/id/it/ja/ko/nl/pl/pt/ru/tr/ua/zh). Modes: auto-pipeline, oferta, ofertas, contacto, deep, interview-prep, interview, pdf, latex, cover, email, add, expand, training, project, tracker, agent-inbox, apply, scan, discover, batch, patterns, offer-prep, titles, upskill, followup, outcome, update, reply-watch, eu-swe, eu-fintech.
- `.agents/skills/career-ops/SKILL.md` — router skill (197 lines) with full mode menu + Codex/agent invocation patterns.
- `config/profile.example.yml` — candidate (name/email/phone/location/linkedin/portfolio/github), target_roles (primary + archetypes with fit levels), narrative (headline, exit_story, superpowers, proof_points).
- Plugins registry: `plugins-registry/*.json` (docx, google-calendar, linkedin-alerts, markdown, obsidian, outlook-interviews, serper, startup-boards, tavily, theirstack) + `plugins/` (apify, gmail, notion).
- Human-in-the-loop: evaluates/drafts, never submits. Applies below 4.0/5 strongly discouraged.
- Free AI engine: `npm run or` (OpenRouter), or docs `content/docs/free-ai-engine.mdx` (OpenCode + free provider, Ollama local).

## starMagic/career-ops-hermes (Hermes port) — v1.9.0 port
- 17 skills in `skills/`: career-ops-apply, batch, compare, contact, deep, evaluate, followup, interview-prep, latex, patterns, pdf, pipeline, project, scan, shared, tracker, training. Each is a proper SKILL.md with `hermes:` frontmatter (tags, related_skills, upstream).
- `./install.sh [--force]` copies skills → `~/.hermes/skills/` (skips existing without --force).
- Ships a Web UI (launchd service, port 8790) + config/profile.example.yml.
- scan skill: 4-level discovery (Nivel 0 local parser → API → browser → web_search), zero-token scan.mjs default.

## santifer/career-ops-docs
- Next.js docs site source. Key content: `content/docs/free-ai-engine.mdx`, `content/docs/introduction/guides/*` (apply-for-a-job, batch-evaluate-offers, interview-modes, scan-job-portals, set-up-playwright), `content/docs/reference/modes/*`.

## andrew-shwetzer/career-ops-plugin-do-not-fork-currently-updating-v2-
- Claude Cowork plugin. 9 skills in `skills/`: track, scan, apply, research + more. 428K on disk.

## JobSpy (1abdelhalim fork of speedyapply/JobSpy — upstream ★4.1K)
- Jobs scraper library: LinkedIn, Indeed, Glassdoor, Google, ZipRecruiter, etc. Python (poetry). Needs proxies/residential IPs for LinkedIn/Indeed from datacenter IPs — gets blocked quickly otherwise.

## job-scraper (1abdelhalim fork of anandanair/job-scraper — upstream ★42)
- GitHub Actions-driven: scrape jobs → parse resume (pdfplumber + Gemini/litellm, 400+ providers) → score JD vs resume → track statuses → custom ATS PDF (reportlab). Supabase storage (init.sql in supabase_setup/). Secrets: LLM_API_KEY, SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY. Resume uploaded as `resume.pdf` to `resumes` bucket.

## job_finder (1abdelhalim fork of ATAboukhadra/job_finder — upstream ★91)
- "AI Apply" — the Egypt/MENA-relevant one. `scrapers/`: **wuzzuf.py, bayt.py, gulftalent.py** (Egypt/MENA boards, no key) + free API boards: Remotive, Arbeitnow, Himalayas, TheMuse, Adzuna (key), JSearch (RapidAPI), LinkedIn/Indeed/Glassdoor/StepStone scrapers, DDG internet search.
- Pipeline: scrape → semantic match (sentence-transformers vs life-story.md + profile.yaml) → tailor LaTeX CV per job (cv_templates/) → cover letter → form answers → digest email (Gmail app password) → Flask dashboard + daemon (default every 48h).
- CLI: `python main.py scrape|match|top|customize|answers|pipeline|daemon|init-profile`. Uses Ollama local LLM (qwen3.5:9b). requirements.txt includes python-jobspy, ddgs, sentence-transformers, flask, lxml.
- Has `Mohamed Abdelhalim Data Engineer.pdf` committed in repo root (the original author's own CV).
