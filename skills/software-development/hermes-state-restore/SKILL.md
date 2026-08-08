---
name: hermes-state-restore
description: "Restore or merge a Hermes state backup into an instance."
version: 1.0.0
metadata:
  hermes:
    tags: [hermes, backup, restore, merge, migration]
    related_skills: [hermes-backup, hermes-agent, github-repo-management]
---

# Restoring / Merging Hermes State from a Backup

The restore/merge side of Hermes backup. The `hermes-backup` skill (user-owned) covers the backup side; this skill covers bringing a backup INTO a (possibly fresh) instance.

**Trigger:** the user shares a git repo containing a snapshot of a Hermes `~/.hermes` directory (SOUL.md, memories/, skills/, cron/, state.db, config.yaml, ...) and asks to restore it, merge what's useful, or "take this one".

## 1. Identify the backup
- `ls -la`, `git log --oneline -10`, `git remote -v` → confirm it's a Hermes state backup and how recent it is.
- Recognizable layout: SOUL.md (+ SOUL.md.bak.*), config.yaml, memories/MEMORY.md + USER.md, skills/<cat>/<skill>/SKILL.md, cron/jobs.json + executions.db, state.db, sessions/, kanban.db, channel_directory.json, gateway_state.json, state/, .initialized. `.env` and `auth.json` must NOT be in the repo.

## 2. Baseline the current instance
- Check local `~/.hermes`: memories/ is often EMPTY, `cronjob list` often 0 jobs, SOUL.md often the stock default.
- A fresh instance → the backup is a pure upgrade; merge is safe with nothing to reconcile.

## 3. Merge vs skip decision table
**Merge** (only what's missing or clearly better):
- `memories/MEMORY.md` + `USER.md` — copy when local store is empty (chmod 600)
- `SOUL.md` — the backup's customized persona beats the default; first `cp SOUL.md SOUL.md.bak.<YYYYMMDD>` (this user wants timestamped backups before SOUL.md changes)
- `skills/` — only skills MISSING locally (recursive diff — see pitfall)
- `scripts/` — helper scripts (e.g. backup-to-github.sh; chmod +x)
- cron jobs — recreate from `cron/jobs.json` via the cronjob tool; the typical backup job is a `no_agent` script job (`script=backup-to-github.sh`, `schedule=every 720m`, `deliver=local`)

**Skip** (old-instance runtime state, not portable):
- `state.db`, `sessions/`, `kanban.db`, `cron/output/`, `executions.db` — chat history/task board of the OLD instance
- `config.yaml` — instance-specific; keep the local one
- `channel_directory.json`, `gateway_state.json`, `state/`, `gateway.*` — platform mappings + live runtime state
- `.env` / `auth.json` — NEVER restore credentials from a repo; the user recreates `.env` by hand

## 4. Sanitize before copying
- `grep -rlE 'ghp_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9]{20,}|xox[baprs]-' <backup>` → only placeholder hits (`ghp_xx...xxxx`, `***`) are acceptable.
- Inspect backup scripts for `REPO_URL` with an embedded PAT; install the placeholder form only, never a real token.

## 5. Copy, verify, finish
- Copy merged items; verify with the SAME recursive diff → zero missing; spot-check a skill loads via skill_view.
- Report the merge map (merged vs skipped) so the user knows what didn't carry over (chat history, config, credentials).

## Pitfalls
- **Top-level dir diff is NOT enough.** Category dirs (`creative/`, `research/`, ...) exist locally while individual skills under them are missing. Always diff every nested skill path: for each `<cat>/<skill>` in the backup, require local `<cat>/<skill>` to exist. (Real session: pass 1 copied 1 skill; the nested diff found 10 more.)
- Skills merged from the user's repo are user-owned content → recommend `hermes curator adopt <name>` before editing them; do not patch directly.
- If the merge ever pushes `state.db` to GitHub, it needs the two-layer secret redaction (see the `hermes-backup` skill, GH013 push protection) — but for local restores it's irrelevant.

## Support files
- `references/merge-worked-example.md` — full worked example: backup inventory, fresh baseline, the 1-vs-10 diff finding, final merge map, curator overlap notes.
