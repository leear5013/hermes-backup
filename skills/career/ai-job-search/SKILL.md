---
name: ai-job-search
description: Use when hunting jobs/internships or job-search AI tooling.
version: 1.0.0
author: hermes-curator
license: MIT
metadata:
  hermes:
    tags: [career, jobs, career-ops, job-search, intern]
    related_skills: [reddit-content-retrieval, github-repo-management]
---

# AI-Assisted Job Search (career-ops ecosystem + how to research it)

## When to Use
- User asks about finding a first job/internship, or how AI agents can help apply.
- User asks about career-ops, job-search repos/skills, automated applications, or resume/portfolio tooling.
- Any "search Reddit/GitHub for what tools actually get people hired" task.

For: first intern/job hunting, automated application pipelines, resume/portfolio strategy. User: Hesham (Data Engineer, PySpark/Kafka/Flink/Airflow/Docker/AWS, Menoufia Univ, graduating June 2026) — wants ONE decisive shot, real community data over AI opinions.

## Verified top repos (2026-08, from r/hermesagent + GitHub API)

| Repo | Stars | What it is |
|---|---|---|
| `santifer/career-ops` | ~63-64k | THE job-search agent pipeline. Scans portals, scores listings A-F into 1.0-5.0, tailors ATS CVs per JD, tracks applications. Runs in AI coding CLIs (Claude Code, Codex, OpenCode, Antigravity). Author got "Head of Applied AI" off it; docs at career-ops.org + santifer.io/career-ops-system. Top-voted rec in r/hermesagent job-search thread |
| `starMagic/career-ops-hermes` | — | Career-ops PORTED to Hermes Agent — 17 native skills. Best fit for this user's Hermes stack |
| `santifer/career-ops-docs` | 54 | Documentation |
| `andrew-shwetzer/career-ops-plugin-*` | 467 | Claude Cowork plugin: 9 AI skills (evaluate postings, ATS resumes, company scans) |
| `shuheng-mo/career-ops-china`, `neveevol7/career-ops-cn`, `DavePenn/career-ops-cn` | 22-75 | China variants (Boss直聘/猎聘/拉勾) — useful pattern for regional portal adapters |
| `kylinfish/tw-house-ops` | 109 | Same ops-style pipeline for house hunting (shows the pattern generalizes) |

## Reddit consensus (r/hermesagent "Anyone using hermes agent for job search?" 1tit0jh, ~19pts)

- **career-ops** = the top community answer ("github find 'career-ops' and configure it. I have tried it, so far it feels good").
- **Working pattern used by multiple people**: resume + `config.yaml` (target job titles + locations) + a skill Hermes runs on cron → vacancy list pushed to Telegram; user redirects promising links to another bot that extracts JD + tailors + applies. Model: "leave a resume and config.yaml, works well".
- **Don't burn tokens on browser automation**: job sites are heavily anti-bot. Alternatives people use: agent-data.dev job-postings API (LinkedIn + Indeed + Wellfound planned, API not browser so no token waste), BrightData scraping tools, computer-use (CUA) for the stubborn sites.
- **Cautionary**: auto-apply spam tools (LazyApply etc.) are widely panned — generic AI answers, irrelevant applications, ATS blacklist risk. Tailored quality beats bulk volume. Some employers explicitly reject AI-written applications (e.g. Anthropic policy) — keep the human in the loop.
- **Real pain point**: job sites block headless browsers/egress IPs; a disabled user in the thread resorted to Hermes controlling THEIR mouse/browser. Egress IP gets flagged after ~3 requests — test with two identical requests before debugging prompts.

## Research method (reusable)

1. Discovery: `web_search("site:reddit.com/r/hermesagent <topic>")` works from this box (ddgs live). Arctic-Shift CANNOT discover old threads: `after=` pagination 400s, `limit=200` 400s (use 100), big subs (cscareerquestions) 422. Only the freshest ~100 posts per sub are reachable — older threads must come from web_search, then fetch by ID.
2. Fetch post + comments via Arctic-Shift by ID (`/posts/ids?ids=` + `/comments/tree?link_id=`).
3. GitHub API repo search: auth via `/data/.git-credentials` `x-access-token` with `Authorization: Bearer` (the `token` scheme 401s). Use a Python script, not shell one-liners with inline JSON (parser blocks them).
4. Clone repos to `/opt/work` (NEVER /data — 500MB cap; user correction). `git clone --depth 1` for big repos.
5. Majority check: count tool/skill mentions across threads (career-ops, skill+config.yaml pattern, API-over-browser) — that's the consensus signal.

## Pitfalls
- Auto-apply spam tools = community red flag. Recommend quality-over-volume pipelines (career-ops scores/tailors before applying).
- The user resents repeated plain "no" and endless loops: deliver the final repo list + how-to in ONE decisive message, don't present incremental options.
- Don't patch user-owned reddit skills from background curation (`hermes curator adopt` needed first) — see reddit-fetch / reddit-content-retrieval.
