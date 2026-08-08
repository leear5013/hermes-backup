# Worked Example — Merging a Hermes Backup into a Fresh Instance (2026-08-08)

Session: user shared `https://github.com/leear5013/hermes-backup.git` ("take this one as you"),
chose **Merge it — pick what's useful, skip the rest**.

## Backup inventory (identified)
- `git log` showed `auto-backup: <ts> (N files)` commits twice daily — a cron-driven backup repo.
- Layout: SOUL.md (customized dual-mode persona) + SOUL.md.bak.20260804-215224, config.yaml,
  channel_directory.json, gateway_state.json, kanban.db, state.db (~15 MB), memories/{MEMORY,USER}.md,
  sessions/ (request dumps + sessions.json), cron/ (jobs.json + executions.db + output/),
  state/, skills/ (14 categories, 81 SKILL.md files), .initialized. No .env / auth.json. ✅ backup repo.

## Fresh-instance baseline
- `/data/.hermes/memories/` EMPTY; `cronjob list` → 0 jobs; SOUL.md = stock 513-byte default;
  scripts/ absent. → Pure upgrade, nothing to reconcile.

## Merge vs skip
- **Merged:** memories (both files, chmod 600), SOUL.md (with `cp → SOUL.md.bak.20260808` first),
  10 missing skills, `scripts/backup-to-github.sh` (chmod +x, placeholder REPO_URL).
- **Skipped:** state.db, sessions/, kanban.db, cron/output/, executions.db, config.yaml,
  channel_directory.json, gateway_state.json, state/ — old-instance runtime state.

## The 1-vs-10 diff finding (key lesson)
Pass 1: `for d in */` over backup `skills/` → only `hermes-model-identity` was missing at
category level → **1 skill copied, 13 "already present"**.
Pass 2: nested loop over `<cat>/<skill>/` → **10 more missing** under existing categories:
- creative/html-to-image, creative/language-learning-sprint
- note-taking/hermes-persona-management
- research/polymarket, research/reddit-content-retrieval, research/reddit-fetch, research/web-research
- social-media/facebook-group-monitoring, social-media/facebook-groups-monitoring
- software-development/hermes-backup

Lesson: category dirs exist locally while individual skills under them don't → always diff at
`<cat>/<skill>` granularity, never top-level only.

## Sanitization (passed)
- `grep -rlE 'ghp_...|sk-...|xox...'` over backup skills → only placeholders
  (`ghp_xx...xxxx`, `sk-xxx...xxxx` in hermes-agent/references/native-mcp.md docs).
- `backup-to-github.sh` used `https://***@github.com/USER/REPO.git` — placeholder form. ✅

## Cron job found in backup (recreated, not restored)
`cron/jobs.json` → one job: `hermes-backup-github`, `script=backup-to-github.sh`,
`no_agent=true`, `schedule=every 720m` (12h), `deliver=local` (silent), origin telegram.

## Curator overlap notes
- `facebook-group-monitoring` (singular) vs `facebook-groups-monitoring` (plural): near-duplicates;
  singular has richer references/scripts, plural's own body says "consider consolidating into one".
- `reddit-fetch` vs `reddit-content-retrieval`: overlap; reddit-content-retrieval is the more
  complete one (explicitly noted in its own pitfalls).
- `hermes-backup` skill itself: user-owned (came from user's repo) → recommend
  `hermes curator adopt software-development/hermes-backup` before any curation edits.
