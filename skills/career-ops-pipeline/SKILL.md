---
name: career-ops-pipeline
description: Use when user asks for URL inbox processor — extract JDs, evaluate, generate reports+PDFs, update tracker, parallel sub-agent workers.
version: 1.0.0
author: Hermes Agent (ported from santifer/career-ops)
license: MIT
metadata:
  hermes:
    tags: [career-ops, job-search, career, ai]
    related_skills: [career-ops-shared]
    upstream: https://github.com/santifer/career-ops
---

# Career Ops Pipeline — Career-Ops for Hermes

> **Ported from [santifer/career-ops](https://github.com/santifer/career-ops) v1.9.0.**
> This skill runs on Hermes Agent. Tool references are adapted for Hermes native tools.
> Original copyright: Santiago Fernández de Valderrama, MIT License.

Process job URLs stored in `data/pipeline.md`. The user adds URLs at any time and then executes `the corresponding Hermes skill` to process them all.

## Workflow

1. **Read** `data/pipeline.md` → search for `- [ ]` items in the "Pending" section
2. **For each pending URL**:
   a. Calculate the next sequential `REPORT_NUM` (read `reports/`, take the highest number + 1)
   b. **Extract JD** using Hermes browser tools (browser_navigate + browser_snapshot) → `web_extract` → `web_search`
   c. If the URL is not accessible → mark as `- [!]` with a note and continue
   d. **Execute full auto-pipeline**: Evaluation A-F → Report .md → PDF (if score >= `auto_pdf_score_threshold`) → Tracker
   e. **Move from "Pending" to "Processed"**: `- [x] #NNN | URL | Company | Role | Score/5 | PDF ✅/❌`

   **About the PDF gate (configurable):** Read `config/profile.yml` → `auto_pdf_score_threshold`. If the key does not exist, default to `3.0` (this mode's original gate). If the evaluation score is less than the threshold, skip PDF generation: write the report normally, show in the header `**PDF:** not generated — run the corresponding Hermes skill {company-slug} to create on demand`, and mark PDF ❌ in the tracker. If the score is ≥ threshold, generate the PDF as usual.

   **Tuning it:** Generating a tailored PDF costs ~30–60s per entry (Hermes browser tools launch + HTML render) and produces files that often go unused — most roles score in the 2.x/3.x range and never reach the application stage. Raise `auto_pdf_score_threshold` (e.g. `4.0`) to write only the report for marginal offers and produce the PDF on demand via `the corresponding Hermes skill {slug}`; set `0` to generate one for every offer. Both modes (Path A `the corresponding Hermes skill` and Path B `batch/batch-runner.sh`) read the same key, so behavior is identical regardless of which path processes an offer.
3. **If there are 3+ pending URLs**, launch agents in parallel (Agent tool with `run_in_background`) to maximize speed.
4. **At the end**, show summary table:

```
| # | Company | Role | Score | PDF | Recommended action |
```

## Format of pipeline.md

```markdown
## Pending
- [ ] https://jobs.example.com/posting/123
- [ ] https://boards.greenhouse.io/company/jobs/456 | Company Inc | Senior PM
- [!] https://private.url/job — Error: login required

## Processed
- [x] #143 | https://jobs.example.com/posting/789 | Acme Corp | AI PM | 4.2/5 | PDF ✅
- [x] #144 | https://boards.greenhouse.io/xyz/jobs/012 | BigCo | SA | 2.1/5 | PDF ❌
```

## Intelligent JD detection from URL

1. **Hermes browser tools (preferred):** `browser_navigate` + `browser_snapshot`. Works with all SPAs.
2. **`web_extract` (fallback):** For static pages or when Hermes browser tools is unavailable.
3. **`web_search` (last resort):** Search in secondary portals that index the JD.

**Special cases:**
- **LinkedIn**: May require login → mark `[!]` and ask the user to paste the text
- **PDF**: If the URL points to a PDF, read it directly with the `read_file`
- **`local:` prefix**: Read the local file. Example: `local:jds/linkedin-pm-ai.md` → read `jds/linkedin-pm-ai.md`

## Automatic numbering

1. List all files in `reports/`
2. Extract the number from the prefix (e.g., `142-medispend...` → 142)
3. New number = maximum found + 1

## Source synchronization

Before processing any URL, verify sync:
```bash
node cv-sync-check.mjs
```
If there is a desynchronization, warn the user before continuing.

